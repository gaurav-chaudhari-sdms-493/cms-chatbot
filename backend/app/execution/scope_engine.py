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

        # 1. Data Modification attempts
        mod_keywords = ["transfer", "reassign", "close", "delete", "update status", "change status", "assign to", "mark as resolved", "suspend"]
        if any(kw in q_lower for kw in mod_keywords) and any(verb in q_lower for verb in ["complaint", "ticket", "officer", "this", "to", "roads", "dept"]):
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
                "> [!NOTE]\n"
                "> Officer payroll, personal HR records, and disciplinary proceedings are **outside the scope** of PMC grievance intelligence analytics."
            )

        # 3. Non-PMC General Knowledge / Politics
        general_keywords = ["election", "political", "politics", "weather", "cricket score", "who is the prime minister", "tell me a joke", "who will win"]
        if any(kw in q_lower for kw in general_keywords):
            return (
                "# ℹ️ Out of Scope Query\n\n"
                "> [!NOTE]\n"
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

        # Handle Out-of-Scope refusal
        if status == "OUT_OF_SCOPE":
            reason = llm_eval.get("out_of_scope_reason") or "Query is outside PMC read-only grievance query scope."
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

        # 1. Headline Number Callout
        first_row = data[0]
        primary_val = None
        for val in first_row.values():
            if isinstance(val, (int, float)):
                primary_val = val
                break

        if primary_val is not None:
            formatted_num = f"{primary_val:,}"
            if is_marathi:
                lines.append(f"### 📊 एकूण/मुख्य संख्या: **{formatted_num}**\n")
            else:
                lines.append(f"### 📊 Key Summary Metric: **{formatted_num}**\n")

        # 2. Markdown Table Formatting
        # Filter out _mar columns from header display if duplicate
        display_cols = [c for c in columns if not c.endswith("_mar")]
        if not display_cols:
            display_cols = columns

        headers = " | ".join([c.replace("_", " ").title() for c in display_cols])
        divider = " | ".join(["---"] * len(display_cols))
        lines.append(f"| {headers} |")
        lines.append(f"| {divider} |")

        for row in data[:25]:  # limit to top 25 rows for concise view
            row_vals = []
            for c in display_cols:
                v = row.get(c, "")
                if isinstance(v, (int, float)):
                    row_vals.append(f"{v:,}")
                else:
                    row_vals.append(str(v or ""))
            lines.append("| " + " | ".join(row_vals) + " |")

        lines.append("\n---")

        # 3. 1-Line Executive Insight
        top_name = str(first_row.get(display_cols[0], "Primary Category/Ward"))
        if is_marathi:
            lines.append(f"> 💡 **कार्यकारी निष्कर्ष:** सर्वात जास्त प्रमाण **{top_name}** मध्ये नोंदवले गेले आहे.\n")
        else:
            lines.append(f"> 💡 **Executive Insight:** Highest volume/metric recorded under **{top_name}**.\n")

        # 4. Attach legacy data caveat for resolution time queries
        if "resolution" in template_intent or "days" in template_intent or "time" in template_intent:
            lines.append("> ⚠️ *Note: Average resolution time statistics are calculated based on active post-go-live CMS era data.*")

        return "\n".join(lines)
