# PMC Officer Query System

> Full Technical Requirements & Implementation Specification for AI Code Writers

This document is the implementation specification for the PMC Officer Query System. It defines the architecture, requirements, data model, template-based NL query workflow, placeholder handling, technology stack, implementation phases, testing, security, and rules for AI coding agents.

**Core principle:** semantic retrieval finds the approved query template; typed placeholder resolution supplies validated values; deterministic parameterized SQL executes the query.

---

PMC Officer Query System

Template-Based Natural Language Query Platform

Full Technical Requirements & Implementation Specification for AI Code Writers


| Item | Specification |
| --- | --- |
| Purpose | Controlled natural-language interface for PMC complaint analytics |
| Primary users | Authorized PMC officers |
| Core method | Semantic template retrieval → typed placeholders → deterministic parameterized SQL |
| Backend | Python + FastAPI |
| Frontend | React |
| Database | PostgreSQL |
| Vector search | pgvector |
| Embedding runtime | Sentence Transformers with a suitable open-source multilingual model |
| Source template set | 200-question entity-aware dataset |


## 1. Executive Summary

This project provides PMC officers with a natural-language interface for querying complaint data without exposing them to SQL. The system should not freely generate SQL for every question. It should retrieve an approved query template, collect or resolve its placeholders, validate those values, execute a parameterized SQL template, and display the result.

Embeddings are used for semantic retrieval only. Categorical/reference values such as department, category, ward and workflow status must be selected from authoritative database-backed controls. Continuous values such as age thresholds, limits and dates use typed numeric/date controls.

```
Officer query
   ↓
Embedding retrieval
   ↓
Top matching templates
   ↓
Officer selects template
   ↓
Extract values already present
   ↓
Find missing placeholders
   ↓
Dropdown/search/date/number inputs
   ↓
Validate + resolve canonical IDs
   ↓
Parameterized approved SQL
   ↓
PostgreSQL
   ↓
Formatted result
```


## 2. Goals and Design Principles

- Correctness over flexibility: approved templates are preferred over arbitrary SQL generation.

- Semantic retrieval rather than keyword-only matching.

- Entity values are separate from query structure.

- Categorical values are controlled by the database; users cannot submit arbitrary categorical strings.

- Continuous values use typed controls and server-side validation.

- Values should be resolved to canonical IDs where reference tables exist.

- SQL must be parameterized and read-only in V1.

- Every execution must be auditable.

- LLMs, if added later, may assist understanding but must not become the unrestricted SQL executor.


## 3. Scope


### 3.1 In Scope

- Natural-language query input.

- Embedding-based template suggestions.

- Top-K ranked template selection.

- Entity extraction from the original query.

- Placeholder detection and fallback questions.

- Database-backed searchable dropdowns for categorical/reference fields.

- Dropdowns for controlled enums such as priority and SLA status.

- Number/date/date-range inputs for continuous values.

- Canonical reference-ID resolution.

- Parameterized SQL execution.

- Result tables and optional visualization metadata.

- Authentication, RBAC, query history and audit logging.

- Template catalog and versioning.


### 3.2 Out of Scope for V1

- Free-form LLM-to-SQL for arbitrary database questions.

- INSERT/UPDATE/DELETE/DROP/ALTER through this interface.

- Autonomous agent loops.

- Unapproved runtime creation of new SQL templates.

- Unrestricted access to every database table.


## 4. Functional Requirements


| ID | Requirement | Description |
| --- | --- | --- |
| FR-01 | Query input | Officer can enter a natural-language question. |
| FR-02 | Template retrieval | Generate query embedding and retrieve active templates. |
| FR-03 | Suggestions | Show ranked top matching templates. |
| FR-04 | Template selection | Officer explicitly selects the intended template. |
| FR-05 | Entity extraction | Reuse values already present in the query when confidently resolved. |
| FR-06 | Placeholder detection | Identify required values still missing. |
| FR-07 | Categorical controls | Use DB-backed dropdown/search for reference fields. |
| FR-08 | Continuous controls | Use number/date/date-range inputs for continuous values. |
| FR-09 | Validation | Validate every value before execution. |
| FR-10 | Canonical IDs | Resolve reference selections to actual database IDs. |
| FR-11 | Preview | Show resolved intent and parameters before execution when enabled. |
| FR-12 | Execution | Execute only approved parameterized templates. |
| FR-13 | Results | Render returned data in a clear tabular/visual form. |
| FR-14 | Errors | Handle no-match, ambiguity, invalid input, DB and execution errors safely. |
| FR-15 | Audit | Record user, template/version, execution status and timing. |
| FR-16 | Administration | Authorized administrators can manage template lifecycle. |


## 5. Non-Functional Requirements


| Area | Requirement |
| --- | --- |
| Security | Authenticated and authorized access; read-only query execution in V1. |
| SQL safety | No arbitrary SQL; only approved templates. |
| Parameter safety | No string concatenation of officer values into SQL. |
| Correctness | Low-confidence retrieval must not silently execute a query. |
| Auditability | Every execution traceable to a template/version and resolved parameter set. |
| Performance | Interactive retrieval and query execution; exact SLOs to be benchmarked. |
| Maintainability | Separate retrieval, entity resolution, placeholder collection and execution modules. |
| Testability | Each template has automated tests and representative NL examples. |
| Privacy | Prefer local/open-source models and avoid unnecessary external API transmission. |


## 6. Database and Schema Context

The supplied PMC schema documentation describes a complaint-centered ER model. It identifies relationships from complaint to department_master, ward_master, category_master, sub_category_master, status_master, user_master, prabhag_master, zone_master and related history/document/feedback entities.


| Entity | Role | Typical fields relevant to this project |
| --- | --- | --- |
| complaint | Base transactional entity | created_at, closed_at, department_id, ward_id, category_id, status_id, priority, sla_status, assigned_to_id |
| department_master | Department reference | id, department_name |
| ward_master | Ward reference | id, ward_name |
| category_master | Category reference | id, category_name |
| sub_category_master | Sub-category reference | id, sub_category_name |
| status_master | Workflow status reference | id, status_name |
| user_master | Officer/citizen reference | id, full_name |


### 6.1 Important Semantic Rule

Do not infer a database column solely from English wording. Use the approved SQL and schema relationships. For example, 'pending' in many current templates is represented by complaint.closed_at IS NULL, while actual workflow values such as Registered, Assigned, Processing, Reopened and Transferred use status_master.status_name.


## 7. Template Model

The existing 200 questions should be normalized into unique structural templates. Rows that differ only by a concrete department/category/ward/status/priority/number should normally share one template.

```
Road:
How many pending complaints in Road department?

Water Supply:
How many pending complaints in Water Supply department?

Drainage:
How many pending complaints in Drainage department?

→ One structural template:

How many pending complaints in {department}?
```


### 7.1 Template Record

```
{
  "template_id": "CMP_029",
  "intent": "pending_complaints_by_department",
  "question_template": "How many pending complaints in {department}?",
  "retrieval_text": "count open pending unresolved complaints filtered by department",
  "placeholders": ["department"],
  "result_type": "ranking",
  "is_active": true,
  "version": 1,
  "sql_template": "SELECT ..."
}
```


## 8. Placeholder System


| Type | Examples | UI | Source / rule |
| --- | --- | --- | --- |
| REFERENCE | department, category, ward, status | Searchable dropdown | Authoritative DB table; return ID + label. |
| ENUM | priority, SLA status | Dropdown | Controlled values. |
| INTEGER | days, limit | Number input | Min/max validation. |
| DECIMAL | percentage/threshold | Number input | Numeric validation. |
| DATE | specific date | Date picker | Date validation. |
| DATE_RANGE | from/to dates | Date-range picker | Start must not exceed end. |
| BOOLEAN | include closed? | Checkbox/toggle | Boolean only. |
| TEXT | complaint number | Text input | Only when explicitly allowed by template. |


### 8.1 Placeholder Metadata

```
{
  "placeholder": "department",
  "data_type": "REFERENCE",
  "input_mode": "searchable_dropdown",
  "source_table": "department_master",
  "source_id_column": "id",
  "source_label_column": "department_name",
  "required": true
}
```


## 9. Canonical Example

```
Officer: How many pending complaints for Public Health Related category?
```


| Phrase | Meaning | Actual mapping | Template value |
| --- | --- | --- | --- |
| pending | Complaint state | complaint.closed_at IS NULL | fixed condition |
| complaints | Base entity | complaint | fixed |
| Public Health Related | Category value | category_master.category_name | {category} |

Template question:

```
How many pending complaints for {category}?
```

At runtime the category selector should obtain valid values from category_master. The selected record should provide both a display label and canonical ID. SQL should bind the ID or a validated reference parameter according to the approved template.


## 10. Retrieval Architecture


### 10.1 Embedding Strategy

- Generate embeddings for structural template/retrieval text, not one embedding per concrete entity value.

- Use an open-source embedding model that can handle the expected language mix; BGE-M3 and multilingual-e5 are candidates to benchmark.

- Store vectors using pgvector.

- Retrieve top K active templates, initially K=5 as a configurable starting point.

- Determine the similarity threshold empirically from a labeled test set.

- Return 'no confident match' instead of forcing a weak result.


### 10.2 Retrieval API Response

```
{
  "query": "How many pending complaints are in Road?",
  "suggestions": [
    {
      "template_id": "CMP_029",
      "question_template": "How many pending complaints in {department}?",
      "score": 0.93,
      "detected_values": {
        "department": {"id": 7, "label": "Road"}
      },
      "missing_placeholders": []
    }
  ]
}
```


## 11. Entity Resolution and Fallback Flow

```
1. Officer enters natural language.
2. Retrieve candidate templates.
3. Officer selects template.
4. Extract values already present.
5. Resolve reference values against DB.
6. If unique and valid → keep the value.
7. If ambiguous → show valid candidates.
8. If missing → generate a typed fallback control.
9. Validate all values.
10. Show resolved query summary.
11. Execute only after all required placeholders are resolved.
```


### 11.1 Important UX Rule

Do not ask redundant fallback questions. If the officer already said 'Road department' and the selected template needs department, reuse the detected Road value after validation.


## 12. Backend Architecture

```
backend/app/
├── api/                 REST endpoints
├── retrieval/           embeddings + pgvector search
├── entities/            extraction + reference resolution
├── templates/           template registry + renderer
├── execution/           SQL validation + execution + result formatting
├── db/                  sessions + repositories
├── schemas/             request/response models
└── core/                configuration + auth + logging
```


### 12.1 Core services


| Service | Responsibility |
| --- | --- |
| QuerySuggestionService | Embedding, retrieval, ranking and suggestion response. |
| EntityExtractionService | Detect candidate values from officer query. |
| ReferenceResolver | Resolve values to authoritative IDs and handle ambiguity. |
| TemplateService | Load active template and placeholder metadata. |
| PlaceholderService | Determine missing values and produce fallback UI definitions. |
| SQLTemplateRenderer | Bind validated parameters to approved templates. |
| SQLSafetyValidator | Reject unsafe statements and invalid template execution. |
| QueryExecutor | Execute parameterized SQL with timeout/row limits. |
| ResultFormatter | Normalize DB output for the frontend. |
| AuditService | Persist execution/audit events. |


## 13. API Requirements


| Endpoint | Purpose |
| --- | --- |
| POST /api/query/suggest | Input NL query; return ranked template suggestions and detected values. |
| GET /api/templates/{id} | Return template and placeholder definitions. |
| GET /api/reference/{source} | Return/search valid categorical reference options. |
| POST /api/query/resolve | Validate submitted placeholder values and return remaining missing values. |
| POST /api/query/execute | Execute fully resolved approved template. |
| GET /api/query/history | Return authorized query history. |
| GET /api/health | Health check. |
| GET /api/admin/templates | Restricted template administration. |


## 14. Frontend Requirements

- Query input/search page.

- Top matching template suggestion cards.

- Template selection state.

- Dynamic placeholder form driven entirely by backend metadata.

- Searchable dropdowns for large categorical/reference tables.

- Normal dropdowns for small enums.

- Number/date/date-range controls for continuous values.

- Ambiguity selection UI.

- Resolved query summary and confirmation.

- Result table with loading/empty/error states.

- Query history.


## 15. Application Tables


| Table | Purpose |
| --- | --- |
| query_templates | Approved reusable query patterns and SQL. |
| query_template_placeholders | Placeholder types, DB source, input modes and validation. |
| query_template_embeddings | Template vectors, or embedding column on query_templates. |
| query_execution_history | Executed template/query history. |
| query_audit_log | Security and audit events. |
| template_test_cases | NL examples mapped to expected templates for retrieval evaluation. |


### 15.1 Suggested query_templates fields

```
id
intent
question_template
retrieval_text
sql_template
result_type
is_active
version
created_at
updated_at
embedding (vector, if stored here)
```


### 15.2 Suggested query_template_placeholders fields

```
id
template_id
placeholder_name
data_type
input_mode
source_table
source_id_column
source_label_column
required
multi_select
min_value
max_value
validation_rule
display_order
```


## 16. SQL Execution Rules

- V1 must be read-only.

- SQL is selected from an approved template registry.

- Officer values are parameters, never SQL fragments.

- Reference selections should normally be converted to canonical IDs.

- Reject unexpected template IDs or inactive versions.

- Use query timeout/statement timeout.

- Apply row/result limits where appropriate.

- Log template/version and execution outcome.

```
Approved template:
SELECT d.department_name, COUNT(*) AS pending_count
FROM complaint c
JOIN department_master d ON c.department_id = d.id
WHERE c.closed_at IS NULL
  AND c.department_id = :department_id
GROUP BY d.department_name;

Parameters:
{"department_id": 7}
```


## 17. Recommended Technology Stack


| Technology | Layer | Use | Priority |
| --- | --- | --- | --- |
| React | Frontend | Officer UI and dynamic query workflow | Required |
| Material UI or equivalent | Frontend | Dropdowns, searchable selectors, forms, tables | Recommended |
| Python | Backend/ML | Application logic and model integration | Required |
| FastAPI | Backend | REST API and orchestration | Required |
| PostgreSQL | Data | PMC data + application metadata | Required |
| pgvector | Vector search | Template embedding storage/search | Required |
| Sentence Transformers | ML runtime | Local embedding generation | Required |
| BGE-M3 / multilingual-e5 candidate | Embedding model | Semantic retrieval; benchmark before final choice | Candidate |
| SQLAlchemy Core | DB access | Parameterized execution and repositories | Recommended |
| Redis | Caching | Reference/query cache where useful | Optional |
| Docker | Deployment | Reproducible packaging | Recommended |
| Nginx | Deployment | Reverse proxy | Recommended |
| Git + GitHub/GitLab | Development | Version control and collaboration | Required |
| Pytest | Testing | Backend unit/integration tests | Required |
| React Testing Library | Testing | Frontend behavior tests | Recommended |
| Prometheus/Grafana | Monitoring | Metrics and dashboards | Optional |


## 18. Repository Structure

```
pmc-officer-query-system/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── retrieval/
│   │   ├── entities/
│   │   ├── templates/
│   │   ├── execution/
│   │   ├── db/
│   │   └── schemas/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── retrieval/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   └── package.json
├── database/
│   ├── migrations/
│   ├── seed/
│   └── template_catalog/
├── docs/
├── docker-compose.yml
└── README.md
```


## 19. Phased Implementation Plan


| Phase | Name | Main work | Deliverable |
| --- | --- | --- | --- |
| 0 | Foundation | Repo, scope, schema mapping, environment, architecture | Skeleton + docs |
| 1 | Template normalization | Analyze 200 rows, deduplicate, define intents/placeholders | Canonical template catalog |
| 2 | Template DB | Migrations, seed data, versioning | Working registry |
| 3 | Embedding retrieval | Model adapter, embeddings, pgvector, top-K, threshold | Suggestion API |
| 4 | Entity resolution | Extraction, DB reference lookup, ambiguity handling | Placeholder service |
| 5 | Dynamic UI | Dropdowns, searchable selectors, number/date controls | Fallback UI |
| 6 | Execution | Parameterized SQL, safety validator, executor, formatter | Safe execution API |
| 7 | Integration | Connect all components end-to-end | Working officer workflow |
| 8 | Security | Auth, RBAC, audit, read-only DB, logging | Hardened system |
| 9 | Testing | Retrieval/entity/SQL/UI/performance tests | Evaluation report |
| 10 | Deployment | Docker, reverse proxy, health checks, monitoring | Deployable release |


## 20. Detailed Phase Tasks for AI Code Writers


### Phase 0 — Foundation

- Create repository and service skeleton.

- Create .env.example without real credentials.

- Document source DB connection configuration using placeholders only.

- Create backend health endpoint and frontend shell.

- Document the architecture before implementing business logic.


### Phase 1 — Template normalization

- Load the supplied 200-row entity-aware CSV.

- Treat original SQL and supplied schema as the source of truth.

- Preserve actual column/table mappings.

- Identify duplicate structural patterns.

- Convert concrete values into placeholders.

- Assign stable intent IDs.

- Manually flag ambiguous templates rather than guessing.


### Phase 2 — Template database

- Create migrations for query_templates and query_template_placeholders.

- Seed canonical templates.

- Add active/version fields.

- Create reference-source metadata.

- Add constraints to avoid invalid placeholder configurations.


### Phase 3 — Retrieval

- Implement an embedding-provider interface.

- Generate vectors from retrieval_text.

- Store vectors in pgvector.

- Implement top-K similarity search.

- Add configurable confidence threshold.

- Build paraphrase test cases from the 200 original questions.


### Phase 4 — Entity resolution

- Extract obvious categorical and numeric values.

- Resolve reference values against authoritative DB tables.

- Return ambiguity rather than guessing.

- Return missing required placeholders.

- Keep extraction independent from SQL execution.


### Phase 5 — Dynamic UI

- Build a generic placeholder form renderer.

- Map REFERENCE to searchable dropdown.

- Map ENUM to dropdown.

- Map INTEGER/DECIMAL to numeric input.

- Map DATE/DATE_RANGE to date controls.

- Never hardcode categorical values in the frontend if they are available from DB.


### Phase 6 — Execution

- Implement approved template lookup.

- Implement parameter binding.

- Implement SQL safety validation.

- Implement query timeout and row limits.

- Return structured results and safe errors.


### Phase 7 — Integration

- Implement query → suggestions → selection → placeholders → preview → execution → result.

- Do not ask redundant fallback questions.

- Persist execution history.


### Phase 8 — Security

- Integrate authentication.

- Apply RBAC.

- Use read-only DB credentials for query execution.

- Audit template/version/user/result status.

- Do not log unnecessary complaint content.


### Phase 9 — Testing

- Measure Top-1/Top-3/Top-5 retrieval accuracy.

- Measure entity extraction and reference resolution accuracy.

- Test every active SQL template.

- Test invalid and malicious input.

- Test no-match and ambiguity behavior.

- Test frontend controls and full integration.


### Phase 10 — Deployment

- Containerize services.

- Separate secrets from images.

- Add health checks and logs.

- Document migration/rollback.

- Add monitoring if required by deployment environment.


## 21. Testing and Acceptance Criteria


| Test area | Acceptance criterion |
| --- | --- |
| Retrieval | Representative paraphrases retrieve the intended template in the agreed Top-K. |
| Template selection | Officer can explicitly choose a suggestion. |
| Entity extraction | Values present in the query are reused when confidently resolved. |
| Categorical validation | Arbitrary/invalid category, department, ward or status cannot be executed. |
| Dropdown correctness | Options come from authoritative DB sources. |
| Numeric validation | Invalid/non-numeric/out-of-range values are rejected. |
| SQL safety | Mutation/arbitrary SQL cannot execute through the interface. |
| Template correctness | Each active template produces expected SQL semantics on test data. |
| Audit | Every successful/failed execution has a traceable record. |
| Failure safety | Low-confidence/no-match queries do not silently execute. |


### 21.1 Key Metrics

- Template retrieval Top-1, Top-3 and Top-5 accuracy.

- Placeholder extraction accuracy.

- Reference resolution accuracy.

- Wrong-template execution rate; target should be zero on approved test cases.

- Query execution success rate.

- Fallback completion rate.

- Median/p95 end-to-end response time.


## 22. Security and Privacy

- Never commit credentials, tokens or connection strings.

- Use environment variables or a secret manager.

- Use a read-only DB account for query execution.

- Use parameterized SQL.

- Do not allow officer text to become SQL syntax.

- Restrict accessible templates by role if required.

- Do not expose internal SQL unnecessarily to officers.

- Log request/template IDs and outcomes without unnecessarily logging sensitive complaint content.

- Apply API authentication, authorization and rate limiting as appropriate.


## 23. AI Code Writer Rules

- Read this document, the schema documentation and the template catalog before modifying query logic.

- Do not replace the template-based architecture with free-form NL-to-SQL.

- Do not invent tables, columns, relationships or categorical values.

- Use the supplied schema and active template registry as the source of truth.

- Keep retrieval, entity resolution, placeholder UI, SQL rendering and execution separate.

- Never concatenate officer values into SQL.

- Do not hardcode DB-backed categorical options in the frontend.

- Use migrations for schema changes.

- Write tests for every new template and placeholder type.

- Do not add LangChain/LangGraph/n8n/MCP unless a concrete requirement is explicitly approved.

- Prefer deterministic code for validation and execution.

- Flag ambiguous requirements rather than silently inventing behavior.

- Never commit secrets.


## 24. Suggested Immediate Work Sequence

1. Review the 200-row template dataset and identify structural duplicates.

1. Create the canonical unique template catalog.

1. Review ambiguous entity mappings against the supplied schema.

1. Define placeholder types and DB source metadata.

1. Create application database migrations.

1. Seed canonical templates and placeholders.

1. Implement DB-backed reference endpoints.

1. Implement embedding generation and pgvector search.

1. Implement /api/query/suggest.

1. Implement placeholder resolution and fallback-question contracts.

1. Implement React suggestion and dynamic placeholder workflow.

1. Implement parameterized SQL execution and safety checks.

1. Add query preview and audit history.

1. Build automated retrieval/entity/SQL/integration tests.


## 25. Future Extensions

- Marathi/Hinglish query support.

- Voice input.

- Template usage analytics.

- Frequently used query suggestions.

- Role-aware templates.

- Charts selected from result metadata.

- Human review workflow for new templates.

- Local LLM assistance for difficult entity extraction while retaining deterministic SQL.

- Feedback loop for template suggestion quality.


## 26. Final Target Architecture

```
PMC Officer
                              │
                              ▼
                    ┌─────────────────────┐
                    │      React UI       │
                    │ Query + Suggestions │
                    │ Dynamic Forms       │
                    │ Results             │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │ Query Orchestrator  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌────────────┐   ┌─────────────┐   ┌─────────────┐
       │ Embedding  │   │    Entity   │   │  Template   │
       │ Retrieval  │   │  Resolver   │   │  Registry   │
       └─────┬──────┘   └──────┬──────┘   └──────┬──────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Placeholder Engine  │
                    │ Typed Controls      │
                    │ Validation          │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ SQL Safety +        │
                    │ Parameter Binding   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ PostgreSQL          │
                    │ + pgvector          │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Result Formatter    │
                    └──────────┬──────────┘
                               ▼
                            Officer
```


## 27. Definition of Project Success

- Officer can ask a natural-language question without knowing SQL.

- System presents useful matching query templates.

- Officer explicitly selects the intended template.

- Values already present are reused after validation.

- Categorical placeholders use valid DB-backed dropdowns/search.

- Continuous values use appropriate typed inputs.

- Invalid values cannot reach SQL execution.

- Only approved parameterized SQL executes.

- Results are understandable to the officer.

- Every execution is auditable.

- The system can be expanded by adding templates rather than rewriting the NL-to-SQL engine.


## 28. Source / Assumption Note

This specification is based on the supplied PMC schema documentation, the 200-question entity-aware template dataset, and the architecture decisions established in this project discussion. Exact production targets such as the final embedding model, similarity threshold, infrastructure sizing and monitoring SLOs should be benchmarked and finalized during implementation.

Security note: source schema material may contain database connection information. Do not copy any real credentials into this document, source code, Docker images, logs or Git history. Use environment variables/secrets management.