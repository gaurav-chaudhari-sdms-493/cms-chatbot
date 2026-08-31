import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class EntityExtractor:
    """Extracts continuous, pattern-based, date range, and complaint ID entities from natural language queries."""

    @staticmethod
    def extract_regex_entities(query_text: str) -> Dict[str, Any]:
        """Extracts numeric limits, complaint numbers, priority, and date range parameters."""
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
