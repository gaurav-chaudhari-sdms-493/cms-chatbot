import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from rapidfuzz import fuzz, process

from app.api.llm_client import call_openrouter_api

logger = logging.getLogger("pmc_chatbot.agents.entity_resolver")

SYNONYM_MAPS: Dict[str, Dict[str, str]] = {
    "department_master": {
        "water": "Water Supply",
        "water supply": "Water Supply",
        "pani": "Water Supply",
        "पानी": "Water Supply",
        "पाणी": "Water Supply",
        "पाणीपुरवठा": "Water Supply",
        "road": "Road",
        "roads": "Road",
        "khadde": "Road",
        "pothole": "Road",
        "potholes": "Road",
        "रस्ते": "Road",
        "रस्ते विभाग": "Road",
        "garbage": "Solid Waste Management",
        "kachra": "Solid Waste Management",
        "कचरा": "Solid Waste Management",
        "swachhata": "Solid Waste Management",
        "arogya": "Health",
        "health": "Health",
        "आरोग्य": "Health",
        "drainage": "Drainage",
        "gutter": "Drainage",
        "गटार": "Drainage",
        "ड्रेनेज": "Drainage",
        "electrical": "Electrical",
        "light": "Electrical",
        "विद्युत": "Electrical",
        "लाइट": "Electrical",
        "building": "Building Permission",
        "permission": "Building Permission",
        "बांधकाम": "Building Permission",
        "encroachment": "Encroachment",
        "atirkaman": "Encroachment",
        "अतिक्रमण": "Encroachment",
        "garden": "Garden",
        "tree": "Garden",
        "उद्यान": "Garden"
    },
    "ward_master": {
        "kothrud": "Kothrud",
        "कोथरूड": "Kothrud",
        "kothrud bavdhan": "Kothrud",
        "hadapsar": "Hadapsar",
        "हडपसर": "Hadapsar",
        "aundh": "Aundh",
        "औंध": "Aundh",
        "sinhagad": "Sinhagad Road",
        "सिंहगड": "Sinhagad Road",
        "nagar road": "Nagar Road",
        "नगर रोड": "Nagar Road",
        "kasba": "Kasba",
        "कसबा": "Kasba",
        "dhankawadi": "Dhankawadi",
        "धनकवडी": "Dhankawadi",
        "bibwewadi": "Bibwewadi",
        "बिबवेवाडी": "Bibwewadi",
        "wanowrie": "Wanowrie",
        "वानवडी": "Wanowrie",
        "bhavani peth": "Bhavani Peth",
        "भवानी पेठ": "Bhavani Peth",
        "shivajinagar": "Shivajinagar",
        "शिवाजीनगर": "Shivajinagar",
        "yerwada": "Yerwada",
        "येरवाडा": "Yerwada",
        "dhole patil": "Dhole Patil Road",
        "ढोले पाटील": "Dhole Patil Road",
        "warje": "Warje",
        "वारजे": "Warje"
    },
    "status_master": {
        "completed": "Resolved",
        "complete": "Resolved",
        "resolved": "Resolved",
        "solved": "Resolved",
        "done": "Resolved",
        "closed": "Closed - Not Valid",
        "closed invalid": "Closed - Not Valid",
        "pending": "Pending",
        "open": "Pending",
        "unresolved": "Pending",
        "active": "Pending",
        "escalated": "Escalated",
        "reopened": "Reopened",
        "assigned": "Assigned",
        "registered": "Registered",
        "processing": "Processing",
        "pending info": "Pending Info",
        "transferred": "Transferred",
        "पूर्ण": "Resolved",
        "सोडवलेल्या": "Resolved",
        "प्रलंबित": "Pending",
        "उघड्या": "Pending",
        "वाढवलेल्या": "Escalated"
    }
}


class EntityResolverAgent:
    """Specialized Agent for Multilingual Entity Extraction, Fuzzy Master Resolution, & Parameter Binding."""

    @staticmethod
    def extract_regex_entities(query_text: str) -> Dict[str, Any]:
        """Extracts regex-based numeric limits, complaint IDs, priority, and date range parameters."""
        extracted: Dict[str, Any] = {}

        # 1. Complaint Number Pattern (e.g. CMS20260001234)
        cms_match = re.search(r'\b(CMS\d{8,14})\b', query_text, re.IGNORECASE)
        if cms_match:
            extracted["complaint_number"] = cms_match.group(1).upper()

        # 2. Limit pattern (e.g. "top 10", "top 5", "10 oldest", "worst 5", "5 best")
        limit_match = re.search(r'\b(?:top|worst|best|oldest|first)?\s*(\d+)\s*(?:officers|complaints|categories|wards|locations|departments)?\b', query_text, re.IGNORECASE)
        if limit_match:
            try:
                val = int(limit_match.group(1))
                if 1 <= val <= 100:
                    extracted["limit"] = val
            except ValueError:
                pass

        # 3. Priority controlled vocabulary matching
        priority_match = re.search(r'\b(high|medium|low|critical|normal)\b', query_text, re.IGNORECASE)
        if priority_match:
            extracted["priority"] = priority_match.group(1).upper()

        # 4. Multilingual Date & Time Window Expressions
        query_lower = query_text.lower()
        now = datetime.now()

        if "this month" in query_lower or "या महिन्यात" in query_lower or "is mahine" in query_lower:
            extracted["date_from"] = datetime(now.year, now.month, 1).isoformat()
            extracted["date_to"] = now.isoformat()
        elif "last month" in query_lower or "गेल्या महिन्यात" in query_lower or "pichle mahine" in query_lower:
            first_of_this_month = datetime(now.year, now.month, 1)
            last_month_end = first_of_this_month - timedelta(days=1)
            first_of_last_month = datetime(last_month_end.year, last_month_end.month, 1)
            extracted["date_from"] = first_of_last_month.isoformat()
            extracted["date_to"] = first_of_this_month.isoformat()
        elif "this week" in query_lower or "या आठवड्यात" in query_lower or "is week" in query_lower or "is hafte" in query_lower:
            start_of_week = now - timedelta(days=now.weekday())
            extracted["date_from"] = datetime(start_of_week.year, start_of_week.month, start_of_week.day).isoformat()
            extracted["date_to"] = now.isoformat()
        elif "last 30 days" in query_lower or "गेल्या ३० दिवसात" in query_lower or "30 days" in query_lower:
            extracted["date_from"] = (now - timedelta(days=30)).isoformat()
            extracted["date_to"] = now.isoformat()
        elif "last 6 months" in query_lower or "गेल्या ६ महिन्यांचा" in query_lower or "6 months" in query_lower:
            extracted["date_from"] = (now - timedelta(days=180)).isoformat()
            extracted["date_to"] = now.isoformat()

        return extracted

    @staticmethod
    def resolve_reference(
        query_text: str,
        source_table: str,
        source_id_col: str,
        source_label_col: str,
        pmc_session: Session,
        threshold: float = 65.0
    ) -> Optional[Dict[str, Any]]:
        """Queries target master table and matches substrings/synonyms using rapidfuzz."""
        if not source_table or not source_id_col or not source_label_col:
            return None

        approved_tables = {
            "department_master", "ward_master", "category_master",
            "sub_category_master", "status_master", "zone_master", "prabhag_master"
        }
        if source_table not in approved_tables:
            return None

        try:
            sql = text(f"SELECT {source_id_col}, {source_label_col} FROM {source_table} ORDER BY {source_id_col} ASC;")
            records = pmc_session.execute(sql).fetchall()
        except Exception:
            return None

        if not records:
            return None

        label_to_id = {}
        candidate_labels = []

        for r in records:
            rec_id = r[0]
            rec_label = str(r[1])
            if rec_label not in label_to_id:
                label_to_id[rec_label] = rec_id
                candidate_labels.append(rec_label)

        query_lower = query_text.lower()
        if source_table in SYNONYM_MAPS:
            for syn_key, target_keyword in SYNONYM_MAPS[source_table].items():
                if syn_key in query_lower:
                    for label, id_val in label_to_id.items():
                        if target_keyword.lower() in label.lower():
                            return {"id": id_val, "label": label, "confidence": 1.0}

        for label, id_val in label_to_id.items():
            if label.lower() in query_lower:
                return {"id": id_val, "label": label, "confidence": 1.0}

        match_result = process.extractOne(query_text, candidate_labels, scorer=fuzz.partial_ratio)
        if match_result and match_result[1] >= threshold:
            best_label = match_result[0]
            return {"id": label_to_id[best_label], "label": best_label, "confidence": round(match_result[1], 2)}

        return None

    @classmethod
    def contextualize_query(
        cls,
        user_query: str,
        session_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        If session_history exists, rewrites short follow-up or ambiguous queries
        (e.g., 'all complains', 'yes', 'resolved ones', 'how many in kothrud')
        into a complete, self-contained standalone question incorporating past context.
        """
        if not session_history:
            return user_query

        words = user_query.strip().split()
        is_short_followup = len(words) <= 6 or any(w.lower() in ["yes", "yeah", "ha", "ho", "sure", "all", "complaints", "complains", "resolved", "pending", "show", "details"] for w in words)
        
        if not is_short_followup:
            return user_query

        history_lines = []
        for m in session_history[-6:]:
            line = f"{m.get('sender')}: {m.get('content')}"
            if m.get('sql_used'):
                line += f" [SQL: {m.get('sql_used')}]"
            history_lines.append(line)

        history_str = "\n".join(history_lines)

        prompt = f"""You are a Query Contextualizer for Pune Municipal Corporation (PMC) Grievance System.
Given the previous conversation history and the latest user query, rewrite the latest query into a standalone, self-contained search question.
Ensure all active entity context (such as department e.g. Road, category e.g. Potholes, ward e.g. Kothrud, status e.g. pending/resolved) from history is preserved in the rewritten question.

EXAMPLES:
1. History:
   user: pothole complaints
   agent: ? Follow-Up Question: How many pending complaints for pothole?
   user: yes
   agent: Total Complaint Count: 282 [SQL: SELECT ... WHERE department_id = 2 ...]
   Latest User Query: "all complains"
   Rewritten Question: all complaints for potholes in Road department

2. History:
   user: water supply complaints in kothrud
   Latest User Query: "show resolved"
   Rewritten Question: resolved water supply complaints in Kothrud ward

CONVERSATION HISTORY:
{history_str}

LATEST USER QUERY: "{user_query}"

Respond strictly with ONLY the rewritten standalone question string (no explanations, no quotes):"""

        try:
            msg = call_openrouter_api(prompt, models=["meta-llama/llama-3.3-70b-instruct", "google/gemini-2.5-flash"])
            if msg and isinstance(msg, dict):
                rewritten = msg.get("content", "").strip().strip('"').strip("'")
                if rewritten and len(rewritten) > 2 and rewritten.lower() != user_query.lower():
                    logger.info(f"Contextualized user query from '{user_query}' -> '{rewritten}'")
                    return rewritten
        except Exception as err:
            logger.warning(f"Failed to contextualize query: {err}")

        return user_query

    @classmethod
    def evaluate_query_with_llm(
        cls,
        user_query: str,
        candidate_templates: List[Any],
        session_history: Optional[List[Dict[str, Any]]] = None,
        pmc_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Invokes OpenRouter LLM to select best matching template and extract bound parameters."""
        templates_summary = []
        for tpl in candidate_templates:
            placeholders_info = []
            for p in getattr(tpl, 'placeholders', []):
                p_name = getattr(p, 'placeholder_name', p.get('placeholder_name') if isinstance(p, dict) else '')
                p_type = getattr(p, 'data_type', p.get('data_type') if isinstance(p, dict) else '')
                p_req = getattr(p, 'required', p.get('required') if isinstance(p, dict) else False)
                placeholders_info.append(f"{p_name} ({p_type}, required={p_req})")

            templates_summary.append({
                "template_id": tpl.template_id,
                "intent": tpl.intent,
                "question_pattern": tpl.question_template,
                "placeholders": placeholders_info
            })

        history_str = ""
        if session_history:
            history_lines = []
            for m in session_history[-6:]:
                line = f"{m.get('sender')}: {m.get('content')}"
                if m.get('sql_used'):
                    line += f" [SQL: {m.get('sql_used')}]"
                history_lines.append(line)
            history_str = "\n".join(history_lines)

        prompt = f"""
You are the OpenRouter Query Selector and Entity Resolution AI for Pune Municipal Corporation (PMC) Grievance System.

OFFICER QUESTION: "{user_query}"

PREVIOUS CHAT HISTORY:
{history_str if history_str else "None"}

CANDIDATE CANONICAL TEMPLATES:
{json.dumps(templates_summary, indent=2)}

SYSTEM RULES:
1. ONLY declare "OUT_OF_SCOPE" if question explicitly asks to modify/delete data, initiate HR actions, or non-PMC general trivia.
2. MULTI-TURN CONTEXT & CONTEXT INHERITANCE:
   - When previous conversation history established a specific entity focus (such as department e.g. "Road", category e.g. "Potholes", ward e.g. "Kothrud", or status), and the officer asks a follow-up ("all complains", "yes", "resolved ones", "how many", "show breakdown"), YOU MUST INHERIT those entity values into `bound_parameters`.
   - E.g. If previous turns were about pothole complaints (Road department) and officer says "all complains", set `bound_parameters` to include {{"department": "Road"}} or {{"category": "Potholes"}} and select the template for department/category complaints.
3. Select template ID whose functional intent best matches the officer's query and accumulated context.
4. Extract bound parameters from question & chat history. Always extract target entity terms specified by the user (e.g. for "pending complaints for glass", extract {{"category": "glass"}} or {{"department": "glass"}}), even if you are unsure whether it exists in master tables.
5. If candidate template matches and has no missing required parameters, set status to "EXECUTE".

Respond strictly with valid JSON:
{{
  "status": "EXECUTE" | "NEEDS_FOLLOWUP" | "OUT_OF_SCOPE",
  "selected_template_id": "<ID>",
  "bound_parameters": {{"limit": 10}},
  "followup_question": "Question..." (if NEEDS_FOLLOWUP),
  "out_of_scope_reason": "Reason..." (if OUT_OF_SCOPE)
}}
"""
        try:
            msg = call_openrouter_api(prompt, models=["meta-llama/llama-3.3-70b-instruct", "google/gemini-2.5-flash"])
            if msg and isinstance(msg, dict):
                content = msg.get("content", "").strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                data = json.loads(content)
                return {
                    "status": data.get("status", "EXECUTE"),
                    "selected_template_id": data.get("selected_template_id"),
                    "bound_parameters": data.get("extracted_parameters") or data.get("bound_parameters") or {},
                    "followup_question": data.get("followup_question"),
                    "out_of_scope_reason": data.get("out_of_scope_reason")
                }
        except Exception as err:
            logger.warning(f"LLM Parameter Evaluation Error: {err}")

        # Fallback to first candidate template
        default_tpl = candidate_templates[0] if candidate_templates else None
        regex_params = cls.extract_regex_entities(user_query)
        return {
            "status": "EXECUTE",
            "selected_template_id": default_tpl.template_id if default_tpl else None,
            "bound_parameters": regex_params,
            "followup_question": None,
            "out_of_scope_reason": None
        }
