# PMC Officer Query System — POC Specification

> Scoped-down proof-of-concept spec, derived from the full implementation spec.
> Goal: validate the core hypothesis cheaply before building auth, RBAC, deployment, and monitoring.

---

## 0. What This POC Exists to Prove

One hypothesis, and only one:

> **Can semantic embedding retrieval reliably map a paraphrased officer question to the correct
> structural query template, and can typed placeholder resolution fill it in without ambiguity —
> at a Top-K accuracy high enough to be usable?**

Everything in this document is scoped to answering that question as cheaply and quickly as
possible. If the answer is no, the rest of the full spec (auth, RBAC, audit, deployment,
monitoring) is not worth building yet. If the answer is yes, the full spec becomes the build plan.

**This POC does NOT try to be secure, multi-user, or deployable.** It runs locally, against a
read-only copy/sample of PMC data, for internal evaluation only.

---

## 1. POC Scope

### 1.1 In Scope

- Reduce the 200-question dataset to a canonical set of ~30–50 structural templates.
- Build a held-out paraphrase test set (this is the deliverable that actually proves or disproves
  the hypothesis — see Section 6).
- Embedding-based template retrieval (Top-K) using pgvector.
- Basic entity extraction: reference values (department, ward, category, status) resolved via
  fuzzy match against the actual DB tables; numeric/date values extracted and validated.
- Placeholder resolution flow: detected values reused, missing values asked for via a minimal form.
- Parameterized, read-only SQL execution against a small set of approved templates.
- A single evaluation report: Top-1/Top-3/Top-5 retrieval accuracy, entity extraction accuracy,
  wrong-template execution rate.

### 1.2 Explicitly Deferred to Production (Not in POC)

| Deferred item | Why it can wait |
| --- | --- |
| Authentication / RBAC | Doesn't affect whether retrieval works |
| Audit logging (full) | A minimal execution log is enough to debug the POC; production audit trail is a separate concern |
| Docker / Nginx / deployment | Runs on a dev machine |
| Monitoring / Prometheus / Grafana | No production traffic to monitor yet |
| Redis caching | Premature until performance is a known bottleneck |
| Template admin UI | Templates are seeded via migration/script, not managed live |
| Multi-language (Marathi/Hinglish) | Adds a variable to an already-uncertain retrieval question — validate English first |
| Query history UI | Not needed to answer the hypothesis |

If the POC succeeds, these get added back in exactly as described in the full spec — nothing here
contradicts that document, it's a subset.

---

## 2. Reduced Template Set

Instead of all 200 rows, Phase 1 of the POC produces a **canonical set of ~30–50 structural
templates**, chosen to:

- Cover the most common intent *shapes* (count by department, count by category, list by ward,
  SLA breach counts, date-range filters, etc.) rather than every literal question.
- Include at least a few templates with **2+ placeholders** (e.g., department + date range) since
  multi-entity extraction is a real risk area the full 200-question set doesn't stress-test well.
- Deliberately include a few **near-duplicate / confusable templates** (e.g., "pending complaints
  by department" vs "complaints closed vs pending by department") — these are exactly the cases
  that will reveal whether retrieval is precise enough, and they're the ones most likely to be
  missing if you only dedupe for convenience.

Template record format is unchanged from the full spec (Section 7.1):

```json
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

---

## 3. Simplified Architecture

```
Officer query (dev console / minimal form)
   ↓
Embedding retrieval (pgvector)
   ↓
Top-K templates + detected values
   ↓
Officer/tester selects template
   ↓
Minimal placeholder form (only for missing values)
   ↓
Validate + resolve canonical IDs
   ↓
Parameterized SQL execution (read-only DB user)
   ↓
Result table + execution log row
```

No auth layer, no gateway, no reverse proxy. FastAPI serves both the API and a minimal React (or
even plain HTML) form directly for internal testers.

### 3.1 Backend structure (trimmed)

```
backend/app/
├── api/            suggest, resolve, execute, health — nothing else
├── retrieval/       embeddings + pgvector search
├── entities/         extraction + reference resolution
├── templates/       template registry (loaded from seed, no admin CRUD)
├── execution/        SQL validation + execution + result formatting
├── db/                sessions + repositories
└── schemas/          request/response models
```

`core/` (auth, RBAC config) is intentionally omitted — add it back only once the POC passes.

---

## 4. Data Model (Trimmed)

Only the tables needed to run and evaluate the pipeline:

| Table | Purpose | Notes vs full spec |
| --- | --- | --- |
| `query_templates` | Canonical templates + embeddings | Same as full spec |
| `query_template_placeholders` | Placeholder metadata | Same as full spec |
| `template_test_cases` | Paraphrased NL → expected template ID | **This is the most important table in the POC** — see Section 6 |
| `query_execution_log` | Minimal execution record: query text, template id, params, status, timing | Replaces the full `query_execution_history` + `query_audit_log` pair — one lightweight table is enough for internal debugging |

No `user_master`-linked auth tables, no RBAC tables.

---

## 5. Entity Extraction — Made Explicit

The full spec left this undefined; the POC must not. For the POC, use a **deterministic,
inspectable approach** rather than a black-box NER model, so failures are diagnosable:

1. For each REFERENCE placeholder type, fuzzy-match substrings of the query against the
   corresponding `*_master` table's label column (e.g., trigram similarity or a lightweight
   library) rather than a trained NER model.
2. For ENUM placeholders, match against the fixed controlled vocabulary list.
3. For numeric/date values, use simple pattern extraction (numbers, date formats, relative terms
   like "last 30 days" mapped to explicit date ranges) with a hardcoded list of recognized
   patterns — not a general date parser guessing intent.
4. If a match is below a similarity threshold, treat it as **not detected** (falls through to the
   fallback form) rather than accepting a low-confidence guess.
5. Log every extraction decision (raw span → matched value → confidence) so extraction accuracy
   can be scored against the test set in Section 6.

This keeps entity resolution debuggable — a hard requirement in a POC where you need to know
*why* something matched or didn't.

---

## 6. Evaluation Plan (The Actual POC Deliverable)

This is the part the original spec was missing and the part that determines whether to proceed.

### 6.1 Build a held-out paraphrase test set

- For each of the ~30–50 canonical templates, write **5–10 paraphrased questions** that were
  **not** part of the original 200-row dataset (different wording, word order, informal phrasing,
  synonyms — "how many complaints are still open in Road" vs "pending complaints Road
  department").
- Include some deliberately ambiguous or out-of-scope questions to test "no confident match"
  behavior (FR-14 / Section 10.1).
- Store as `template_test_cases`: `{nl_question, expected_template_id, expected_entities}`.

### 6.2 Metrics to compute

| Metric | What it tells you | Rough bar to consider "proceed" |
| --- | --- | --- |
| Top-1 retrieval accuracy | Does the best match land correctly without officer scanning a list | Target ≥ 70–80% |
| Top-3 retrieval accuracy | Is the correct template at least visible to the officer | Target ≥ 90% |
| Entity extraction accuracy | Are reference/numeric values correctly detected | Target ≥ 85% on unambiguous phrasing |
| Wrong-template execution rate | Did the officer ever get led to execute the wrong template | Target = 0% (this is the non-negotiable one) |
| No-match precision | Does the system correctly say "no match" instead of forcing a weak result | Should not silently guess below threshold |

### 6.3 Decision point

After running the test set:

- **If Top-3 accuracy and wrong-template execution rate meet the bar** → architecture is
  validated, proceed to the full spec (auth, RBAC, audit, deployment, remaining templates).
- **If Top-1/Top-3 accuracy is low** → the problem is almost certainly the embedding model choice
  or `retrieval_text` quality, not the overall architecture — iterate on those before assuming the
  approach itself is wrong.
- **If entity extraction accuracy is low** → the fuzzy-matching approach in Section 5 needs
  tuning (thresholds, alias lists for common department/category name variants) before scaling to
  200+ templates.

---

## 7. SQL Execution (Unchanged Principles, Smaller Surface)

Same non-negotiables as the full spec, just applied to fewer templates:

- Read-only DB user.
- Parameterized queries only — no string concatenation.
- Reject any template ID not in the active seeded set.
- Query timeout + row limit.
- Every execution recorded in `query_execution_log` (template id, version, params, status, timing)
  even without full audit/RBAC.

---

## 8. Tech Stack (Trimmed)

| Technology | Layer | Included in POC? |
| --- | --- | --- |
| FastAPI | Backend | Yes |
| PostgreSQL + pgvector | Data / vector search | Yes |
| Sentence Transformers (one model, not a bake-off) | Embeddings | Yes — pick one candidate (e.g. multilingual-e5-base) and commit for the POC; benchmarking alternatives is a production concern |
| SQLAlchemy Core | DB access | Yes |
| Minimal React or plain HTML form | Frontend | Yes, bare minimum — just enough to test the flow manually |
| Pytest | Testing / eval scoring | Yes |
| Docker, Nginx, Redis, Prometheus/Grafana, Material UI | — | **No**, deferred |

---

## 9. POC Work Sequence

1. Reduce the 200-row dataset to ~30–50 canonical templates (include near-duplicates and
   multi-placeholder cases deliberately).
2. Seed `query_templates` + `query_template_placeholders` via migration/script.
3. Write the held-out paraphrase test set into `template_test_cases` (Section 6.1) — do this
   *before* touching retrieval code, so there's no temptation to tune retrieval against the eval
   set.
4. Implement embedding generation + pgvector Top-K retrieval.
5. Implement deterministic entity extraction (Section 5).
6. Implement placeholder fallback form (minimal UI) + validation.
7. Implement parameterized execution against the reduced template set.
8. Run the evaluation (Section 6.2) and produce the accuracy report.
9. Make the go/no-go call (Section 6.3).

No auth, deployment, or admin phases — those only start once step 9 says "go."

---

## 10. AI Code Writer Rules (Unchanged)

Same discipline as the full spec applies even at POC scale:

- Do not replace the template-based architecture with free-form NL-to-SQL, even to make the POC
  "look smarter."
- Do not invent tables, columns, or categorical values not present in the supplied schema.
- Never concatenate officer values into SQL, even in throwaway POC code.
- Keep retrieval, entity resolution, and execution in separate modules — POC code often gets
  promoted to production as-is, so don't take shortcuts that make that harder later.
- Flag ambiguous template/entity mappings rather than guessing.

---

## 11. Definition of POC Success

- A held-out paraphrase test set exists and was not used to tune retrieval.
- Top-1/Top-3 retrieval accuracy and wrong-template execution rate are measured and reported
  (Section 6.2).
- At least one multi-placeholder template and one pair of confusable templates were included in
  testing, not just easy single-entity cases.
- A clear go/no-go recommendation is produced for whether to invest in the full production spec.
