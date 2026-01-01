# resume/utils/ats/hbps_scorer.py
"""
HBPS - Human Best Practice Score

Measures what a recruiter sees in their 10-SECOND GLANCE.

This is fundamentally different from ATS scoring:
- ATS = Can software parse this?
- HBPS = Will a human keep reading after 6 seconds?

Research: Recruiters spend 6-7 seconds on initial resume scan (Ladders, 2018)
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class HBPSResult:
    """Human Best Practice Score result"""
    score: int  # 0-100
    rating: str  # Excellent, Good, Fair, Needs Work
    
    # Breakdown (what humans notice in 10 seconds)
    first_impression_score: int  # Above the fold impact
    scannability_score: int      # Can eyes jump through it quickly?
    impact_numbers_score: int    # Do metrics POP?
    credibility_score: int       # Recognizable signals?
    clarity_score: int           # Clear career story?
    
    summary: str
    what_recruiter_sees: List[str]  # What stands out in 6 seconds
    recommendations: List[str]


def _clean_text(text: str) -> str:
    """Clean LaTeX markup (works on LaTeX from PDF/DOCX conversion)"""
    # Remove LaTeX commands but keep content: \command{content} -> content
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+\*?\s*', ' ', text)
    text = re.sub(r'[{}\\]', ' ', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


def _get_first_third(text: str) -> str:
    """Get the first third of the resume (above the fold) - skip LaTeX preamble"""
    # Find document body start (skip preamble)
    doc_start = text.find('\\begin{document}')
    if doc_start == -1:
        # No document environment, use whole text
        doc_start = 0
    else:
        # Start after \begin{document}
        doc_start = text.find('\n', doc_start) + 1
        if doc_start == 0:
            doc_start = len(text)
    
    # Get document body
    doc_body = text[doc_start:]
    doc_end = doc_body.find('\\end{document}')
    if doc_end != -1:
        doc_body = doc_body[:doc_end]
    
    # Get first third of document body
    lines = doc_body.split('\n')
    third = max(1, len(lines) // 3)
    return '\n'.join(lines[:third])


# ============ HBPS SCORING FUNCTIONS ============

def _score_first_impression(text: str) -> Tuple[int, List[str]]:
    """
    Score: What does recruiter see FIRST? (Above the fold)
    - Name prominent?
    - Summary/headline present?
    - Current role visible?
    """
    first_third = _get_first_third(text).lower()
    text_lower = _clean_text(text).lower()
    standouts = []
    score = 0
    
    # Check for summary/headline (20 points)
    summary_keywords = ["summary", "professional summary", "objective", "profile", "about"]
    if any(kw in first_third for kw in summary_keywords):
        score += 25
        standouts.append("✓ Professional summary visible at top")
    
    # Check for current/recent job title visible early (25 points)
    job_indicators = ["experience", "work experience", "senior", "manager", "engineer", 
                      "developer", "analyst", "lead", "director", "associate"]
    if any(ind in first_third for ind in job_indicators):
        score += 25
        standouts.append("✓ Current role visible early")
    
    # Check for contact info at top (25 points)
    contact_patterns = [r'[\w\.-]+@[\w\.-]+', r'\+?\d[\d\-\s]{8,}', r'linkedin', r'github']
    if any(re.search(p, first_third) for p in contact_patterns):
        score += 25
        standouts.append("✓ Contact info easy to find")
    
    # Check for skills visible early (25 points)
    if "skills" in first_third or "technologies" in first_third:
        score += 25
        standouts.append("✓ Skills section visible early")
    
    return min(100, score), standouts


def _score_scannability(text: str) -> int:
    """
    Score: Can eyes jump through quickly?
    - Bullet points (not paragraphs)
    - Short bullets (≤2 lines ~20 words)
    - Clear section breaks
    """
    score = 0
    clean = _clean_text(text)
    
    # Has bullet points? (40 points)
    has_bullets = '\\item' in text or 'itemize' in text.lower() or '•' in text
    if has_bullets:
        score += 40
    
    # Check for section headers (30 points)
    section_pattern = r'\\section\*?\{|^[A-Z][A-Z\s]+$'
    sections = re.findall(section_pattern, text, re.MULTILINE)
    if len(sections) >= 3:
        score += 30
    elif len(sections) >= 1:
        score += 15
    
    # Average line length (30 points)
    lines = [l.strip() for l in clean.split('\n') if l.strip()]
    if lines:
        avg_line_length = sum(len(l.split()) for l in lines) / len(lines)
        if avg_line_length <= 15:  # Short lines = scannable
            score += 30
        elif avg_line_length <= 20:
            score += 20
        else:
            score += 10
    
    return min(100, score)


def _score_impact_numbers(text: str) -> Tuple[int, List[str]]:
    """
    Score: Do NUMBERS pop out?
    Recruiters' eyes are drawn to: $, %, numbers
    
    Measures: How prominent are metrics in the first half?
    """
    # Handle LaTeX math mode percentages before cleaning
    text_for_percents = text
    text_for_percents = re.sub(r'\$(\d+)\s*\\?%', r'\1%', text_for_percents)
    text_for_percents = re.sub(r'(\d+)\s*\\%', r'\1%', text_for_percents)
    
    clean = _clean_text(text_for_percents).lower()
    first_half = clean[:len(clean)//2]
    
    standouts = []
    
    # Find impactful numbers
    dollar_matches = re.findall(r'\$[\d,]+[kmb]?', clean)
    percent_matches = re.findall(r'\d+%', clean)
    multiplier_matches = re.findall(r'\d+x\b', clean)
    big_numbers = re.findall(r'[\d,]{4,}', clean)  # Numbers with 4+ digits
    
    # Are they in the first half? (Prominence matters)
    first_half_metrics = (
        len(re.findall(r'\$[\d,]+[kmb]?', first_half)) +
        len(re.findall(r'\d+%', first_half)) +
        len(re.findall(r'\d+x\b', first_half))
    )
    
    total_metrics = len(dollar_matches) + len(percent_matches) + len(multiplier_matches)
    
    # Build standouts
    if percent_matches:
        standouts.append(f"📈 {percent_matches[0]} - percentage achievement")
    if big_numbers and not dollar_matches:
        standouts.append(f"🔢 Large numbers ({big_numbers[0]}) catch eye")
    
    # Score based on metric density and placement
    if total_metrics >= 8 and first_half_metrics >= 3:
        score = 100
    elif total_metrics >= 5:
        score = 80
    elif total_metrics >= 3:
        score = 60
    elif total_metrics >= 1:
        score = 40
    else:
        score = 20
    
    return score, standouts


def _score_credibility(text: str) -> Tuple[int, List[str]]:
    """
    Score: Instant credibility signals
    - Recognizable company names
    - Prestigious education
    - Certifications
    - Years of experience
    """
    clean = _clean_text(text).lower()
    standouts = []
    score = 30  # Base score
    
    # Look for years of experience
    years_match = re.search(r'(\d+)\+?\s*years?', clean)
    if years_match:
        years = int(years_match.group(1))
        if years >= 5:
            score += 20
            standouts.append(f"⏱️ {years}+ years experience")
        elif years >= 2:
            score += 10
            standouts.append(f"⏱️ {years} years experience")
    
    # Certifications (25 points)
    cert_keywords = ["certified", "certification", "certificate", "aws", "pmp", 
                     "cpa", "cfa", "cissp", "professional"]
    if any(kw in clean for kw in cert_keywords):
        score += 25
        standouts.append("📜 Professional certification")
    
    # Education keywords (25 points)
    edu_keywords = ["university", "college", "bachelor", "master", "mba", "phd", 
                    "degree", "b.s.", "m.s.", "b.a.", "m.a."]
    if any(kw in clean for kw in edu_keywords):
        score += 25
        standouts.append("🎓 Formal education visible")
    
    return min(100, score), standouts


def _score_clarity(text: str) -> int:
    """
    Score: Is the career story clear at a glance?
    - Job titles present and clear
    - Dates present
    - Logical progression
    """
    clean = _clean_text(text).lower()
    score = 0
    
    # Check for date patterns (25 points)
    date_patterns = [
        r'\b20\d{2}\b',  # Years like 2020
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
        r'present|current',
    ]
    dates_found = sum(1 for p in date_patterns if re.search(p, clean))
    if dates_found >= 2:
        score += 30
    elif dates_found >= 1:
        score += 15
    
    # Check for job title patterns (35 points)
    title_keywords = ["manager", "engineer", "developer", "analyst", "designer",
                      "director", "lead", "senior", "associate", "specialist",
                      "coordinator", "consultant", "architect", "administrator"]
    titles_found = sum(1 for t in title_keywords if t in clean)
    if titles_found >= 3:
        score += 35
    elif titles_found >= 1:
        score += 20
    
    # Check for company/employer indicators (35 points)
    company_indicators = ["at ", "company", "inc", "llc", "ltd", "corp"]
    if any(ind in clean for ind in company_indicators):
        score += 35
    
    return min(100, score)


# ============ MAIN SCORING FUNCTION ============

def calculate_hbps_score(resume_text: str) -> HBPSResult:
    """
    Calculate Human Best Practice Score (HBPS).
    
    Measures what a recruiter perceives in their 6-10 second initial scan.
    
    Args:
        resume_text: Resume content (LaTeX or plain text)
        
    Returns:
        HBPSResult with score and what the recruiter sees
    """
    all_standouts = []
    recommendations = []
    
    # 1. First Impression (25%)
    first_score, first_standouts = _score_first_impression(resume_text)
    all_standouts.extend(first_standouts)
    if first_score < 60:
        recommendations.append("Add a professional summary at the top")
    
    # 2. Scannability (20%)
    scan_score = _score_scannability(resume_text)
    if scan_score < 60:
        recommendations.append("Use shorter bullet points for better scannability")
    
    # 3. Impact Numbers (25%)
    impact_score, impact_standouts = _score_impact_numbers(resume_text)
    all_standouts.extend(impact_standouts)
    if impact_score < 60:
        recommendations.append("Add more metrics ($, %, numbers) that pop visually")
    
    # 4. Credibility (15%)
    cred_score, cred_standouts = _score_credibility(resume_text)
    all_standouts.extend(cred_standouts)
    if cred_score < 50:
        recommendations.append("Highlight years of experience and certifications")
    
    # 5. Clarity (15%)
    clarity_score = _score_clarity(resume_text)
    if clarity_score < 60:
        recommendations.append("Make job titles and dates more prominent")
    
    # Calculate weighted overall score
    overall = int(
        first_score * 0.25 +
        scan_score * 0.20 +
        impact_score * 0.25 +
        cred_score * 0.15 +
        clarity_score * 0.15
    )
    
    # Determine rating
    if overall >= 80:
        rating = "Excellent"
        summary = "Strong first impression! Recruiters will want to read more."
    elif overall >= 60:
        rating = "Good"
        summary = "Good visual impact. Small tweaks could make it pop more."
    elif overall >= 40:
        rating = "Fair"
        summary = "May not grab attention in a 6-second scan. Needs work."
    else:
        rating = "Needs Work"
        summary = "Likely to be skipped. Improve visual impact and structure."
    
    return HBPSResult(
        score=overall,
        rating=rating,
        first_impression_score=first_score,
        scannability_score=scan_score,
        impact_numbers_score=impact_score,
        credibility_score=cred_score,
        clarity_score=clarity_score,
        summary=summary,
        what_recruiter_sees=all_standouts[:5],  # Top 5 things they notice
        recommendations=recommendations[:4]
    )

