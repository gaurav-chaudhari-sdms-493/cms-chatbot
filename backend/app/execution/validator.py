import re


class SQLSafetyValidator:
    """Validator enforcing read-only SELECT constraints on template execution."""

    DISALLOWED_KEYWORDS = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "EXEC",
        "EXECUTE",
        "CREATE",
        "REPLACE",
    ]

    @classmethod
    def validate_sql(cls, sql_text: str) -> bool:
        """
        Ensures SQL statement begins with SELECT and contains no mutation keywords.
        """
        cleaned_sql = sql_text.strip()
        if not cleaned_sql.upper().startswith("SELECT") and not cleaned_sql.upper().startswith("WITH"):
            return False

        # Reject any forbidden mutation keyword
        for keyword in cls.DISALLOWED_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, cleaned_sql, re.IGNORECASE):
                return False

        return True
