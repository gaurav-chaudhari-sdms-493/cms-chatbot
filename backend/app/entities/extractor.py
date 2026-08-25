import re
from typing import Dict, Any, List, Optional


class EntityExtractor:
    """Extracts continuous, pattern-based, and enum entities from natural language queries."""

    @staticmethod
    def extract_regex_entities(query_text: str) -> Dict[str, Any]:
        """Extracts numeric limits and date range indicators using pattern matching."""
        extracted = {}

        # 1. Limit pattern (e.g. "top 10", "top 5")
        limit_match = re.search(r'\btop\s+(\d+)\b', query_text, re.IGNORECASE)
        if limit_match:
            try:
                extracted["limit"] = int(limit_match.group(1))
            except ValueError:
                pass

        # 2. Priority controlled vocabulary matching
        priority_match = re.search(r'\b(high|medium|low|critical|normal)\b', query_text, re.IGNORECASE)
        if priority_match:
            extracted["priority"] = priority_match.group(1).upper()

        return extracted
