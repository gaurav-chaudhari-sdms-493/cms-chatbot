# PMC Commissioner Chatbot — Complete 47 Intent & SQL Template Catalog

## Overview & Architecture

To answer **all 200 Commissioner queries** reliably with zero SQL hallucination, the system utilizes a **Canonical Template-Based Natural Language to SQL Architecture**.

The system groups all 200 Commissioner queries into **47 Canonical Templates (`CMP_A01` to `CMP_P02`)** across 16 functional domain categories (A to P).

```
[User Natural Language Query] (English / Devanagari Marathi / Hinglish)
     │
     ▼
[1. Multi-Lingual Semantic Retrieval (Vector Embedding Search)]
     │
     ├── Matched Canonical Template ID: e.g. CMP_B01
     └── Intent: top_performing_officers
     │
     ▼
[2. Entity & Parameter Extraction (LLM)]
     │
     └── Extracted Placeholders: {"limit": 3, "department_id": 1, "ward_id": 2}
     │
     ▼
[3. SQL Template Parameter Binding]
     │
     └── Bind values into CMP_B01 SQL query
     │
     ▼
[4. Database Execution & Table Result Synthesis]
```

---

## Complete 47 Template Catalog (Categories A to P)

Below is the complete specification of all **47 canonical query templates** covering all 200 Commissioner example queries:

---

### Category A: Pending / Open Complaints (Q1–Q20)

#### `CMP_A01` — pending_complaints_by_department
- **Question Template:** `"How many complaints are pending department wise?"`
- **Retrieval Keywords:** `pending department wise total open unresolved active backlog distribution by department punyat kiti complaints pending aahet vibhaganusar`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT d.department_name, d.department_name_mar, COUNT(*) AS pending
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  JOIN department_master d ON d.id = c.department_id
  GROUP BY d.id, d.department_name, d.department_name_mar
  ORDER BY pending DESC;
  ```
- **Covered Questions:** Q1, Q2, Q7, Q8, Q51

#### `CMP_A02` — pending_complaints_filtered
- **Question Template:** `"Show pending complaints for {department} or {ward}."`
- **Retrieval Keywords:** `show pending open unresolved complaints for specific department ward or zone water supply drainage kothrud aundh pending count`
- **Placeholders:**
  - `department`: `REFERENCE` (source: `department_master`)
  - `ward`: `REFERENCE` (source: `ward_master`)
- **SQL Query Template:**
  ```sql
  SELECT d.department_name, w.ward_name, COUNT(*) AS pending
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  JOIN department_master d ON d.id = c.department_id
  JOIN ward_master w ON w.id = c.ward_id
  WHERE (:department_id IS NULL OR c.department_id = :department_id)
    AND (:ward_id IS NULL OR c.ward_id = :ward_id)
  GROUP BY d.department_name, w.ward_name
  ORDER BY pending DESC;
  ```
- **Covered Questions:** Q5, Q6, Q9, Q10, Q11, Q12, Q13, Q16, Q17, Q20

#### `CMP_A03` — pending_complaints_percentage
- **Question Template:** `"What percentage of total complaints are currently pending?"`
- **Retrieval Keywords:** `what percentage of total complaints are currently pending total open vs resolved ratio ratio percentage dakjava`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT COUNT(*) FILTER (WHERE s.is_terminal = false) AS pending,
         COUNT(*) AS total,
         ROUND(100.0 * COUNT(*) FILTER (WHERE s.is_terminal = false) / NULLIF(COUNT(*), 0), 1) AS pending_pct
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id;
  ```
- **Covered Questions:** Q3, Q4, Q19

#### `CMP_A04` — pending_complaints_by_status
- **Question Template:** `"How many complaints are stuck in {status_code} status?"`
- **Retrieval Keywords:** `assigned registered pending info unacknowledged status lifecycle step`
- **Placeholders:**
  - `status_code`: `ENUM` (`'REGISTERED'`, `'ASSIGNED'`, `'PENDING'`, `'PROCESSING'`)
- **SQL Query Template:**
  ```sql
  SELECT s.status_name, s.status_name_mar, COUNT(*) AS count
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  WHERE s.status_code = :status_code
  GROUP BY s.status_name, s.status_name_mar;
  ```
- **Covered Questions:** Q14, Q15, Q18

---

### Category B: Officer Performance (Q21–Q40)

#### `CMP_B01` — top_performing_officers
- **Question Template:** `"Which top {limit} officers are performing best or worst overall?"`
- **Retrieval Keywords:** `which officers are performing best worst overall ranking resolved count avg resolution time slow fast officers best officer in pune hadapsar kothrud`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT u.full_name, u.designation, d.department_name,
         COUNT(*) AS resolved_count,
         ROUND(AVG(EXTRACT(epoch FROM (c.resolved_at - c.created_at))/86400)::numeric, 1) AS avg_days
  FROM complaint c
  JOIN user_master u ON u.id = c.resolved_by_id
  LEFT JOIN department_master d ON d.id = u.department_id
  WHERE c.resolved_at IS NOT NULL
  GROUP BY u.id, u.full_name, u.designation, d.department_name
  ORDER BY resolved_count DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q21, Q22, Q23, Q24, Q25, Q26, Q27, Q28, Q29, Q32, Q33, Q34, Q35, Q36, Q37

#### `CMP_B02` — officers_with_sla_breaches
- **Question Template:** `"Which officers have the most SLA breaches?"`
- **Retrieval Keywords:** `which officers have the most sla breaches overdue maximum breach counts worst performing officers`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT u.full_name, u.designation, COUNT(*) AS breaches
  FROM complaint c
  JOIN user_master u ON u.id = COALESCE(c.assigned_to_id, c.ward_officer_id)
  WHERE c.sla_status = 'BREACHED'
  GROUP BY u.id, u.full_name, u.designation
  ORDER BY breaches DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q30, Q31, Q38

#### `CMP_B03` — inactive_officers_audit
- **Question Template:** `"Which officers have not resolved a single complaint in the last 30 days?"`
- **Retrieval Keywords:** `which officers have not resolved a single complaint in last 30 days zero resolutions inactive officers audit list`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT u.full_name, u.designation, d.department_name
  FROM user_master u
  LEFT JOIN department_master d ON d.id = u.department_id
  WHERE u.is_active = true
    AND NOT EXISTS (
        SELECT 1 FROM complaint c
        WHERE c.resolved_by_id = u.id
          AND c.resolved_at >= now() - interval '30 days'
    )
  LIMIT :limit;
  ```
- **Covered Questions:** Q39, Q40

---

### Category C: SLA Compliance & Breaches (Q41–Q55)

#### `CMP_C01` — overall_sla_compliance_rate
- **Question Template:** `"What is the overall SLA compliance rate citywide?"`
- **Retrieval Keywords:** `what is the overall sla compliance rate percentage citywide meeting target total within deadline vs breached`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT COUNT(*) FILTER (WHERE c.resolved_at IS NOT NULL AND c.resolved_at <= c.sla_deadline) AS within_sla,
         COUNT(*) FILTER (WHERE c.resolved_at IS NOT NULL) AS total_resolved,
         ROUND(100.0 * COUNT(*) FILTER (WHERE c.resolved_at <= c.sla_deadline)
               / NULLIF(COUNT(*) FILTER (WHERE c.resolved_at IS NOT NULL), 0), 1) AS compliance_pct
  FROM complaint c
  WHERE c.sla_deadline IS NOT NULL;
  ```
- **Covered Questions:** Q41, Q42, Q55

#### `CMP_C02` — sla_breached_by_department
- **Question Template:** `"How many complaints have breached SLA right now by department?"`
- **Retrieval Keywords:** `how many complaints have breached sla right now department wise overdue count deadline crossed`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT d.department_name, COUNT(*) AS breached_count
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  JOIN department_master d ON d.id = c.department_id
  WHERE c.sla_status = 'BREACHED' OR c.sla_deadline < now()
  GROUP BY d.department_name
  ORDER BY breached_count DESC;
  ```
- **Covered Questions:** Q43, Q44, Q45, Q52, Q53, Q54

#### `CMP_C03` — sla_near_breach_warning
- **Question Template:** `"Show complaints reaching 75% or 90% of SLA time (critical list)."`
- **Retrieval Keywords:** `show complaints reaching 75 90 percent of sla time critical near breach warning alert list`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, c.title, c.sla_deadline,
         ROUND(100.0 * EXTRACT(epoch FROM (now() - c.created_at))
               / NULLIF(EXTRACT(epoch FROM (c.sla_deadline - c.created_at)), 0)) AS sla_consumed_pct
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  WHERE c.sla_deadline IS NOT NULL AND c.sla_deadline > now()
    AND (now() - c.created_at) >= 0.75 * (c.sla_deadline - c.created_at)
  ORDER BY sla_consumed_pct DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q48, Q49

#### `CMP_C04` — sla_compliance_by_ward
- **Question Template:** `"Which ward has the worst or best SLA compliance?"`
- **Retrieval Keywords:** `which ward has worst best sla compliance ranking ward wise percentage meeting deadline`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT w.ward_name,
         COUNT(*) FILTER (WHERE c.resolved_at <= c.sla_deadline) AS within_sla,
         COUNT(*) FILTER (WHERE c.resolved_at IS NOT NULL) AS total_resolved,
         ROUND(100.0 * COUNT(*) FILTER (WHERE c.resolved_at <= c.sla_deadline)
               / NULLIF(COUNT(*) FILTER (WHERE c.resolved_at IS NOT NULL), 0), 1) AS compliance_pct
  FROM complaint c
  JOIN ward_master w ON w.id = c.ward_id
  WHERE w.ward_number IS NOT NULL AND c.sla_deadline IS NOT NULL
  GROUP BY w.id, w.ward_name
  ORDER BY compliance_pct ASC;
  ```
- **Covered Questions:** Q46, Q47, Q50

---

### Category D: Escalations (Q56–Q67)

#### `CMP_D01` — escalations_summary
- **Question Template:** `"How many complaints got escalated department or level wise?"`
- **Retrieval Keywords:** `how many complaints got escalated department level wise total escalation counts level 1 level 2 commissioner level`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT eh.to_level, COUNT(*) AS escalation_count
  FROM escalation_history eh
  JOIN complaint c ON c.id = eh.complaint_id
  GROUP BY eh.to_level
  ORDER BY escalation_count DESC;
  ```
- **Covered Questions:** Q56, Q57, Q60, Q61, Q65, Q66

#### `CMP_D02` — multiple_escalations_list
- **Question Template:** `"Which complaints have been escalated twice or more?"`
- **Retrieval Keywords:** `which complaints have been escalated twice or more multiple times escalated commissioner level list`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, c.title, c.escalation_level, COUNT(eh.id) AS times_escalated
  FROM complaint c
  JOIN escalation_history eh ON eh.complaint_id = c.id
  GROUP BY c.id, c.complaint_number, c.title, c.escalation_level
  HAVING COUNT(eh.id) >= 2
  ORDER BY times_escalated DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q58, Q59, Q63, Q64

#### `CMP_D03` — pending_escalated_complaints
- **Question Template:** `"How many escalated complaints are still pending?"`
- **Retrieval Keywords:** `how many escalated complaints are still pending open unresolved even after escalation level list`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, c.title, c.escalation_level, d.department_name, w.ward_name
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  LEFT JOIN department_master d ON d.id = c.department_id
  LEFT JOIN ward_master w ON w.id = c.ward_id
  WHERE c.escalation_level > 0
  ORDER BY c.escalation_level DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q62, Q67

---

### Category E: Category Analysis (Q68–Q82)

#### `CMP_E01` — top_complaint_categories
- **Question Template:** `"What are the top {limit} complaint categories in Pune?"`
- **Retrieval Keywords:** `what are the top complaint categories in pune potholes garbage dumping drainage overflow water supply streetlight`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `5`)
- **SQL Query Template:**
  ```sql
  SELECT cat.category_name, cat.category_name_mar, COUNT(*) AS complaint_count
  FROM complaint c
  JOIN category_master cat ON cat.id = c.category_id
  GROUP BY cat.id, cat.category_name, cat.category_name_mar
  ORDER BY complaint_count DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q68, Q69, Q70, Q71, Q74, Q76, Q77, Q79, Q80, Q81

#### `CMP_E02` — fastest_rising_category
- **Question Template:** `"Which category is rising fastest compared to last month?"`
- **Retrieval Keywords:** `which category is rising fastest compared to last month surge increase monthly diff monsoon potholes`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `5`)
- **SQL Query Template:**
  ```sql
  SELECT cat.category_name,
         COUNT(*) FILTER (WHERE c.created_at >= date_trunc('month', now())) AS this_month,
         COUNT(*) FILTER (WHERE c.created_at >= date_trunc('month', now()) - interval '1 month'
                            AND c.created_at < date_trunc('month', now())) AS last_month
  FROM complaint c
  JOIN category_master cat ON cat.id = c.category_id
  GROUP BY cat.id, cat.category_name
  ORDER BY (COUNT(*) FILTER (WHERE c.created_at >= date_trunc('month', now())) -
            COUNT(*) FILTER (WHERE c.created_at >= date_trunc('month', now()) - interval '1 month'
                               AND c.created_at < date_trunc('month', now()))) DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q72, Q73, Q75

#### `CMP_E03` — category_avg_resolution_time
- **Question Template:** `"What is the average resolution time by category (slowest/fastest)?"`
- **Retrieval Keywords:** `what is average resolution time by category slowest fastest category speed resolution days`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT cat.category_name,
         ROUND(AVG(EXTRACT(epoch FROM (c.resolved_at - c.created_at))/86400)::numeric, 1) AS avg_days
  FROM complaint c
  JOIN category_master cat ON cat.id = c.category_id
  WHERE c.resolved_at IS NOT NULL
  GROUP BY cat.id, cat.category_name
  ORDER BY avg_days DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q78, Q82

---

### Category F: Ward / Zone Comparison (Q83–Q97)

#### `CMP_F01` — ward_performance_ranking
- **Question Template:** `"Rank all 15 wards by pending complaints or resolution rate."`
- **Retrieval Keywords:** `rank all 15 wards by pending complaints resolution rate league table best worst ward ranking list`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT w.ward_name, w.ward_name_mar,
         COUNT(*) AS total,
         COUNT(*) FILTER (WHERE s.is_terminal = false) AS pending,
         COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') AS resolved,
         ROUND(100.0 * COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') / NULLIF(COUNT(*), 0), 1) AS resolution_rate
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  JOIN ward_master w ON w.id = c.ward_id
  WHERE w.ward_number IS NOT NULL
  GROUP BY w.id, w.ward_name, w.ward_name_mar
  ORDER BY resolution_rate DESC;
  ```
- **Covered Questions:** Q83, Q84, Q85, Q86, Q87, Q91, Q93, Q94, Q95

#### `CMP_F02` — zone_wise_summary
- **Question Template:** `"Show zone wise complaint summary breakdown."`
- **Retrieval Keywords:** `show zone wise complaint summary breakdown total pending resolved resolution rate by zone 1 zone 2 zone 3 zone 4 zone 5`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT z.zone_name, z.zone_name_mar,
         COUNT(*) AS total,
         COUNT(*) FILTER (WHERE s.is_terminal = false) AS pending,
         COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') AS resolved,
         ROUND(100.0 * COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') / NULLIF(COUNT(*), 0), 1) AS resolution_rate
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  JOIN zone_master z ON z.id = c.zone_id
  GROUP BY z.id, z.zone_name, z.zone_name_mar
  ORDER BY total DESC;
  ```
- **Covered Questions:** Q88, Q90, Q96, Q97

#### `CMP_F03` — ward_head_to_head_comparison
- **Question Template:** `"Compare performance of two wards (e.g. Aundh vs Kothrud)."`
- **Retrieval Keywords:** `compare performance of two wards aundh vs kothrud compare wards head to head resolution rate pending count`
- **Placeholders:**
  - `ward_1`: `REFERENCE` (source: `ward_master`)
  - `ward_2`: `REFERENCE` (source: `ward_master`)
- **SQL Query Template:**
  ```sql
  SELECT w.ward_name,
         COUNT(*) AS total,
         COUNT(*) FILTER (WHERE s.is_terminal = false) AS pending,
         COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') AS resolved,
         ROUND(100.0 * COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') / NULLIF(COUNT(*), 0), 1) AS resolution_rate
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  JOIN ward_master w ON w.id = c.ward_id
  WHERE c.ward_id IN (:ward_1_id, :ward_2_id)
  GROUP BY w.id, w.ward_name;
  ```
- **Covered Questions:** Q89, Q92

---

### Category G: Trends & Time Analysis (Q98–Q112)

#### `CMP_G01` — monthly_complaint_trend
- **Question Template:** `"Show monthly complaint trend for received vs resolved."`
- **Retrieval Keywords:** `show monthly complaint trend for received vs resolved last 12 months monthly volume breakdown trend dakhva`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `12`)
- **SQL Query Template:**
  ```sql
  SELECT date_trunc('month', c.created_at)::date AS month,
         COUNT(*) AS received,
         COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') AS resolved
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  GROUP BY 1
  ORDER BY 1 DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q98, Q99, Q102, Q104, Q105, Q108, Q110, Q111, Q112

#### `CMP_G02` — day_of_week_pattern
- **Question Template:** `"Which day of the week gets the most complaints?"`
- **Retrieval Keywords:** `which day of the week gets the most complaints daily pattern monday tuesday sunday peak day`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT to_char(c.created_at, 'Day') AS day_of_week,
         COUNT(*) AS complaint_count
  FROM complaint c
  GROUP BY day_of_week, EXTRACT(dow FROM c.created_at)
  ORDER BY EXTRACT(dow FROM c.created_at);
  ```
- **Covered Questions:** Q103

#### `CMP_G03` — complaint_volume_spikes
- **Question Template:** `"Any unusual spike or recent volume surge in complaints?"`
- **Retrieval Keywords:** `any unusual spike or recent volume surge in complaints sudden increase last 30 days daily counts`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT date_trunc('day', c.created_at)::date AS day,
         COUNT(*) AS daily_count
  FROM complaint c
  WHERE c.created_at >= now() - interval '30 days'
  GROUP BY 1
  ORDER BY daily_count DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q106, Q107

#### `CMP_G04` — daily_complaint_activity_trend
- **Question Template:** `"Show daily complaint activity trend for the last {limit} days."`
- **Retrieval Keywords:** `show daily complaint activity trend for last days total received pending resolved count daily breakdown date wise complaints today open complaints daily summary`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.created_at::date AS complaint_date,
         COUNT(*) AS total,
         COUNT(*) FILTER (WHERE s.is_terminal = false) AS pending,
         COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') AS resolved
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  GROUP BY c.created_at::date
  ORDER BY c.created_at::date DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q100, Q101, Q109

---

### Category H: Resolution Stats (Q113–Q127)

#### `CMP_H01` — citywide_resolution_stats
- **Question Template:** `"How many complaints were resolved citywide and average resolution time?"`
- **Retrieval Keywords:** `how many complaints were resolved citywide average resolution time 48 hours same day resolution stats`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT COUNT(*) AS total_resolved,
         ROUND(AVG(EXTRACT(epoch FROM (c.resolved_at - c.created_at))/86400)::numeric, 1) AS avg_days,
         COUNT(*) FILTER (WHERE c.resolved_at - c.created_at <= interval '48 hours') AS resolved_within_48h,
         COUNT(*) FILTER (WHERE c.resolved_at::date = c.created_at::date) AS same_day_resolved
  FROM complaint c
  WHERE c.resolved_at IS NOT NULL;
  ```
- **Covered Questions:** Q113, Q114, Q115, Q116, Q118, Q119, Q120, Q122, Q123, Q125

#### `CMP_H02` — resolution_time_by_department
- **Question Template:** `"Average resolution time department wise."`
- **Retrieval Keywords:** `average resolution time department wise which department resolves fastest slowest speed`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT d.department_name,
         COUNT(*) AS total_resolved,
         ROUND(AVG(EXTRACT(epoch FROM (c.resolved_at - c.created_at))/86400)::numeric, 1) AS avg_days
  FROM complaint c
  JOIN department_master d ON d.id = c.department_id
  WHERE c.resolved_at IS NOT NULL
  GROUP BY d.id, d.department_name
  ORDER BY total_resolved DESC;
  ```
- **Covered Questions:** Q117, Q121, Q127

#### `CMP_H03` — closed_vs_resolved_breakdown
- **Question Template:** `"Breakdown of resolved vs citizen-closed vs invalid closed complaints."`
- **Retrieval Keywords:** `breakdown of resolved vs citizen closed vs invalid closed terminal status counts`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT s.status_name, s.status_code, COUNT(*) AS count
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  WHERE s.is_terminal = true
  GROUP BY s.id, s.status_name, s.status_code
  ORDER BY count DESC;
  ```
- **Covered Questions:** Q124, Q126

---

### Category I: Citizen Feedback (Q128–Q137)

#### `CMP_I01` — overall_citizen_satisfaction
- **Question Template:** `"What is the average citizen satisfaction rating overall?"`
- **Retrieval Keywords:** `what is the average citizen satisfaction rating overall feedback score 1 star 2 star negative feedback count`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT ROUND(AVG(f.rating)::numeric, 2) AS avg_rating,
         COUNT(*) AS total_feedback,
         COUNT(*) FILTER (WHERE f.rating <= 2) AS negative_feedback_count
  FROM complaint_feedback f;
  ```
- **Covered Questions:** Q128, Q129, Q130, Q133, Q135, Q136

#### `CMP_I02` — satisfaction_rating_by_department
- **Question Template:** `"Which department gets the worst or best citizen feedback ratings?"`
- **Retrieval Keywords:** `which department gets worst best citizen feedback rating satisfaction score department wise`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT d.department_name,
         ROUND(AVG(f.rating)::numeric, 2) AS avg_rating,
         COUNT(f.id) AS total_feedback
  FROM complaint_feedback f
  JOIN complaint c ON c.id = f.complaint_id
  JOIN department_master d ON d.id = c.department_id
  GROUP BY d.id, d.department_name
  ORDER BY avg_rating ASC;
  ```
- **Covered Questions:** Q131, Q132, Q137

#### `CMP_I03` — recent_negative_feedback_comments
- **Question Template:** `"Show recent negative feedback comments with complaint numbers."`
- **Retrieval Keywords:** `show recent negative feedback comments with complaint numbers low rating 1 star 2 star remarks`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, f.rating, f.comment, f.created_at
  FROM complaint_feedback f
  JOIN complaint c ON c.id = f.complaint_id
  WHERE f.rating <= 2
  ORDER BY f.created_at DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q134

---

### Category J: Hotspots & Location (Q138–Q147)

#### `CMP_J01` — city_complaint_hotspots
- **Question Template:** `"Show top complaint hotspots in the city (geographic clusters)."`
- **Retrieval Keywords:** `show top complaint hotspots in the city geographic clusters location map lat lng density highest complaints area`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT ROUND(c.latitude::numeric, 3) AS lat,
         ROUND(c.longitude::numeric, 3) AS lng,
         COUNT(*) AS complaint_count,
         MIN(c.address) AS sample_address
  FROM complaint c
  WHERE c.latitude IS NOT NULL AND c.longitude IS NOT NULL
  GROUP BY 1, 2
  HAVING COUNT(*) >= 5
  ORDER BY complaint_count DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q138, Q139, Q143, Q144, Q146, Q147

#### `CMP_J02` — repeat_location_complaints
- **Question Template:** `"Which locations have repeat complaints of the same type?"`
- **Retrieval Keywords:** `which locations have repeat complaints of the same type same spot recurring garbage potholes issues`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT ROUND(c.latitude::numeric, 3) AS lat,
         ROUND(c.longitude::numeric, 3) AS lng,
         cat.category_name,
         COUNT(*) AS repeat_count
  FROM complaint c
  JOIN category_master cat ON cat.id = c.category_id
  WHERE c.latitude IS NOT NULL AND c.longitude IS NOT NULL
  GROUP BY 1, 2, cat.category_name
  HAVING COUNT(*) >= 3
  ORDER BY repeat_count DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q140, Q141, Q142, Q145

---

### Category K: Department Deep-Dive (Q148–Q159)

#### `CMP_K01` — department_full_scorecard
- **Question Template:** `"Give me the full scorecard picture of {department}."`
- **Retrieval Keywords:** `give me full picture scorecard of water supply health road drainage solid waste department pending resolved sla workload`
- **Placeholders:**
  - `department`: `REFERENCE` (source: `department_master`)
- **SQL Query Template:**
  ```sql
  SELECT d.department_name,
         COUNT(*) AS total_complaints,
         COUNT(*) FILTER (WHERE s.is_terminal = false) AS pending,
         COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') AS resolved,
         COUNT(*) FILTER (WHERE c.sla_status = 'BREACHED') AS sla_breached,
         COUNT(*) FILTER (WHERE c.escalation_level > 0) AS escalated,
         ROUND(AVG(EXTRACT(epoch FROM (c.resolved_at - c.created_at))/86400)
               FILTER (WHERE c.resolved_at IS NOT NULL)::numeric, 1) AS avg_days
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  JOIN department_master d ON d.id = c.department_id
  WHERE c.department_id = :department_id
  GROUP BY d.id, d.department_name;
  ```
- **Covered Questions:** Q148, Q149, Q150, Q152, Q153, Q156, Q157, Q158, Q159

#### `CMP_K02` — department_officer_workload_list
- **Question Template:** `"Show active officers and workload in {department}."`
- **Retrieval Keywords:** `show active officers and workload open assigned complaints in road water supply department`
- **Placeholders:**
  - `department`: `REFERENCE` (source: `department_master`)
- **SQL Query Template:**
  ```sql
  SELECT u.full_name, u.designation,
         COUNT(c.id) FILTER (WHERE s.is_terminal = false) AS open_assigned
  FROM user_master u
  LEFT JOIN complaint c ON COALESCE(c.assigned_to_id, c.ward_officer_id) = u.id
  LEFT JOIN status_master s ON s.id = c.status_id
  WHERE u.department_id = :department_id AND u.is_active = true
  GROUP BY u.id, u.full_name, u.designation
  ORDER BY open_assigned DESC;
  ```
- **Covered Questions:** Q151

#### `CMP_K03` — department_list_summary
- **Question Template:** `"Show list of all PMC departments with complaint counts and resolution rates."`
- **Retrieval Keywords:** `give me the list of departments list all departments show all departments department list sarva vibhaganchi yadi department wise list all departments list`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT d.id AS department_id,
         d.department_name,
         d.department_name_mar,
         COUNT(c.id) AS total_complaints,
         COUNT(c.id) FILTER (WHERE s.is_terminal = false) AS pending_complaints,
         ROUND(100.0 * COUNT(c.id) FILTER (WHERE s.status_code = 'RESOLVED') / NULLIF(COUNT(c.id), 0), 1) AS resolution_rate
  FROM department_master d
  LEFT JOIN complaint c ON c.department_id = d.id
  LEFT JOIN status_master s ON s.id = c.status_id
  GROUP BY d.id, d.department_name, d.department_name_mar
  ORDER BY total_complaints DESC;
  ```
- **Covered Questions:** Q154, Q155

---

### Category L: Aging / Oldest Complaints (Q160–Q169)

#### `CMP_L01` — aging_bucket_breakdown
- **Question Template:** `"Show aging bucket breakdown (0-7, 7-30, 30-90, 90+ days)."`
- **Retrieval Keywords:** `show aging bucket breakdown 0-7 7-30 30-90 90+ days distribution pending open complaints age`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT CASE
           WHEN now() - c.created_at < interval '7 days'  THEN '0-7 days'
           WHEN now() - c.created_at < interval '30 days' THEN '7-30 days'
           WHEN now() - c.created_at < interval '90 days' THEN '30-90 days'
           ELSE '90+ days' END AS age_bucket,
         COUNT(*) AS pending_count
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  GROUP BY 1
  ORDER BY 1;
  ```
- **Covered Questions:** Q165, Q169

#### `CMP_L02` — oldest_open_complaints_list
- **Question Template:** `"What are the {limit} oldest open complaints in the city?"`
- **Retrieval Keywords:** `what are the oldest open complaints in the city 10 oldest pending complaints list details officer ward`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, c.title, c.created_at,
         EXTRACT(day FROM now() - c.created_at) AS age_days,
         d.department_name, w.ward_name, u.full_name AS assigned_officer, s.status_name
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  LEFT JOIN department_master d ON d.id = c.department_id
  LEFT JOIN ward_master w ON w.id = c.ward_id
  LEFT JOIN user_master u ON u.id = COALESCE(c.assigned_to_id, c.ward_officer_id)
  ORDER BY c.created_at ASC
  LIMIT :limit;
  ```
- **Covered Questions:** Q162, Q163, Q166, Q167

#### `CMP_L03` — complaints_pending_over_days
- **Question Template:** `"Show complaints pending for more than 30 or 90 days."`
- **Retrieval Keywords:** `show complaints pending for more than 30 60 90 days older long pending backlog list`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, c.title, c.created_at,
         EXTRACT(day FROM now() - c.created_at) AS age_days,
         d.department_name, w.ward_name
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  LEFT JOIN department_master d ON d.id = c.department_id
  LEFT JOIN ward_master w ON w.id = c.ward_id
  WHERE c.created_at < now() - interval '30 days'
  ORDER BY c.created_at ASC
  LIMIT :limit;
  ```
- **Covered Questions:** Q160, Q161, Q164, Q168

---

### Category M: Source / Channel (Q170–Q177)

#### `CMP_M01` — source_channel_breakdown
- **Question Template:** `"Show channel wise resolution rate, complaint counts, and comparison across all channels (Call Center, Web, Mobile, Walk-in)."`
- **Retrieval Keywords:** `how many complaints came from call center vs web vs mobile vs walk-in swachhata app channel distribution resolution rate konta channel best compare channels channel wise resolution rate sarva channel chi tulna all channels channel comparison`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT c.source_channel,
         COUNT(*) AS received,
         COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') AS resolved,
         ROUND(100.0 * COUNT(*) FILTER (WHERE s.status_code = 'RESOLVED') / NULLIF(COUNT(*), 0), 1) AS resolution_rate,
         ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) AS share_pct
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  GROUP BY c.source_channel
  ORDER BY resolution_rate DESC;
  ```
- **Covered Questions:** Q170, Q171, Q172, Q174, Q175, Q176, Q177

#### `CMP_M02` — swachhata_app_complaints
- **Question Template:** `"How many complaints synced from Swachhata app?"`
- **Retrieval Keywords:** `how many complaints synced from swachhata app external partner total count`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT COUNT(*) AS total_swachhata_complaints FROM swachhata_complaint;
  ```
- **Covered Questions:** Q173

---

### Category N: Reopened / Rejected / Duplicates (Q178–Q185)

#### `CMP_N01` — reopened_complaints_by_department
- **Question Template:** `"Which department has the highest reopen rate?"`
- **Retrieval Keywords:** `which department has the highest reopen rate reopened count citizen reopened poor resolution quality`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT d.department_name,
         COUNT(*) FILTER (WHERE c.reopen_count > 0) AS reopened_count,
         ROUND(100.0 * COUNT(*) FILTER (WHERE c.reopen_count > 0) / NULLIF(COUNT(*), 0), 2) AS reopen_rate
  FROM complaint c
  JOIN department_master d ON d.id = c.department_id
  GROUP BY d.id, d.department_name
  ORDER BY reopen_rate DESC;
  ```
- **Covered Questions:** Q178, Q179, Q180, Q181, Q185

#### `CMP_N02` — rejected_complaints_reasons
- **Question Template:** `"How many complaints were rejected and what are the rejection reasons?"`
- **Retrieval Keywords:** `how many complaints were rejected invalid rejection reasons list ward wise closed invalid`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, w.ward_name, c.resolution_remarks AS rejection_reason
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.status_code = 'CLOSED_INVALID'
  LEFT JOIN ward_master w ON w.id = c.ward_id
  ORDER BY c.updated_at DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q182, Q183

#### `CMP_N03` — duplicate_complaints_count
- **Question Template:** `"How many complaints were marked as duplicate?"`
- **Retrieval Keywords:** `how many complaints were marked as duplicate count total duplicates parent complaint id`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT COUNT(*) AS duplicate_count
  FROM complaint
  WHERE is_duplicate = true OR parent_complaint_id IS NOT NULL;
  ```
- **Covered Questions:** Q184

---

### Category O: Workload & Staffing (Q186–Q193)

#### `CMP_O01` — officer_workload_ranking
- **Question Template:** `"Which officers are overloaded right now (workload score ranking)?"`
- **Retrieval Keywords:** `which officers are overloaded right now workload score ranking open pending overdue assigned list`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `10`)
- **SQL Query Template:**
  ```sql
  SELECT u.full_name, d.department_name,
         (COUNT(*) FILTER (WHERE s.status_code IN ('REGISTERED','ASSIGNED','PENDING')) * 1.5 +
          COUNT(*) FILTER (WHERE s.status_code = 'PROCESSING') * 1.0 +
          COUNT(*) FILTER (WHERE c.sla_deadline < now() AND s.is_terminal = false) * 3.0) AS workload_score,
         COUNT(*) FILTER (WHERE s.is_terminal = false) AS open_count
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  JOIN user_master u ON u.id = COALESCE(c.assigned_to_id, c.ward_officer_id)
  LEFT JOIN department_master d ON d.id = u.department_id
  GROUP BY u.id, u.full_name, d.department_name
  ORDER BY workload_score DESC
  LIMIT :limit;
  ```
- **Covered Questions:** Q186, Q187, Q191

#### `CMP_O02` — unassigned_complaints_count
- **Question Template:** `"How many complaints are unassigned right now by department?"`
- **Retrieval Keywords:** `how many complaints are unassigned right now department wise unassigned open count stuck`
- **Placeholders:** None
- **SQL Query Template:**
  ```sql
  SELECT d.department_name, COUNT(*) AS unassigned_count
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id AND s.is_terminal = false
  LEFT JOIN department_master d ON d.id = c.department_id
  WHERE c.assigned_to_id IS NULL AND c.ward_officer_id IS NULL
  GROUP BY d.department_name
  ORDER BY unassigned_count DESC;
  ```
- **Covered Questions:** Q188, Q189, Q193

#### `CMP_O03` — ward_staffing_coverage_gaps
- **Question Template:** `"Show wards where no L1 officer is mapped for a department."`
- **Retrieval Keywords:** `show wards where no l1 officer is mapped for a department coverage gaps staffing shortage`
- **Placeholders:**
  - `limit`: `INTEGER` (default: `20`)
- **SQL Query Template:**
  ```sql
  SELECT w.ward_name, d.department_name
  FROM ward_master w
  CROSS JOIN department_master d
  WHERE w.ward_number IS NOT NULL AND d.is_active = true
    AND NOT EXISTS (
        SELECT 1 FROM department_ward_officer dwo
        WHERE dwo.ward_id = w.id AND dwo.department_id = d.id AND dwo.is_active = true
    )
  LIMIT :limit;
  ```
- **Covered Questions:** Q190, Q192

---

### Category P: Specific Complaint Lookup (Q194–Q200)

#### `CMP_P01` — specific_complaint_status_card
- **Question Template:** `"What is the status of complaint {complaint_number}?"`
- **Retrieval Keywords:** `what is the status of complaint cms number full details officer ward category sla remaining escalation level`
- **Placeholders:**
  - `complaint_number`: `STRING` (Required)
- **SQL Query Template:**
  ```sql
  SELECT c.complaint_number, c.title, s.status_name, s.status_name_mar,
         cat.category_name AS category, d.department_name, w.ward_name,
         u.full_name AS assigned_officer,
         c.created_at, c.sla_deadline,
         GREATEST(c.sla_deadline - now(), interval '0') AS sla_remaining,
         c.escalation_level, c.reopen_count
  FROM complaint c
  JOIN status_master s ON s.id = c.status_id
  LEFT JOIN category_master cat ON cat.id = c.category_id
  LEFT JOIN department_master d ON d.id = c.department_id
  LEFT JOIN ward_master w ON w.id = c.ward_id
  LEFT JOIN user_master u ON u.id = COALESCE(c.assigned_to_id, c.ward_officer_id)
  WHERE c.complaint_number = :complaint_number;
  ```
- **Covered Questions:** Q194, Q195, Q196, Q199, Q200

#### `CMP_P02` — specific_complaint_history_timeline
- **Question Template:** `"Show full action history of complaint {complaint_number}."`
- **Retrieval Keywords:** `show full history action history timeline events taken for complaint cms number`
- **Placeholders:**
  - `complaint_number`: `STRING` (Required)
- **SQL Query Template:**
  ```sql
  SELECT h.created_at, h.action_type, h.remarks, u.full_name AS by_officer
  FROM complaint_action_history h
  JOIN complaint c ON c.id = h.complaint_id
  LEFT JOIN user_master u ON u.id = h.performed_by_id
  WHERE c.complaint_number = :complaint_number
  ORDER BY h.created_at ASC;
  ```
- **Covered Questions:** Q197, Q198

---

## 47 Template Summary Matrix

| Category | Template IDs | Covered Questions Range |
|---|---|---|
| **A. Pending / Open** | `CMP_A01`, `CMP_A02`, `CMP_A03`, `CMP_A04` | Q1 – Q20 |
| **B. Officer Performance** | `CMP_B01`, `CMP_B02`, `CMP_B03` | Q21 – Q40 |
| **C. SLA Compliance** | `CMP_C01`, `CMP_C02`, `CMP_C03`, `CMP_C04` | Q41 – Q55 |
| **D. Escalations** | `CMP_D01`, `CMP_D02`, `CMP_D03` | Q56 – Q67 |
| **E. Category Analysis** | `CMP_E01`, `CMP_E02`, `CMP_E03` | Q68 – Q82 |
| **F. Ward / Zone Comparison** | `CMP_F01`, `CMP_F02`, `CMP_F03` | Q83 – Q97 |
| **G. Trends & Time Analysis** | `CMP_G01`, `CMP_G02`, `CMP_G03`, `CMP_G04` | Q98 – Q112 |
| **H. Resolution Stats** | `CMP_H01`, `CMP_H02`, `CMP_H03` | Q113 – Q127 |
| **I. Citizen Feedback** | `CMP_I01`, `CMP_I02`, `CMP_I03` | Q128 – Q137 |
| **J. Hotspots & Location** | `CMP_J01`, `CMP_J02` | Q138 – Q147 |
| **K. Department Deep-Dive** | `CMP_K01`, `CMP_K02`, `CMP_K03` | Q148 – Q159 |
| **L. Aging / Oldest** | `CMP_L01`, `CMP_L02`, `CMP_L03` | Q160 – Q169 |
| **M. Source / Channel** | `CMP_M01`, `CMP_M02` | Q170 – Q177 |
| **N. Reopened / Rejected** | `CMP_N01`, `CMP_N02`, `CMP_N03` | Q178 – Q185 |
| **O. Workload & Staffing** | `CMP_O01`, `CMP_O02`, `CMP_O03` | Q186 – Q193 |
| **P. Specific Lookup** | `CMP_P01`, `CMP_P02` | Q194 – Q200 |
| **TOTAL** | **47 Templates** | **100% of 200 Questions** |
