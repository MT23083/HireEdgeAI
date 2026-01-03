"""
Document Upload, Downloads, ATS Scoring, and Utilities Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from typing import Optional
import sys
from pathlib import Path
import io
import zipfile

# Add parent directory to path for imports
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from resume.services.document_converter import convert_document
from resume.services.latex_compiler import check_pdflatex_installed
from resume.services.ai_editor import is_api_configured
from resume.services.session_manager import session_manager
from resume.utils.ats import (
    calculate_ats_universal_score, calculate_hbps_score, calculate_ats_jd_score
)
from resume.utils.file_handlers import extract_name_from_latex, sanitize_filename
from .models import ScoreRequest, ScoreResponse

router = APIRouter()


# ============ Document Upload/Conversion ============

@router.post("/session/{session_id}/upload")
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """Upload and convert document (PDF/DOCX/TEX) to LaTeX"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Read file content
    file_content = await file.read()
    
    # Convert
    result = convert_document(file_content, file.filename)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)
    
    # Update session
    session_manager.update_latex(
        session_id,
        result.latex_content,
        save_version=True,
        description=f"Uploaded: {file.filename}"
    )
    
    return {
        "success": True,
        "message": f"File '{file.filename}' converted successfully",
        "latex": result.latex_content,
        "warnings": result.warnings
    }


# ============ ATS Scoring ============

@router.post("/session/{session_id}/score", response_model=ScoreResponse)
async def calculate_scores(session_id: str, request: ScoreRequest = ScoreRequest()):
    """Calculate ATS and HBPS scores"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    latex_source = request.latex or session.current_latex
    job_description = request.job_description or session.job_description
    
    # Calculate scores
    ats_universal = calculate_ats_universal_score(latex_source)
    hbps = calculate_hbps_score(latex_source)
    ats_jd = None
    
    if job_description and job_description.strip():
        ats_jd = calculate_ats_jd_score(latex_source, job_description)
    
    # Convert to dict
    def to_dict(result):
        if result is None:
            return None
        return {
            "score": result.score,
            "rating": result.rating,
            "summary": result.summary,
            **{k: v for k, v in result.__dict__.items() if k not in ["score", "rating", "summary"]}
        }
    
    return ScoreResponse(
        ats_universal=to_dict(ats_universal),
        hbps=to_dict(hbps),
        ats_jd=to_dict(ats_jd)
    )


# ============ Downloads ============

@router.get("/session/{session_id}/download/tex")
async def download_tex(session_id: str):
    """Download LaTeX source file"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    user_name = extract_name_from_latex(session.current_latex)
    filename = f"{sanitize_filename(user_name)}_resume.tex"
    
    return Response(
        content=session.current_latex,
        media_type="text/x-tex",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/session/{session_id}/download/zip")
async def download_zip(session_id: str):
    """Download ZIP containing both TEX and PDF"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.compiled_pdf:
        raise HTTPException(status_code=400, detail="No compiled PDF available")
    
    user_name = extract_name_from_latex(session.current_latex)
    base_name = sanitize_filename(user_name)
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{base_name}_resume.tex", session.current_latex)
        zf.writestr(f"{base_name}_resume.pdf", session.compiled_pdf)
    
    zip_buffer.seek(0)
    filename = f"{base_name}_resume.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ============ Utility Endpoints ============

@router.get("/check-dependencies")
async def check_dependencies():
    """Check if required dependencies (pdflatex, etc.) are installed"""
    pdf_latex_ok, pdf_latex_msg = check_pdflatex_installed()
    ai_configured = is_api_configured()
    
    return {
        "pdflatex": {
            "installed": pdf_latex_ok,
            "message": pdf_latex_msg
        },
        "openai": {
            "configured": ai_configured
        }
    }

