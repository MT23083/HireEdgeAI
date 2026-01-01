# resume/utils/ats/ats_universal_scorer.py
"""
ATS Score WITHOUT Job Description

Uses universal, objective criteria that NEVER need updating:
- Section presence (Experience, Education, Skills, Contact)
- Measurable results (numbers, percentages, metrics)
- Action verbs at bullet starts
- Resume length and structure
- Parsing safety (no complex formatting)

These are timeless resume best practices recognized by all ATS systems.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass 
class ATSUniversalResult:
    """Result of universal ATS scoring (no JD needed)"""
    score: int  # 0-100
    rating: str  # Excellent, Good, Fair, Needs Work
    
    # Breakdown
    section_score: int  # 0-100
    metrics_score: int  # 0-100
    action_verbs_score: int  # 0-100
    structure_score: int  # 0-100
    design_score: int  # 0-100 (NEW: Design & Template compatibility)
    
    # Details
    found_sections: List[str]
    missing_sections: List[str]
    metrics_count: int
    action_verbs_count: int
    word_count: int
    design_issues: List[str]  # NEW: Design problems found
    
    summary: str
    recommendations: List[str]


# ============ UNIVERSAL CRITERIA (Never need updating) ============

# These section names are UNIVERSAL across all industries
REQUIRED_SECTIONS = {
    "experience": ["experience", "work experience", "professional experience", 
                   "employment", "work history", "career history"],
    "education": ["education", "academic", "qualifications", "degrees", 
                  "academic background"],
    "skills": ["skills", "technical skills", "core competencies", "expertise",
               "technologies", "competencies", "abilities"],
}

RECOMMENDED_SECTIONS = {
    "contact": ["email", "phone", "linkedin", "@", "github"],  # Look for patterns, not headers
    "summary": ["summary", "professional summary", "objective", "profile", "about me"],
}


def _clean_text(text: str) -> str:
    """Clean LaTeX and normalize (works on LaTeX from PDF/DOCX conversion)"""
    # Remove LaTeX commands but keep content: \command{content} -> content
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+\*?\s*', ' ', text)
    text = re.sub(r'[{}\\]', ' ', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


# ============ SCORING FUNCTIONS ============

def _score_sections(text: str) -> Tuple[int, List[str], List[str]]:
    """Score presence of required sections (25 points)"""
    text_lower = _clean_text(text)
    found = []
    missing = []
    
    for section, variants in REQUIRED_SECTIONS.items():
        if any(v in text_lower for v in variants):
            found.append(section.title())
        else:
            missing.append(section.title())
    
    # Check contact info (patterns, not headers)
    has_contact = any(p in text_lower for p in RECOMMENDED_SECTIONS["contact"])
    if has_contact:
        found.append("Contact Info")
    else:
        missing.append("Contact Info")
    
    # ENHANCED: Check for hard skills vs soft skills separation
    skills_section_found = any(v in text_lower for v in REQUIRED_SECTIONS["skills"])
    if skills_section_found:
        # Check if hard skills are present (technical terms)
        hard_skill_indicators = [
            'python', 'java', 'javascript', 'sql', 'c++', 'react', 'angular', 'vue',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'jenkins', 'terraform',
            'tableau', 'power bi', 'excel', 'postgresql', 'mysql', 'mongodb',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'
        ]
        has_hard_skills = any(indicator in text_lower for indicator in hard_skill_indicators)
        
        # Check if soft skills are present
        soft_skill_indicators = [
            'leadership', 'communication', 'teamwork', 'collaboration', 'problem-solving',
            'analytical', 'time management', 'project management', 'mentoring'
        ]
        has_soft_skills = any(indicator in text_lower for indicator in soft_skill_indicators)
        
        if not has_hard_skills:
            missing.append("Hard Skills (Technical)")
        if not has_soft_skills:
            missing.append("Soft Skills")
    
    # Score: each section worth 25 points (4 sections total)
    score = min(100, len(found) * 25)
    return score, found, missing


def _score_metrics(text: str) -> Tuple[int, int]:
    """Score measurable achievements - numbers, %, $ (25 points)"""
    # First, extract percentages from LaTeX math mode before cleaning
    # Handle: $60\%$, 60\%, 60%, etc.
    text_for_percents = text
    # Convert LaTeX math mode percentages to plain: $60\%$ -> 60%
    text_for_percents = re.sub(r'\$(\d+)\s*\\?%', r'\1%', text_for_percents)
    text_for_percents = re.sub(r'(\d+)\s*\\%', r'\1%', text_for_percents)
    
    text_clean = _clean_text(text_for_percents)
    
    # Patterns for metrics (universal - never change)
    patterns = [
        r'\d+%',           # Percentages (now handles LaTeX escaped)
        r'\$[\d,]+',       # Dollar amounts
        r'[\d,]+\+',       # Numbers with plus
        r'\d+x\b',         # Multipliers (word boundary)
        r'\d+\s+years?',   # Years of experience
        r'\d+\s+months?',  # Months
        r'\d+\s+team',      # Team size
        r'\d+\s+projects?',  # Project count
        r'\d+\s+clients?',   # Client count
        r'[\d,]+\s+users?',  # User count
        r'[\d,]+\s+customers?',
    ]
    
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text_clean))
    
    # Score: 0 metrics = 20, 3+ metrics = 60, 6+ = 80, 10+ = 100
    if count >= 10:
        score = 100
    elif count >= 6:
        score = 80
    elif count >= 3:
        score = 60
    elif count >= 1:
        score = 40
    else:
        score = 20
    
    return score, count


def _score_action_verbs(text: str) -> Tuple[int, int]:
    """Score action verbs at bullet starts (25 points) - STRICT: must be at bullet start"""
    # These verbs are UNIVERSAL and timeless
    action_verbs = {
        # Achievement
        "achieved", "accomplished", "attained", "exceeded", "delivered",
        # Creation
        "built", "created", "designed", "developed", "established", "launched",
        # Leadership
        "led", "managed", "directed", "supervised", "coordinated", "mentored",
        # Improvement
        "improved", "increased", "enhanced", "optimized", "streamlined", "reduced",
        # Execution
        "implemented", "executed", "performed", "conducted", "operated",
        # Analysis
        "analyzed", "evaluated", "assessed", "researched", "investigated",
        # Communication
        "presented", "negotiated", "collaborated", "partnered", "facilitated",
    }
    
    # Find all bullet points
    import re
    # Match \item followed by content
    bullets = re.findall(r'\\item\s+([A-Z][^\\]+?)(?=\\item|\\end|\Z)', text, re.DOTALL)
    
    bullets_with_action_verbs = 0
    total_action_verbs = 0
    
    for bullet in bullets:
        # Clean bullet text
        bullet_clean = _clean_text(bullet)
        words = bullet_clean.split()
        
        # Check if first word (after cleaning) is an action verb
        if words:
            first_word = words[0].rstrip('.,;:')
            if first_word in action_verbs:
                bullets_with_action_verbs += 1
        
        # Count all action verbs in bullet
        total_action_verbs += sum(1 for word in words if word.rstrip('.,;:') in action_verbs)
    
    # Score based on percentage of bullets starting with action verbs
    if bullets:
        action_verb_ratio = bullets_with_action_verbs / len(bullets)
        if action_verb_ratio >= 0.9:  # 90%+ bullets start with action verbs
            score = 100
        elif action_verb_ratio >= 0.7:  # 70%+
            score = 80
        elif action_verb_ratio >= 0.5:  # 50%+
            score = 60
        elif action_verb_ratio >= 0.3:  # 30%+
            score = 40
        else:
            score = 20
    else:
        # No bullets found - check for any action verbs in text
        text_clean = _clean_text(text)
        words = text_clean.split()
        count = sum(1 for word in words if word.rstrip('.,;:') in action_verbs)
        if count >= 10:
            score = 60
        elif count >= 5:
            score = 40
        else:
            score = 20
        total_action_verbs = count
    
    return score, total_action_verbs


def _score_structure(text: str) -> Tuple[int, int]:
    """Score resume length and structure (25 points)"""
    text_clean = _clean_text(text)
    words = text_clean.split()
    word_count = len(words)
    
    # Has bullet points?
    has_bullets = 'itemize' in text.lower() or '\\item' in text or '•' in text
    
    # Optimal length: 400-700 words (1 page equivalent)
    if 400 <= word_count <= 700:
        length_score = 50
    elif 300 <= word_count < 400 or 700 < word_count <= 900:
        length_score = 40
    elif 200 <= word_count < 300 or 900 < word_count <= 1100:
        length_score = 30
    else:
        length_score = 20
    
    # Bullet points add 50 points
    bullet_score = 50 if has_bullets else 20
    
    score = length_score + bullet_score
    return min(100, score), word_count


# ============ MAIN SCORING FUNCTION ============

def _check_tailored_title(resume_text: str) -> Tuple[bool, str]:
    """Check if resume has a tailored title/role in summary"""
    import re
    # Find summary section
    summary_match = re.search(r'\\section\*\{[^}]*[Ss]ummary[^}]*\}(.*?)(?=\\section|\Z)', resume_text, re.DOTALL)
    if not summary_match:
        return False, "No summary section found"
    
    summary = _clean_text(summary_match.group(1))
    
    # Common job titles/roles
    role_indicators = [
        'analyst', 'engineer', 'developer', 'manager', 'specialist', 'consultant',
        'architect', 'scientist', 'designer', 'coordinator', 'director', 'lead'
    ]
    
    has_role = any(indicator in summary for indicator in role_indicators)
    
    if has_role:
        return True, "Role/title mentioned in summary"
    else:
        return False, "Add your target role/title in the summary section"


def _score_design_and_template(resume_text: str) -> Tuple[int, List[str]]:
    """
    Score resume design and template for ATS compatibility.
    
    ATS systems struggle with:
    - Complex layouts (tables, columns, multi-column)
    - Graphics/images
    - Non-standard fonts
    - Headers/footers
    - Text boxes
    
    Returns: (score 0-100, list of design issues)
    """
    issues = []
    score = 100  # Start perfect, deduct for issues
    
    # 1. Check for tables (major ATS parsing issue)
    table_count = resume_text.count('\\begin{table}') + resume_text.count('\\begin{tabular}')
    if table_count > 0:
        score -= 30
        issues.append(f"Contains {table_count} table(s) - ATS systems struggle with tables")
    
    # 2. Check for multi-column layout
    if '\\begin{multicols}' in resume_text or '\\twocolumn' in resume_text:
        score -= 25
        issues.append("Uses multi-column layout - ATS prefers single column")
    
    # 3. Check for graphics/images
    image_count = resume_text.count('\\includegraphics') + resume_text.count('\\graphicspath')
    if image_count > 0:
        score -= 20
        issues.append(f"Contains {image_count} image(s) - Images can't be parsed by ATS")
    
    # 4. Check for complex positioning (text boxes, absolute positioning)
    if '\\textbox' in resume_text or '\\tikz' in resume_text or '\\put(' in resume_text:
        score -= 15
        issues.append("Uses complex positioning - May confuse ATS parsers")
    
    # 5. Check for headers/footers (can interfere with parsing)
    if '\\fancyhead' in resume_text or '\\fancyfoot' in resume_text or '\\pagestyle{fancy}' in resume_text:
        score -= 10
        issues.append("Uses custom headers/footers - May interfere with ATS parsing")
    
    # 6. Check for too many custom packages (indicates complex design)
    package_count = len(re.findall(r'\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}', resume_text))
    if package_count > 15:
        score -= 10
        issues.append(f"Uses {package_count} packages - Complex design may confuse ATS")
    elif package_count > 10:
        score -= 5
        issues.append(f"Uses {package_count} packages - Consider simplifying")
    
    # 7. Check for decorative fonts (non-standard)
    decorative_fonts = ['\\usepackage{fontspec}', '\\usepackage{fontawesome}', '\\usepackage{fontawesome5}']
    decorative_count = sum(1 for font in decorative_fonts if font in resume_text)
    if decorative_count > 1:
        score -= 5
        issues.append("Uses multiple decorative font packages - Stick to standard fonts")
    
    # 8. Check for color usage (excessive colors can be problematic)
    color_commands = resume_text.count('\\textcolor{') + resume_text.count('\\color{')
    if color_commands > 10:
        score -= 5
        issues.append("Uses many colors - ATS works best with black text")
    
    # 9. Check for hyperlinks (OK, but too many can be problematic)
    hyperlink_count = resume_text.count('\\href{')
    if hyperlink_count > 8:
        score -= 5
        issues.append(f"Contains {hyperlink_count} hyperlinks - Consider reducing")
    
    # 10. Check for simple, clean structure (positive)
    # If using standard article class with minimal customization, that's good
    if '\\documentclass{article}' in resume_text or '\\documentclass[11pt,a4paper]{article}' in resume_text:
        if score < 100:
            score += 5  # Bonus for using standard article class
    elif '\\documentclass{moderncv}' in resume_text or '\\documentclass{altacv}' in resume_text:
        score -= 10
        issues.append("Uses CV-specific class - May have parsing issues")
    
    # Ensure score is between 0-100
    score = max(0, min(100, score))
    
    return score, issues


def calculate_ats_universal_score(resume_text: str) -> ATSUniversalResult:
    """
    Calculate ATS score using universal criteria (no JD needed).
    
    Measures objective, timeless resume qualities:
    - Section completeness (including hard/soft skills)
    - Quantifiable achievements  
    - Action verbs at bullet starts
    - Structure and length
    - Tailored title in summary
    
    Args:
        resume_text: Resume content (LaTeX or plain text)
        
    Returns:
        ATSUniversalResult with score and detailed breakdown
    """
    recommendations = []
    
    # 1. Sections (20%) - Reduced weight to make room for new checks
    section_score, found, missing = _score_sections(resume_text)
    if missing:
        recommendations.append(f"Add missing sections: {', '.join(missing)}")
    
    # 2. Metrics (25%)
    metrics_score, metrics_count = _score_metrics(resume_text)
    if metrics_count < 5:
        recommendations.append("Add more quantifiable achievements (numbers, %, $)")
    
    # 3. Action Verbs (25%) - Now checks if verbs are at bullet START
    verbs_score, verbs_count = _score_action_verbs(resume_text)
    # Check bullet structure
    import re
    bullets = re.findall(r'\\item\s+', resume_text)
    if bullets:
        bullets_with_verbs = len([b for b in bullets if True])  # Simplified check
        if len(bullets) > 0 and verbs_count < len(bullets) * 0.7:
            recommendations.append("Start more bullets with action verbs (Led, Built, Achieved, Analyzed)")
    
    # 4. Structure (15%) - Reduced weight
    structure_score, word_count = _score_structure(resume_text)
    if word_count < 350:
        recommendations.append("Resume may be too short - aim for 400-700 words")
    elif word_count > 800:
        recommendations.append("Resume may be too long - aim for 400-700 words (1 page)")
    
    # 5. NEW: Design & Template (15%)
    design_score, design_issues = _score_design_and_template(resume_text)
    if design_issues:
        recommendations.extend(design_issues[:2])  # Add top 2 design issues
    
    # 6. NEW: Tailored Title (10%)
    has_title, title_msg = _check_tailored_title(resume_text)
    title_score = 100 if has_title else 50
    if not has_title:
        recommendations.append("Add your target role/title in the summary section")
    
    # Calculate overall score with new weighting
    overall = int(
        section_score * 0.20 +
        metrics_score * 0.25 +
        verbs_score * 0.25 +
        structure_score * 0.15 +
        design_score * 0.15 +
        title_score * 0.10
    )
    
    # CRITICAL: Cap the score if any major component is weak
    # A perfect score (100) should only be possible if all components are strong
    min_component_score = min(section_score, metrics_score, verbs_score, structure_score, design_score)
    
    # If any component is below 70, cap the overall score
    if min_component_score < 70:
        overall = min(overall, 85)  # Cap at 85 if any component is weak
    elif min_component_score < 80:
        overall = min(overall, 90)  # Cap at 90 if any component is below 80
    # If all components are 80+, allow up to 100
    
    # Determine rating
    if overall >= 85:
        rating = "Excellent"
        summary = "Your resume follows ATS best practices well!"
    elif overall >= 70:
        rating = "Good"
        summary = "Good foundation. Small improvements could boost your score."
    elif overall >= 55:
        rating = "Fair"
        summary = "Your resume needs some optimization for ATS systems."
    else:
        rating = "Needs Work"
        summary = "Significant improvements needed for ATS compatibility."
    
    return ATSUniversalResult(
        score=overall,
        rating=rating,
        section_score=section_score,
        metrics_score=metrics_score,
        action_verbs_score=verbs_score,
        structure_score=structure_score,
        design_score=design_score,
        found_sections=found,
        missing_sections=missing,
        metrics_count=metrics_count,
        action_verbs_count=verbs_count,
        word_count=word_count,
        design_issues=design_issues,
        summary=summary,
        recommendations=recommendations[:6]  # Show up to 6 recommendations
    )

