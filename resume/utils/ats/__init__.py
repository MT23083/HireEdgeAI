# resume/utils/ats/__init__.py
"""
Resume Scoring System

Three complementary scores:
1. ATS Score (with JD) - Semantic similarity matching
2. ATS Score (without JD) - Universal parsing criteria  
3. HBPS Score - Human Best Practice Score (10-second scan impact)
"""

from .ats_jd_scorer import calculate_ats_jd_score, ATSJDResult
from .ats_universal_scorer import calculate_ats_universal_score, ATSUniversalResult
from .hbps_scorer import calculate_hbps_score, HBPSResult

__all__ = [
    # ATS with Job Description
    "calculate_ats_jd_score",
    "ATSJDResult",
    # ATS Universal (without JD)
    "calculate_ats_universal_score", 
    "ATSUniversalResult",
    # Human Best Practice Score
    "calculate_hbps_score",
    "HBPSResult",
]

