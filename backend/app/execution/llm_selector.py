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
1. ONLY declare "OUT_OF_SCOPE" if the question explicitly asks to modify/delete data (e.g. transfer/reassign ticket, close complaint), initiate HR actions, or non-PMC political trivia.
2. All analytical, comparison, and reporting queries (e.g. "give me the list of departments", "channel wise resolution rate", "compare channels", "top categories") ARE IN SCOPE. Match them to the candidate template list.
3. IMPORTANT CANONICAL TEMPLATE MAPPINGS:
   - Template CMP_M01 handles ALL source channel queries: channel breakdown, channel resolution rates, best channel, channel comparison, and "all channels" / "सर्व चॅनेलची तुलना" requests.
   - Template CMP_K03 handles general department list queries ("give me the list of departments", "list all departments", "सर्व विभागांची यादी").
4. If a candidate template has NO required placeholders (like CMP_M01 for channel breakdown or CMP_K03 for department list), set status to "EXECUTE" immediately — DO NOT ask follow-up questions.
5. Extract parameter values from the officer's question or chat history for required placeholders. Only set status to "NEEDS_FOLLOWUP" if a REQUIRED parameter (e.g. specific ward or officer name) is genuinely missing.
6. If all required parameters are resolved or template has no required parameters, set status to "EXECUTE".

Respond strictly with a valid JSON object matching this exact schema:
{{
  "status": "EXECUTE" | "NEEDS_FOLLOWUP" | "OUT_OF_SCOPE",
  "selected_template_id": "CMP_M01" (or matching template ID),
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
                        if k in ["department", "ward", "zone", "category", "sub_category"]:
                            table_name = f"{k}_master"
                            label_col = f"{k}_name" if k in ["department", "ward", "category", "zone"] else "name"
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
