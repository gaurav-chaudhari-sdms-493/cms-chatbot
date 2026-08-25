# PMC Database Meaningful Schema & Entity Relationships Specification

**Database**: `pmc_cms_new1`  
**Connection String**: `postgresql://cms-readonly-user:rfwxwbwyeue@115.160.211.220:2419/pmc_cms_new1`  
**Meaningful Entities & Views**: **60 tables**

---

## 1. High-Level Entity-Relationship (ER) Architecture

```mermaid
erDiagram
    COMPLAINT ||--o{ DEPARTMENT_MASTER : "department_id"
    COMPLAINT ||--o{ WARD_MASTER : "ward_id"
    COMPLAINT ||--o{ CATEGORY_MASTER : "category_id"
    COMPLAINT ||--o{ SUB_CATEGORY_MASTER : "sub_category_id"
    COMPLAINT ||--o{ STATUS_MASTER : "status_id"
    COMPLAINT ||--o{ USER_MASTER : "citizen_id / assigned_to_id"
    COMPLAINT ||--o{ PRABHAG_MASTER : "prabhag_id"
    COMPLAINT ||--o{ ZONE_MASTER : "zone_id"
    COMPLAINT ||--|{ COMPLAINT_ACTION_HISTORY : "complaint_id"
    COMPLAINT ||--|{ COMPLAINT_DOCUMENT : "complaint_id"
    COMPLAINT ||--|{ COMPLAINT_FEEDBACK : "complaint_id"
    COMPLAINT ||--|{ CALLCENTER_FEEDBACK : "complaint_id"
    USER_MASTER ||--o{ ROLE_MASTER : "user_role_mapping"
    DEPARTMENT_MASTER ||--o{ DEPARTMENT_WARD_OFFICER : "department_id"
    WARD_MASTER ||--o{ DEPARTMENT_WARD_OFFICER : "ward_id"
```

---

## 2. Table Summary & Relationship Matrix

| Table Name | Row Count | Primary Key | Foreign Keys / Entity Relations | Indexes | Description |
| --- | --- | --- | --- | --- | --- |
| `address_alias` | 0 | `id` | `ward_id` ➡️ `ward_master.id`<br/>`prabhag_id` ➡️ `prabhag_master.id`<br/>`verified_by_id` ➡️ `user_master.id` | 4 indexes | Location name alias mappings for Pune landmarks. |
| `ai_analysis_settings` | 1 | `id` | None | 1 indexes | Configuration parameters for AI analytics & NLP processing. |
| `assignment_rotation` | 1,694 | `id` | `prabhag_id` ➡️ `prabhag_master.id`<br/>`department_id` ➡️ `department_master.id` | 2 indexes | Auto-assignment rotation ladder for distributing incoming complaints to field officers. |
| `callcenter_feedback` | 332,597 | `id` | `complaint_id` ➡️ `complaint.id` | 3 indexes | Outbound call center follow-up ratings and citizen feedback collected by agents. |
| `category_master` | 90 | `id` | None | 2 indexes | Primary complaint category classification (Potholes, Garbage Dumping, Water Leakage, Drainage Overflow). |
| `category_routing_rule` | 0 | `id` | `category_id` ➡️ `category_master.id`<br/>`sub_category_id` ➡️ `sub_category_master.id`<br/>`ward_id` ➡️ `ward_master.id` | 2 indexes | Default routing rules mapping specific complaint categories to default departments. |
| `complaint` | 573,573 | `id` | `citizen_id` ➡️ `user_master.id`<br/>`category_id` ➡️ `category_master.id`<br/>`sub_category_id` ➡️ `sub_category_master.id`<br/>`status_id` ➡️ `status_master.id`<br/>`zone_id` ➡️ `zone_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`prabhag_id` ➡️ `prabhag_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`assigned_to_id` ➡️ `user_master.id`<br/>`resolved_by_id` ➡️ `user_master.id`<br/>`registered_by_id` ➡️ `user_master.id`<br/>`parent_complaint_id` ➡️ `complaint.id`<br/>`peth_id` ➡️ `peth_master.id`<br/>`external_app_id` ➡️ `external_app.id` | 23 indexes | Central transactional table holding all PMC citizen grievances, SLA deadlines, locations, and routing state. |
| `complaint_action_history` | 2,268,267 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`from_status_id` ➡️ `status_master.id`<br/>`to_status_id` ➡️ `status_master.id`<br/>`from_user_id` ➡️ `user_master.id`<br/>`to_user_id` ➡️ `user_master.id`<br/>`performed_by_id` ➡️ `user_master.id` | 6 indexes | Audit log of all complaint state transitions, status updates, officer reassignment actions, and remarks. |
| `complaint_assignment` | 326,069 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`assigned_to_id` ➡️ `user_master.id`<br/>`category_id` ➡️ `category_master.id` | 6 indexes | Tracks officer assignments, reassignment history, and workload distribution per complaint. |
| `complaint_categories` | 64,039 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`category_id` ➡️ `category_master.id`<br/>`sub_category_id` ➡️ `sub_category_master.id` | 5 indexes | Junction table mapping specific sub-categories and categories to municipal departments. |
| `complaint_cross_transfer_request` | 11 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`category_id` ➡️ `category_master.id`<br/>`sub_category_id` ➡️ `sub_category_master.id` | 1 indexes | Inter-departmental complaint transfer requests and approval workflow logs. |
| `complaint_document` | 409,343 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`uploaded_by_id` ➡️ `user_master.id` | 3 indexes | Stores uploaded media attachments, photos, and document proofs for complaint registration & resolution. |
| `complaint_feedback` | 184,487 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`citizen_id` ➡️ `user_master.id` | 4 indexes | Citizen feedback, ratings, and satisfaction reviews submitted via mobile app or web portal. |
| `daily_summary` | 433,084 | `id` | `zone_id` ➡️ `zone_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`category_id` ➡️ `category_master.id` | 4 indexes | Daily statistical metrics on registered, pending, resolved, and breached complaints. |
| `department_master` | 166 | `id` | None | 2 indexes | PMC administrative departments (Road, Solid Waste Management, Drainage, Water Supply, Electrical, etc.). |
| `department_ward_config` | 0 | `id` | `department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id` | 2 indexes | Department configuration settings per ward. |
| `department_ward_officer` | 1,436 | `id` | `department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`user_id` ➡️ `user_master.id`<br/>`prabhag_id` ➡️ `prabhag_master.id` | 8 indexes | Maps specific officers to department-ward jurisdiction responsibility matrix. |
| `designation_master` | 869 | `id` | None | 2 indexes | Official designations and rank designations for municipal staff. |
| `escalation_history` | 75 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`from_user_id` ➡️ `user_master.id`<br/>`to_user_id` ➡️ `user_master.id` | 3 indexes | Log of triggered SLA escalations across hierarchy tiers. |
| `escalation_rule` | 2,394 | `id` | `category_id` ➡️ `category_master.id` | 3 indexes | SLA escalation logic defining automated escalation paths when deadlines pass. |
| `external_app` | 3 | `id` | None | 5 indexes | External application integration credentials and API endpoints. |
| `fcm_token` | 0 | `id` | `user_id` ➡️ `user_master.id` | 3 indexes | Firebase Cloud Messaging tokens for mobile push notifications. |
| `geocoding_cache` | 0 | `id` | None | 3 indexes | Geocoding location lookup cache for address resolution. |
| `holiday_master` | 35 | `id` | None | 3 indexes | Official municipal calendar holidays excluded from SLA resolution clock calculations. |
| `ladder_slot` | 0 | `id` | None | 1 indexes | Auto-assignment ladder slot configuration. |
| `ladder_slot_assignment` | 0 | `id` | `user_id` ➡️ `user_master.id` | 2 indexes | Current active assignments on rotation ladders. |
| `ladder_slot_department` | 0 | `id` | `department_id` ➡️ `department_master.id` | 2 indexes | Department mapping for assignment rotation ladders. |
| `location_correction_log` | 0 | `id` | `complaint_id` ➡️ `complaint.id` | 4 indexes | Audit trail of citizen or officer location boundary corrections. |
| `notification_log` | 17,817 | `id` | `user_id` ➡️ `user_master.id`<br/>`complaint_id` ➡️ `complaint.id` | 6 indexes | Log of sent SMS, Email, and Push notifications. |
| `notification_preference` | 0 | `id` | `user_id` ➡️ `user_master.id` | 2 indexes | User communication channel preferences. |
| `notification_template` | 16 | `id` | None | 3 indexes | Templates for citizen notification messages. |
| `officer_jurisdiction` | 7,923 | `id` | `user_id` ➡️ `user_master.id`<br/>`zone_id` ➡️ `zone_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`prabhag_id` ➡️ `prabhag_master.id`<br/>`department_id` ➡️ `department_master.id` | 4 indexes | Defines geographic & department boundaries assigned to individual officers. |
| `officer_performance` | 15,512 | `id` | `user_id` ➡️ `user_master.id` | 2 indexes | Pre-calculated monthly KPI performance metrics for field officers. |
| `officer_transfer_log` | 0 | `id` | `user_id` ➡️ `user_master.id`<br/>`department_id` ➡️ `department_master.id` | 7 indexes | Historical record of officer transfers between wards/departments. |
| `permission` | 30 | `id` | None | 5 indexes | Granular system permission definitions. |
| `peth_master` | 0 | `id` | None | 2 indexes | Historical peth area classifications within Pune municipal limits. |
| `prabhag_master` | 125 | `id` | None | 3 indexes | Municipal electoral prabhags (constituencies) within wards. |
| `role_master` | 18 | `id` | None | 2 indexes | RBAC user roles (Citizen, Officer, Ward Engineer, Department Admin, System Admin). |
| `role_permission` | 232 | `id` | `role_id` ➡️ `role_master.id`<br/>`permission_id` ➡️ `permission.id` | 4 indexes | Permission mappings assigned to specific user roles. |
| `sla_configuration` | 9 | `id` | `category_id` ➡️ `category_master.id`<br/>`sub_category_id` ➡️ `sub_category_master.id` | 2 indexes | Defines SLA target resolution hours and grace periods by category & priority. |
| `sla_display_settings` | 1 | `id` | None | 1 indexes | UI display rules and color thresholds for SLA status indicators. |
| `status_master` | 10 | `id` | None | 2 indexes | Workflow status codes (Registered, Assigned, Escalated, Pending Info, Transferred, Resolved, Closed). |
| `sub_category_master` | 504 | `id` | None | 3 indexes | Detailed sub-issue types under each main category. |
| `swachhata_category` | 20 | `id` | None | 2 indexes | Swachh Bharat Swachhata cleanliness complaint categories. |
| `swachhata_complaint` | 16 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`swachhata_category_id` ➡️ `swachhata_category.id` | 3 indexes | Swachh Bharat integration complaint records. |
| `user_master` | 432,880 | `id` | None | 10 indexes | All users in the system including citizens, field officers, ward engineers, department heads, and call center staff. |
| `user_role_mapping` | 42,109 | `id` | `user_id` ➡️ `user_master.id`<br/>`role_id` ➡️ `role_master.id` | 3 indexes | Maps users to one or more user roles. |
| `vw_dd_awaiting_feedback_7d` | 284,007 | `id` | `category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id` | 0 indexes | View: Complaints awaiting citizen feedback within 7 days. |
| `vw_dd_due_24h` | 36 | `id` | `status_id` ➡️ `status_master.id`<br/>`category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id`<br/>`assigned_to_id` ➡️ `user_master.id` | 0 indexes | View: Complaints expiring within 24 hours. |
| `vw_dd_due_3d` | 101 | `id` | `status_id` ➡️ `status_master.id`<br/>`category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id`<br/>`assigned_to_id` ➡️ `user_master.id` | 0 indexes | View: Complaints expiring within 3 days. |
| `vw_dd_escalated_to_ac` | 15 | `id` | `status_id` ➡️ `status_master.id`<br/>`category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id`<br/>`assigned_to_id` ➡️ `user_master.id` | 0 indexes | View: Complaints escalated to Additional Commissioner level. |
| `vw_dd_kpi_live` | 1 | `None` | None | 0 indexes | View: Real-time top-level KPI metrics summary. |
| `vw_dd_late_complaints` | 24,373 | `id` | `status_id` ➡️ `status_master.id`<br/>`category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id`<br/>`assigned_to_id` ➡️ `user_master.id` | 0 indexes | View: Open complaints currently breaching SLA deadline. |
| `vw_dd_open_complaints` | 31,677 | `id` | `status_id` ➡️ `status_master.id`<br/>`category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id`<br/>`assigned_to_id` ➡️ `user_master.id` | 0 indexes | View: Active open complaints across all wards. |
| `vw_dd_reopened` | 12,236 | `id` | `category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id` | 0 indexes | View: Reopened complaints tracking view. |
| `vw_dd_resolved` | 488,586 | `id` | `category_id` ➡️ `category_master.id`<br/>`department_id` ➡️ `department_master.id`<br/>`ward_id` ➡️ `ward_master.id`<br/>`zone_id` ➡️ `zone_master.id` | 0 indexes | View: Resolved complaints analytical view. |
| `vw_dd_swachhata_failures` | 0 | `id` | `complaint_id` ➡️ `complaint.id`<br/>`swachhata_category_id` ➡️ `swachhata_category.id` | 0 indexes | View: Failed or SLA-breached Swachhata complaints. |
| `ward_master` | 32 | `id` | None | 3 indexes | PMC administrative regional wards (Aundh-Baner, Kothrud-Bavdhan, Hadapsar, Ahmednagar Road, etc.). |
| `ward_performance` | 448 | `id` | `ward_id` ➡️ `ward_master.id` | 2 indexes | Pre-calculated monthly performance rollups per ward. |
| `zone_master` | 14 | `id` | None | 2 indexes | Administrative zonal divisions grouping multiple wards across Pune city. |

---

## 3. Detailed Table, Column, Key & Relationship Specifications

### Table / View: `address_alias`
**Description**: Location name alias mappings for Pune landmarks.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `prabhag_id` ➡️ **`prabhag_master.id`** (Many-to-One (N:1))
  - `verified_by_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `address_alias_pkey`: `CREATE UNIQUE INDEX address_alias_pkey ON public.address_alias USING btree (id)`
  - `address_alias_alias_text`: `CREATE INDEX address_alias_alias_text ON public.address_alias USING btree (alias_text)`
  - `address_alias_ward_id`: `CREATE INDEX address_alias_ward_id ON public.address_alias USING btree (ward_id)`
  - `idx_address_alias_trgm`: `CREATE INDEX idx_address_alias_trgm ON public.address_alias USING gin (alias_text gin_trgm_ops)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('address_alias_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `alias_text` | `character varying` | NO | `-` | - |
| `alias_text_mar` | `character varying` | YES | `-` | - |
| `canonical_address` | `text` | NO | `-` | - |
| `latitude` | `numeric` | YES | `-` | - |
| `longitude` | `numeric` | YES | `-` | - |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `prabhag_id` | `integer` | YES | `-` | 🔗 FK ➡️ `prabhag_master.id` |
| `alias_type` | `USER-DEFINED` | YES | `'LANDMARK'::enum_address_alias_alias_type` | - |
| `source` | `USER-DEFINED` | YES | `'ADMIN_ADDED'::enum_address_alias_source` | - |
| `is_verified` | `boolean` | YES | `false` | - |
| `verified_by_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `usage_count` | `integer` | YES | `0` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `ai_analysis_settings`
**Description**: Configuration parameters for AI analytics & NLP processing.  
- **Total Rows**: 1  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `ai_analysis_settings_pkey`: `CREATE UNIQUE INDEX ai_analysis_settings_pkey ON public.ai_analysis_settings USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('ai_analysis_settings_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `ai_analysis_visible` | `boolean` | NO | `true` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

---

### Table / View: `assignment_rotation`
**Description**: Auto-assignment rotation ladder for distributing incoming complaints to field officers.  
- **Total Rows**: 1,694  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `prabhag_id` ➡️ **`prabhag_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `assignment_rotation_pkey`: `CREATE UNIQUE INDEX assignment_rotation_pkey ON public.assignment_rotation USING btree (id)`
  - `assignment_rotation_unique`: `CREATE UNIQUE INDEX assignment_rotation_unique ON public.assignment_rotation USING btree (routing_type, prabhag_id, department_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('assignment_rotation_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `routing_type` | `character varying` | NO | `-` | - |
| `prabhag_id` | `integer` | NO | `-` | 🔗 FK ➡️ `prabhag_master.id` |
| `department_id` | `integer` | NO | `-` | 🔗 FK ➡️ `department_master.id` |
| `last_officer_id` | `integer` | YES | `-` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

---

### Table / View: `callcenter_feedback`
**Description**: Outbound call center follow-up ratings and citizen feedback collected by agents.  
- **Total Rows**: 332,597  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `callcenter_feedback_pkey`: `CREATE UNIQUE INDEX callcenter_feedback_pkey ON public.callcenter_feedback USING btree (id)`
  - `callcenter_feedback_legacy_id_key`: `CREATE UNIQUE INDEX callcenter_feedback_legacy_id_key ON public.callcenter_feedback USING btree (legacy_id)`
  - `callcenter_feedback_complaint_id`: `CREATE INDEX callcenter_feedback_complaint_id ON public.callcenter_feedback USING btree (complaint_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('callcenter_feedback_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `feedback` | `text` | YES | `-` | - |
| `feedback_reason` | `character varying` | YES | `-` | - |
| `officer_feedback` | `text` | YES | `-` | - |
| `officer_feedback_reason` | `character varying` | YES | `-` | - |
| `non_performing_officer` | `character varying` | YES | `-` | - |
| `legacy_id` | `bigint` | NO | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `now()` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

---

### Table / View: `category_master`
**Description**: Primary complaint category classification (Potholes, Garbage Dumping, Water Leakage, Drainage Overflow).  
- **Total Rows**: 90  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `category_master_category_code_key`: `CREATE UNIQUE INDEX category_master_category_code_key ON public.category_master USING btree (category_code)`
  - `category_master_pkey`: `CREATE UNIQUE INDEX category_master_pkey ON public.category_master USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('category_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `category_code` | `character varying` | NO | `-` | - |
| `category_name` | `character varying` | NO | `-` | - |
| `category_name_mar` | `character varying` | YES | `-` | - |
| `description` | `text` | YES | `-` | - |
| `icon` | `character varying` | YES | `-` | - |
| `display_order` | `integer` | YES | `0` | - |
| `default_routing_type` | `USER-DEFINED` | NO | `'WARD'::enum_category_master_default_routing_type` | - |
| `default_department_id` | `integer` | YES | `-` | - |
| `default_sla_hours` | `numeric` | NO | `72` | - |
| `default_priority` | `USER-DEFINED` | YES | `'NORMAL'::enum_category_master_default_priority` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `category_type` | `character varying` | YES | `-` | - |
| `routing_area_type` | `USER-DEFINED` | NO | `'PRABHAG'::enum_category_master_routing_area_type` | - |
| `resolved_photo_required` | `boolean` | NO | `true` | - |

---

### Table / View: `category_routing_rule`
**Description**: Default routing rules mapping specific complaint categories to default departments.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `sub_category_id` ➡️ **`sub_category_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `category_routing_rule_pkey`: `CREATE UNIQUE INDEX category_routing_rule_pkey ON public.category_routing_rule USING btree (id)`
  - `category_routing_rule_category_id_ward_id`: `CREATE INDEX category_routing_rule_category_id_ward_id ON public.category_routing_rule USING btree (category_id, ward_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('category_routing_rule_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `category_id` | `integer` | NO | `-` | 🔗 FK ➡️ `category_master.id` |
| `sub_category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `sub_category_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `routing_type` | `USER-DEFINED` | NO | `-` | - |
| `target_department_id` | `integer` | YES | `-` | - |
| `target_user_id` | `integer` | YES | `-` | - |
| `priority` | `integer` | YES | `0` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `complaint`
**Description**: Central transactional table holding all PMC citizen grievances, SLA deadlines, locations, and routing state.  
- **Total Rows**: 573,573  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `citizen_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `sub_category_id` ➡️ **`sub_category_master.id`** (Many-to-One (N:1))
  - `status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `prabhag_id` ➡️ **`prabhag_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `assigned_to_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `resolved_by_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `registered_by_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `parent_complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `peth_id` ➡️ **`peth_master.id`** (Many-to-One (N:1))
  - `external_app_id` ➡️ **`external_app.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `complaint_complaint_number_key`: `CREATE UNIQUE INDEX complaint_complaint_number_key ON public.complaint USING btree (complaint_number)`
  - `complaint_pkey`: `CREATE UNIQUE INDEX complaint_pkey ON public.complaint USING btree (id)`
  - `complaint_assigned_to_id`: `CREATE INDEX complaint_assigned_to_id ON public.complaint USING btree (assigned_to_id)`
  - `complaint_category_id`: `CREATE INDEX complaint_category_id ON public.complaint USING btree (category_id)`
  - `complaint_citizen_id`: `CREATE INDEX complaint_citizen_id ON public.complaint USING btree (citizen_id)`
  - `complaint_complaint_number`: `CREATE INDEX complaint_complaint_number ON public.complaint USING btree (complaint_number)`
  - `complaint_created_at`: `CREATE INDEX complaint_created_at ON public.complaint USING btree (created_at)`
  - `complaint_department_id`: `CREATE INDEX complaint_department_id ON public.complaint USING btree (department_id)`
  - `complaint_priority`: `CREATE INDEX complaint_priority ON public.complaint USING btree (priority)`
  - `complaint_sla_status`: `CREATE INDEX complaint_sla_status ON public.complaint USING btree (sla_status)`
  - `complaint_status_id`: `CREATE INDEX complaint_status_id ON public.complaint USING btree (status_id)`
  - `complaint_ward_id`: `CREATE INDEX complaint_ward_id ON public.complaint USING btree (ward_id)`
  - `idx_complaint_escalated_main`: `CREATE INDEX idx_complaint_escalated_main ON public.complaint USING btree (escalated_to_main_dept)`
  - `idx_complaint_external_app_id`: `CREATE INDEX idx_complaint_external_app_id ON public.complaint USING btree (external_app_id)`
  - `idx_complaint_temp_complaint_id`: `CREATE UNIQUE INDEX idx_complaint_temp_complaint_id ON public.complaint USING btree (temp_complaint_id) WHERE (temp_complaint_id IS NOT NULL)`
  - `idx_complaint_ward_officer`: `CREATE INDEX idx_complaint_ward_officer ON public.complaint USING btree (ward_officer_id)`
  - `idx_complaint_registered_by_id`: `CREATE INDEX idx_complaint_registered_by_id ON public.complaint USING btree (registered_by_id)`
  - `idx_complaint_resolved_by_id`: `CREATE INDEX idx_complaint_resolved_by_id ON public.complaint USING btree (resolved_by_id)`
  - `idx_complaint_resolved_at`: `CREATE INDEX idx_complaint_resolved_at ON public.complaint USING btree (resolved_at)`
  - `idx_complaint_closed_at`: `CREATE INDEX idx_complaint_closed_at ON public.complaint USING btree (closed_at)`
  - `idx_complaint_status_deadline`: `CREATE INDEX idx_complaint_status_deadline ON public.complaint USING btree (status_id, sla_deadline)`
  - `idx_complaint_status_scope`: `CREATE INDEX idx_complaint_status_scope ON public.complaint USING btree (status_id, ward_id, department_id, sla_status)`
  - `idx_complaint_status_assigned`: `CREATE INDEX idx_complaint_status_assigned ON public.complaint USING btree (status_id, assigned_to_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('complaint_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | NO | `-` | - |
| `citizen_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `sub_category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `sub_category_master.id` |
| `title` | `character varying` | NO | `-` | - |
| `description` | `text` | NO | `-` | - |
| `description_mar` | `text` | YES | `-` | - |
| `description_language` | `USER-DEFINED` | YES | `'en'::enum_complaint_description_language` | - |
| `status_id` | `integer` | NO | `-` | 🔗 FK ➡️ `status_master.id` |
| `priority` | `USER-DEFINED` | YES | `'NORMAL'::enum_complaint_priority` | - |
| `source_channel` | `USER-DEFINED` | YES | `'WEB'::enum_complaint_source_channel` | - |
| `latitude` | `numeric` | YES | `-` | - |
| `longitude` | `numeric` | YES | `-` | - |
| `address` | `text` | YES | `-` | - |
| `landmark` | `character varying` | YES | `-` | - |
| `location_input_type` | `USER-DEFINED` | YES | `-` | - |
| `gis_confidence` | `numeric` | YES | `-` | - |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `prabhag_id` | `integer` | YES | `-` | 🔗 FK ➡️ `prabhag_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `routing_type` | `USER-DEFINED` | YES | `-` | - |
| `assigned_to_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `sla_hours` | `numeric` | YES | `-` | - |
| `sla_deadline` | `timestamp with time zone` | YES | `-` | - |
| `sla_paused_at` | `timestamp with time zone` | YES | `-` | - |
| `sla_paused_duration_mins` | `integer` | YES | `0` | - |
| `sla_status` | `USER-DEFINED` | YES | `'ON_TRACK'::enum_complaint_sla_status` | - |
| `escalation_level` | `integer` | YES | `0` | - |
| `last_escalated_at` | `timestamp with time zone` | YES | `-` | - |
| `resolution_remarks` | `text` | YES | `-` | - |
| `resolution_remarks_mar` | `text` | YES | `-` | - |
| `resolved_at` | `timestamp with time zone` | YES | `-` | - |
| `resolved_by_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `closed_at` | `timestamp with time zone` | YES | `-` | - |
| `registered_by_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `is_duplicate` | `boolean` | YES | `false` | - |
| `parent_complaint_id` | `integer` | YES | `-` | 🔗 FK ➡️ `complaint.id` |
| `reopen_count` | `integer` | YES | `0` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `ward_officer_id` | `integer` | YES | `-` | - |
| `escalated_to_main_dept` | `boolean` | NO | `false` | - |
| `escalated_to_main_dept_at` | `timestamp with time zone` | YES | `-` | - |
| `escalation_reason` | `text` | YES | `-` | - |
| `prabhag_number` | `integer` | YES | `-` | - |
| `external_reference_id` | `character varying` | YES | `-` | - |
| `peth_id` | `integer` | YES | `-` | 🔗 FK ➡️ `peth_master.id` |
| `temp_complaint_id` | `bigint` | YES | `-` | - |
| `external_app_id` | `integer` | YES | `-` | 🔗 FK ➡️ `external_app.id` |
| `temp_comp_id` | `character varying` | YES | `-` | - |

---

### Table / View: `complaint_action_history`
**Description**: Audit log of all complaint state transitions, status updates, officer reassignment actions, and remarks.  
- **Total Rows**: 2,268,267  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `from_status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `to_status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `from_user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `to_user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `performed_by_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `complaint_action_history_pkey`: `CREATE UNIQUE INDEX complaint_action_history_pkey ON public.complaint_action_history USING btree (id)`
  - `complaint_action_history_complaint_id`: `CREATE INDEX complaint_action_history_complaint_id ON public.complaint_action_history USING btree (complaint_id)`
  - `complaint_action_history_created_at`: `CREATE INDEX complaint_action_history_created_at ON public.complaint_action_history USING btree (created_at)`
  - `idx_complaint_action_history_performed_by_id`: `CREATE INDEX idx_complaint_action_history_performed_by_id ON public.complaint_action_history USING btree (performed_by_id)`
  - `idx_complaint_action_history_from_user_id`: `CREATE INDEX idx_complaint_action_history_from_user_id ON public.complaint_action_history USING btree (from_user_id)`
  - `idx_complaint_action_history_to_user_id`: `CREATE INDEX idx_complaint_action_history_to_user_id ON public.complaint_action_history USING btree (to_user_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('complaint_action_history_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `action_type` | `USER-DEFINED` | NO | `-` | - |
| `from_status_id` | `integer` | YES | `-` | 🔗 FK ➡️ `status_master.id` |
| `to_status_id` | `integer` | YES | `-` | 🔗 FK ➡️ `status_master.id` |
| `from_user_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `to_user_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `performed_by_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `remarks` | `text` | YES | `-` | - |
| `remarks_mar` | `text` | YES | `-` | - |
| `metadata` | `jsonb` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `complaint_assignment`
**Description**: Tracks officer assignments, reassignment history, and workload distribution per complaint.  
- **Total Rows**: 326,069  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `assigned_to_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `complaint_assignment_pkey`: `CREATE UNIQUE INDEX complaint_assignment_pkey ON public.complaint_assignment USING btree (id)`
  - `complaint_assignment_assigned_to_id_is_current`: `CREATE INDEX complaint_assignment_assigned_to_id_is_current ON public.complaint_assignment USING btree (assigned_to_id, is_current)`
  - `complaint_assignment_category_id`: `CREATE INDEX complaint_assignment_category_id ON public.complaint_assignment USING btree (category_id)`
  - `complaint_assignment_complaint_id_is_current`: `CREATE INDEX complaint_assignment_complaint_id_is_current ON public.complaint_assignment USING btree (complaint_id, is_current)`
  - `complaint_assignment_status`: `CREATE INDEX complaint_assignment_status ON public.complaint_assignment USING btree (status)`
  - `idx_complaint_assignment_assigned_by_id`: `CREATE INDEX idx_complaint_assignment_assigned_by_id ON public.complaint_assignment USING btree (assigned_by_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('complaint_assignment_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `assigned_to_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `assigned_by_id` | `integer` | YES | `-` | - |
| `assignment_type` | `USER-DEFINED` | YES | `'AUTO'::enum_complaint_assignment_assignment_type` | - |
| `reason` | `text` | YES | `-` | - |
| `is_current` | `boolean` | YES | `true` | - |
| `assigned_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `acknowledged_at` | `timestamp with time zone` | YES | `-` | - |
| `completed_at` | `timestamp with time zone` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `status` | `USER-DEFINED` | NO | `'PENDING'::enum_complaint_assignment_status` | - |
| `resolution_remarks` | `text` | YES | `-` | - |

---

### Table / View: `complaint_categories`
**Description**: Junction table mapping specific sub-categories and categories to municipal departments.  
- **Total Rows**: 64,039  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `sub_category_id` ➡️ **`sub_category_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `complaint_categories_pkey`: `CREATE UNIQUE INDEX complaint_categories_pkey ON public.complaint_categories USING btree (id)`
  - `unique_complaint_category`: `CREATE UNIQUE INDEX unique_complaint_category ON public.complaint_categories USING btree (complaint_id, category_id)`
  - `idx_complaint_categories_category_id`: `CREATE INDEX idx_complaint_categories_category_id ON public.complaint_categories USING btree (category_id)`
  - `idx_complaint_categories_complaint_id`: `CREATE INDEX idx_complaint_categories_complaint_id ON public.complaint_categories USING btree (complaint_id)`
  - `idx_complaint_categories_is_primary`: `CREATE INDEX idx_complaint_categories_is_primary ON public.complaint_categories USING btree (is_primary)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('complaint_categories_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `category_id` | `integer` | NO | `-` | 🔗 FK ➡️ `category_master.id` |
| `sub_category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `sub_category_master.id` |
| `is_primary` | `boolean` | NO | `false` | - |
| `display_order` | `integer` | NO | `0` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `complaint_cross_transfer_request`
**Description**: Inter-departmental complaint transfer requests and approval workflow logs.  
- **Total Rows**: 11  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `sub_category_id` ➡️ **`sub_category_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `complaint_cross_transfer_request_pkey`: `CREATE UNIQUE INDEX complaint_cross_transfer_request_pkey ON public.complaint_cross_transfer_request USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('complaint_cross_transfer_request_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `requested_by_id` | `integer` | NO | `-` | - |
| `transfer_to_id` | `integer` | NO | `-` | - |
| `reception_id` | `integer` | NO | `-` | - |
| `reason` | `text` | NO | `-` | - |
| `status` | `character varying` | NO | `'PENDING'::character varying` | - |
| `reception_remarks` | `text` | YES | `-` | - |
| `decided_at` | `timestamp with time zone` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `sub_category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `sub_category_master.id` |

---

### Table / View: `complaint_document`
**Description**: Stores uploaded media attachments, photos, and document proofs for complaint registration & resolution.  
- **Total Rows**: 409,343  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `uploaded_by_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `complaint_document_pkey`: `CREATE UNIQUE INDEX complaint_document_pkey ON public.complaint_document USING btree (id)`
  - `complaint_document_complaint_id`: `CREATE INDEX complaint_document_complaint_id ON public.complaint_document USING btree (complaint_id)`
  - `idx_complaint_document_uploaded_by_id`: `CREATE INDEX idx_complaint_document_uploaded_by_id ON public.complaint_document USING btree (uploaded_by_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('complaint_document_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `document_type` | `USER-DEFINED` | YES | `'COMPLAINT_IMAGE'::enum_complaint_document_document_type` | - |
| `file_name` | `character varying` | NO | `-` | - |
| `file_path` | `character varying` | NO | `-` | - |
| `file_url` | `character varying` | YES | `-` | - |
| `file_size` | `integer` | YES | `-` | - |
| `mime_type` | `character varying` | YES | `-` | - |
| `uploaded_by_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `is_primary` | `boolean` | YES | `false` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `complaint_feedback`
**Description**: Citizen feedback, ratings, and satisfaction reviews submitted via mobile app or web portal.  
- **Total Rows**: 184,487  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `citizen_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `complaint_feedback_pkey`: `CREATE UNIQUE INDEX complaint_feedback_pkey ON public.complaint_feedback USING btree (id)`
  - `complaint_feedback_citizen_id`: `CREATE INDEX complaint_feedback_citizen_id ON public.complaint_feedback USING btree (citizen_id)`
  - `complaint_feedback_complaint_id`: `CREATE INDEX complaint_feedback_complaint_id ON public.complaint_feedback USING btree (complaint_id)`
  - `complaint_feedback_complaint_id_unique`: `CREATE UNIQUE INDEX complaint_feedback_complaint_id_unique ON public.complaint_feedback USING btree (complaint_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('complaint_feedback_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `citizen_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `rating` | `integer` | NO | `-` | - |
| `is_satisfied` | `boolean` | NO | `-` | - |
| `comment` | `text` | YES | `-` | - |
| `reopen_requested` | `boolean` | YES | `false` | - |
| `reopen_reason` | `text` | YES | `-` | - |
| `feedback_channel` | `USER-DEFINED` | YES | `'WEB'::enum_complaint_feedback_feedback_channel` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `daily_summary`
**Description**: Daily statistical metrics on registered, pending, resolved, and breached complaints.  
- **Total Rows**: 433,084  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `daily_summary_pkey`: `CREATE UNIQUE INDEX daily_summary_pkey ON public.daily_summary USING btree (id)`
  - `daily_summary_department_id_summary_date`: `CREATE INDEX daily_summary_department_id_summary_date ON public.daily_summary USING btree (department_id, summary_date)`
  - `daily_summary_summary_date`: `CREATE INDEX daily_summary_summary_date ON public.daily_summary USING btree (summary_date)`
  - `daily_summary_ward_id_summary_date`: `CREATE INDEX daily_summary_ward_id_summary_date ON public.daily_summary USING btree (ward_id, summary_date)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('daily_summary_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `summary_date` | `date` | NO | `-` | - |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `total_received` | `integer` | YES | `0` | - |
| `total_resolved` | `integer` | YES | `0` | - |
| `total_closed` | `integer` | YES | `0` | - |
| `total_pending` | `integer` | YES | `0` | - |
| `total_escalated` | `integer` | YES | `0` | - |
| `total_reopened` | `integer` | YES | `0` | - |
| `sla_on_track` | `integer` | YES | `0` | - |
| `sla_at_risk` | `integer` | YES | `0` | - |
| `sla_breached` | `integer` | YES | `0` | - |
| `sla_compliance_percent` | `numeric` | YES | `-` | - |
| `critical_count` | `integer` | YES | `0` | - |
| `high_count` | `integer` | YES | `0` | - |
| `normal_count` | `integer` | YES | `0` | - |
| `low_count` | `integer` | YES | `0` | - |
| `web_count` | `integer` | YES | `0` | - |
| `mobile_count` | `integer` | YES | `0` | - |
| `call_center_count` | `integer` | YES | `0` | - |
| `walk_in_count` | `integer` | YES | `0` | - |
| `avg_resolution_hours` | `numeric` | YES | `-` | - |
| `avg_first_response_hours` | `numeric` | YES | `-` | - |
| `avg_rating` | `numeric` | YES | `-` | - |
| `satisfaction_percent` | `numeric` | YES | `-` | - |
| `feedback_count` | `integer` | YES | `0` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `department_master`
**Description**: PMC administrative departments (Road, Solid Waste Management, Drainage, Water Supply, Electrical, etc.).  
- **Total Rows**: 166  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `department_master_department_code_key`: `CREATE UNIQUE INDEX department_master_department_code_key ON public.department_master USING btree (department_code)`
  - `department_master_pkey`: `CREATE UNIQUE INDEX department_master_pkey ON public.department_master USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('department_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `department_code` | `character varying` | NO | `-` | - |
| `department_name` | `character varying` | NO | `-` | - |
| `department_name_mar` | `character varying` | YES | `-` | - |
| `description` | `text` | YES | `-` | - |
| `contact_email` | `character varying` | YES | `-` | - |
| `contact_phone` | `character varying` | YES | `-` | - |
| `hod_user_id` | `integer` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `routing_area_type` | `USER-DEFINED` | NO | `'PRABHAG'::enum_department_master_routing_area_type` | - |
| `include_all_prabhag` | `boolean` | NO | `false` | - |

---

### Table / View: `department_ward_config`
**Description**: Department configuration settings per ward.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `department_ward_config_pkey`: `CREATE UNIQUE INDEX department_ward_config_pkey ON public.department_ward_config USING btree (id)`
  - `idx_dwc_unique_dept_ward`: `CREATE UNIQUE INDEX idx_dwc_unique_dept_ward ON public.department_ward_config USING btree (department_id, ward_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('department_ward_config_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `department_id` | `integer` | NO | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | NO | `-` | 🔗 FK ➡️ `ward_master.id` |
| `max_officers` | `integer` | NO | `3` | - |
| `escalation_threshold_hours` | `integer` | NO | `24` | - |
| `contact_phone` | `character varying` | YES | `-` | - |
| `contact_email` | `character varying` | YES | `-` | - |
| `office_location` | `text` | YES | `-` | - |
| `is_active` | `boolean` | NO | `true` | - |
| `created_by` | `integer` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `department_ward_officer`
**Description**: Maps specific officers to department-ward jurisdiction responsibility matrix.  
- **Total Rows**: 1,436  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `prabhag_id` ➡️ **`prabhag_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `department_ward_officer_pkey`: `CREATE UNIQUE INDEX department_ward_officer_pkey ON public.department_ward_officer USING btree (id)`
  - `idx_dwo_active`: `CREATE INDEX idx_dwo_active ON public.department_ward_officer USING btree (is_active)`
  - `idx_dwo_department`: `CREATE INDEX idx_dwo_department ON public.department_ward_officer USING btree (department_id)`
  - `idx_dwo_dept_ward`: `CREATE INDEX idx_dwo_dept_ward ON public.department_ward_officer USING btree (department_id, ward_id)`
  - `idx_dwo_prabhag`: `CREATE INDEX idx_dwo_prabhag ON public.department_ward_officer USING btree (prabhag_id)`
  - `idx_dwo_unique_assignment`: `CREATE UNIQUE INDEX idx_dwo_unique_assignment ON public.department_ward_officer USING btree (department_id, ward_id, user_id, prabhag_id) WHERE (is_active = true)`
  - `idx_dwo_user`: `CREATE INDEX idx_dwo_user ON public.department_ward_officer USING btree (user_id)`
  - `idx_dwo_ward`: `CREATE INDEX idx_dwo_ward ON public.department_ward_officer USING btree (ward_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('department_ward_officer_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `department_id` | `integer` | NO | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | NO | `-` | 🔗 FK ➡️ `ward_master.id` |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `prabhag_id` | `integer` | YES | `-` | 🔗 FK ➡️ `prabhag_master.id` |
| `is_head` | `boolean` | NO | `false` | - |
| `is_active` | `boolean` | NO | `true` | - |
| `assigned_by` | `integer` | YES | `-` | - |
| `assigned_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `valid_from` | `date` | NO | `CURRENT_DATE` | - |
| `valid_until` | `date` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `designation_master`
**Description**: Official designations and rank designations for municipal staff.  
- **Total Rows**: 869  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `designation_master_designation_code_key`: `CREATE UNIQUE INDEX designation_master_designation_code_key ON public.designation_master USING btree (designation_code)`
  - `designation_master_pkey`: `CREATE UNIQUE INDEX designation_master_pkey ON public.designation_master USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('designation_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `designation_code` | `character varying` | NO | `-` | - |
| `designation_name` | `character varying` | NO | `-` | - |
| `designation_name_mar` | `character varying` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp without time zone` | YES | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp without time zone` | YES | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `escalation_history`
**Description**: Log of triggered SLA escalations across hierarchy tiers.  
- **Total Rows**: 75  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `from_user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `to_user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `escalation_history_pkey`: `CREATE UNIQUE INDEX escalation_history_pkey ON public.escalation_history USING btree (id)`
  - `escalation_history_complaint_id`: `CREATE INDEX escalation_history_complaint_id ON public.escalation_history USING btree (complaint_id)`
  - `escalation_history_escalated_at`: `CREATE INDEX escalation_history_escalated_at ON public.escalation_history USING btree (escalated_at)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('escalation_history_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `escalation_rule_id` | `integer` | YES | `-` | - |
| `from_level` | `integer` | NO | `-` | - |
| `to_level` | `integer` | NO | `-` | - |
| `from_user_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `to_user_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `escalation_type` | `USER-DEFINED` | YES | `'AUTO'::enum_escalation_history_escalation_type` | - |
| `triggered_by` | `USER-DEFINED` | YES | `'SLA_BREACH'::enum_escalation_history_triggered_by` | - |
| `reason` | `text` | YES | `-` | - |
| `sla_status_at_escalation` | `USER-DEFINED` | YES | `-` | - |
| `hours_elapsed` | `numeric` | YES | `-` | - |
| `notifications_sent` | `jsonb` | YES | `-` | - |
| `escalated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `escalation_rule`
**Description**: SLA escalation logic defining automated escalation paths when deadlines pass.  
- **Total Rows**: 2,394  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `escalation_rule_pkey`: `CREATE UNIQUE INDEX escalation_rule_pkey ON public.escalation_rule USING btree (id)`
  - `escalation_rule_category_id`: `CREATE INDEX escalation_rule_category_id ON public.escalation_rule USING btree (category_id)`
  - `escalation_rule_escalation_type_from_level`: `CREATE INDEX escalation_rule_escalation_type_from_level ON public.escalation_rule USING btree (escalation_type, from_level)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('escalation_rule_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `rule_name` | `character varying` | NO | `-` | - |
| `description` | `text` | YES | `-` | - |
| `escalation_type` | `USER-DEFINED` | NO | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `priority` | `USER-DEFINED` | YES | `-` | - |
| `from_level` | `integer` | NO | `-` | - |
| `to_level` | `integer` | NO | `-` | - |
| `trigger_hours` | `numeric` | NO | `-` | - |
| `target_role_code` | `character varying` | YES | `-` | - |
| `target_user_id` | `integer` | YES | `-` | - |
| `notify_current_assignee` | `boolean` | YES | `true` | - |
| `notify_higher_authority` | `boolean` | YES | `true` | - |
| `auto_reassign` | `boolean` | YES | `false` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `external_app`
**Description**: External application integration credentials and API endpoints.  
- **Total Rows**: 3  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `external_app_api_token_key`: `CREATE UNIQUE INDEX external_app_api_token_key ON public.external_app USING btree (api_token)`
  - `external_app_app_code_key`: `CREATE UNIQUE INDEX external_app_app_code_key ON public.external_app USING btree (app_code)`
  - `external_app_pkey`: `CREATE UNIQUE INDEX external_app_pkey ON public.external_app USING btree (id)`
  - `idx_external_app_api_token`: `CREATE INDEX idx_external_app_api_token ON public.external_app USING btree (api_token)`
  - `idx_external_app_app_code`: `CREATE INDEX idx_external_app_app_code ON public.external_app USING btree (app_code)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('external_app_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `app_code` | `character varying` | NO | `-` | - |
| `app_name` | `character varying` | NO | `-` | - |
| `api_token` | `character varying` | NO | `-` | - |
| `contact_email` | `character varying` | YES | `-` | - |
| `is_active` | `boolean` | NO | `true` | - |
| `last_used_at` | `timestamp with time zone` | YES | `-` | - |
| `request_count` | `integer` | NO | `0` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `api_key_plain` | `character varying` | YES | `-` | - |

---

### Table / View: `fcm_token`
**Description**: Firebase Cloud Messaging tokens for mobile push notifications.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `fcm_token_pkey`: `CREATE UNIQUE INDEX fcm_token_pkey ON public.fcm_token USING btree (id)`
  - `fcm_token_token_key`: `CREATE UNIQUE INDEX fcm_token_token_key ON public.fcm_token USING btree (token)`
  - `idx_fcm_token_user_active`: `CREATE INDEX idx_fcm_token_user_active ON public.fcm_token USING btree (user_id, is_active)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('fcm_token_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `token` | `text` | NO | `-` | - |
| `device_info` | `character varying` | YES | `-` | - |
| `is_active` | `boolean` | NO | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `geocoding_cache`
**Description**: Geocoding location lookup cache for address resolution.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `geocoding_cache_pkey`: `CREATE UNIQUE INDEX geocoding_cache_pkey ON public.geocoding_cache USING btree (id)`
  - `geocoding_cache_input_hash`: `CREATE UNIQUE INDEX geocoding_cache_input_hash ON public.geocoding_cache USING btree (input_hash)`
  - `geocoding_cache_resolved_ward_id`: `CREATE INDEX geocoding_cache_resolved_ward_id ON public.geocoding_cache USING btree (resolved_ward_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('geocoding_cache_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `input_address` | `text` | NO | `-` | - |
| `input_hash` | `character varying` | NO | `-` | - |
| `geocode_provider` | `USER-DEFINED` | NO | `-` | - |
| `latitude` | `numeric` | YES | `-` | - |
| `longitude` | `numeric` | YES | `-` | - |
| `formatted_address` | `text` | YES | `-` | - |
| `resolved_ward_id` | `integer` | YES | `-` | - |
| `resolved_prabhag_id` | `integer` | YES | `-` | - |
| `resolved_zone_id` | `integer` | YES | `-` | - |
| `confidence` | `numeric` | YES | `-` | - |
| `is_within_pmc` | `boolean` | YES | `true` | - |
| `raw_response` | `jsonb` | YES | `-` | - |
| `hit_count` | `integer` | YES | `1` | - |
| `last_used_at` | `timestamp with time zone` | YES | `-` | - |
| `expires_at` | `timestamp with time zone` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `holiday_master`
**Description**: Official municipal calendar holidays excluded from SLA resolution clock calculations.  
- **Total Rows**: 35  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `holiday_master_pkey`: `CREATE UNIQUE INDEX holiday_master_pkey ON public.holiday_master USING btree (id)`
  - `holiday_master_legacy_id_key`: `CREATE UNIQUE INDEX holiday_master_legacy_id_key ON public.holiday_master USING btree (legacy_id)`
  - `holiday_master_holiday_date`: `CREATE INDEX holiday_master_holiday_date ON public.holiday_master USING btree (holiday_date)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('holiday_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `holiday_date` | `date` | NO | `-` | - |
| `name` | `character varying` | NO | `-` | - |
| `is_half_day` | `boolean` | NO | `false` | - |
| `is_active` | `boolean` | NO | `true` | - |
| `legacy_id` | `bigint` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `now()` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

---

### Table / View: `ladder_slot`
**Description**: Auto-assignment ladder slot configuration.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `ladder_slot_pkey`: `CREATE UNIQUE INDEX ladder_slot_pkey ON public.ladder_slot USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('ladder_slot_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `slot_type` | `USER-DEFINED` | NO | `-` | - |
| `area_ward_id` | `integer` | YES | `-` | - |
| `area_zone_id` | `integer` | YES | `-` | - |
| `area_peth_id` | `integer` | YES | `-` | - |
| `area_prabhag_ids` | `jsonb` | YES | `-` | - |
| `level` | `USER-DEFINED` | NO | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `ladder_slot_assignment`
**Description**: Current active assignments on rotation ladders.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `ladder_slot_assignment_pkey`: `CREATE UNIQUE INDEX ladder_slot_assignment_pkey ON public.ladder_slot_assignment USING btree (id)`
  - `ladder_slot_assignment_ladder_slot_id_user_id_is_active`: `CREATE INDEX ladder_slot_assignment_ladder_slot_id_user_id_is_active ON public.ladder_slot_assignment USING btree (ladder_slot_id, user_id, is_active)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('ladder_slot_assignment_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `ladder_slot_id` | `integer` | NO | `-` | - |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `is_primary` | `boolean` | YES | `false` | - |
| `valid_from` | `timestamp with time zone` | YES | `-` | - |
| `valid_to` | `timestamp with time zone` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `ladder_slot_department`
**Description**: Department mapping for assignment rotation ladders.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `ladder_slot_department_pkey`: `CREATE UNIQUE INDEX ladder_slot_department_pkey ON public.ladder_slot_department USING btree (id)`
  - `ladder_slot_department_unique`: `CREATE UNIQUE INDEX ladder_slot_department_unique ON public.ladder_slot_department USING btree (ladder_slot_id, department_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('ladder_slot_department_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `ladder_slot_id` | `integer` | NO | `-` | - |
| `department_id` | `integer` | NO | `-` | 🔗 FK ➡️ `department_master.id` |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `location_correction_log`
**Description**: Audit trail of citizen or officer location boundary corrections.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `location_correction_log_pkey`: `CREATE UNIQUE INDEX location_correction_log_pkey ON public.location_correction_log USING btree (id)`
  - `location_correction_log_complaint_id`: `CREATE INDEX location_correction_log_complaint_id ON public.location_correction_log USING btree (complaint_id)`
  - `location_correction_log_corrected_by_id`: `CREATE INDEX location_correction_log_corrected_by_id ON public.location_correction_log USING btree (corrected_by_id)`
  - `location_correction_log_created_at`: `CREATE INDEX location_correction_log_created_at ON public.location_correction_log USING btree (created_at)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('location_correction_log_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `correction_type` | `USER-DEFINED` | NO | `-` | - |
| `original_ward_id` | `integer` | YES | `-` | - |
| `corrected_ward_id` | `integer` | YES | `-` | - |
| `original_prabhag_id` | `integer` | YES | `-` | - |
| `corrected_prabhag_id` | `integer` | YES | `-` | - |
| `original_latitude` | `numeric` | YES | `-` | - |
| `original_longitude` | `numeric` | YES | `-` | - |
| `corrected_latitude` | `numeric` | YES | `-` | - |
| `corrected_longitude` | `numeric` | YES | `-` | - |
| `original_address` | `text` | YES | `-` | - |
| `corrected_address` | `text` | YES | `-` | - |
| `reason` | `text` | YES | `-` | - |
| `corrected_by_id` | `integer` | NO | `-` | - |
| `is_bulk_correction` | `boolean` | YES | `false` | - |
| `correction_source` | `USER-DEFINED` | YES | `'GIS_ADMIN'::enum_location_correction_log_correction_source` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `notification_log`
**Description**: Log of sent SMS, Email, and Push notifications.  
- **Total Rows**: 17,817  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `notification_log_pkey`: `CREATE UNIQUE INDEX notification_log_pkey ON public.notification_log USING btree (id)`
  - `idx_notification_log_bell_icon`: `CREATE INDEX idx_notification_log_bell_icon ON public.notification_log USING btree (user_id, is_read, created_at)`
  - `notification_log_complaint_id`: `CREATE INDEX notification_log_complaint_id ON public.notification_log USING btree (complaint_id)`
  - `notification_log_created_at`: `CREATE INDEX notification_log_created_at ON public.notification_log USING btree (created_at)`
  - `notification_log_status`: `CREATE INDEX notification_log_status ON public.notification_log USING btree (status)`
  - `notification_log_user_id`: `CREATE INDEX notification_log_user_id ON public.notification_log USING btree (user_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('notification_log_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `template_id` | `integer` | YES | `-` | - |
| `user_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `complaint_id` | `integer` | YES | `-` | 🔗 FK ➡️ `complaint.id` |
| `channel` | `USER-DEFINED` | NO | `-` | - |
| `recipient` | `character varying` | NO | `-` | - |
| `subject` | `character varying` | YES | `-` | - |
| `message_body` | `text` | NO | `-` | - |
| `status` | `USER-DEFINED` | YES | `'PENDING'::enum_notification_log_status` | - |
| `external_id` | `character varying` | YES | `-` | - |
| `error_message` | `text` | YES | `-` | - |
| `retry_count` | `integer` | YES | `0` | - |
| `sent_at` | `timestamp with time zone` | YES | `-` | - |
| `delivered_at` | `timestamp with time zone` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `title` | `character varying` | YES | `-` | - |
| `is_read` | `boolean` | NO | `false` | - |
| `read_at` | `timestamp with time zone` | YES | `-` | - |
| `link` | `character varying` | YES | `-` | - |
| `title_mr` | `character varying` | YES | `-` | - |

---

### Table / View: `notification_preference`
**Description**: User communication channel preferences.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `notification_preference_pkey`: `CREATE UNIQUE INDEX notification_preference_pkey ON public.notification_preference USING btree (id)`
  - `notification_preference_user_id_channel_event_type`: `CREATE UNIQUE INDEX notification_preference_user_id_channel_event_type ON public.notification_preference USING btree (user_id, channel, event_type)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('notification_preference_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `channel` | `USER-DEFINED` | NO | `-` | - |
| `event_type` | `USER-DEFINED` | NO | `-` | - |
| `is_enabled` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `notification_template`
**Description**: Templates for citizen notification messages.  
- **Total Rows**: 16  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `notification_template_pkey`: `CREATE UNIQUE INDEX notification_template_pkey ON public.notification_template USING btree (id)`
  - `notification_template_template_code_key`: `CREATE UNIQUE INDEX notification_template_template_code_key ON public.notification_template USING btree (template_code)`
  - `notification_template_event_type_channel_language`: `CREATE INDEX notification_template_event_type_channel_language ON public.notification_template USING btree (event_type, channel, language)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('notification_template_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `template_code` | `character varying` | NO | `-` | - |
| `template_name` | `character varying` | NO | `-` | - |
| `description` | `text` | YES | `-` | - |
| `event_type` | `USER-DEFINED` | NO | `-` | - |
| `channel` | `USER-DEFINED` | NO | `-` | - |
| `language` | `USER-DEFINED` | YES | `'en'::enum_notification_template_language` | - |
| `subject` | `character varying` | YES | `-` | - |
| `body_template` | `text` | NO | `-` | - |
| `variables` | `jsonb` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `officer_jurisdiction`
**Description**: Defines geographic & department boundaries assigned to individual officers.  
- **Total Rows**: 7,923  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `prabhag_id` ➡️ **`prabhag_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `officer_jurisdiction_pkey`: `CREATE UNIQUE INDEX officer_jurisdiction_pkey ON public.officer_jurisdiction USING btree (id)`
  - `officer_jurisdiction_department_id`: `CREATE INDEX officer_jurisdiction_department_id ON public.officer_jurisdiction USING btree (department_id)`
  - `officer_jurisdiction_user_id`: `CREATE INDEX officer_jurisdiction_user_id ON public.officer_jurisdiction USING btree (user_id)`
  - `officer_jurisdiction_ward_id`: `CREATE INDEX officer_jurisdiction_ward_id ON public.officer_jurisdiction USING btree (ward_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('officer_jurisdiction_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `jurisdiction_type` | `USER-DEFINED` | NO | `-` | - |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `prabhag_id` | `integer` | YES | `-` | 🔗 FK ➡️ `prabhag_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `is_primary` | `boolean` | YES | `true` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `level` | `USER-DEFINED` | YES | `-` | - |

---

### Table / View: `officer_performance`
**Description**: Pre-calculated monthly KPI performance metrics for field officers.  
- **Total Rows**: 15,512  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `officer_performance_pkey`: `CREATE UNIQUE INDEX officer_performance_pkey ON public.officer_performance USING btree (id)`
  - `officer_performance_user_id_period_type_period_start`: `CREATE INDEX officer_performance_user_id_period_type_period_start ON public.officer_performance USING btree (user_id, period_type, period_start)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('officer_performance_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `period_type` | `USER-DEFINED` | NO | `-` | - |
| `period_start` | `date` | NO | `-` | - |
| `period_end` | `date` | NO | `-` | - |
| `assigned_count` | `integer` | YES | `0` | - |
| `resolved_count` | `integer` | YES | `0` | - |
| `transferred_out` | `integer` | YES | `0` | - |
| `transferred_in` | `integer` | YES | `0` | - |
| `pending_count` | `integer` | YES | `0` | - |
| `sla_compliance_percent` | `numeric` | YES | `-` | - |
| `avg_resolution_hours` | `numeric` | YES | `-` | - |
| `avg_first_response_hours` | `numeric` | YES | `-` | - |
| `citizen_satisfaction` | `numeric` | YES | `-` | - |
| `escalation_count` | `integer` | YES | `0` | - |
| `reopen_count` | `integer` | YES | `0` | - |
| `performance_score` | `numeric` | YES | `-` | - |
| `rank_in_ward` | `integer` | YES | `-` | - |
| `rank_in_department` | `integer` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `officer_transfer_log`
**Description**: Historical record of officer transfers between wards/departments.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `officer_transfer_log_pkey`: `CREATE UNIQUE INDEX officer_transfer_log_pkey ON public.officer_transfer_log USING btree (id)`
  - `idx_otl_department`: `CREATE INDEX idx_otl_department ON public.officer_transfer_log USING btree (department_id)`
  - `idx_otl_effective_date`: `CREATE INDEX idx_otl_effective_date ON public.officer_transfer_log USING btree (effective_date)`
  - `idx_otl_from_ward`: `CREATE INDEX idx_otl_from_ward ON public.officer_transfer_log USING btree (from_ward_id)`
  - `idx_otl_status`: `CREATE INDEX idx_otl_status ON public.officer_transfer_log USING btree (status)`
  - `idx_otl_to_ward`: `CREATE INDEX idx_otl_to_ward ON public.officer_transfer_log USING btree (to_ward_id)`
  - `idx_otl_user`: `CREATE INDEX idx_otl_user ON public.officer_transfer_log USING btree (user_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('officer_transfer_log_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `department_id` | `integer` | NO | `-` | 🔗 FK ➡️ `department_master.id` |
| `from_ward_id` | `integer` | YES | `-` | - |
| `to_ward_id` | `integer` | YES | `-` | - |
| `transfer_type` | `USER-DEFINED` | NO | `-` | - |
| `reason` | `text` | YES | `-` | - |
| `effective_date` | `date` | NO | `-` | - |
| `end_date` | `date` | YES | `-` | - |
| `initiated_by` | `integer` | YES | `-` | - |
| `approved_by` | `integer` | YES | `-` | - |
| `status` | `USER-DEFINED` | NO | `'PENDING'::enum_officer_transfer_log_status` | - |
| `rejection_reason` | `text` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `permission`
**Description**: Granular system permission definitions.  
- **Total Rows**: 30  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `permission_code_key`: `CREATE UNIQUE INDEX permission_code_key ON public.permission USING btree (code)`
  - `permission_pkey`: `CREATE UNIQUE INDEX permission_pkey ON public.permission USING btree (id)`
  - `idx_permission_code_unique`: `CREATE UNIQUE INDEX idx_permission_code_unique ON public.permission USING btree (code)`
  - `idx_permission_module`: `CREATE INDEX idx_permission_module ON public.permission USING btree (module)`
  - `idx_permission_resource_action`: `CREATE INDEX idx_permission_resource_action ON public.permission USING btree (resource, action)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('permission_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `code` | `character varying` | NO | `-` | - |
| `name` | `character varying` | NO | `-` | - |
| `description` | `text` | YES | `-` | - |
| `resource` | `character varying` | NO | `-` | - |
| `action` | `character varying` | NO | `-` | - |
| `module` | `character varying` | NO | `-` | - |
| `is_system` | `boolean` | NO | `false` | - |
| `metadata` | `jsonb` | NO | `'"{}"'::jsonb` | - |
| `created_at` | `timestamp with time zone` | NO | `now()` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

---

### Table / View: `peth_master`
**Description**: Historical peth area classifications within Pune municipal limits.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `peth_master_peth_code_key`: `CREATE UNIQUE INDEX peth_master_peth_code_key ON public.peth_master USING btree (peth_code)`
  - `peth_master_pkey`: `CREATE UNIQUE INDEX peth_master_pkey ON public.peth_master USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('peth_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `peth_code` | `character varying` | NO | `-` | - |
| `peth_name` | `character varying` | NO | `-` | - |
| `peth_name_mar` | `character varying` | YES | `-` | - |
| `ward_id` | `integer` | YES | `-` | - |
| `zone_id` | `integer` | YES | `-` | - |
| `display_order` | `integer` | YES | `0` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `prabhag_master`
**Description**: Municipal electoral prabhags (constituencies) within wards.  
- **Total Rows**: 125  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `prabhag_master_pkey`: `CREATE UNIQUE INDEX prabhag_master_pkey ON public.prabhag_master USING btree (id)`
  - `prabhag_master_prabhag_code_key`: `CREATE UNIQUE INDEX prabhag_master_prabhag_code_key ON public.prabhag_master USING btree (prabhag_code)`
  - `prabhag_master_ward_id`: `CREATE INDEX prabhag_master_ward_id ON public.prabhag_master USING btree (ward_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('prabhag_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `ward_id` | `integer` | NO | `-` | - |
| `prabhag_code` | `character varying` | NO | `-` | - |
| `prabhag_name` | `character varying` | NO | `-` | - |
| `prabhag_name_mar` | `character varying` | YES | `-` | - |
| `prabhag_number` | `integer` | YES | `-` | - |
| `boundary_geojson` | `jsonb` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `center_lat` | `numeric` | YES | `-` | - |
| `center_lng` | `numeric` | YES | `-` | - |
| `peth_id` | `integer` | YES | `-` | - |

---

### Table / View: `role_master`
**Description**: RBAC user roles (Citizen, Officer, Ward Engineer, Department Admin, System Admin).  
- **Total Rows**: 18  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `role_master_pkey`: `CREATE UNIQUE INDEX role_master_pkey ON public.role_master USING btree (id)`
  - `role_master_role_code_key`: `CREATE UNIQUE INDEX role_master_role_code_key ON public.role_master USING btree (role_code)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('role_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `role_code` | `character varying` | NO | `-` | - |
| `role_name` | `character varying` | NO | `-` | - |
| `role_name_mar` | `character varying` | YES | `-` | - |
| `description` | `text` | YES | `-` | - |
| `hierarchy_level` | `integer` | NO | `0` | - |
| `permissions` | `jsonb` | YES | `'{}'::jsonb` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `role_permission`
**Description**: Permission mappings assigned to specific user roles.  
- **Total Rows**: 232  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `role_id` ➡️ **`role_master.id`** (Many-to-One (N:1))
  - `permission_id` ➡️ **`permission.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `role_permission_pkey`: `CREATE UNIQUE INDEX role_permission_pkey ON public.role_permission USING btree (id)`
  - `idx_role_permission_permission_id`: `CREATE INDEX idx_role_permission_permission_id ON public.role_permission USING btree (permission_id)`
  - `idx_role_permission_role_id`: `CREATE INDEX idx_role_permission_role_id ON public.role_permission USING btree (role_id)`
  - `idx_role_permission_unique`: `CREATE UNIQUE INDEX idx_role_permission_unique ON public.role_permission USING btree (role_id, permission_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('role_permission_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `role_id` | `integer` | NO | `-` | 🔗 FK ➡️ `role_master.id` |
| `permission_id` | `integer` | NO | `-` | 🔗 FK ➡️ `permission.id` |
| `granted_at` | `timestamp with time zone` | NO | `now()` | - |
| `granted_by` | `integer` | YES | `-` | - |
| `conditions` | `jsonb` | NO | `'"{}"'::jsonb` | - |
| `created_at` | `timestamp with time zone` | NO | `now()` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

---

### Table / View: `sla_configuration`
**Description**: Defines SLA target resolution hours and grace periods by category & priority.  
- **Total Rows**: 9  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `sub_category_id` ➡️ **`sub_category_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `sla_configuration_pkey`: `CREATE UNIQUE INDEX sla_configuration_pkey ON public.sla_configuration USING btree (id)`
  - `sla_configuration_category_id_priority`: `CREATE INDEX sla_configuration_category_id_priority ON public.sla_configuration USING btree (category_id, priority)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('sla_configuration_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `sub_category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `sub_category_master.id` |
| `priority` | `USER-DEFINED` | NO | `-` | - |
| `resolution_hours` | `numeric` | NO | `-` | - |
| `warning_threshold_percent` | `integer` | YES | `75` | - |
| `critical_threshold_percent` | `integer` | YES | `90` | - |
| `escalation_l1_hours` | `numeric` | YES | `-` | - |
| `escalation_l2_hours` | `numeric` | YES | `-` | - |
| `escalation_l3_hours` | `numeric` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `sla_display_settings`
**Description**: UI display rules and color thresholds for SLA status indicators.  
- **Total Rows**: 1  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `sla_display_settings_pkey`: `CREATE UNIQUE INDEX sla_display_settings_pkey ON public.sla_display_settings USING btree (id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('sla_display_settings_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `escalation_row_color_1` | `character varying` | NO | `'#fff3cd'::character varying` | - |
| `escalation_row_color_2` | `character varying` | NO | `'#ffe5cc'::character varying` | - |
| `escalation_row_color_3` | `character varying` | NO | `'#f8d7da'::character varying` | - |
| `updated_at` | `timestamp with time zone` | NO | `now()` | - |

---

### Table / View: `status_master`
**Description**: Workflow status codes (Registered, Assigned, Escalated, Pending Info, Transferred, Resolved, Closed).  
- **Total Rows**: 10  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `status_master_pkey`: `CREATE UNIQUE INDEX status_master_pkey ON public.status_master USING btree (id)`
  - `status_master_status_code_key`: `CREATE UNIQUE INDEX status_master_status_code_key ON public.status_master USING btree (status_code)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('status_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `status_code` | `character varying` | NO | `-` | - |
| `status_name` | `character varying` | NO | `-` | - |
| `status_name_mar` | `character varying` | YES | `-` | - |
| `description` | `text` | YES | `-` | - |
| `status_group` | `USER-DEFINED` | NO | `-` | - |
| `display_order` | `integer` | YES | `0` | - |
| `color_code` | `character varying` | YES | `-` | - |
| `is_terminal` | `boolean` | YES | `false` | - |
| `sla_pause` | `boolean` | YES | `false` | - |
| `requires_remarks` | `boolean` | YES | `true` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `sub_category_master`
**Description**: Detailed sub-issue types under each main category.  
- **Total Rows**: 504  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `sub_category_master_pkey`: `CREATE UNIQUE INDEX sub_category_master_pkey ON public.sub_category_master USING btree (id)`
  - `sub_category_master_sub_category_code_key`: `CREATE UNIQUE INDEX sub_category_master_sub_category_code_key ON public.sub_category_master USING btree (sub_category_code)`
  - `sub_category_master_category_id`: `CREATE INDEX sub_category_master_category_id ON public.sub_category_master USING btree (category_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('sub_category_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `category_id` | `integer` | NO | `-` | - |
| `sub_category_code` | `character varying` | NO | `-` | - |
| `sub_category_name` | `character varying` | NO | `-` | - |
| `sub_category_name_mar` | `character varying` | YES | `-` | - |
| `description` | `text` | YES | `-` | - |
| `display_order` | `integer` | YES | `0` | - |
| `override_sla_hours` | `numeric` | YES | `-` | - |
| `override_priority` | `USER-DEFINED` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `override_routing_type` | `character varying` | YES | `NULL::character varying` | - |
| `override_department_id` | `integer` | YES | `-` | - |

---

### Table / View: `swachhata_category`
**Description**: Swachh Bharat Swachhata cleanliness complaint categories.  
- **Total Rows**: 20  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `swachhata_category_pkey`: `CREATE UNIQUE INDEX swachhata_category_pkey ON public.swachhata_category USING btree (id)`
  - `swachhata_category_swachhata_id_key`: `CREATE UNIQUE INDEX swachhata_category_swachhata_id_key ON public.swachhata_category USING btree (swachhata_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('swachhata_category_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `swachhata_id` | `integer` | NO | `-` | - |
| `name` | `character varying` | NO | `-` | - |
| `name_mar` | `character varying` | YES | `-` | - |
| `pmc_category_id` | `integer` | NO | `-` | - |
| `default_sla_hours` | `numeric` | YES | `-` | - |
| `display_order` | `integer` | NO | `0` | - |
| `is_active` | `boolean` | NO | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `swachhata_complaint`
**Description**: Swachh Bharat integration complaint records.  
- **Total Rows**: 16  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `swachhata_category_id` ➡️ **`swachhata_category.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `swachhata_complaint_complaint_id_key`: `CREATE UNIQUE INDEX swachhata_complaint_complaint_id_key ON public.swachhata_complaint USING btree (complaint_id)`
  - `swachhata_complaint_pkey`: `CREATE UNIQUE INDEX swachhata_complaint_pkey ON public.swachhata_complaint USING btree (id)`
  - `idx_swachhata_complaint_sync_status`: `CREATE INDEX idx_swachhata_complaint_sync_status ON public.swachhata_complaint USING btree (sync_status)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('swachhata_complaint_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | NO | `-` | 🔗 FK ➡️ `complaint.id` |
| `swachhata_category_id` | `integer` | NO | `-` | 🔗 FK ➡️ `swachhata_category.id` |
| `swachhata_complaint_id` | `integer` | YES | `-` | - |
| `swachhata_generic_id` | `character varying` | YES | `-` | - |
| `sync_status` | `character varying` | NO | `'PENDING'::character varying` | - |
| `synced_at` | `timestamp with time zone` | YES | `-` | - |
| `last_error` | `text` | YES | `-` | - |
| `retry_count` | `integer` | NO | `0` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `user_master`
**Description**: All users in the system including citizens, field officers, ward engineers, department heads, and call center staff.  
- **Total Rows**: 432,880  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `user_master_employee_code_key`: `CREATE UNIQUE INDEX user_master_employee_code_key ON public.user_master USING btree (employee_code)`
  - `user_master_mobile_key`: `CREATE UNIQUE INDEX user_master_mobile_key ON public.user_master USING btree (mobile)`
  - `user_master_pkey`: `CREATE UNIQUE INDEX user_master_pkey ON public.user_master USING btree (id)`
  - `idx_user_master_legacy_user_id`: `CREATE UNIQUE INDEX idx_user_master_legacy_user_id ON public.user_master USING btree (legacy_user_id) WHERE (legacy_user_id IS NOT NULL)`
  - `idx_user_master_prabhag_id`: `CREATE INDEX idx_user_master_prabhag_id ON public.user_master USING btree (prabhag_id)`
  - `user_master_department_id`: `CREATE INDEX user_master_department_id ON public.user_master USING btree (department_id)`
  - `user_master_employee_code`: `CREATE INDEX user_master_employee_code ON public.user_master USING btree (employee_code)`
  - `user_master_mobile`: `CREATE INDEX user_master_mobile ON public.user_master USING btree (mobile)`
  - `user_master_user_type`: `CREATE INDEX user_master_user_type ON public.user_master USING btree (user_type)`
  - `user_master_ward_id`: `CREATE INDEX user_master_ward_id ON public.user_master USING btree (ward_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('user_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `user_type` | `USER-DEFINED` | NO | `-` | - |
| `full_name` | `character varying` | NO | `-` | - |
| `full_name_mar` | `character varying` | YES | `-` | - |
| `mobile` | `character varying` | YES | `-` | - |
| `email` | `character varying` | YES | `-` | - |
| `password_hash` | `character varying` | YES | `-` | - |
| `employee_code` | `character varying` | YES | `-` | - |
| `designation` | `character varying` | YES | `-` | - |
| `aadhaar_number` | `character varying` | YES | `-` | - |
| `address` | `text` | YES | `-` | - |
| `department_id` | `integer` | YES | `-` | - |
| `ward_id` | `integer` | YES | `-` | - |
| `zone_id` | `integer` | YES | `-` | - |
| `preferred_language` | `USER-DEFINED` | YES | `'en'::enum_user_master_preferred_language` | - |
| `profile_image_url` | `character varying` | YES | `-` | - |
| `is_verified` | `boolean` | YES | `false` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `last_login_at` | `timestamp with time zone` | YES | `-` | - |
| `created_by` | `integer` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `prabhag_id` | `integer` | YES | `-` | - |
| `legacy_user_id` | `integer` | YES | `-` | - |

---

### Table / View: `user_role_mapping`
**Description**: Maps users to one or more user roles.  
- **Total Rows**: 42,109  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `user_id` ➡️ **`user_master.id`** (Many-to-One (N:1))
  - `role_id` ➡️ **`role_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `user_role_mapping_pkey`: `CREATE UNIQUE INDEX user_role_mapping_pkey ON public.user_role_mapping USING btree (id)`
  - `user_role_mapping_user_id_role_id`: `CREATE UNIQUE INDEX user_role_mapping_user_id_role_id ON public.user_role_mapping USING btree (user_id, role_id)`
  - `idx_user_role_mapping_assigned_by`: `CREATE INDEX idx_user_role_mapping_assigned_by ON public.user_role_mapping USING btree (assigned_by)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('user_role_mapping_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `user_id` | `integer` | NO | `-` | 🔗 FK ➡️ `user_master.id` |
| `role_id` | `integer` | NO | `-` | 🔗 FK ➡️ `role_master.id` |
| `is_primary` | `boolean` | YES | `false` | - |
| `assigned_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `assigned_by` | `integer` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `vw_dd_awaiting_feedback_7d`
**Description**: View: Complaints awaiting citizen feedback within 7 days.  
- **Total Rows**: 284,007  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `resolved_at` | `timestamp with time zone` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |

---

### Table / View: `vw_dd_due_24h`
**Description**: View: Complaints expiring within 24 hours.  
- **Total Rows**: 36  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `assigned_to_id` ➡️ **`user_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `status_id` | `integer` | YES | `-` | 🔗 FK ➡️ `status_master.id` |
| `status_code` | `character varying` | YES | `-` | - |
| `status_group` | `USER-DEFINED` | YES | `-` | - |
| `sla_status` | `USER-DEFINED` | YES | `-` | - |
| `sla_deadline` | `timestamp with time zone` | YES | `-` | - |
| `escalation_level` | `integer` | YES | `-` | - |
| `reopen_count` | `integer` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `assigned_to_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `created_at` | `timestamp with time zone` | YES | `-` | - |

---

### Table / View: `vw_dd_due_3d`
**Description**: View: Complaints expiring within 3 days.  
- **Total Rows**: 101  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `assigned_to_id` ➡️ **`user_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `status_id` | `integer` | YES | `-` | 🔗 FK ➡️ `status_master.id` |
| `status_code` | `character varying` | YES | `-` | - |
| `status_group` | `USER-DEFINED` | YES | `-` | - |
| `sla_status` | `USER-DEFINED` | YES | `-` | - |
| `sla_deadline` | `timestamp with time zone` | YES | `-` | - |
| `escalation_level` | `integer` | YES | `-` | - |
| `reopen_count` | `integer` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `assigned_to_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `created_at` | `timestamp with time zone` | YES | `-` | - |

---

### Table / View: `vw_dd_escalated_to_ac`
**Description**: View: Complaints escalated to Additional Commissioner level.  
- **Total Rows**: 15  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `assigned_to_id` ➡️ **`user_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `status_id` | `integer` | YES | `-` | 🔗 FK ➡️ `status_master.id` |
| `status_code` | `character varying` | YES | `-` | - |
| `status_group` | `USER-DEFINED` | YES | `-` | - |
| `sla_status` | `USER-DEFINED` | YES | `-` | - |
| `sla_deadline` | `timestamp with time zone` | YES | `-` | - |
| `escalation_level` | `integer` | YES | `-` | - |
| `reopen_count` | `integer` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `assigned_to_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `created_at` | `timestamp with time zone` | YES | `-` | - |

---

### Table / View: `vw_dd_kpi_live`
**Description**: View: Real-time top-level KPI metrics summary.  
- **Total Rows**: 1  
- **Primary Key(s)**: `None`  
- **Foreign Key Relationships**: None

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `open_count` | `integer` | YES | `-` | - |
| `late_count` | `integer` | YES | `-` | - |
| `due_3d` | `integer` | YES | `-` | - |
| `due_24h` | `integer` | YES | `-` | - |
| `escalated_to_ac` | `integer` | YES | `-` | - |
| `avg_open_age_days` | `numeric` | YES | `-` | - |
| `oldest_open_days` | `numeric` | YES | `-` | - |

---

### Table / View: `vw_dd_late_complaints`
**Description**: View: Open complaints currently breaching SLA deadline.  
- **Total Rows**: 24,373  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `assigned_to_id` ➡️ **`user_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `status_id` | `integer` | YES | `-` | 🔗 FK ➡️ `status_master.id` |
| `status_code` | `character varying` | YES | `-` | - |
| `status_group` | `USER-DEFINED` | YES | `-` | - |
| `sla_status` | `USER-DEFINED` | YES | `-` | - |
| `sla_deadline` | `timestamp with time zone` | YES | `-` | - |
| `escalation_level` | `integer` | YES | `-` | - |
| `reopen_count` | `integer` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `assigned_to_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `created_at` | `timestamp with time zone` | YES | `-` | - |

---

### Table / View: `vw_dd_open_complaints`
**Description**: View: Active open complaints across all wards.  
- **Total Rows**: 31,677  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `status_id` ➡️ **`status_master.id`** (Many-to-One (N:1))
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))
  - `assigned_to_id` ➡️ **`user_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `status_id` | `integer` | YES | `-` | 🔗 FK ➡️ `status_master.id` |
| `status_code` | `character varying` | YES | `-` | - |
| `status_group` | `USER-DEFINED` | YES | `-` | - |
| `sla_status` | `USER-DEFINED` | YES | `-` | - |
| `sla_deadline` | `timestamp with time zone` | YES | `-` | - |
| `escalation_level` | `integer` | YES | `-` | - |
| `reopen_count` | `integer` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |
| `assigned_to_id` | `integer` | YES | `-` | 🔗 FK ➡️ `user_master.id` |
| `created_at` | `timestamp with time zone` | YES | `-` | - |

---

### Table / View: `vw_dd_reopened`
**Description**: View: Reopened complaints tracking view.  
- **Total Rows**: 12,236  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `reopen_count` | `integer` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | YES | `-` | - |
| `resolved_at` | `timestamp with time zone` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |

---

### Table / View: `vw_dd_resolved`
**Description**: View: Resolved complaints analytical view.  
- **Total Rows**: 488,586  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `category_id` ➡️ **`category_master.id`** (Many-to-One (N:1))
  - `department_id` ➡️ **`department_master.id`** (Many-to-One (N:1))
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
  - `zone_id` ➡️ **`zone_master.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_number` | `character varying` | YES | `-` | - |
| `resolved_at` | `timestamp with time zone` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | YES | `-` | - |
| `sla_deadline` | `timestamp with time zone` | YES | `-` | - |
| `on_time` | `boolean` | YES | `-` | - |
| `legacy_excluded` | `boolean` | YES | `-` | - |
| `days_to_close` | `numeric` | YES | `-` | - |
| `category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `category_master.id` |
| `department_id` | `integer` | YES | `-` | 🔗 FK ➡️ `department_master.id` |
| `ward_id` | `integer` | YES | `-` | 🔗 FK ➡️ `ward_master.id` |
| `zone_id` | `integer` | YES | `-` | 🔗 FK ➡️ `zone_master.id` |

---

### Table / View: `vw_dd_swachhata_failures`
**Description**: View: Failed or SLA-breached Swachhata complaints.  
- **Total Rows**: 0  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `complaint_id` ➡️ **`complaint.id`** (Many-to-One (N:1))
  - `swachhata_category_id` ➡️ **`swachhata_category.id`** (Many-to-One (N:1))

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | YES | `-` | 🔑 PRIMARY KEY |
| `complaint_id` | `integer` | YES | `-` | 🔗 FK ➡️ `complaint.id` |
| `swachhata_category_id` | `integer` | YES | `-` | 🔗 FK ➡️ `swachhata_category.id` |
| `swachhata_complaint_id` | `integer` | YES | `-` | - |
| `swachhata_generic_id` | `character varying` | YES | `-` | - |
| `sync_status` | `character varying` | YES | `-` | - |
| `synced_at` | `timestamp with time zone` | YES | `-` | - |
| `last_error` | `text` | YES | `-` | - |
| `retry_count` | `integer` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | YES | `-` | - |
| `updated_at` | `timestamp with time zone` | YES | `-` | - |

---

### Table / View: `ward_master`
**Description**: PMC administrative regional wards (Aundh-Baner, Kothrud-Bavdhan, Hadapsar, Ahmednagar Road, etc.).  
- **Total Rows**: 32  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `ward_master_pkey`: `CREATE UNIQUE INDEX ward_master_pkey ON public.ward_master USING btree (id)`
  - `ward_master_ward_code_key`: `CREATE UNIQUE INDEX ward_master_ward_code_key ON public.ward_master USING btree (ward_code)`
  - `ward_master_zone_id`: `CREATE INDEX ward_master_zone_id ON public.ward_master USING btree (zone_id)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('ward_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `zone_id` | `integer` | NO | `-` | - |
| `ward_code` | `character varying` | NO | `-` | - |
| `ward_name` | `character varying` | NO | `-` | - |
| `ward_name_mar` | `character varying` | YES | `-` | - |
| `ward_number` | `integer` | YES | `-` | - |
| `description` | `text` | YES | `-` | - |
| `boundary_geojson` | `jsonb` | YES | `-` | - |
| `center_lat` | `numeric` | YES | `-` | - |
| `center_lng` | `numeric` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `boundary` | `jsonb` | YES | `-` | - |

---

### Table / View: `ward_performance`
**Description**: Pre-calculated monthly performance rollups per ward.  
- **Total Rows**: 448  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**:
  - `ward_id` ➡️ **`ward_master.id`** (Many-to-One (N:1))
- **Database Indexes**:
  - `ward_performance_pkey`: `CREATE UNIQUE INDEX ward_performance_pkey ON public.ward_performance USING btree (id)`
  - `ward_performance_ward_id_period_type_period_start`: `CREATE INDEX ward_performance_ward_id_period_type_period_start ON public.ward_performance USING btree (ward_id, period_type, period_start)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('ward_performance_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `ward_id` | `integer` | NO | `-` | 🔗 FK ➡️ `ward_master.id` |
| `period_type` | `USER-DEFINED` | NO | `-` | - |
| `period_start` | `date` | NO | `-` | - |
| `period_end` | `date` | NO | `-` | - |
| `total_complaints` | `integer` | YES | `0` | - |
| `resolved_count` | `integer` | YES | `0` | - |
| `pending_count` | `integer` | YES | `0` | - |
| `sla_compliance_percent` | `numeric` | YES | `-` | - |
| `avg_resolution_hours` | `numeric` | YES | `-` | - |
| `citizen_satisfaction` | `numeric` | YES | `-` | - |
| `escalation_rate` | `numeric` | YES | `-` | - |
| `reopen_rate` | `numeric` | YES | `-` | - |
| `rank_in_zone` | `integer` | YES | `-` | - |
| `rank_city_wide` | `integer` | YES | `-` | - |
| `performance_score` | `numeric` | YES | `-` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---

### Table / View: `zone_master`
**Description**: Administrative zonal divisions grouping multiple wards across Pune city.  
- **Total Rows**: 14  
- **Primary Key(s)**: `id`  
- **Foreign Key Relationships**: None
- **Database Indexes**:
  - `zone_master_pkey`: `CREATE UNIQUE INDEX zone_master_pkey ON public.zone_master USING btree (id)`
  - `zone_master_zone_code_key`: `CREATE UNIQUE INDEX zone_master_zone_code_key ON public.zone_master USING btree (zone_code)`

| Column Name | Data Type | Nullable | Default | Key / Relationship |
| --- | --- | --- | --- | --- |
| `id` | `integer` | NO | `nextval('zone_master_id_seq'::regclass)` | 🔑 PRIMARY KEY |
| `zone_code` | `character varying` | NO | `-` | - |
| `zone_name` | `character varying` | NO | `-` | - |
| `zone_name_mar` | `character varying` | YES | `-` | - |
| `description` | `text` | YES | `-` | - |
| `boundary_geojson` | `jsonb` | YES | `-` | - |
| `is_active` | `boolean` | YES | `true` | - |
| `created_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |
| `updated_at` | `timestamp with time zone` | NO | `CURRENT_TIMESTAMP` | - |

---
