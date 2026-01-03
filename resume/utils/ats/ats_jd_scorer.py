# resume/utils/ats/ats_jd_scorer.py
"""
ATS Score WITH Job Description

Production-grade hybrid scoring using:
- LLM-based JD keyword classification (cached)
- TF-IDF cosine similarity
- SBERT semantic similarity

This is the most accurate score - requires a job description.
"""

from __future__ import annotations
import re
import math
import os
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Any
from collections import Counter

# Optional dependencies
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Required dependency - SBERT for semantic similarity
from sentence_transformers import SentenceTransformer, util


@dataclass
class JDKeywords:
    """Classified keywords from job description"""
    must_have: List[str]
    nice_to_have: List[str]
    soft_skills: List[str]


@dataclass
class ATSJDResult:
    """Result of ATS scoring with job description"""
    score: int  # 0-100
    rating: str  # Excellent, Good, Fair, Needs Work
    matched_keywords: List[str]
    missing_keywords: List[str]
    summary: str


# ============ TEXT PROCESSING ============

# Stop words to filter out
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'must', 'can', 'need',
    'our', 'you', 'your', 'we', 'they', 'their', 'this', 'that', 'it',
    'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'not', 'only', 'same', 'so', 'than', 'too', 'very',
    'just', 'also', 'now', 'here', 'there', 'when', 'where', 'why', 'how',
    'what', 'which', 'who', 'whom', 'able', 'about', 'above', 'across',
}


def _clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+\*?\s*', ' ', text)
    text = re.sub(r'[{}\\]', ' ', text)
    text = re.sub(r'https?://\S+', '', text)
    # Replace ampersands with 'and' to preserve phrase meaning
    text = re.sub(r'&', ' and ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


def _extract_terms(text: str) -> List[str]:
    """Extract words and meaningful bigrams from text"""
    text = _clean_text(text)
    
    # Extract words - improved regex to handle hyphenated terms and word boundaries
    # Match: words with letters/numbers/hyphens (preserve hyphenated terms like "hands-on")
    words = re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', text)
    
    # Filter out stop words and very short words (keep meaningful terms)
    valid_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    # Generate bigrams from filtered words (no stop words in the list now)
    # Only create bigrams if both words are meaningful
    bigrams = []
    for i in range(len(valid_words) - 1):
        w1, w2 = valid_words[i], valid_words[i+1]
        # Only create bigram if both words are substantial
        if len(w1) > 2 and len(w2) > 2:
            bigrams.append(f"{w1} {w2}")
    
    return valid_words + bigrams


# ============ LLM KEYWORD CLASSIFICATION ============

# Cache for JD keywords (JD hash -> JDKeywords)
_jd_keywords_cache: Dict[str, JDKeywords] = {}


def _get_openai_client() -> Optional[Any]:
    """Get OpenAI client if available"""
    if not OPENAI_AVAILABLE:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _get_openai_model() -> str:
    """Get the OpenAI model to use"""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _hash_jd(job_description: str) -> str:
    """Generate hash for job description (for caching)"""
    return hashlib.md5(job_description.encode('utf-8')).hexdigest()


def classify_jd_keywords_llm(job_description: str, use_cache: bool = True) -> JDKeywords:
    """
    Uses a cheap LLM to extract and classify JD keywords.
    Called ONCE per JD and cached.
    
    Args:
        job_description: The job description text
        use_cache: Whether to use cached results (default: True)
        
    Returns:
        JDKeywords with classified keywords
    """
    # Check cache first
    jd_hash = _hash_jd(job_description)
    if use_cache and jd_hash in _jd_keywords_cache:
        return _jd_keywords_cache[jd_hash]
    
    client = _get_openai_client()
    
    # Fallback if OpenAI not available
    if not client:
        # Fallback: extract basic keywords without classification
        terms = _extract_terms(job_description)
        keywords = [t for t in set(terms) if t not in STOP_WORDS and len(t) > 2]
        result = JDKeywords(
            must_have=keywords[:15],
            nice_to_have=keywords[15:25],
            soft_skills=[]
        )
        if use_cache:
            _jd_keywords_cache[jd_hash] = result
        return result
    
    prompt = f"""Extract keywords from the job description and classify them.

Rules:
- must_have: technical skills, tools, programming languages, mandatory requirements (e.g., Java, Python, AWS, 3+ years experience)
- nice_to_have: optional skills, bonus experience, preferred qualifications
- soft_skills: communication, leadership, teamwork, problem-solving, collaboration, etc.

Return ONLY valid JSON in this format:
{{
  "must_have": ["keyword1", "keyword2", ...],
  "nice_to_have": ["keyword1", "keyword2", ...],
  "soft_skills": ["skill1", "skill2", ...]
}}

- Max 15 must_have, 10 nice_to_have, 8 soft_skills
- Use concise, single keywords or short phrases (2-3 words max)
- Be specific (e.g., "Java" not "programming languages")

Job Description:
{job_description}"""

    try:
        response = client.chat.completions.create(
            model=_get_openai_model(),
            temperature=0,  # Deterministic
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        
        result = JDKeywords(
            must_have=data.get("must_have", [])[:15],
            nice_to_have=data.get("nice_to_have", [])[:10],
            soft_skills=data.get("soft_skills", [])[:8]
        )
        
        # Cache result
        if use_cache:
            _jd_keywords_cache[jd_hash] = result
        
        return result
        
    except Exception as e:
        # Fallback on error
        terms = _extract_terms(job_description)
        keywords = [t for t in set(terms) if t not in STOP_WORDS and len(t) > 2]
        result = JDKeywords(
            must_have=keywords[:15],
            nice_to_have=keywords[15:25],
            soft_skills=[]
        )
        if use_cache:
            _jd_keywords_cache[jd_hash] = result
        return result


# ============ SBERT SEMANTIC SIMILARITY ============

_sbert_model: Optional[Any] = None


def _get_sbert_model():
    """Lazy load SBERT model (required dependency)"""
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sbert_model


def sbert_similarity(resume_text: str, job_description: str) -> float:
    """
    Compute semantic similarity using SBERT embeddings.
    
    Args:
        resume_text: Resume content
        job_description: Job description
        
    Returns:
        Similarity score between 0 and 1
    """
    model = _get_sbert_model()
    
    # Clean text for better embeddings
    resume_clean = _clean_text(resume_text)[:1000]  # Limit length
    jd_clean = _clean_text(job_description)[:1000]
    
    emb_resume = model.encode(resume_clean, convert_to_tensor=True)
    emb_jd = model.encode(jd_clean, convert_to_tensor=True)
    
    similarity = float(util.cos_sim(emb_resume, emb_jd)[0][0])
    return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]


# ============ KEYWORD SCORING ============

def keyword_match_score(resume_terms: Set[str], jd_keywords: JDKeywords) -> float:
    """
    Calculate weighted keyword match score.
    
    Args:
        resume_terms: Set of terms extracted from resume (lowercase)
        jd_keywords: Classified JD keywords
        
    Returns:
        Score between 0 and 1
    """
    score = 0.0
    max_score = 0.0
    
    # Normalize resume terms to lowercase set for matching
    resume_lower = {t.lower() for t in resume_terms}
    
    # Must-have keywords (weight: 3.0)
    for skill in jd_keywords.must_have:
        max_score += 3.0
        skill_lower = skill.lower()
        # Check exact match or if skill is contained in any resume term
        if skill_lower in resume_lower or any(skill_lower in term for term in resume_lower):
            score += 3.0
    
    # Nice-to-have keywords (weight: 1.5)
    for skill in jd_keywords.nice_to_have:
        max_score += 1.5
        skill_lower = skill.lower()
        if skill_lower in resume_lower or any(skill_lower in term for term in resume_lower):
            score += 1.5
    
    # Soft skills (weight: 0.5)
    for skill in jd_keywords.soft_skills:
        max_score += 0.5
        skill_lower = skill.lower()
        if skill_lower in resume_lower or any(skill_lower in term for term in resume_lower):
            score += 0.5
    
    if max_score == 0:
        return 1.0
    
    return score / max_score


# ============ TF-IDF + COSINE SIMILARITY ============

def _compute_tf(terms: List[str]) -> Dict[str, float]:
    """Compute term frequency"""
    count = Counter(terms)
    total = len(terms)
    if total == 0:
        return {}
    return {term: c / total for term, c in count.items()}


def _compute_idf(doc1_terms: List[str], doc2_terms: List[str]) -> Dict[str, float]:
    """Compute IDF for two documents"""
    all_terms = set(doc1_terms) | set(doc2_terms)
    idf = {}
    for term in all_terms:
        doc_count = (1 if term in doc1_terms else 0) + (1 if term in doc2_terms else 0)
        idf[term] = math.log(3 / (doc_count + 1)) + 1  # Smoothed IDF
    return idf


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Compute cosine similarity between two vectors"""
    if not vec1 or not vec2:
        return 0.0
    
    common = set(vec1.keys()) & set(vec2.keys())
    if not common:
        return 0.0
    
    dot = sum(vec1[k] * vec2[k] for k in common)
    mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


# ============ MAIN SCORING FUNCTION ============

def calculate_ats_jd_score(resume_text: str, job_description: str, use_llm: bool = True) -> ATSJDResult:
    """
    Calculate ATS score using hybrid approach: LLM keyword classification + TF-IDF + SBERT.
    
    Production-grade scoring that combines:
    - LLM-based keyword classification (60% weight)
    - TF-IDF cosine similarity (25% weight)
    - SBERT semantic similarity (15% weight)
    
    Args:
        resume_text: Resume content (LaTeX or plain text)
        job_description: The job description to match against
        use_llm: Whether to use LLM for keyword classification (default: True)
        
    Returns:
        ATSJDResult with score 0-100 and matched/missing keywords
    """
    # Extract terms for TF-IDF
    resume_terms_list = _extract_terms(resume_text)
    jd_terms_list = _extract_terms(job_description)
    resume_terms_set = set(resume_terms_list)
    
    # Phase 1: JD keyword classification (LLM)
    if use_llm:
        jd_keywords = classify_jd_keywords_llm(job_description, use_cache=True)
        keyword_score = keyword_match_score(resume_terms_set, jd_keywords)
        
        # Get matched and missing keywords for display
        resume_lower = {t.lower() for t in resume_terms_set}
        matched = []
        missing = []
        
        for skill in jd_keywords.must_have:
            skill_lower = skill.lower()
            if skill_lower in resume_lower or any(skill_lower in term for term in resume_lower):
                matched.append(skill)
            else:
                missing.append(skill)
        
        # Limit display keywords
        matched = matched[:15]
        missing = missing[:10]
    else:
        # Fallback: simple keyword matching without LLM
        jd_keywords_set = {t for t in set(jd_terms_list) if t not in STOP_WORDS and len(t) > 2}
        matched = sorted(jd_keywords_set & resume_terms_set, key=len, reverse=True)[:15]
        missing = sorted(jd_keywords_set - resume_terms_set, key=len, reverse=True)[:10]
        keyword_score = len(matched) / len(jd_keywords_set) if jd_keywords_set else 0.0
    
    # Phase 2: TF-IDF similarity
    idf = _compute_idf(resume_terms_list, jd_terms_list)
    resume_tf = _compute_tf(resume_terms_list)
    jd_tf = _compute_tf(jd_terms_list)
    
    resume_tfidf = {t: resume_tf.get(t, 0) * idf.get(t, 1) for t in resume_terms_set}
    jd_tfidf = {t: jd_tf.get(t, 0) * idf.get(t, 1) for t in set(jd_terms_list)}
    
    tfidf_score = _cosine_similarity(resume_tfidf, jd_tfidf)
    
    # Phase 3: SBERT semantic similarity
    semantic_score = sbert_similarity(resume_text, job_description)
    
    # Final blended score (weighted combination)
    final_score = (
        0.6 * keyword_score +
        0.25 * tfidf_score +
        0.15 * semantic_score
    ) * 100
    
    score = int(min(100, max(0, final_score)))
    
    # Determine rating
    if score >= 80:
        rating = "Excellent"
        summary_base = "Strong match! Your resume aligns well with this job."
    elif score >= 60:
        rating = "Good"
        summary_base = "Good match. Adding missing keywords could improve your score."
    elif score >= 40:
        rating = "Fair"
        summary_base = "Partial match. Consider tailoring your resume more to this role."
    else:
        rating = "Needs Work"
        summary_base = "Low match. Your resume may not pass ATS for this job."
    
    # Enhanced summary with breakdown
    if use_llm:
        summary = f"{summary_base} Keyword match: {int(keyword_score*100)}%, Semantic: {int(semantic_score*100)}%, TF-IDF: {int(tfidf_score*100)}%"
    else:
        summary = summary_base
    
    return ATSJDResult(
        score=score,
        rating=rating,
        matched_keywords=matched,
        missing_keywords=missing,
        summary=summary
    )

