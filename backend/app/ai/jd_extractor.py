import re
from typing import List, Set
from app.models import ScorecardCriterion

COMMON_SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "go",
    "ruby", "php", "swift", "kotlin", "rust", "scala", "r", "perl", "sql",
    # Frontend & Fullstack
    "react", "react.js", "next.js", "angular", "vue", "vue.js", "html", "css",
    "tailwind", "bootstrap", "redux", "graphql", "node.js", "express",
    # Backend frameworks
    "fastapi", "django", "flask", "spring", "spring boot", "asp.net", "rails",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "ci/cd",
    "jenkins", "ansible", "linux", "git", "github", "gitlab", "microservices",
    # Databases & Storage
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "snowflake", "kafka", "rabbitmq",
    # Data & AI
    "machine learning", "deep learning", "nlp", "llm", "pytorch", "tensorflow",
    "pandas", "numpy", "scikit-learn", "data science", "spark", "hadoop",
    # Process, Compliance & Methodologies
    "agile", "scrum", "rest api", "unit testing", "system design", "kyc", "aml", "excel", "compliance"
]

def extract_scorecard_from_jd(jd_text: str) -> List[ScorecardCriterion]:
    criteria: List[ScorecardCriterion] = []
    seen_names: Set[str] = set()

    # 1. Experience extraction
    # Matches: "3-5 years", "5+ years", "minimum 4 years", "at least 3 yrs", etc.
    exp_patterns = [
        r'(?:minimum|at least|min\.?)\s*(\d+(?:\.\d+)?)\s*(?:-|to|\+)?\s*(\d+(?:\.\d+)?)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant\s+)?experience)?',
        r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant\s+)?experience)?',
        r'(\d+(?:\.\d+)?)\+\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant\s+)?experience)?',
    ]
    for pattern in exp_patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            groups = [g for g in match.groups() if g]
            if len(groups) == 2:
                name = f"{groups[0]}-{groups[1]} years experience"
            elif len(groups) == 1:
                name = f"{groups[0]}+ years experience"
            else:
                name = match.group(0).strip()
            if name.lower() not in seen_names:
                criteria.append(ScorecardCriterion(
                    name=name,
                    type="experience",
                    weight=1.5,
                    required=True
                ))
                seen_names.add(name.lower())
            break

    # 2. Notice period extraction
    notice_patterns = [
        r'(?:notice\s*period|joining\s*time)[\w\s:]*?(\d{1,3})\s*(?:days?|months?|weeks?)',
        r'(\d{1,3})\s*(?:days?|months?|weeks?)\s*notice(?:\s*period)?',
        r'(immediate\s*(?:joiner|joining))'
    ]
    for pattern in notice_patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            text = match.group(0).strip()
            name = f"Notice: {text}"
            if name.lower() not in seen_names:
                criteria.append(ScorecardCriterion(
                    name=name,
                    type="notice",
                    weight=1.0,
                    required=False
                ))
                seen_names.add(name.lower())
            break

    # 3. CTC / Salary extraction
    salary_patterns = [
        r'(?:ctc|salary|budget|compensation)[\s:]*?(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lac|l)',
        r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lac)',
        r'(?:ctc|salary|budget)[\s:]*?(?:up to|upto|max)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lac)'
    ]
    for pattern in salary_patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            text = match.group(0).strip()
            name = f"CTC: {text}"
            if name.lower() not in seen_names:
                criteria.append(ScorecardCriterion(
                    name=name,
                    type="ctc",
                    weight=1.0,
                    required=False
                ))
                seen_names.add(name.lower())
            break

    # 4. Required section vs general sections for skills
    # Look for "must have" or "requirements" sections
    req_section_match = re.search(
        r'(?:requirements?|must have|required skills?|technical qualifications?|key skills?):?([\s\S]*?)(?:\n\s*\n|responsibilities|benefits|about us|who you are|nice to have|$)',
        jd_text,
        re.IGNORECASE
    )
    required_text = req_section_match.group(1) if req_section_match else ""

    # Match skills against vocabulary
    jd_lower = jd_text.lower()
    req_lower = required_text.lower()

    for skill in COMMON_SKILLS:
        # Word boundary search with optional plural 's' (e.g. 'rest api' or 'rest apis')
        pattern = rf'\b{re.escape(skill)}(?:s)?\b'
        if re.search(pattern, jd_lower):
            is_in_required = bool(re.search(pattern, req_lower)) if req_lower else False
            skill_name = skill.title() if len(skill) > 4 else skill.upper()
            if skill in ["aws", "gcp", "sql", "k8s", "nlp", "llm", "css", "html", "kyc", "aml"]:
                skill_name = skill.upper()
            elif skill in ["react.js", "node.js", "next.js", "vue.js"]:
                skill_name = skill.capitalize()

            if skill_name.lower() not in seen_names:
                criteria.append(ScorecardCriterion(
                    name=skill_name,
                    type="skill",
                    weight=1.5 if is_in_required else 1.0,
                    required=is_in_required
                ))
                seen_names.add(skill_name.lower())

    # Fallback if no skills were matched
    if not any(c.type == "skill" for c in criteria):
        criteria.append(ScorecardCriterion(
            name="General Technical Competence",
            type="skill",
            weight=1.0,
            required=False
        ))

    return criteria
