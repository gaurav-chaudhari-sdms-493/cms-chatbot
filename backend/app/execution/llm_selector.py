import json
import logging
from typing import Dict, Any, List, Optional
from app.api.llm_client import call_openrouter_api
from app.entities.resolver import EntityResolver
from app.entities.extractor import EntityExtractor

logger = logging.getLogger("pmc_chatbot.llm_selector")

class OpenRouterTemplateSelector:
    """
    Uses OpenRouter API to select the canonical query template, resolve entity placeholders,
    generate interactive follow-up questions for missing required parameters, or refuse out-of-scope requests.
    """

    @classmethod
    def evaluate_query(
        cls,
        user_query: str,
        candidate_templates: List[Any],
        session_history: Optional[List[Dict[str, Any]]] = None,
        pmc_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluates user query and candidate templates.
        Returns dict with:
          - status: 'EXECUTE' | 'NEEDS_FOLLOWUP' | 'OUT_OF_SCOPE'
          - selected_template_id: Optional[str]
          - bound_parameters: Dict[str, Any]
          - followup_question: Optional[str]
          - out_of_scope_reason: Optional[str]
        """
        # 1. First check quick out-of-scope rules (data edit, HR, election, general knowledge)
        q_lower = user_query.lower()
        is_mod = any(w in q_lower for w in ["transfer", "reassign", "close ticket", "update status", "suspend officer", "salary", "election", "who will win"])
        if is_mod:
            return {
                "status": "OUT_OF_SCOPE",
                "selected_template_id": None,
                "bound_parameters": {},
                "followup_question": None,
                "out_of_scope_reason": "Requested action is outside PMC read-only grievance query scope (e.g. data modification, HR action, or non-PMC general knowledge)."
            }

        # 2. Format candidate templates context for OpenRouter
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

        # 3. Format multi-turn context
        history_str = ""
        if session_history:
            history_str = "\n".join([f"{m.get('sender')}: {m.get('content')}" for m in session_history[-6:]])

        prompt = f"""
You are the OpenRouter Query Selector and Entity Resolution AI for Pune Municipal Corporation (PMC) Grievance System.

OFFICER QUESTION: "{user_query}"

PREVIOUS CHAT HISTORY:
{history_str if history_str else "None"}

CANDIDATE CANONICAL TEMPLATES:

{json.dumps(templates_summary, indent=2)}

SYSTEM RULES:
1. ONLY declare "OUT_OF_SCOPE" if the question explicitly asks to modify/delete data (e.g. transfer/reassign ticket, close complaint), initiate HR/payroll actions, or non-PMC general trivia (e.g. weather, elections).
2. ALL PMC municipal grievance analytics, complaint statistics, channel comparisons, officer performance metrics, aging trends, and location/prabhag breakdowns ARE IN SCOPE.
3. DYNAMIC TEMPLATE SELECTION:
   - Carefully review the `intent`, `question_pattern`, `retrieval_text`, and `placeholders` for each candidate template in CANDIDATE CANONICAL TEMPLATES.
   - Select the candidate template ID whose functional scope and intent best match the officer's query.
   - If a candidate template has no required placeholders or only optional placeholders (e.g., optional department, ward, or limit), set status to "EXECUTE" immediately — DO NOT return "NEEDS_FOLLOWUP" or "OUT_OF_SCOPE" if the candidate template matches.
4. PARAMETER EXTRACTION:
   - Extract parameter values from the officer's question AND chat history for required or optional placeholders (e.g., department name, ward name, complaint number, limit, age days).
   - If the officer does NOT explicitly specify a numeric limit (e.g. "top 5", "top 10", "first 20") in their query, DO NOT set a "limit" parameter — leave "limit" as null so all matching rows are returned without truncation.
   - If the user provides a specific ticket/complaint ID (e.g. WA32811, CMS20260005678), extract it as "complaint_number" and match to the specific complaint lookup template.
5. MULTI-TURN & AFFIRMATIVE RESPONSE RESOLUTION:
   - If previous chat history shows the AI asked a follow-up question and officer responds with affirmative words ("yes", "yeah", "sure", "ok", "proceed", "do it", "show me", "ha", "ho") or an intent phrase ("complaint of this ward", "pending complaints", "show complaints"), YOU MUST set status to "EXECUTE".
   - Inherit the entity (ward name or department name) from the history into extracted_parameters (e.g. {{"ward": "Hadapsar - Mundhwa"}} or {{"department": "Traffic"}}).
   - Match to the relevant candidate template for that entity and DO NOT return NEEDS_FOLLOWUP.
6. ENTITY-ONLY INPUTS:
   - If the officer inputs ONLY an entity name (e.g., "Hadapsar - Mundhwa" or "Water Supply") without explicit intent, match to the candidate template for pending complaints of that entity, extract the parameter, and set status to "EXECUTE".
7. MULTILINGUAL & MARATHLISH TERMINOLOGY:
   - "tasks", "takrari", "kaam", "complaints", "grievances" all refer to PMC complaints.
   - "yething", "madhye", "chya", "til" are Marathi location prepositional indicators. E.g., "kasba yething completed tasks" means completed/resolved complaints in Kasba ward.
8. STATUS PLACEHOLDER FLEXIBILITY:
   - The `status` placeholder in templates (such as CMP_A02) handles ALL complaint statuses including "completed", "resolved", "pending", "open", "escalated", "closed", "assigned", "reopened".
   - NEVER declare a question "OUT_OF_SCOPE" for asking about completed/resolved/escalated complaints if a template with a `status` placeholder (such as CMP_A02) is present in CANDIDATE CANONICAL TEMPLATES. Select the template (e.g. CMP_A02), extract status (e.g. "completed") and entity (e.g. ward="Kasba"), and set status to "EXECUTE".

Respond strictly with a valid JSON object matching this exact schema:
{{
  "status": "EXECUTE" | "NEEDS_FOLLOWUP" | "OUT_OF_SCOPE",
  "selected_template_id": "<ID of selected candidate template>",
  "confidence": 0.95,
  "extracted_parameters": {{"limit": 10}},
  "followup_question": "Which specific department would you like to view?" (only if status is NEEDS_FOLLOWUP),
  "out_of_scope_reason": "Explanation..." (only if status is OUT_OF_SCOPE)
}}
"""

        try:
            openrouter_msg = call_openrouter_api(prompt, models=["google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct"])
            if openrouter_msg and isinstance(openrouter_msg, dict):
                resp_text = openrouter_msg.get("content", "")
                json_str = resp_text.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()

                parsed = json.loads(json_str)
                status = parsed.get("status", "EXECUTE")
                template_id = parsed.get("selected_template_id")
                extracted = parsed.get("extracted_parameters", {})

                # Resolve extracted parameter strings to Master DB IDs if pmc_session is provided
                bound_params = {}
                if pmc_session:
                    for k, v in extracted.items():
                        if k in ["department", "ward", "zone", "category", "sub_category", "status"]:
                            table_name = f"{k}_master"
                            label_col = f"{k}_name" if k in ["department", "ward", "category", "zone", "status"] else "name"
                            ref = EntityResolver.resolve_reference(
                                query_text=str(v),
                                source_table=table_name,
                                source_id_col="id",
                                source_label_col=label_col,
                                pmc_session=pmc_session,
                                threshold=50.0
                            )
                            if ref:
                                bound_params[k] = ref["id"]
                                bound_params[f"{k}_id"] = ref["id"]
                            else:
                                bound_params[k] = v
                        else:
                            bound_params[k] = v
                else:
                    bound_params = extracted

                return {
                    "status": status,
                    "selected_template_id": template_id,
                    "bound_parameters": bound_params,
                    "followup_question": parsed.get("followup_question"),
                    "out_of_scope_reason": parsed.get("out_of_scope_reason")
                }
        except Exception as err:
            logger.warning(f"OpenRouterTemplateSelector JSON parsing failed: {err}")

        # Fallback to candidate #1 if OpenRouter call returned direct execution
        top_template = candidate_templates[0] if candidate_templates else None
        return {
            "status": "EXECUTE",
            "selected_template_id": top_template.template_id if top_template else None,
            "bound_parameters": {},
            "followup_question": None,
            "out_of_scope_reason": None
        }
