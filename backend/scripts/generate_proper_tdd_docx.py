import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_shading(cell, color_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_document(output_path):
    doc = docx.Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Staffing AI Screening Portal | Technical Design Document")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun = fp.add_run("Page ")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
        # Note: XML page field can be added if needed

    # Palette
    C_PRIMARY = RGBColor(0x9F, 0x12, 0x39)  # Deep Crimson
    C_NAVY = RGBColor(0x0F, 0x17, 0x2A)     # Slate 900
    C_SLATE = RGBColor(0x33, 0x41, 0x55)    # Slate 700
    C_MUTED = RGBColor(0x64, 0x74, 0x8B)    # Slate 500
    HEX_HEADER_BG = "0F172A"                # Dark Slate header
    HEX_ALT_ROW = "F8FAFC"                  # Very light slate row
    HEX_CRIMSON_BG = "FFF1F2"               # Light Rose tint
    HEX_CODE_BG = "F1F5F9"                  # Slate 100

    # Document Title Block
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    run_title = p_title.add_run("Technical Design Document")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(24)
    run_title.bold = True
    run_title.font.color.rgb = C_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run("AI Resume Screening Tool & Client Shortlist Portal (Company A, Noida)")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = C_NAVY

    # Project Links & Metadata Callout Card
    card_table = doc.add_table(rows=4, cols=2)
    card_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(card_table, color="E2E8F0", sz="6", val="single")

    meta_rows = [
        ("GitHub Repository", "https://github.com/<your-username>/staffing-resume-portal"),
        ("Live Application", "https://staffing-resume-portal.vercel.app  (API: https://staffing-resume-api.onrender.com)"),
        ("Target Organization", "Company A, Noida (120 staff, 70 recruiters, ₹40-50 cr revenue, 300 requisitions/month)"),
        ("Author & Version", "Staffing AI Engineering Team | Version 1.0 (Production Release)")
    ]

    for idx, (label, val) in enumerate(meta_rows):
        row = card_table.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        set_cell_shading(cell_lbl, "F8FAFC")
        set_cell_shading(cell_val, "FFFFFF")
        set_cell_margins(cell_lbl, top=70, bottom=70, left=120, right=120)
        set_cell_margins(cell_val, top=70, bottom=70, left=120, right=120)

        p0 = cell_lbl.paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.font.name = "Calibri"
        r0.font.size = Pt(9.5)
        r0.bold = True
        r0.font.color.rgb = C_NAVY

        p1 = cell_val.paragraphs[0]
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.name = "Calibri"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = C_SLATE
        if "http" in val:
            r1.font.color.rgb = C_PRIMARY
            r1.bold = True

    # Spacing
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(8)
    p_sp.paragraph_format.space_after = Pt(0)

    # Helper functions for structured writing
    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(16)
        run.bold = True
        run.font.color.rgb = C_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(12.5)
        run.bold = True
        run.font.color.rgb = C_NAVY
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.bold = True
        run.font.color.rgb = C_SLATE
        return p

    def add_p(text, bold_prefix=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "Calibri"
            r_pre.font.size = Pt(10)
            r_pre.bold = True
            r_pre.font.color.rgb = C_NAVY
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.color.rgb = C_SLATE
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_before = Pt(1.5)
        p.paragraph_format.space_after = Pt(1.5)
        p.paragraph_format.line_spacing = 1.12
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "Calibri"
            r_pre.font.size = Pt(9.5)
            r_pre.bold = True
            r_pre.font.color.rgb = C_NAVY
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.color.rgb = C_SLATE
        return p

    def add_callout_box(text):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_shading(cell, HEX_CODE_BG)
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        set_table_borders(table, color="CBD5E1", sz="4", val="single")
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(text)
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_before = Pt(4)
        p_after.paragraph_format.space_after = Pt(0)

    # ----------------------------------------------------
    # SECTION: DEMO REVIEWER ACCOUNTS
    # ----------------------------------------------------
    add_h1("Reviewer Demo Accounts")
    add_p("The system is seeded with five pre-configured user accounts representing all distinct organizational roles across the staffing agency and corporate hiring clients:")

    demo_table = doc.add_table(rows=6, cols=5)
    demo_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(demo_table, color="CBD5E1", sz="4")

    headers = ["Role", "Email", "Password", "Organization", "Access Scope & Capabilities"]
    for i, h in enumerate(headers):
        cell = demo_table.cell(0, i)
        set_cell_shading(cell, HEX_HEADER_BG)
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    credentials = [
        ("Recruiter", "recruiter@talentbridge.in", "Recruiter@123", "TalentBridge Staffing", "Create JDs, edit scorecards, bulk upload CVs, view AI scores with verbatim evidence, manage candidate pipeline."),
        ("Senior Recruiter", "senior.recruiter@talentbridge.in", "Recruiter@123", "TalentBridge Staffing", "Agency-wide candidate sourcing, evaluation, and client submission permissions."),
        ("Client 1 (IT Services)", "hiring@techcorp.in", "Client@123", "TechCorp Solutions", "Reviews shortlists for Senior Java Developer (Ritika Bansal CND-91022 & Pooja Nair CND-91088). Masked contacts until interview stage."),
        ("Client 2 (Banking)", "hiring@finserv.in", "Client@123", "FinServ India", "Reviews shortlists for KYC Analyst (Arjun Rawat CND-91047). Strictly scoped; cannot access TechCorp candidates."),
        ("Delivery Head", "head@talentbridge.in", "DeliveryHead@123", "TalentBridge Staffing", "Executive dashboard (/delivery), agency metrics, recruiter workload, and AI vs. Recruiter rank audits.")
    ]

    for row_idx, cred in enumerate(credentials, start=1):
        bg = HEX_ALT_ROW if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(cred):
            cell = demo_table.cell(row_idx, col_idx)
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            r.font.color.rgb = C_SLATE
            if col_idx in (0, 2):
                r.bold = True

    # ----------------------------------------------------
    # SECTION 1: ARCHITECTURE
    # ----------------------------------------------------
    add_h1("1. Architecture Overview & Decisions")
    add_p("The platform is engineered specifically for multi-client staffing agencies where recruitment teams process hundreds of incoming CVs per requisition, generate evidence-backed candidate shortlists, and securely share masked profiles with corporate client hiring managers.")

    add_callout_box(
        "+-----------------------------------------------------------------------------------+\n"
        "|                                  CLIENT LAYER                                     |\n"
        "|  +----------------------------------+     +------------------------------------+  |\n"
        "|  |       Recruiter Portal           |     |     Client Hiring Manager Portal   |  |\n"
        "|  |  Next.js 14 (App Router, React)  |     |   Next.js 14 (Mobile-First, SSR)   |  |\n"
        "|  +-----------------+----------------+     +-----------------+------------------+  |\n"
        "+--------------------|----------------------------------------|---------------------+\n"
        "                     | HTTP / HTTPS / JSON                    | HTTP / HTTPS / JSON\n"
        "                     v                                        v\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|                              APPLICATION BACKEND (Render)                         |\n"
        "|  FastAPI (Python 3.11 ASGI)                                                        |\n"
        "|  ├── Routers: /auth, /requisitions, /candidates, /submissions, /pipeline, /clients|\n"
        "|  ├── Security: JWT Bearer Tokens, Bcrypt, Client Scoping Guards (404 enforcement) |\n"
        "|  ├── AI Engine: Deterministic Rule-Based Regex Extractor & Weighted Scorer        |\n"
        "|  └── CV Pipeline: pdfplumber -> pdf2image/pytesseract OCR -> python-docx          |\n"
        "+-----------------------------------------------------------------------------------+\n"
        "                                        | Motor (Async Driver)\n"
        "                                        | Beanie ODM (Pydantic v2)\n"
        "                                        v\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|                               DATABASE LAYER (MongoDB Atlas)                      |\n"
        "|  MongoDB 7.0 Document Database                                                    |\n"
        "|  ├── users (unique email index)                                                   |\n"
        "|  ├── clients                                                                      |\n"
        "|  ├── requisitions (embedded ScorecardCriterion array)                             |\n"
        "|  ├── candidates (unique SHA-256 fingerprint index, raw_text vs blind_text)        |\n"
        "|  ├── submissions (compound req+score DESC, unique req+candidate, client index)    |\n"
        "|  └── audit_logs (append-only timeline index)                                      |\n"
        "+-----------------------------------------------------------------------------------+"
    )

    add_h2("Technical Rationale for Architectural Choices")
    add_bullet(" Parsing 50+ PDF/DOCX resumes simultaneously involves substantial I/O disk writes, text extraction, and async MongoDB writes. FastAPI's native async/await architecture running on Uvicorn prevents worker starvation during bulk uploads.", "FastAPI over Flask / Django:")
    add_bullet(" Complex domain models (such as custom weighted scorecard criteria and criterion evidence) are validated automatically at request time with sub-millisecond execution overhead.", "Pydantic v2 Strict Data Validation:")
    add_bullet(" Generates interactive /docs and /redoc automatically, allowing staffing operational teams and frontend engineers to test contracts directly.", "Interactive OpenAPI Documentation:")
    add_bullet(" Resumes have semi-structured, variable schemas (differing skill tags, multi-line employment histories, variable-length text quotes). Storing this in relational tables would require 4+ join tables (candidate_skills, candidate_experiences, submission_criteria_evidences).", "MongoDB over PostgreSQL:")
    add_bullet(" Scorecard criteria are strictly owned by a single requisition and are always queried together with it. Embedding them as an array inside the Requisition document eliminates join latency and guarantees atomic updates when recruiters edit criteria.", "Embedded Scorecards in Requisitions:")
    add_bullet(" Server Components pre-render shell pages and fetch critical metadata quickly, ensuring optimal latency for enterprise recruiters scanning dozens of candidate cards.", "Next.js 14 App Router:")

    # ----------------------------------------------------
    # SECTION 2: DATA MODEL
    # ----------------------------------------------------
    add_h1("2. Data Model & Collection Design")
    add_p("The database is organized into six purpose-built MongoDB collections using Beanie ODM (Pydantic v2 document models):")

    add_bullet(" Stores agency recruiters and client hiring managers. Email has a unique index. Fields: email, hashed_password (bcrypt), full_name, role (recruiter | client_hiring_manager | delivery_head), client_id (optional foreign key scoping client managers), is_active, created_at.", "users Collection:")
    add_bullet(" Stores corporate client organizations. Fields: name, contact_email, created_at.", "clients Collection:")
    add_bullet(" Represents open job orders. Fields: title, client_id, jd_text, scorecard (embedded list of ScorecardCriterion: name, type, weight, required), status (open | closed | on_hold), created_by, created_at, updated_at.", "requisitions Collection:")
    add_bullet(" Stores parsed resume profiles. Privacy-first architecture: bifurcates raw_text (retained for human inspection) and blind_text (stripped of names, emails, phones, gender markers, age, marital status for AI scoring). Fields: full_name, email, phone, current_role, experience_years, skills, notice_days, fingerprint (unique SHA-256 hash), consent (embedded ConsentRecord: given, timestamp, purpose: 'hiring'), file_name, created_at.", "candidates Collection:")
    add_bullet(" The primary operational collection linking a candidate to a requisition. Fields: requisition_id, candidate_id, client_id, ai_score (0.0 - 100.0), criteria_scores (embedded list of CriterionEvidence: criterion_name, score, evidence_quotes, matched), pipeline_stage (sourced -> screened -> shortlisted -> client_reviewed -> interview -> offer -> joined), client_decision (pending | shortlisted | rejected | interview_proposed), rejection_reason, interview_slot, recruiter_viewed (boolean guard), submitted_at, updated_at.", "submissions Collection (Core):")
    add_bullet(" Immutable, append-only compliance trail required under the DPDP Act 2023. Fields: candidate_id, viewer_user_id, viewer_role, requisition_id, action (viewed | consent_updated | deleted), timestamp.", "audit_logs Collection:")

    add_h2("Embedding vs Referencing Decisions")
    embed_table = doc.add_table(rows=5, cols=3)
    embed_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(embed_table, color="CBD5E1", sz="4")

    headers_embed = ["Entity Pair", "Design Strategy", "Technical Justification"]
    for i, h in enumerate(headers_embed):
        cell = embed_table.cell(0, i)
        set_cell_shading(cell, HEX_HEADER_BG)
        set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    embed_data = [
        ("Requisition -> ScorecardCriterion", "Embedded", "Criteria are strictly owned by a single job requisition (<20 items). Never exist independently; embedding eliminates join overhead."),
        ("Candidate -> ConsentRecord", "Embedded", "1-to-1 attribute directly attached to the candidate's personal data lifecycle under DPDP regulations."),
        ("Submission -> CriterionEvidence", "Embedded", "Point-in-time scoring breakdown immutable to that submission; always rendered together with the candidate match card."),
        ("Submission -> Candidate & Requisition", "Referenced", "Many-to-many relationship. A candidate can be submitted across multiple jobs; requisitions hold dozens of candidates. Independent indexing is essential.")
    ]

    for row_idx, row_data in enumerate(embed_data, start=1):
        bg = HEX_ALT_ROW if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            cell = embed_table.cell(row_idx, col_idx)
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=70, bottom=70, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            r.font.color.rgb = C_SLATE
            if col_idx == 1:
                r.bold = True

    # ----------------------------------------------------
    # SECTION 3: MAIN FLOWS
    # ----------------------------------------------------
    add_h1("3. Main Operational Flows")
    add_h2("Flow A: Recruiter Sourcing to Client Submission")
    add_bullet(" Recruiter pastes the raw Job Description text into /requisitions/new and selects the client company.", "1. Requisition Intake:")
    add_bullet(" Deterministic regex extracts required years of experience, notice period cap, compensation budgets, and core technical skills into a weighted scorecard in <50ms.", "2. Automated Scorecard Extraction:")
    add_bullet(" Recruiter fine-tunes weights (0.5 to 2.0), marks mandatory skills (required=True), and saves.", "3. Scorecard Calibration:")
    add_bullet(" Recruiter uploads batches of resumes (PDF or DOCX). Native text is parsed via pdfplumber; scanned resumes fall back to Tesseract OCR.", "4. Bulk Resume Ingestion:")
    add_bullet(" Computes SHA-256 fingerprint. If the candidate already exists in the agency database, links them to the new requisition without duplicating personal records.", "5. Fingerprint Deduplication:")
    add_bullet(" Sanitizes raw text into blind_text, scores against the scorecard, and captures verbatim sentence quotes.", "6. Blind Scoring & Evidence Capture:")
    add_bullet(" Candidates are ranked by score. Recruiters must open and view candidate details (enforced by recruiter_viewed=True server check) before submitting to the client portal.", "7. Shortlist Review & Human Gatekeeping:")
    add_bullet(" DELETE /requisitions/{id} removes the job order and automatically purges all linked submissions, maintaining database integrity.", "8. Requisition Deletion:")

    add_h2("Flow B: Client Review & Interview Scheduling")
    add_bullet(" Client hiring manager logs in at /client/portal. All API queries strictly enforce user's client_id boundary.", "1. Scoped Authentication:")
    add_bullet(" Candidate phone numbers and email addresses are masked behind privacy lock badges.", "2. Privacy-First Masking:")
    add_bullet(" Hiring manager reviews pre-screened shortlists, examines overall match scores, and reads exact quoted evidence sentences.", "3. Evidence-Backed Evaluation:")
    add_bullet(" One-click shortlist, structured rejection with mandatory reason, or proposal of interview dates/times.", "4. Actionable Decisions:")
    add_bullet(" When an interview slot is proposed, candidate pipeline stage advances to interview, automatically revealing phone and email to schedule the call.", "5. Contact Disclosure:")

    # ----------------------------------------------------
    # SECTION 4: AI SCORING ENGINE
    # ----------------------------------------------------
    add_h1("4. AI Scoring Engine & Algorithmic Fairness")
    add_p("The platform relies on a high-throughput, deterministic matching architecture rather than external LLM APIs, providing sub-50ms execution speed, zero per-token API costs, and 100% reproducible results.")

    add_h2("Scoring Formula & Evidence Extraction")
    add_bullet(" Searches blind text for exact skill terms with word-boundary awareness (\\b{skill}(?:s)?\\b) to eliminate false positives. Extracts the exact matching sentence from the CV as a quoted evidence line. Exact match = 1.0; simplified variation = 0.8.", "Skill Evaluation:")
    add_bullet(" Parses required years from criterion. Full score (1.0) if candidate meets target; 0.7 if within 1 year; 0.4 if junior.", "Experience Evaluation:")
    add_bullet(" Immediate joiners (<=15 days) receive 1.0; <=30 days = 0.8; <=60 days = 0.5; >60 days = 0.2.", "Notice Period Evaluation:")
    add_bullet(" Overall Match Score = (sum(criterion_score_i * weight_i) / sum(weight_i)) * 100.", "Weighted Aggregate:")
    add_bullet(" If ANY criterion marked required=True receives a score of 0.0, the candidate's total score is strictly capped at 60.0. The candidate is NEVER automatically rejected, ensuring human recruiters retain final decision-making power.", "Mandatory Criterion 60% Cap:")

    add_h2("Algorithmic Fairness (Blind Scoring Pipeline)")
    add_bullet(" Strips dates of birth (DOB), age, gender markers (Mr/Mrs/Male/Female), marital status, nationality, and photo indicators before scoring.", "1. Demographic Stripping:")
    add_bullet(" Names and contacts in scoring input are replaced with generic tokens ([Candidate], [Candidate Email]).", "2. Identity Masking:")
    add_bullet(" Evaluates exclusively on technical competencies, project history, and job constraints.", "3. Pure Merit Evaluation:")

    # ----------------------------------------------------
    # SECTION 5: UI & DESIGN SYSTEM
    # ----------------------------------------------------
    add_h1("5. UI & Design System")
    add_p("Designed according to strict executive enterprise aesthetics, moving away from generic blue AI templates:")
    add_bullet(" Slate grays (slate-900 headers, slate-600 body, slate-50 canvas).", "Neutral Palette:")
    add_bullet(" Deep Crimson / Ruby (rose-600 / #E11D48) for primary CTAs, active badges, and focused borders, providing a distinctive high-end ATS identity.", "Brand Accent:")
    add_bullet(" Emerald (>=70% match), Amber (40-69% match), Rose (<40% match).", "Semantic Statuses:")
    add_bullet(" Clean typography on data cards; mobile-first responsive layout for client managers reviewing shortlists on smartphones.", "Typography & Layout:")

    add_h2("8 Core Application Screens")
    screens = [
        ("1. /login", "Role-aware authentication with pre-populated demo login buttons for instant recruiter, client, and executive access."),
        ("2. /dashboard", "Recruiter operational hub showing active requisitions, candidate metrics, pipeline distribution, and inline Delete actions."),
        ("3. /requisitions/new", "Split-pane JD intake view. Recruiter pastes job descriptions to trigger instant scorecard generation."),
        ("4. /requisitions/[id]/scorecard", "Interactive scorecard table to calibrate weights, add criteria, toggle mandatory flags, or delete the requisition."),
        ("5. /requisitions/[id]/upload", "Drag-and-drop batch CV upload zone supporting up to 500 files with per-file progress and duplicate warnings."),
        ("6. /requisitions/[id]/candidates", "Ranked candidate shortlist with prominent match score badges, inline verbatim CV quotes, and candidate profile drawer."),
        ("7. /requisitions/[id]/pipeline", "7-stage visual Kanban board (Sourced -> Screened -> Shortlisted -> Client Reviewed -> Interview -> Offer -> Joined)."),
        ("8. /client/portal", "Distraction-free client portal with contact masking, one-click shortlist/reject actions, and interview slot proposals.")
    ]
    for s_title, s_desc in screens:
        add_bullet(f" {s_desc}", s_title)

    # ----------------------------------------------------
    # SECTION 6: SECURITY & DPDP COMPLIANCE
    # ----------------------------------------------------
    add_h1("6. Security & DPDP Act 2023 Compliance")
    add_bullet(" Signed HMAC-SHA256 tokens with 8-hour expiration. Passwords hashed using salted bcrypt.", "JWT Authentication & Bcrypt Hashing:")
    add_bullet(" Endpoints enforce recruiter_only, recruiter_or_delivery, or client_only access.", "Role-Based Access Control (RBAC):")
    add_bullet(" The get_client_scoped_submission() guard verifies user client_id. Unauthorized requests return HTTP 404 (not 403) to prevent ID enumeration across corporate clients.", "Multi-Tenant Isolation (404 Defense):")
    add_bullet(" DELETE /candidates/{id} permanently purges candidate profile, submissions, and audit logs.", "Right to Erasure (DPDP):")
    add_bullet(" DELETE /requisitions/{id} permanently deletes the requisition and cascades to clean up all associated submissions.", "Requisition Cascade Deletion:")
    add_bullet(" Every profile view records viewer ID, role, and UTC timestamp in audit_logs.", "Immutable Audit Logging:")

    # ----------------------------------------------------
    # SECTION 7: WHAT WAS CUT & ROADMAP
    # ----------------------------------------------------
    add_h1("7. Scope Boundaries & Future Roadmap")
    add_h2("Deferred Scope (Deliberately Cut for Core Focus)")
    add_bullet(" While the backend deletion endpoint is fully implemented and tested, a dedicated self-service portal for candidates to withdraw consent was deferred.", "Candidate Self-Service Consent Portal:")
    add_bullet(" Automated email/SMS notifications via SendGrid/Twilio; client actions currently update database records in real time.", "External Webhook / Email Messaging:")
    add_bullet(" Generating branded PDF shortlist dossiers for offline executive reviews.", "PDF Dossier Export:")

    add_h2("Next Development Priorities (v2 Roadmap)")
    add_bullet(" Dedicated self-service portal for candidates to query and withdraw personal data under DPDP Act rules.", "1. Data Subject Access Portal:")
    add_bullet(" Visual variance reports analyzing discrepancies between initial AI ranking and recruiter stage promotions.", "2. AI Alignment Analytics:")
    add_bullet(" Combining deterministic regex matching with local embedding vector search for legacy resume databases.", "3. Hybrid Semantic Search:")

    # ----------------------------------------------------
    # SECTION 8: ASSUMPTIONS
    # ----------------------------------------------------
    add_h1("8. Core Engineering Assumptions")
    assumptions = [
        ("A1 - Scoring Cap: ", "Missing a required criterion caps candidate score at 60/100 rather than rejecting outright, preserving human oversight."),
        ("A2 - Blind Text Stripping: ", "Personal demographics (name, email, phone, gender, age, marital status) are removed from AI scoring input."),
        ("A3 - Deduplication Fingerprint: ", "Candidate fingerprint is computed as SHA-256(email:phone) to link repeat applicants to new jobs without data duplication."),
        ("A4 - Purpose Limitation: ", "Consent is stored as an embedded record with timestamp and purpose: 'hiring'."),
        ("A5 - Contact Masking: ", "Client portal hides email and phone until the candidate reaches the interview stage."),
        ("A6 - Deterministic Extraction: ", "Regex and curated taxonomies are used instead of LLM calls to eliminate API costs, latency, and hallucinations."),
        ("A7 - 7-Stage Pipeline: ", "Recruitment lifecycle follows sourced -> screened -> shortlisted -> client_reviewed -> interview -> offer -> joined."),
        ("A8 - File Storage: ", "Resumes are stored on local persistent disk (backend/uploads/) with modular architecture ready for S3 / Cloudflare R2."),
        ("A9 - CTC Flexibility: ", "Compensation budgets are scored based on disclosure in CV rather than acting as a rigid filter."),
        ("A10 - Client User Provisioning: ", "Client accounts are created administratively by agency leadership; public self-registration is intentionally disabled.")
    ]
    for a_title, a_desc in assumptions:
        add_bullet(a_desc, a_title)

    doc.save(output_path)
    print(f"Successfully generated proper Word document at: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, "Technical-Design-Document.docx")
    build_document(out)
