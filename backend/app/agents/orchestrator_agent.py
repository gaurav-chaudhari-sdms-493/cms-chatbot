import time
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import sync_pmc_engine
from app.db.dynamic_schema import fetch_live_database_schema
from app.agents.scope_agent import ScopeAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.entity_resolver_agent import EntityResolverAgent
from app.agents.sql_executor_agent import SQLExecutorAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.fastmcp_agent import FastMCPAgent

logger = logging.getLogger("pmc_chatbot.agents.orchestrator")
PMC_SessionMaker = sessionmaker(bind=sync_pmc_engine)


class MasterOrchestratorAgent:
    """
    Master Orchestrator Agent for PMC Grievance Intelligence.
    Coordinates sub-agents (Scope, Retriever, EntityResolver, SQLExecutor, Synthesis, FastMCP)
    to process natural language questions end-to-end.
    """

    @classmethod
    def process_query(
        cls,
        query_text: str,
        metadata_session: Session,
        session_history: Optional[List[Dict[str, Any]]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Main multi-agent query processing pipeline.
        Returns unified dictionary with markdown_report, sql_used, template_id, candidate_templates, execution_time_ms, etc.
        """
        start_time = time.time()
        pmc_session = PMC_SessionMaker()

        try:
            # Step 1: ScopeAgent Out-of-Scope Pre-Check
            refusal_msg = ScopeAgent.check_out_of_scope(query_text)
            if refusal_msg:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "REFUSED",
                    "content": refusal_msg,
                    "sql_used": "",
                    "template_id": None,
                    "candidate_templates": [],
                    "execution_time_ms": elapsed_ms,
                    "retry_count": 0
                }

            # Step 2: Contextualize user query using chat history & Hybrid Semantic Candidate Search
            search_query = query_text
            if session_history:
                search_query = EntityResolverAgent.contextualize_query(query_text, session_history)

            candidate_tuples = RetrieverAgent.get_top_candidates(
                query_text=search_query,
                metadata_session=metadata_session,
                top_k=5
            )

            if search_query != query_text:
                raw_tuples = RetrieverAgent.get_top_candidates(
                    query_text=query_text,
                    metadata_session=metadata_session,
                    top_k=3
                )
                existing_ids = {tpl.template_id for tpl, _ in candidate_tuples}
                for tpl, score in raw_tuples:
                    if tpl.template_id not in existing_ids:
                        candidate_tuples.append((tpl, score))

            candidate_templates = [tpl for tpl, _ in candidate_tuples] if candidate_tuples else []
            candidate_details = [
                {
                    "template_id": tpl.template_id,
                    "intent": tpl.intent,
                    "question_template": tpl.question_template,
                    "score": round(float(score), 4) if score is not None else 0.0
                }
                for tpl, score in candidate_tuples
            ] if candidate_tuples else []

            # Step 3: EntityResolverAgent & LLM Evaluation
            eval_res = None
            if candidate_templates:
                eval_res = EntityResolverAgent.evaluate_query_with_llm(
                    user_query=search_query,
                    candidate_templates=candidate_templates,
                    session_history=session_history,
                    pmc_session=pmc_session
                )

            status = eval_res.get("status") if eval_res else "UNMATCHED"

            # Handle LLM-determined Out-of-Scope refusal
            if status == "OUT_OF_SCOPE":
                reason = eval_res.get("out_of_scope_reason") or "Query is outside PMC read-only grievance query scope."
                ScopeAgent.log_unmatched_query(
                    query_text=query_text,
                    reason=reason,
                    candidate_ids=[c.get("template_id") for c in candidate_details],
                    metadata_session=metadata_session
                )
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "REFUSED",
                    "content": f"# ℹ️ Out of Scope Query\n\n> [!NOTE]\n> {reason}",
                    "sql_used": "",
                    "template_id": None,
                    "candidate_templates": candidate_details,
                    "execution_time_ms": elapsed_ms,
                    "retry_count": 0
                }

            # Handle Interactive Follow-Up Question
            if status == "NEEDS_FOLLOWUP":
                followup = eval_res.get("followup_question") or "Please specify which department or ward you would like to view statistics for."
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "FOLLOW_UP",
                    "content": f"### ❓ Follow-Up Question\n\n{followup}",
                    "sql_used": "",
                    "template_id": eval_res.get("selected_template_id"),
                    "candidate_templates": candidate_details,
                    "execution_time_ms": elapsed_ms,
                    "retry_count": 0
                }

            # Step 4: SQLExecutorAgent Safe Template Execution
            if status == "EXECUTE" and eval_res and eval_res.get("selected_template_id"):
                template_id = eval_res.get("selected_template_id")
                bound_params = eval_res.get("bound_parameters", {})
                if "limit" not in bound_params:
                    bound_params["limit"] = 10

                # Resolve text parameters to master table primary key IDs
                ref_mappings = {
                    "department": ("department_master", "id", "department_name", "department_id"),
                    "ward": ("ward_master", "id", "ward_name", "ward_id"),
                    "status": ("status_master", "id", "status_name", "status_id"),
                    "zone": ("zone_master", "id", "zone_name", "zone_id"),
                    "category": ("category_master", "id", "category_name", "category_id")
                }

                unresolved_entities = []

                for param_key, (tbl, id_col, label_col, target_key) in ref_mappings.items():
                    val = bound_params.get(param_key) or bound_params.get(target_key)
                    if val is not None:
                        if isinstance(val, str) and not val.isdigit():
                            res = EntityResolverAgent.resolve_reference(
                                query_text=str(val),
                                source_table=tbl,
                                source_id_col=id_col,
                                source_label_col=label_col,
                                pmc_session=pmc_session
                            )
                            if res and "id" in res:
                                bound_params[target_key] = res["id"]
                                bound_params[param_key] = res["id"]
                            else:
                                bound_params[target_key] = None
                                bound_params[param_key] = None
                                if param_key in ["department", "ward", "category", "zone"]:
                                    unresolved_entities.append(str(val))
                        elif isinstance(val, (int, str)) and str(val).isdigit():
                            bound_params[target_key] = int(val)
                            bound_params[param_key] = int(val)

                # Check if query_text specifies an entity term after 'for', 'about', 'under', or 'in' not matched in master tables
                import re
                target_match = re.search(r'\b(?:for|about|under|in)\s+([a-zA-Z0-9_\s]{3,25})\b', query_text, re.IGNORECASE)
                if target_match:
                    potential_term = target_match.group(1).strip()
                    stopwords = {"pending", "resolved", "closed", "open", "today", "yesterday", "all", "total", "more", "pune", "pmc", "complaint", "complaints"}
                    if potential_term.lower() not in stopwords:
                        found_in_master = False
                        for tbl, id_col, label_col in [
                            ("department_master", "id", "department_name"),
                            ("ward_master", "id", "ward_name"),
                            ("category_master", "id", "category_name"),
                            ("zone_master", "id", "zone_name")
                        ]:
                            res = EntityResolverAgent.resolve_reference(
                                query_text=potential_term,
                                source_table=tbl,
                                source_id_col=id_col,
                                source_label_col=label_col,
                                pmc_session=pmc_session
                            )
                            if res and "id" in res:
                                found_in_master = True
                                break
                        if not found_in_master and potential_term not in unresolved_entities:
                            unresolved_entities.append(potential_term)

                try:
                    exec_res = SQLExecutorAgent.execute_template(
                        template_id=template_id,
                        parameters=bound_params,
                        metadata_session=metadata_session,
                        pmc_session=pmc_session,
                        max_rows=50
                    )
                    data = exec_res.get("data", [])
                    columns = exec_res.get("columns", [])
                    sql_used = exec_res.get("sql_template", "")

                    is_mar = ScopeAgent.is_marathi_query(query_text)
                    markdown_report = SynthesisAgent.generate_report(
                        query_text=query_text,
                        sql_used=sql_used,
                        columns=columns,
                        data=data,
                        is_marathi=is_mar,
                        unresolved_entities=unresolved_entities if unresolved_entities else None
                    )

                    elapsed_ms = round((time.time() - start_time) * 1000, 2)
                    return {
                        "status": "SUCCESS",
                        "content": markdown_report,
                        "sql_used": exec_res.get("sql_template"),
                        "template_id": template_id,
                        "candidate_templates": candidate_details,
                        "execution_time_ms": elapsed_ms,
                        "retry_count": 0
                    }
                except Exception as exec_err:
                    logger.warning(f"SQLExecutorAgent template execution failed for '{template_id}': {exec_err}")

            # Step 5: FastMCPAgent Autonomous Tool Loop Fallback
            logger.info("Handing off query to FastMCPAgent autonomous tool-calling loop...")
            live_schema = fetch_live_database_schema()
            history_str = ""
            if session_history:
                history_lines = []
                for m in session_history[-6:]:
                    line = f"{m.get('sender')}: {m.get('content')}"
                    if m.get('sql_used'):
                        line += f" [SQL: {m.get('sql_used')}]"
                    history_lines.append(line)
                history_str = "\n".join(history_lines)

            effective_question = search_query if search_query != query_text else query_text

            sql_used, columns, rows, steps_taken = FastMCPAgent.run_tool_loop(
                schema_context=live_schema,
                question=effective_question,
                max_steps=max_retries + 2,
                history_context=history_str
            )

            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            if sql_used and len(rows) > 0:
                markdown_report = SynthesisAgent.synthesize_with_llm(
                    query_text=query_text,
                    sql_used=sql_used,
                    columns=columns,
                    rows=rows
                )
                return {
                    "status": "SUCCESS",
                    "content": markdown_report,
                    "sql_used": sql_used,
                    "template_id": None,
                    "candidate_templates": candidate_details,
                    "execution_time_ms": elapsed_ms,
                    "retry_count": steps_taken - 1
                }
            else:
                is_mar = ScopeAgent.is_marathi_query(query_text)
                fallback_report = SynthesisAgent.generate_report(
                    query_text=query_text,
                    sql_used=sql_used or "-- Query returned 0 matching database records",
                    columns=columns,
                    data=[],
                    is_marathi=is_mar
                )
                return {
                    "status": "SUCCESS",
                    "content": fallback_report,
                    "sql_used": sql_used or "-- No matching records found",
                    "template_id": None,
                    "candidate_templates": candidate_details,
                    "execution_time_ms": elapsed_ms,
                    "retry_count": max_retries
                }

        finally:
            pmc_session.close()
