from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from rapidfuzz import fuzz, process

SYNONYM_MAPS: Dict[str, Dict[str, str]] = {
    "department_master": {
        # English & Romanized Marathi & Devanagari -> Canonical Keyword
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


class EntityResolver:
    """Resolves categorical string spans against database master tables using fuzzy matching & multilingual synonyms."""

    @staticmethod
    def resolve_reference(
        query_text: str,
        source_table: str,
        source_id_col: str,
        source_label_col: str,
        pmc_session: Session,
        threshold: float = 65.0
    ) -> Optional[Dict[str, Any]]:
        """
        Queries target master table, matches substrings of query_text against labels & synonyms using rapidfuzz,
        and returns canonical { "id": id_val, "label": label_val } if score >= threshold.
        """
        if not source_table or not source_id_col or not source_label_col:
            return None

        approved_tables = {
            "department_master",
            "ward_master",
            "category_master",
            "sub_category_master",
            "status_master",
            "zone_master",
            "prabhag_master"
        }
        if source_table not in approved_tables:
            return None

        # Fetch records from target master table ordered by primary key ID ASC
        try:
            sql = text(f"SELECT {source_id_col}, {source_label_col} FROM {source_table} ORDER BY {source_id_col} ASC;")
            records = pmc_session.execute(sql).fetchall()
        except Exception:
            return None

        if not records:
            return None

        # Build candidate maps: label -> id (preserving lowest primary key ID for duplicate names)
        label_to_id = {}
        candidate_labels = []

        for r in records:
            rec_id = r[0]
            rec_label = str(r[1])
            if rec_label not in label_to_id:
                label_to_id[rec_label] = rec_id
                candidate_labels.append(rec_label)

        # 1. Check Synonym Map First
        query_lower = query_text.lower()
        if source_table in SYNONYM_MAPS:
            for syn_key, target_keyword in SYNONYM_MAPS[source_table].items():
                if syn_key in query_lower:
                    # Find candidate label containing target_keyword
                    for label, id_val in label_to_id.items():
                        if target_keyword.lower() in label.lower():
                            return {
                                "id": id_val,
                                "label": label,
                                "confidence": 1.0
                            }

        # 2. Direct Substring / RapidFuzz Matching
        for label, id_val in label_to_id.items():
            if label.lower() in query_lower:
                return {
                    "id": id_val,
                    "label": label,
                    "confidence": 1.0
                }

        match_result = process.extractOne(
            query_text,
            candidate_labels,
            scorer=fuzz.partial_ratio
        )

        if match_result and match_result[1] >= threshold:
            best_label = match_result[0]
            matched_id = label_to_id[best_label]
            return {
                "id": matched_id,
                "label": best_label,
                "confidence": round(match_result[1], 2)
            }

        return None
