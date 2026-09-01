import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.models import UnmatchedScopeQueryLog

logger = logging.getLogger("pmc_chatbot.agents.scope")

MARATHI_INDICATORS = [
    "पुण्यात", "तक्रारी", "प्रलंबित", "विभाग", "कोथरूड", "दाखवा", "किती", "आहेत",
    "पाणी", "कचरा", "रस्ते", "अधिकारी", "कामगिरी", "सध्या", "या महिन्यात", "गेल्या",
    "kiti", "aahet", "dakjava", "dakhava", "madhe", "sadhya", "sagLyat"
]


class ScopeAgent:
    """Specialized Agent for Scope Evaluation, Out-of-Scope Refusal, & Language Detection."""

    @staticmethod
    def is_marathi_query(query_text: str) -> bool:
        """Detects if query is in Marathi (Devanagari script or Marathlish)."""
        q_lower = query_text.lower()
        return any(ind in q_lower or ind in query_text for ind in MARATHI_INDICATORS)

    @classmethod
    def check_out_of_scope(cls, query_text: str) -> Optional[str]:
        """Detects out-of-scope requests and returns a polite refusal message."""
        q_lower = query_text.lower()

        # 1. Data Modification attempts
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
    def log_unmatched_query(
        cls,
        query_text: str,
        reason: str,
        candidate_ids: List[str],
        metadata_session: Session
    ) -> None:
        """Logs PMC queries that could not be matched to canonical templates for developer scope expansion backlog."""
        try:
            unmatched_log = UnmatchedScopeQueryLog(
                query_text=query_text,
                reason=reason,
                candidate_template_ids=candidate_ids
            )
            metadata_session.add(unmatched_log)
            metadata_session.commit()
            logger.info(f"Logged unmatched PMC scope query ID #{unmatched_log.id}: '{query_text}'")
        except Exception as e:
            metadata_session.rollback()
            logger.warning(f"Could not log unmatched scope query: {e}")
