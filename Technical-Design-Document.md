# Technical Design Document
## AI Resume Screening & Client Shortlist Portal (Company A, Noida)

**GitHub Repository**: `https://github.com/<your-username>/staffing-resume-portal`  
**Live Application**: `https://staffing-resume-portal.vercel.app` (Backend: `https://staffing-resume-api.onrender.com`)

---

## Demo Reviewer Accounts

| Role | Email | Password | Organization / Client | Scope |
|---|---|---|---|---|
| **Recruiter** | `recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing | Create JDs, upload CVs, view AI scores with verbatim evidence, manage candidate pipeline. |
| **Senior Recruiter** | `senior.recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing | Agency-wide sourcing & screening permissions. |
| **Client 1 (IT Services)** | `hiring@techcorp.in` | `Client@123` | **TechCorp Solutions** | Reviews shortlists for **Senior Java Developer** (includes Ritika Bansal & Pooja Nair); masked contacts until interview stage. |
| **Client 2 (Banking)** | `hiring@finserv.in` | `Client@123` | **FinServ India** | Reviews shortlists for **KYC Analyst** (includes Arjun Rawat); strictly scoped to FinServ candidates. |
| **Delivery Head** | `head@talentbridge.in` | `DeliveryHead@123` | TalentBridge Staffing | Executive oversight dashboard (`/delivery`), recruiter activity stats, and AI vs. recruiter alignment audit. |

---

## 1. Architecture Overview

### Why This Architecture

This platform is specifically engineered for multi-client staffing agencies where recruitment teams process hundreds of incoming CVs per requisition, generate evidence-backed candidate shortlists, and securely share masked profiles with corporate client hiring managers.

```
+-----------------------------------------------------------------------------------+
|                                  CLIENT LAYER                                     |
|                                                                                   |
|  +----------------------------------+     +------------------------------------+  |
|  |       Recruiter Portal           |     |     Client Hiring Manager Portal   |  |
|  |  Next.js 14 (App Router, React)  |     |   Next.js 14 (Mobile-First, SSR)   |  |
|  +-----------------+----------------+     +-----------------+------------------+  |
+--------------------|----------------------------------------|---------------------+
                     | HTTP / HTTPS / JSON                    | HTTP / HTTPS / JSON
                     v                                        v
+-----------------------------------------------------------------------------------+
|                              APPLICATION BACKEND (Render)                         |
|                                                                                   |
|  FastAPI (Python 3.11, Asynchronous ASGI)                                          |
|  ├── Routers: /auth, /requisitions, /candidates, /submissions, /pipeline, /client |
|  ├── Security: JWT Bearer Tokens, Bcrypt, Client Scoping Guards (404 enforcement) |
|  ├── AI Engine: Deterministic Rule-Based Regex Extractor & Weighted Scorer        |
|  └── CV Pipeline: pdfplumber -> pdf2image/pytesseract OCR -> python-docx          |
+-----------------------------------------------------------------------------------+
                                        | Motor (Async Driver)
                                        | Beanie ODM (Pydantic v2)
                                        v
+-----------------------------------------------------------------------------------+
|                               DATABASE LAYER (MongoDB Atlas)                      |
|                                                                                   |
|  MongoDB 7.0 Document Database                                                    |
|  ├── users (unique email index)                                                   |
|  ├── clients                                                                      |
|  ├── requisitions (embedded ScorecardCriterion array)                             |
|  ├── candidates (unique SHA-256 fingerprint index, raw_text vs blind_text)        |
|  ├── submissions (compound req+score DESC, unique req+candidate, client index)    |
|  └── audit_logs (append-only timeline index)                                      |
+-----------------------------------------------------------------------------------+
```

#### Why FastAPI over Flask/Django
1. **Asynchronous Non-Blocking I/O**: Parsing 50 PDF/DOCX resumes simultaneously involves substantial I/O disk writes, text extraction, and async MongoDB writes. FastAPI's native `async`/`await` architecture running on Uvicorn prevents worker starvation during bulk uploads.
2. **Pydantic v2 Strict Data Validation**: Complex domain models (such as custom weighted scorecard criteria and criterion evidence) are validated automatically at request time with high performance.
3. **Automated Interactive OpenAPI Documentation**: Generates `/docs` and `/redoc` automatically, allowing staffing operational teams and frontend engineers to inspect request/response contracts without external documentation tools.

#### Why MongoDB over PostgreSQL
1. **Natural Document Structure of CVs**: Resumes have semi-structured, variable schemas (differing skill tags, multi-line employment histories, variable-length text quotes). Storing this in relational tables would require multiple join tables (`candidate_skills`, `candidate_experiences`, `submission_criteria_evidences`).
2. **Embedded Scorecards in Requisitions**: Scorecard criteria are strictly owned by a single requisition and are always queried together with it. Embedding them as an array inside the `Requisition` document eliminates join latency and guarantees atomic updates when recruiters edit criteria.
3. **Submissions as a High-Throughput Linking Collection**: The `submissions` collection links candidates to requisitions and clients while storing point-in-time scoring snapshots (`ai_score`, `criteria_scores`), enabling compound indexing for instant candidate ranking.

#### Why Next.js 14 App Router
1. **Fast Initial Load & RSC**: Server Components pre-render shell pages and fetch critical metadata quickly, ensuring optimal latency for enterprise users.
2. **Clean File-Based Routing for 8 Core Screens**: The App Router directory hierarchy (`/login`, `/dashboard`, `/requisitions/new`, `/requisitions/[id]/scorecard`, `/requisitions/[id]/upload`, `/requisitions/[id]/candidates`, `/requisitions/[id]/pipeline`, `/client/portal`) cleanly mirrors the recruiter and client workflows.
3. **Client-Side Transitions & React Query Cache**: The recruiter portal uses `@tanstack/react-query` to provide instant search filtering, real-time stage updates, and optimistic UI updates without full-page reloads.

#### Cloud Deployment Strategy
- **Backend**: Render.com (Python Web Service) running Uvicorn ASGI.
- **Frontend**: Vercel (Edge Network & Serverless) for instant deployments and global edge CDN delivery.
- **Database**: MongoDB Atlas M0 Free Cluster with replica sets, automated backups, and TLS encryption in transit.

---

## 2. Data Model

### Collections

#### `users`
Represents internal staffing agency staff and external corporate client hiring managers.
- `id` (PydanticObjectId / ObjectId)
- `email` (Indexed string, unique=True): Login identifier.
- `hashed_password` (str): Bcrypt hash with per-user salt.
- `full_name` (str): Display name.
- `role` (UserRole enum): `recruiter`, `client_hiring_manager`, or `delivery_head`.
- `client_id` (Optional[str]): Foreign key to `clients` collection. Populated **only** for `client_hiring_manager` roles. Guaranteed to scope client access.
- `is_active` (bool): Soft deactivation flag.
- `created_at` (datetime): Timestamp.

#### `clients`
Represents client organizations that hire through the staffing firm.
- `id` (ObjectId)
- `name` (str): Organization name (e.g., "TechCorp Solutions", "FinServ India").
- `contact_email` (str): Client corporate contact email.
- `created_at` (datetime)

#### `requisitions`
Represents open job orders submitted by clients.
- `id` (ObjectId)
- `title` (str): Job title (e.g., "Senior Java Developer").
- `client_id` (str): Reference to the issuing client organization.
- `jd_text` (str): Full text of the Job Description.
- `scorecard` (List[ScorecardCriterion]): **Embedded** list of evaluation criteria.
  - `ScorecardCriterion`:
    - `name` (str): Criterion title (e.g., "Spring Boot", "5-8 years experience").
    - `type` (str): Criterion type (`skill`, `experience`, `notice`, `ctc`, `other`).
    - `weight` (float): Relative weight (0.5 to 2.0; default 1.0; 1.5 for mandatory).
    - `required` (bool): If True, a score of 0.0 caps the total candidate match score at 60.0.
- `status` (str): `open`, `closed`, `on_hold`.
- `created_by` (str): Recruiter user ID.
- `created_at`, `updated_at` (datetime)

#### `candidates`
Stores candidate profiles extracted from resumes. Adheres to privacy guidelines by bifurcating display data and blind scoring data.
- `id` (ObjectId)
- `full_name` (str): Candidate legal name (used for recruiter display).
- `email`, `phone` (Optional[str]): Direct candidate contact channels (masked for clients).
- `current_role` (Optional[str]): Current job designation.
- `experience_years` (Optional[float]): Total professional experience.
- `skills` (List[str]): Extracted technical and domain skills.
- `notice_days` (Optional[int]): Availability / notice period in calendar days.
- `raw_text` (str): Verbatim text extracted from the uploaded resume file.
- `blind_text` (str): Cleaned version of `raw_text` with all personal identifiers (name, email, phone, gender, age, marital status, nationality) stripped. **This field is the sole input fed to the AI scoring engine.**
- `fingerprint` (Indexed string, unique=True): SHA-256 hash of normalized `email:phone` (or `name:role` fallback) used for instantaneous deduplication.
- `consent` (ConsentRecord embedded model): `{ given: bool, timestamp: datetime, purpose: "hiring" }`.
- `file_name` (str): Original uploaded document name.
- `created_at` (datetime)

#### `submissions` (Key Collection)
The central operational collection representing the application of a candidate to a specific job requisition.
- `id` (ObjectId)
- `requisition_id` (str): Reference to `requisitions`.
- `candidate_id` (str): Reference to `candidates`.
- `client_id` (str): Copied from `requisition.client_id` to enable client-scoped queries.
- `ai_score` (float, 0.0 - 100.0): Overall weighted match score computed by the AI scoring engine.
- `criteria_scores` (List[CriterionEvidence]): Detailed evidence list.
  - `criterion_name` (str)
  - `score` (float, 0.0 to 1.0)
  - `evidence_quotes` (List[str]): Exact sentence quotes extracted from the CV.
  - `matched` (bool): High-level match boolean.
- `pipeline_stage` (PipelineStage enum): `sourced` -> `screened` -> `shortlisted` -> `client_reviewed` -> `interview` -> `offer` -> `joined`.
- `client_decision` (ClientDecision enum): `pending`, `shortlisted`, `rejected`, `interview_proposed`.
- `rejection_reason` (Optional[str]): Mandatory justification if client rejects candidate.
- `interview_slot` (Optional[datetime]): Timestamp proposed by client for interview.
- `recruiter_viewed` (bool): Guard flag. A recruiter must view the candidate's full profile before `submit_to_client` is permitted.
- `recruiter_viewed_at` (Optional[datetime])
- `submitted_at`, `updated_at` (datetime)

**Indexes on `submissions`:**
1. Compound index: `[("requisition_id", ASCENDING), ("ai_score", DESCENDING)]` — powers the ranked candidate shortlist view.
2. Single index: `[("client_id", ASCENDING)]` — optimizes client portal queries.
3. Unique compound index: `[("requisition_id", ASCENDING), ("candidate_id", ASCENDING)]` — prevents duplicate submissions for the same candidate under the same job requisition.

#### `audit_logs`
Append-only tamper-evident audit trail for data access and compliance tracking.
- `id` (ObjectId)
- `candidate_id` (str): Target candidate.
- `viewer_user_id` (str): Authenticated user ID who accessed the record.
- `viewer_role` (str): Role of the viewer (`recruiter`, `client_hiring_manager`, `delivery_head`).
- `requisition_id` (Optional[str]): Associated job requisition context.
- `action` (str): Action performed (`viewed`, `consent_updated`, `deleted`).
- `timestamp` (datetime): UTC access timestamp.

### Embedding vs Referencing Decisions

| Entity Pair | Strategy | Technical Justification |
|---|---|---|
| `Requisition` -> `ScorecardCriterion` | **Embedded** | Scorecard criteria are strictly owned by a single requisition. They never exist independently, are always read whenever the requisition is retrieved, and total fewer than 20 items per requisition. Embedding avoids multi-table joins. |
| `Candidate` -> `ConsentRecord` | **Embedded** | Consent is a 1-to-1 attribute directly attached to the candidate's personal data lifecycle under data protection laws. |
| `Submission` -> `CriterionEvidence` | **Embedded** | The scoring breakdown represents a point-in-time snapshot computed for that specific submission. It is immutable unless re-scored and is always rendered as part of the candidate card. |
| `Submission` -> `Candidate` & `Requisition` | **Referenced** | Many-to-many relationship. A candidate can be submitted to multiple requisitions over time; requisitions have dozens of candidate submissions. Independent querying, indexing, and sorting are essential. |
| `AuditLog` -> `Candidate` & `User` | **Referenced** | Audit logs are append-only time-series data. Embedding logs into candidates would cause unbounded document growth violating MongoDB's 16MB document size limit. |

---

## 3. Main User Flows

```
+-----------------------------------------------------------------------------------+
| RECRUITER WORKFLOW                                                                |
|                                                                                   |
|  [Paste Job Description]                                                          |
|          │                                                                        |
|          ▼                                                                        |
|  [AI Extractor parses Skills, Experience, Notice, CTC into Scorecard]             |
|          │                                                                        |
|          ▼                                                                        |
|  [Recruiter adjusts weights & required toggles in Scorecard Editor]               |
|          │                                                                        |
|          ▼                                                                        |
|  [Bulk Upload Resumes (PDF / DOCX)] ──> [Fingerprint Deduplication]               |
|          │                                                                        |
|          ▼                                                                        |
|  [Blind Text Sanitization & AI Evidence-Based Scoring]                            |
|          │                                                                        |
|          ▼                                                                        |
|  [Ranked Shortlist View with Match % & Exact CV Evidence Quotes]                  |
|          │                                                                        |
|          ▼                                                                        |
|  [Recruiter inspects Candidate Profile] (Flags recruiter_viewed=True + Audit Log)  |
|          │                                                                        |
|          ▼                                                                        |
|  [Submit to Client] (Pipeline stage advances to client_reviewed)                  |
+-----------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------+
| CLIENT HIRING MANAGER WORKFLOW                                                    |
|                                                                                   |
|  [Login via Client Portal] (Scoped strictly to user's client_id)                  |
|          │                                                                        |
|          ▼                                                                        |
|  [Review Submitted Candidates] (Personal email & phone masked with Lock icon)      |
|          │                                                                        |
|          ▼                                                                        |
|  [Examine AI Match Score & Transparent Evidence Quotes]                           |
|          │                                                                        |
|          ├──> [Shortlist Candidate]                                               |
|          │                                                                        |
|          ├──> [Reject Candidate] (Requires structured rejection reason)           |
|          │                                                                        |
|          └──> [Propose Interview Slot] ────────────────────────────────────────┐  |
|                                                                                │  |
|  [Pipeline stage -> interview: Contact information automatically unmasked!] <──┘  |
+-----------------------------------------------------------------------------------+
```

### Recruiter: JD Intake -> Ranked List
1. **Intake**: Recruiter pastes the raw Job Description text and specifies the client.
2. **Extraction**: The system runs `extract_scorecard_from_jd()` to parse required experience, notice period, budget/CTC, and core skill keywords into a structured scorecard.
3. **Refinement**: Recruiter reviews the generated scorecard in the UI, fine-tunes weights (0.5 to 2.0), marks mandatory qualifications (`required=True`), and saves the requisition.
4. **Bulk Ingestion**: Recruiter uploads a batch of resumes (up to 50 files; PDF or DOCX).
5. **Deduplication**: Each resume is hashed to generate a unique fingerprint. If a candidate already exists in the system, they are linked to the new requisition without creating duplicate records.
6. **Scoring & Ranking**: The AI engine scores the sanitized blind text against the scorecard and saves exact quote evidence.
7. **Review & Gatekeeping**: The recruiter views the ranked shortlist. To submit a candidate to the client portal, the recruiter must open and inspect the full profile first (enforced by `recruiter_viewed=True` server check).

### Client: Review Shortlist
1. **Secure Scoped Access**: The client hiring manager logs in with their credentials. All API endpoints enforce `client_id` boundaries.
2. **Contact Masking**: The client views submitted candidates with full skills, experience, and AI evidence quotes, but direct contact numbers and email addresses are hidden behind a lock indicator.
3. **Decision Making**: For each candidate, the hiring manager can:
   - **Shortlist**: Confirms interest.
   - **Reject**: Must provide a rejection reason (e.g., "Notice period too long", "Tech stack mismatch").
   - **Propose Interview**: Selects a preferred date and time slot.
4. **Contact Disclosure**: Proposing an interview advances the candidate to the `interview` pipeline stage, which automatically unmasks the contact details so the client can schedule the discussion.

### Pipeline: Tracking
The Kanban board visualizes candidates across 7 clear stages:
`sourced` -> `screened` -> `shortlisted` -> `client_reviewed` -> `interview` -> `offer` -> `joined`.

---

## 4. AI Component

### JD Scorecard Extraction
The scorecard extraction engine uses a deterministic regex and keyword-matching architecture rather than an external LLM API:
- **Experience Pattern Recognizer**: Matches expressions like `5-8 years of experience in Java`, `minimum 4 years`, `at least 3 yrs`. Captures lower and upper bounds and automatically assigns high weight (`1.5`) and `required=True`.
- **Notice Period Pattern Recognizer**: Extracts constraints like `notice period up to 60 days`, `30 days notice`, or `immediate joiner`.
- **CTC / Budget Pattern Recognizer**: Recognizes Indian compensation structures such as `CTC 18-25 LPA`, `budget up to 14 lakhs`, `salary 12-20 LPA`.
- **Skill Vocabulary Matcher**: Matches across a normalized glossary of 60+ programming languages, frameworks, cloud tools, databases, and compliance keywords with word-boundary awareness (`\b{skill}(?:s)?\b`) to avoid false positives (e.g., preventing "C" from matching inside "React").
- **Required Section Detection**: Matches headers like `Requirements:`, `Must Have:`, or `Qualifications:` to mark skills within those sections as `required=True`.

*Why deterministic regex over LLM?*
- Zero API key dependencies or per-token usage costs.
- Sub-50 millisecond execution speed.
- Completely deterministic and reproducible results.
- Free of hallucinations or variable output formats.

### CV Parsing & Blind Text Generation
1. **Document Ingestion**:
   - Native text PDFs are parsed using `pdfplumber`.
   - If extracted text is under 50 characters (e.g. scanned or rasterized documents), the engine falls back to `pdf2image` and `pytesseract` OCR.
   - Word documents are parsed using `python-docx`.
2. **Profile Extraction**: Heuristic regex extracts email, 10-digit Indian mobile numbers, current job title, years of experience, and skill tags.
3. **Blind Text Sanitization (Bias Mitigation)**:
   - Strips lines containing personal demographic indicators: Date of Birth (`DOB`), Age, Gender/Sex, Marital Status, Nationality, and Photo indicators.
   - Strips honorifics and salutations (`Mr.`, `Mrs.`, `Ms.`, `Dr.`).
   - Replaces candidate's name occurrences with `[Candidate]`.
   - Replaces email and phone numbers with `[Candidate Email]` and `[Candidate Phone]`.
   - **Result**: The scoring algorithm evaluates purely on merit, technical competencies, and project history.

### Scoring with Verbatim Evidence Quotes
The scoring function `score_candidate()` computes scores on a criterion-by-criterion basis:

1. **Skill Evaluation**:
   - Word-boundary search on blind text (`\b{name}(?:s)?\b`).
   - If exact match is found, score = `1.0` and verbatim matching sentences from the CV are captured as evidence quotes.
   - If fuzzy/simplified match is found (e.g. "React.js" vs "ReactJS"), score = `0.8`.
   - If present in extracted skill summary, score = `0.9`.
2. **Experience Evaluation**:
   - Parses target years from criterion name (e.g. "5-8 years" -> 5.0).
   - If `candidate_years >= target_years`, score = `1.0`.
   - If within 1 year (`candidate_years >= target_years - 1.0`), score = `0.7`.
   - If less, score = `0.4`.
3. **Notice Period Evaluation**:
   - `<= 15 days`: score = `1.0` (immediate joiner premium).
   - `<= 30 days`: score = `0.8`.
   - `<= 60 days`: score = `0.5`.
   - `> 60 days`: score = `0.2`.
4. **Weighted Aggregate Calculation**:
   $$\text{Overall Score} = \left( \frac{\sum (\text{criterion\_score}_i \times \text{weight}_i)}{\sum \text{weight}_i} \right) \times 100$$
5. **Required Criterion Cap (Never Auto-Reject)**:
   - If **any** criterion marked `required=True` receives a score of `0.0`, the overall score is strictly capped at **60.0**:
   $$\text{Final Score} = \min(\text{Overall Score}, 60.0)$$
   - *Rationale*: A missing required skill or insufficient experience lowers candidate ranking below qualified peers while still keeping them visible in the portal for manual recruiter consideration.

### Failure Handling & Resilience
- **Empty or Zero-Byte PDF**: Handled gracefully without crashing; returns clear user-facing error message `"Could not extract sufficient text from {filename}"`.
- **Corrupt PDF / Malformed DOCX**: Caught in `try...except` block, logging an error status in the upload batch response while allowing remaining files in the batch to continue processing.
- **OCR Fallback**: Automatically invokes Tesseract OCR if text extraction yield is low.
- **Duplicate Detection**: Computes SHA-256 fingerprint; if found, links existing candidate to new requisition without creating redundant database entries.

---

## 5. UI & Design Decisions

### Design Language & System
- **Color Palette**: Executive Crimson & Slate design system:
  - Neutral Base: Slate grays (`slate-900` headings, `slate-600` body, `slate-50` page backgrounds).
  - Primary Accent: Deep crimson / ruby (`rose-600` / `#E11D48`) for actions, branding, and focused states, avoiding generic blue ATS styling.
  - Semantic Statuses: Emerald (`emerald-600`) for top matches (≥70%), Amber (`amber-500`) for moderate matches (40-69%), Rose (`rose-600`) for low matches (<40%).
- **Typography**: Inter system font stack for clean legibility on data tables and cards.
- **Mobile-First Client Portal**: The client review portal is fully responsive with card layouts designed for quick decision-making on smartphones.

### 8 Key Screens

1. **Login Screen (`/login`)**: Role-aware authentication with pre-populated demo login buttons for one-click recruiter and client access.
2. **Recruiter Dashboard (`/dashboard`)**: Metric overview of active requisitions, open positions, candidate volumes, and pipeline distributions.
3. **Requisition Intake (`/requisitions/new`)**: Split-pane interface to paste JDs, select clients, and trigger instantaneous scorecard generation.
4. **Scorecard Editor (`/requisitions/[id]/scorecard`)**: Interactive table to add, delete, weigh, and mark criteria as mandatory before resume ingestion.
5. **Bulk Resume Upload (`/requisitions/[id]/upload`)**: Drag-and-drop file upload zone supporting up to 50 resumes with per-file progress, validation, and duplicate alerts.
6. **Ranked Candidate Shortlist (`/requisitions/[id]/candidates`)**:
   - Prominent match badge displaying score and color.
   - Direct inline quotation of exact CV evidence lines corresponding to each requirement.
   - Filter bar by score, notice period, and status.
   - "Submit to Client" action button guarded by recruiter profile review status.
7. **Pipeline Kanban Board (`/requisitions/[id]/pipeline`)**: 7-stage visual board with drag-and-drop progression tracking.
8. **Client Shortlist Portal (`/client/portal`)**: Clean, distraction-free view for hiring managers. Personal contacts are masked; one-click "Shortlist", "Reject", and "Propose Interview" actions streamline decisions.

### Loading, Empty & Error States
- **Skeletons**: Pulse skeleton loaders maintain layout stability while fetching server data.
- **Empty States**: Custom illustrations with contextual call-to-action buttons (e.g. "No candidates uploaded yet — Upload CVs").
- **Error Boundaries**: Toast alerts and inline warning banners with retry actions.

---

## 6. Security & Compliance

### Authentication & Authorization
- **JWT Bearer Authentication**: Signed using HMAC-SHA256 with 8-hour token expiration (`settings.access_token_expire_minutes = 480`).
- **Role-Based Access Control (RBAC)**: Guards enforce permissions:
  - `recruiter_only`: Uploading CVs, modifying scorecards, creating requisitions, submitting to client.
  - `client_only`: Reviewing client-scoped shortlists, proposing interview slots, recording hiring decisions.
  - `delivery_head`: Agency-wide analytics and audit trail monitoring.
- **Client Scoping & Enumeration Defense**:
  - The `get_client_scoped_submission()` guard checks that the requested submission's `client_id` strictly equals the authenticated user's `client_id`.
  - When an unauthorized client attempts to access another client's submission, the API responds with **HTTP 404 Not Found** (instead of 403 Forbidden). This prevents attackers from enumerating valid submission IDs across different corporate clients.

### DPDP Act (Digital Personal Data Protection Act) Compliance
1. **Explicit Purpose Limitation**: Every candidate document embeds a `ConsentRecord` recording consent timestamp and specific purpose (`purpose: "hiring"`).
2. **Right to Erasure / Deletion Endpoint**: `DELETE /candidates/{id}` purges candidate profile data, associated submissions, and audit log entries from the primary database.
3. **Immutable Audit Logging**: Every view of a candidate's profile records the viewer's ID, role, timestamp, and context in the `audit_logs` collection.
4. **Blind Scoring**: Demographics, names, gender indicators, and contact channels are stripped before AI evaluation to ensure algorithmic fairness.
5. **Contact Masking**: Client hiring managers cannot view phone numbers or email addresses until an interview is formally requested.

---

## 7. What Was Cut & What's Next

### Cut from Scope (Optional Depth Deferred)
- **Weekly AI vs. Recruiter Comparison Report**: A delivery head report tracking variance between initial AI match ranks and recruiter manual overrides. Deferred to prioritize core workflow stability.
- **Self-Service Candidate Erasure UI**: The backend deletion endpoint (`DELETE /candidates/{id}`) is complete and tested; a dedicated candidate-facing web portal for self-service consent withdrawal will follow in v2.

### What to Build Next (Priority Roadmap)
1. **Consent Management & Data Subject Portal**: Dedicated UI for candidates to view, download, or withdraw consent and request data deletion under DPDP regulations.
2. **Delivery Head Analytics Dashboard**: Visual charts comparing AI ranking accuracy against final hiring outcomes and client interview conversion rates.
3. **Automated Notification Engine**: Transactional emails (via SendGrid/Postmark) notifying clients when shortlists are ready and alerting recruiters when clients propose interview slots.
4. **Elasticsearch / Semantic Vector Search**: Hybrid keyword + vector embedding search to query candidate repositories across legacy talent pools.
5. **PDF Shortlist Export**: Exporting branded candidate dossiers with AI evidence summaries for offline distribution to corporate executives.

---

## 8. Assumptions

- **A1 — Scoring Cap**: Missing a mandatory/required criterion caps the candidate's total match score at 60/100 rather than disqualifying them outright, ensuring human recruiters retain final oversight.
- **A2 — Blind Text Stripping**: Names, emails, phone numbers, gender indicators (Mr/Mrs/Male/Female), dates of birth, age, and marital status are removed from the scoring input. Technical skills, work history, and educational credentials are fully preserved.
- **A3 — Deduplication Fingerprint**: The candidate fingerprint is computed as `SHA-256(normalized_email:last_10_digits_phone)`. If contact details are absent, it falls back to `SHA-256(normalized_name:normalized_role)`. Re-uploading an existing candidate for a new job order links the candidate to a new `Submission` without duplicating personal records.
- **A4 — Consent Model**: Consent is stored as a boolean flag with a UTC timestamp and purpose label (`"hiring"`). It is assumed that the recruiting firm has obtained candidate consent prior to resume upload.
- **A5 — Contact Masking**: Phone numbers and email addresses are masked in the client portal until the candidate's pipeline stage advances to `interview`, `offer`, or `joined`.
- **A6 — Deterministic JD Extraction**: Deterministic regular expressions and curated skill taxonomies are preferred over LLMs to avoid API key dependencies, ensure sub-second response times, and provide predictable results.
- **A7 — Pipeline Stages**: The recruitment lifecycle follows 7 distinct stages: `sourced` -> `screened` -> `shortlisted` -> `client_reviewed` -> `interview` -> `offer` -> `joined`. "Shortlisted" denotes internal agency approval; "Client Reviewed" denotes submission to the client portal.
- **A8 — File Storage**: Resumes are stored on local persistent disk storage (`./uploads`). For production environments, this can be switched to S3 or Cloudflare R2 by updating the upload handler.
- **A9 — CTC Extraction & Evaluation**: Salary budgets are extracted only when explicitly formatted in the JD. The CTC criterion evaluates whether compensation requirements are addressed in the CV rather than enforcing a rigid cutoff.
- **A10 — Client User Provisioning**: Client records and hiring manager accounts are provisioned administratively by agency leadership (or via seed script). Hiring managers are assigned a fixed `client_id` upon creation; self-registration is intentionally disabled.
