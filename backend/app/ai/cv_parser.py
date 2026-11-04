import re
import hashlib
import io
from typing import Dict, Any, Tuple, Optional, List
import docx
import pdfplumber
from app.ai.jd_extractor import COMMON_SKILLS

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages).strip()
    except Exception:
        text = ""

    # Fallback to OCR if extracted text is too short (< 50 chars)
    if len(text) < 50:
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            images = convert_from_bytes(file_bytes)
            ocr_pages = [pytesseract.image_to_string(img) for img in images]
            ocr_text = "\n".join(ocr_pages).strip()
            if len(ocr_text) > len(text):
                text = ocr_text
        except Exception:
            pass
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()

def extract_profile_and_blind_text(raw_text: str, filename: str = "") -> Tuple[Dict[str, Any], str, Optional[str]]:
    if not raw_text or len(raw_text.strip()) < 10:
        return {}, "", f"Could not extract sufficient text from {filename}"

    # 1. Extract Email
    email = None
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
    if email_match:
        email = email_match.group(0).lower().strip()

    # 2. Extract Phone (Indian mobile numbers: 10 digits starting with 6-9, optional +91/0 prefix)
    phone = None
    phone_matches = re.findall(r'(?:(?:\+91|91|0)?[-\s]?)?([6-9]\d{9})\b', raw_text)
    if phone_matches:
        phone = phone_matches[0]

    # 3. Extract Name
    name = None
    name_prefix_match = re.search(
        r'(?:name|full\s*name|candidate\s*name)\s*[:\-]\s*([A-Za-z\s\.\']{2,40})',
        raw_text,
        re.IGNORECASE
    )
    if name_prefix_match:
        name = name_prefix_match.group(1).strip()
    else:
        # Check first non-empty lines before contact info
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for line in lines[:5]:
            if re.search(r'^(?:resume|curriculum\s*vitae|cv|profile|biodata|bio-data)\b', line, re.IGNORECASE):
                continue
            if "@" in line or any(c.isdigit() for c in line):
                continue
            words = line.split()
            if 1 <= len(words) <= 4 and all(re.match(r'^[A-Za-z\.\']+$', w) for w in words):
                # Avoid common section headers
                if line.lower() not in ["summary", "skills", "experience", "education", "contact", "objective"]:
                    name = line
                    break

    if not name:
        name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

    # Clean up name: remove titles like Mr, Mrs, Ms
    name = re.sub(r'^(?:Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?)\s+', '', name, flags=re.IGNORECASE).strip()

    # 4. Extract Current Role
    current_role = None
    role_match = re.search(
        r'(?:current\s*role|designation|title|position)\s*[:\-]\s*([A-Za-z\s\/\-]{2,40})',
        raw_text,
        re.IGNORECASE
    )
    if role_match:
        current_role = role_match.group(1).strip()
    else:
        # Look for typical job titles in the first 15 lines
        common_roles = [
            "software engineer", "senior software engineer", "full stack developer",
            "frontend developer", "backend developer", "python developer", "java developer",
            "devops engineer", "data engineer", "data scientist", "machine learning engineer",
            "tech lead", "engineering manager", "qa engineer", "system architect"
        ]
        for role in common_roles:
            if re.search(rf'\b{re.escape(role)}\b', raw_text[:800], re.IGNORECASE):
                current_role = role.title()
                break

    # 5. Extract Experience Years
    experience_years = None
    exp_matches = re.findall(
        r'(?:total\s*experience|experience)?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:\+|-to\s*\d+)?\s*(?:years?|yrs?)',
        raw_text,
        re.IGNORECASE
    )
    if exp_matches:
        try:
            # Pick the largest or first valid experience value
            vals = [float(v) for v in exp_matches if float(v) <= 40]
            if vals:
                experience_years = max(vals)
        except Exception:
            pass

    # 6. Extract Notice Period Days
    notice_days = None
    notice_match = re.search(
        r'(?:notice\s*period|notice)[\w\s:]*?(\d{1,3})\s*(days?|months?|weeks?)',
        raw_text,
        re.IGNORECASE
    )
    if notice_match:
        val = int(notice_match.group(1))
        unit = notice_match.group(2).lower()
        if "month" in unit:
            notice_days = val * 30
        elif "week" in unit:
            notice_days = val * 7
        else:
            notice_days = val
    elif re.search(r'immediate\s*(?:joiner|joining)', raw_text, re.IGNORECASE):
        notice_days = 0

    # 7. Extract Skills
    skills = []
    text_lower = raw_text.lower()
    for skill in COMMON_SKILLS:
        if re.search(rf'\b{re.escape(skill)}\b', text_lower):
            skill_name = skill.upper() if skill in ["aws", "gcp", "sql", "k8s", "nlp", "llm", "css", "html"] else skill.title()
            if skill_name not in skills:
                skills.append(skill_name)

    # 8. Generate Fingerprint
    # sha256(normalize(email) + normalize(phone)) if both exist
    # else sha256(normalize(name) + normalize(role))
    norm_email = email.strip().lower() if email else ""
    norm_phone = "".join(filter(str.isdigit, phone))[-10:] if phone else ""
    norm_name = re.sub(r'[^a-zA-Z]', '', name).lower()
    norm_role = re.sub(r'[^a-zA-Z]', '', current_role or "").lower()

    if norm_email and norm_phone:
        fp_str = f"{norm_email}:{norm_phone}"
    elif norm_email:
        fp_str = f"{norm_email}:{norm_name}"
    else:
        fp_str = f"{norm_name}:{norm_role}"
    fingerprint = hashlib.sha256(fp_str.encode("utf-8")).hexdigest()

    # 9. Create Blind Text (Strip protected attributes: DOB, Age, Gender, Marital Status, Nationality, Name, Contacts)
    blind_lines = []
    protected_regex = re.compile(
        r'(?:date\s*of\s*birth|dob|age\s*[:\-]|gender\s*[:\-]|sex\s*[:\-]|marital\s*status|nationality|photo\b|\[photo\]|\[image\])',
        re.IGNORECASE
    )
    salutation_regex = re.compile(
        r'^(?:mr\.|mrs\.|ms\.|miss)\s+',
        re.IGNORECASE
    )

    for line in raw_text.splitlines():
        # Remove lines matching protected demographic indicators
        if protected_regex.search(line):
            continue
        # Strip salutations if present
        line = salutation_regex.sub('', line)
        blind_lines.append(line)

    blind_text = "\n".join(blind_lines)

    # Replace candidate's own full name
    if name and len(name) > 2:
        blind_text = re.sub(rf'\b{re.escape(name)}\b', '[Candidate]', blind_text, flags=re.IGNORECASE)

    # Mask email and phone
    if email:
        blind_text = blind_text.replace(email, '[Candidate Email]')
    if phone:
        blind_text = blind_text.replace(phone, '[Candidate Phone]')

    profile = {
        "full_name": name,
        "email": email,
        "phone": phone,
        "current_role": current_role,
        "experience_years": experience_years,
        "skills": skills,
        "notice_days": notice_days,
        "fingerprint": fingerprint,
    }

    return profile, blind_text, None
