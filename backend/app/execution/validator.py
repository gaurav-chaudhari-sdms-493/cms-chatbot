import re


class SQLValidationError(ValueError):
    """Raised when SQL fails safety validation constraints."""
    pass


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
        Ensures SQL statement begins with SELECT or WITH and contains no mutation keywords.
        """
        cleaned_sql = sql_text.strip()
        if not cleaned_sql.upper().startswith("SELECT") and not cleaned_sql.upper().startswith("WITH"):
            raise SQLValidationError("SQL statement must begin with SELECT or WITH.")

        # Reject any forbidden mutation keyword
        for keyword in cls.DISALLOWED_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, cleaned_sql, re.IGNORECASE):
                raise SQLValidationError(f"Forbidden SQL keyword detected: '{keyword}'")

        return True

