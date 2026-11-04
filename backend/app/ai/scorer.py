import re
from typing import List, Tuple
from app.models import ScorecardCriterion, CriterionEvidence, Candidate

def _find_evidence_lines(text: str, pattern: str, max_quotes: int = 2) -> List[str]:
    quotes = []
    lines = text.splitlines()
    regex = re.compile(pattern, re.IGNORECASE)
    for line in lines:
        cleaned = line.strip()
        if cleaned and regex.search(cleaned):
            if len(cleaned) > 200:
                cleaned = cleaned[:197] + "..."
            if cleaned not in quotes:
                quotes.append(cleaned)
            if len(quotes) >= max_quotes:
                break
    return quotes

def score_candidate(candidate: Candidate, scorecard: List[ScorecardCriterion]) -> Tuple[List[CriterionEvidence], float]:
    blind_text = candidate.blind_text or candidate.raw_text or ""
    evidences: List[CriterionEvidence] = []
    
    if not scorecard:
        return [], 0.0

    for crit in scorecard:
        crit_type = crit.type.lower()
        name = crit.name.strip()
        matched = False
        score = 0.0
        quotes: List[str] = []

        if crit_type == "skill":
            pattern = rf'\b{re.escape(name)}\b'
            quotes = _find_evidence_lines(blind_text, pattern)
            if quotes:
                matched = True
                score = 1.0
            else:
                # Fuzzy / partial check (e.g. "React" matching "React.js" or "ReactJS")
                simplified = re.sub(r'[\.\-\s]', '', name)
                if simplified and len(simplified) > 2:
                    fuzzy_pattern = rf'\b{re.escape(simplified)}\w*'
                    quotes = _find_evidence_lines(blind_text, fuzzy_pattern)
                    if quotes:
                        matched = True
                        score = 0.8

            # Check if skill was extracted in candidate.skills list
            if not matched and any(s.lower() == name.lower() for s in candidate.skills):
                matched = True
                score = 0.9
                quotes = [f"Identified in candidate skills profile: {name}"]

        elif crit_type == "experience":
            # Extract target years from criterion name e.g. "3-5 years" or "5+ years"
            req_years = 0.0
            num_match = re.search(r'(\d+(?:\.\d+)?)', name)
            if num_match:
                req_years = float(num_match.group(1))

            quotes = _find_evidence_lines(
                blind_text,
                r'(?:total\s*experience|experience)?\s*[:\-]?\s*\d+(?:\.\d+)?\s*(?:\+|-to\s*\d+)?\s*(?:years?|yrs?)'
            )
            cand_years = candidate.experience_years or 0.0

            if cand_years >= req_years and req_years > 0:
                matched = True
                score = 1.0
            elif cand_years >= max(0.0, req_years - 1.0) and req_years > 0:
                matched = True
                score = 0.7
            elif cand_years > 0:
                matched = False
                score = 0.4
            else:
                matched = False
                score = 0.0

            if not quotes and cand_years > 0:
                quotes = [f"Total detected experience: {cand_years} years"]

        elif crit_type == "notice":
            quotes = _find_evidence_lines(blind_text, r'notice|immediate\s*joiner')
            cand_notice = candidate.notice_days

            if cand_notice is not None:
                if cand_notice <= 15:
                    matched = True
                    score = 1.0
                elif cand_notice <= 30:
                    matched = True
                    score = 0.8
                elif cand_notice <= 60:
                    matched = False
                    score = 0.5
                else:
                    matched = False
                    score = 0.2
            else:
                # Neutral if not specified in text
                score = 0.5
                matched = False

            if not quotes and cand_notice is not None:
                quotes = [f"Detected notice period: {cand_notice} days"]

        elif crit_type == "ctc":
            quotes = _find_evidence_lines(blind_text, r'ctc|salary|lpa|compensation')
            if quotes:
                matched = True
                score = 0.8
            else:
                score = 0.5
                matched = False

        else:
            # "other" or general criterion
            words = [w for w in re.split(r'\W+', name) if len(w) > 3]
            if words:
                pattern = '|'.join(re.escape(w) for w in words)
                quotes = _find_evidence_lines(blind_text, pattern)
                if quotes:
                    matched = True
                    score = 1.0
                else:
                    score = 0.0
            else:
                score = 0.5

        evidences.append(CriterionEvidence(
            criterion_name=name,
            score=round(score, 2),
            evidence_quotes=quotes,
            matched=matched
        ))

    # Calculate overall score
    total_weight = sum(c.weight for c in scorecard)
    if total_weight <= 0:
        total_weight = float(len(scorecard))

    weighted_sum = sum(ev.score * c.weight for ev, c in zip(evidences, scorecard))
    overall_score = (weighted_sum / total_weight) * 100.0

    # Capped if any required criterion has score 0.0
    has_unmet_required = any(c.required and ev.score == 0.0 for ev, c in zip(evidences, scorecard))
    if has_unmet_required:
        overall_score = min(overall_score, 60.0)

    overall_score = round(max(0.0, min(100.0, overall_score)), 1)
    return evidences, overall_score
