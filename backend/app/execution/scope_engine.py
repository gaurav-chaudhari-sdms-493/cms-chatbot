import re
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.retrieval.vector_store import VectorSearchEngine
from app.entities.extractor import EntityExtractor
from app.entities.resolver import EntityResolver
from app.execution.executor import QueryExecutor

from app.execution.retriever import HybridTemplateRetriever
from app.execution.llm_selector import OpenRouterTemplateSelector
from app.db.models import UnmatchedScopeQueryLog

logger = logging.getLogger("pmc_chatbot.scope_engine")

MARATHI_INDICATORS = [
    "पुण्यात", "तक्रारी", "प्रलंबित", "विभाग", "कोथरूड", "दाखवा", "किती", "आहेत",
    "पाणी", "कचरा", "रस्ते", "अधिकारी", "कामगिरी", "सध्या", "या महिन्यात", "गेल्या",
    "kiti", "aahet", "dakjava", "dakhava", "madhe", "sadhya", "sagLyat"
]


class ScopeAnswerEngine:
    """Template-based answering engine for PMC Commissioner Scope Categories A–P."""

    @staticmethod
    def is_marathi_query(query_text: str) -> bool:
        """Detects if query is in Marathi (Devanagari or Marathlish)."""
        q_lower = query_text.lower()
        return any(ind in q_lower or ind in query_text for ind in MARATHI_INDICATORS)

    @staticmethod
    def check_out_of_scope(query_text: str) -> Optional[str]:
        """Detects out-of-scope requests and returns a polite refusal message."""
        q_lower = query_text.lower()

        # 1. Data Modification attempts (DO NOT block read-only status queries like "what is the status of complaint")
        mod_keywords = [
            "transfer complaint", "reassign complaint", "delete complaint", "delete ticket",
            "change status to", "update status to", "mark as resolved", "mark as closed",
            "suspend officer", "fire officer", "cancel complaint"
        ]
        if any(kw in q_lower for kw in mod_keywords):
            return (
                "# ⚠️ Action Not Allowed (Read-Only Mode)\n\n"
                "> [!IMPORTANT]\n"
                "> I am a **read-only grievance analytics assistant** for PMC senior leadership. "
                "I cannot modify data, transfer complaints, close tickets, or initiate HR actions.\n\n"
                "Please use the official PMC CMS administrative workflow portal to perform status updates or reassignments."
            )

        # 2. HR & Payroll queries
        hr_keywords = ["salary", "payroll", "disciplinary", "suspend officer", "fire officer", "fire him", "fire her", "terminate officer"]
        if any(kw in q_lower for kw in hr_keywords):
            return (
                "# ⚠️ Out of Scope (HR / Payroll)\n\n"
                "> \n"
                "> Officer payroll, personal HR records, and disciplinary proceedings are **outside the scope** of PMC grievance intelligence analytics."
            )

        # 3. Non-PMC General Knowledge / Politics
        general_keywords = ["election", "political", "politics", "weather", "cricket score", "who is the prime minister", "tell me a joke", "who will win"]
        if any(kw in q_lower for kw in general_keywords):
            return (
                "# ⚠️ Out of Scope Query\n\n"
                "> \n"
                "> This AI chatbot is strictly dedicated to **Pune Municipal Corporation (PMC) Grievance Management, Officer Performance, and Zonal Intelligence Analytics**."
            )

        return None

    @classmethod
    def answer_scope_query(
        cls,
        query_text: str,
        metadata_session: Session,
        pmc_session: Session,
        session_history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Attempts to answer query using OpenRouter RRF hybrid retrieval over Categories A–P.
        Supports multi-turn follow-up questions, entity binding, and out-of-scope refusal.
        """
        # 1. Quick check for explicit Out-of-Scope
        refusal_msg = cls.check_out_of_scope(query_text)
        if refusal_msg:
            return {
                "status": "REFUSED",
                "content": refusal_msg,
                "sql_used": None,
                "template_id": None
            }

        # 2. Hybrid RRF Retrieval (E5 Dense Vector + Lexical BM25)
        candidate_tuples = HybridTemplateRetriever.get_top_candidates(
            query_text=query_text,
            metadata_session=metadata_session,
            top_k=5
        )

        if not candidate_tuples:
            return None

        candidate_templates = [tpl for tpl, _ in candidate_tuples]
        candidate_details = [
            {
                "template_id": tpl.template_id,
                "intent": tpl.intent,
                "question_template": tpl.question_template,
                "score": round(float(score), 4) if score is not None else 0.0
            }
            for tpl, score in candidate_tuples
        ]

        # 3. OpenRouter LLM Evaluation & Parameter Resolution
        llm_eval = OpenRouterTemplateSelector.evaluate_query(
            user_query=query_text,
            candidate_templates=candidate_templates,
            session_history=session_history,
            pmc_session=pmc_session
        )

        status = llm_eval.get("status", "EXECUTE")

        # Handle Out-of-Scope refusal & log for scope expansion backlog
        if status == "OUT_OF_SCOPE":
            reason = llm_eval.get("out_of_scope_reason") or "Query is outside PMC read-only grievance query scope."
            
            # Log valid PMC query that couldn't be matched to existing templates for developers to review
            try:
                cand_ids = [t.get("template_id") for t in candidate_details if isinstance(t, dict)]
                unmatched_log = UnmatchedScopeQueryLog(
                    query_text=query_text,
                    reason=reason,
                    candidate_template_ids=cand_ids
                )
                metadata_session.add(unmatched_log)
                metadata_session.commit()
                logger.info(f"Logged unmatched PMC scope query ID #{unmatched_log.id}: '{query_text}'")
            except Exception as e:
                metadata_session.rollback()
                logger.warning(f"Could not log unmatched query: {e}")

            return {
                "status": "REFUSED",
                "content": f"# ℹ️ Out of Scope Query\n\n> [!NOTE]\n> {reason}",
                "sql_used": None,
                "template_id": None,
                "candidate_templates": candidate_details
            }

        # Handle Interactive Follow-Up Question
        if status == "NEEDS_FOLLOWUP":
            followup = llm_eval.get("followup_question") or "Please specify which department or ward you would like to view statistics for."
            return {
                "status": "FOLLOW_UP",
                "content": f"### ❓ Follow-Up Question\n\n{followup}",
                "sql_used": None,
                "template_id": llm_eval.get("selected_template_id"),
                "candidate_templates": candidate_details
            }

        # Status == "EXECUTE"
        template_id = llm_eval.get("selected_template_id") or candidate_templates[0].template_id
        bound_params = llm_eval.get("bound_parameters", {})

        # Ensure limit fallback
        if "limit" not in bound_params:
            bound_params["limit"] = 10

        # 4. Securely execute template SQL
        try:
            exec_res = QueryExecutor.execute_template(
                template_id=template_id,
                parameters=bound_params,
                metadata_session=metadata_session,
                pmc_session=pmc_session,
                max_rows=50
            )
        except Exception as err:
            logger.warning(f"Template execution failed for {template_id}: {err}")
            return None

        data = exec_res.get("data", [])
        columns = exec_res.get("columns", [])
        sql_used = exec_res.get("sql_template", "")

        # 5. Format Executive Report
        is_mar = cls.is_marathi_query(query_text)
        markdown_content = cls.format_executive_report(
            query_text=query_text,
            template_intent=candidate_templates[0].intent if candidate_templates else "general_query",
            columns=columns,
            data=data,
            is_marathi=is_mar
        )

        return {
            "status": "SUCCESS",
            "content": markdown_content,
            "sql_used": exec_res.get("sql_used") or exec_res.get("sql_template"),
            "template_id": template_id,
            "candidate_templates": candidate_details,
            "execution_time_ms": exec_res.get("execution_time_ms")
        }

    @staticmethod
    def format_executive_report(
        query_text: str,
        template_intent: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        is_marathi: bool = False
    ) -> str:
        """Formats tabular DB output into executive-ready Markdown per Commissioner specifications."""
        if not data:
            if is_marathi:
                return "### ℹ️ माहिती\n\nदिलेल्या शोधासाठी कोणतीही प्रलंबित/माहिती नोंदी आढळल्या नाहीत."
            return "### ℹ️ Analytics Result\n\nNo records found matching the specified criteria."

        lines = []

        # Filter out _mar columns from header display if duplicate
        display_cols = [c for c in columns if not c.endswith("_mar")]
        if not display_cols:
            display_cols = columns

        # Identify numeric count columns & calculate actual total sum
        count_cols = [
            c for c in display_cols
            if any(k in c.lower() for k in ['received', 'total', 'count', 'pending', 'resolved', 'assigned', 'breached', 'open', 'complaints'])
        ]
        primary_num_col = count_cols[0] if count_cols else None

        if primary_num_col:
            total_sum = sum(
                row.get(primary_num_col, 0)
                for row in data
                if isinstance(row.get(primary_num_col), (int, float))
            )
            formatted_num = f"{total_sum:,}"
            num_label = primary_num_col.replace("_", " ").title()
            if is_marathi:
                lines.append(f"### 📊 एकूण {num_label}: **{formatted_num}**\n")
            else:
                lines.append(f"### 📊 Total {num_label}: **{formatted_num}**\n")

        # 2. Markdown Table Formatting
        headers = " | ".join([c.replace("_", " ").title() for c in display_cols])
        divider = " | ".join(["---"] * len(display_cols))
        lines.append(f"| {headers} |")
        lines.append(f"| {divider} |")

        for row in data:
            row_vals = []
            for c in display_cols:
                v = row.get(c, "")
                if isinstance(v, (int, float)):
                    row_vals.append(f"{v:,}")
                else:
                    # Clean string values: strip newlines, carriage returns, and replace unescaped pipes
                    v_str = str(v or "").replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("|", "╱").strip()
                    row_vals.append(v_str if v_str else "-")
            lines.append("| " + " | ".join(row_vals) + " |")

        lines.append("\n---")

        # 3. Accurate Executive Insight
        # Find non-numeric, non-date dimension column for grouping insight
        dim_cols = [
            c for c in display_cols
            if not any(k in c.lower() for k in ['month', 'date', 'time', 'year', 'created', 'id', 'pct', 'rate', 'percentage'])
            and not isinstance(data[0].get(c), (int, float))
        ]

        if primary_num_col and data:
            max_row = max(data, key=lambda r: (r.get(primary_num_col) or 0) if isinstance(r.get(primary_num_col), (int, float)) else 0)
            max_val = max_row.get(primary_num_col)

            if dim_cols:
                top_dim_col = dim_cols[0]
                top_name = str(max_row.get(top_dim_col, "-"))
                if top_name and top_name != "-":
                    if is_marathi:
                        lines.append(f"> 💡 **कार्यकारी निष्कर्ष:** सर्वात जास्त प्रमाण **{top_name}** ({max_val:,} तक्रारी) मध्ये नोंदवले गेले आहे.\n")
                    else:
                        lines.append(f"> 💡 **Executive Insight:** Highest volume recorded under **{top_name}** ({max_val:,} complaints).\n")
            else:
                # Time series / Date dimension only
                date_col = [c for c in display_cols if any(k in c.lower() for k in ['month', 'date', 'year'])][0] if any(any(k in c.lower() for k in ['month', 'date', 'year']) for c in display_cols) else None
                if date_col:
                    top_date = str(max_row.get(date_col, "-"))
                    if is_marathi:
                        lines.append(f"> 💡 **कार्यकारी निष्कर्ष:** सर्वात जास्त प्रमाण **{top_date}** ({max_val:,} तक्रारी) दरम्यान नोंदवले गेले आहे.\n")
                    else:
                        lines.append(f"> 💡 **Executive Insight:** Highest volume recorded in period **{top_date}** ({max_val:,} complaints).\n")

        # 4. Attach legacy data caveat for resolution time queries
        if "resolution" in template_intent or "days" in template_intent or "time" in template_intent:
            lines.append("> ⚠️ *Note: Average resolution time statistics are calculated based on active post-go-live CMS era data.*")

        return "\n".join(lines)
