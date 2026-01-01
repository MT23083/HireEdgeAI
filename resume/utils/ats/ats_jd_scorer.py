# resume/utils/ats/ats_jd_scorer.py
"""
ATS Score WITH Job Description

Uses TF-IDF + Cosine Similarity to measure semantic match between resume and JD.
This is the most accurate score - requires a job description.
"""

from __future__ import annotations
import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from collections import Counter


@dataclass
class ATSJDResult:
    """Result of ATS scoring with job description"""
    score: int  # 0-100
    rating: str  # Excellent, Good, Fair, Needs Work
    matched_keywords: List[str]
    missing_keywords: List[str]
    summary: str


# ============ TEXT PROCESSING ============

def _clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+\*?\s*', ' ', text)
    text = re.sub(r'[{}\\]', ' ', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


def _extract_terms(text: str) -> List[str]:
    """Extract words and bigrams from text"""
    text = _clean_text(text)
    # Single words
    words = re.findall(r'[a-z][a-z0-9\-\.]+[a-z0-9]|[a-z]', text)
    # Bigrams for multi-word terms
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    return words + bigrams


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

def calculate_ats_jd_score(resume_text: str, job_description: str) -> ATSJDResult:
    """
    Calculate ATS score by comparing resume against job description.
    
    Uses TF-IDF weighted cosine similarity - the industry standard approach.
    
    Args:
        resume_text: Resume content (LaTeX or plain text)
        job_description: The job description to match against
        
    Returns:
        ATSJDResult with score 0-100 and matched/missing keywords
    """
    # Extract terms
    resume_terms = _extract_terms(resume_text)
    jd_terms = _extract_terms(job_description)
    
    # Filter JD terms to get keywords (remove stop words, short words)
    jd_keywords = {t for t in set(jd_terms) if t not in STOP_WORDS and len(t) > 2}
    resume_set = set(resume_terms)
    
    # Find matched and missing keywords
    matched = sorted(jd_keywords & resume_set, key=len, reverse=True)[:15]
    missing = sorted(jd_keywords - resume_set, key=len, reverse=True)[:10]
    
    # Compute TF-IDF vectors
    idf = _compute_idf(resume_terms, jd_terms)
    
    resume_tf = _compute_tf(resume_terms)
    jd_tf = _compute_tf(jd_terms)
    
    resume_tfidf = {t: resume_tf.get(t, 0) * idf.get(t, 1) for t in resume_set}
    jd_tfidf = {t: jd_tf.get(t, 0) * idf.get(t, 1) for t in set(jd_terms)}
    
    # Calculate similarity
    similarity = _cosine_similarity(resume_tfidf, jd_tfidf)
    
    # Also factor in keyword match ratio
    if jd_keywords:
        keyword_ratio = len(matched) / len(jd_keywords)
    else:
        keyword_ratio = 1.0
    
    # Combined score (70% similarity, 30% keyword ratio)
    raw_score = (similarity * 0.7 + keyword_ratio * 0.3) * 100
    score = min(100, max(0, int(raw_score * 1.3)))  # Scale up slightly
    
    # Determine rating
    if score >= 80:
        rating = "Excellent"
        summary = "Strong match! Your resume aligns well with this job."
    elif score >= 60:
        rating = "Good"
        summary = "Good match. Adding missing keywords could improve your score."
    elif score >= 40:
        rating = "Fair"
        summary = "Partial match. Consider tailoring your resume more to this role."
    else:
        rating = "Needs Work"
        summary = "Low match. Your resume may not pass ATS for this job."
    
    return ATSJDResult(
        score=score,
        rating=rating,
        matched_keywords=matched,
        missing_keywords=missing,
        summary=summary
    )

