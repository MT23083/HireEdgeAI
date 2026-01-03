"""
Resume Builder API Routes
Main router that combines all resume-related endpoints
"""

from fastapi import APIRouter
from .session_latex import router as session_latex_router
from .sections_ai import router as sections_ai_router
from .files_scoring import router as files_scoring_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(session_latex_router)
router.include_router(sections_ai_router)
router.include_router(files_scoring_router)

