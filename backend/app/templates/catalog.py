"""
Canonical Seed Catalog of Structural Templates for PMC Officer Query System.
Normalizes concrete questions into structural templates with typed placeholders.
"""

from typing import List, Dict, Any

CANONICAL_TEMPLATES: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. Citywide Overview Templates
    # -------------------------------------------------------------------------
    {
        "template_id": "CMP_001",
        "intent": "citywide_pending_complaints_count",
        "question_template": "How many pending complaints are there citywide?",
        "retrieval_text": "how many pending complaints are there citywide total pending open unresolved complaints count active backlog",
        "placeholders": [],
        "result_type": "scalar",
        "is_active": True,
        "version": 1,
        "sql_template": "SELECT COUNT(*) as pending_count FROM complaint WHERE closed_at IS NULL;"
    },
    {
        "template_id": "CMP_002",
        "intent": "citywide_pending_by_status",
        "question_template": "Show open complaints breakdown by workflow status.",
        "retrieval_text": "show open complaints breakdown by workflow status master distribution pending count registered assigned processing escalated",
        "placeholders": [],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT s.status_name, COUNT(*) as complaint_count
FROM complaint c
JOIN status_master s ON c.status_id = s.id
WHERE c.closed_at IS NULL
GROUP BY s.status_name
ORDER BY complaint_count DESC;
        """.strip()
    },
    {
        "template_id": "CMP_003",
        "intent": "registered_complaints_today",
        "question_template": "How many complaints were registered today?",
        "retrieval_text": "how many complaints were registered today current date logged received count",
        "placeholders": [],
        "result_type": "scalar",
        "is_active": True,
        "version": 1,
        "sql_template": "SELECT COUNT(*) as today_registered FROM complaint WHERE created_at::date = CURRENT_DATE;"
    },

    # -------------------------------------------------------------------------
    # 2. Department-Filtered Templates
    # -------------------------------------------------------------------------
    {
        "template_id": "CMP_010",
        "intent": "pending_complaints_by_department",
        "question_template": "How many pending complaints in {department}?",
        "retrieval_text": "how many pending complaints in department open unresolved complaints count filtered by department",
        "placeholders": [
            {
                "placeholder_name": "department",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "department_master",
                "source_id_column": "id",
                "source_label_column": "department_name",
                "required": True,
                "display_order": 1
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT d.department_name, COUNT(*) as pending_count
FROM complaint c
JOIN department_master d ON c.department_id = d.id
WHERE c.closed_at IS NULL AND c.department_id = :department_id
GROUP BY d.department_name;
        """.strip()
    },
    {
        "template_id": "CMP_011",
        "intent": "top_departments_by_pending",
        "question_template": "Which top {limit} departments have the most pending complaints?",
        "retrieval_text": "which top departments have the most pending complaints ranking highest backlog list",
        "placeholders": [
            {
                "placeholder_name": "limit",
                "data_type": "INTEGER",
                "input_mode": "number_input",
                "required": True,
                "default_value": 10,
                "min_value": 1,
                "max_value": 100,
                "display_order": 1
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT d.department_name, COUNT(*) as pending_count
FROM complaint c
JOIN department_master d ON c.department_id = d.id
WHERE c.closed_at IS NULL
GROUP BY d.department_name
ORDER BY pending_count DESC
LIMIT :limit;
        """.strip()
    },
    {
        "template_id": "CMP_012",
        "intent": "department_complaints_by_status",
        "question_template": "Show status breakdown for complaints in {department}.",
        "retrieval_text": "show status breakdown for complaints in department registered assigned resolved closed in department",
        "placeholders": [
            {
                "placeholder_name": "department",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "department_master",
                "source_id_column": "id",
                "source_label_column": "department_name",
                "required": True,
                "display_order": 1
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT s.status_name, COUNT(*) as count
FROM complaint c
JOIN status_master s ON c.status_id = s.id
WHERE c.department_id = :department_id
GROUP BY s.status_name
ORDER BY count DESC;
        """.strip()
    },

    # -------------------------------------------------------------------------
    # 3. Ward & Zone Templates
    # -------------------------------------------------------------------------
    {
        "template_id": "CMP_020",
        "intent": "pending_complaints_by_ward",
        "question_template": "How many pending complaints in {ward}?",
        "retrieval_text": "how many pending complaints in ward office open unresolved complaints count in ward area jurisdiction",
        "placeholders": [
            {
                "placeholder_name": "ward",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "ward_master",
                "source_id_column": "id",
                "source_label_column": "ward_name",
                "required": True,
                "display_order": 1
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT w.ward_name, COUNT(*) as pending_count
FROM complaint c
JOIN ward_master w ON c.ward_id = w.id
WHERE c.closed_at IS NULL AND c.ward_id = :ward_id
GROUP BY w.ward_name;
        """.strip()
    },
    {
        "template_id": "CMP_021",
        "intent": "ward_department_matrix",
        "question_template": "Show pending complaints in {ward} broken down by department.",
        "retrieval_text": "show pending complaints in ward broken down by department matrix distribution",
        "placeholders": [
            {
                "placeholder_name": "ward",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "ward_master",
                "source_id_column": "id",
                "source_label_column": "ward_name",
                "required": True,
                "display_order": 1
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT d.department_name, COUNT(*) as pending_count
FROM complaint c
JOIN department_master d ON c.department_id = d.id
WHERE c.closed_at IS NULL AND c.ward_id = :ward_id
GROUP BY d.department_name
ORDER BY pending_count DESC;
        """.strip()
    },

    # -------------------------------------------------------------------------
    # 4. Category & Sub-Category Templates
    # -------------------------------------------------------------------------
    {
        "template_id": "CMP_030",
        "intent": "pending_complaints_by_category",
        "question_template": "How many pending complaints for {category}?",
        "retrieval_text": "how many pending complaints for category type potholes garbage dumping drainage overflow water leakage issue",
        "placeholders": [
            {
                "placeholder_name": "category",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "category_master",
                "source_id_column": "id",
                "source_label_column": "category_name",
                "required": True,
                "display_order": 1
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT cat.category_name, COUNT(*) as pending_count
FROM complaint c
JOIN category_master cat ON c.category_id = cat.id
WHERE c.closed_at IS NULL AND c.category_id = :category_id
GROUP BY cat.category_name;
        """.strip()
    },

    # -------------------------------------------------------------------------
    # 5. SLA Breach & Late Complaints
    # -------------------------------------------------------------------------
    {
        "template_id": "CMP_040",
        "intent": "sla_breached_complaints_count",
        "question_template": "How many complaints have breached SLA citywide?",
        "retrieval_text": "how many complaints have breached sla deadline citywide overdue late complaints count",
        "placeholders": [],
        "result_type": "scalar",
        "is_active": True,
        "version": 1,
        "sql_template": "SELECT COUNT(*) as breached_count FROM vw_dd_late_complaints;"
    },
    {
        "template_id": "CMP_041",
        "intent": "sla_breached_by_department",
        "question_template": "How many SLA breached complaints in {department}?",
        "retrieval_text": "how many sla breached complaints in department overdue deadline passed late count in department",
        "placeholders": [
            {
                "placeholder_name": "department",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "department_master",
                "source_id_column": "id",
                "source_label_column": "department_name",
                "required": True,
                "display_order": 1
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT d.department_name, COUNT(*) as breached_count
FROM vw_dd_late_complaints l
JOIN department_master d ON l.department_id = d.id
WHERE l.department_id = :department_id
GROUP BY d.department_name;
        """.strip()
    },

    # -------------------------------------------------------------------------
    # 6. Multi-Placeholder & Date-Range Filters
    # -------------------------------------------------------------------------
    {
        "template_id": "CMP_050",
        "intent": "department_pending_in_ward",
        "question_template": "How many pending complaints for {department} in {ward}?",
        "retrieval_text": "how many pending complaints for department in ward location both parameters filtered by department and ward",
        "placeholders": [
            {
                "placeholder_name": "department",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "department_master",
                "source_id_column": "id",
                "source_label_column": "department_name",
                "required": True,
                "display_order": 1
            },
            {
                "placeholder_name": "ward",
                "data_type": "REFERENCE",
                "input_mode": "searchable_dropdown",
                "source_table": "ward_master",
                "source_id_column": "id",
                "source_label_column": "ward_name",
                "required": True,
                "display_order": 2
            }
        ],
        "result_type": "tabular",
        "is_active": True,
        "version": 1,
        "sql_template": """
SELECT d.department_name, w.ward_name, COUNT(*) as pending_count
FROM complaint c
JOIN department_master d ON c.department_id = d.id
JOIN ward_master w ON c.ward_id = w.id
WHERE c.closed_at IS NULL AND c.department_id = :department_id AND c.ward_id = :ward_id
GROUP BY d.department_name, w.ward_name;
        """.strip()
    }
]
