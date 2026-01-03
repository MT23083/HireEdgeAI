"""
Session Management, LaTeX Management, and PDF Compilation Routes
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Optional
import sys
from pathlib import Path
import base64

# Add parent directory to path for imports
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from resume.services.latex_compiler import compile_latex_to_pdf
from resume.services.session_manager import session_manager
from resume.utils.file_handlers import extract_name_from_latex, sanitize_filename
from .models import (
    SessionCreateRequest, SessionCreateResponse, SessionStateResponse,
    LatexUpdateRequest, LatexUpdateResponse, CompileRequest, CompileResponse
)

router = APIRouter()

# Load default template
TEMPLATES_DIR = ROOT_DIR / "resume" / "templates"
DEFAULT_TEMPLATE = TEMPLATES_DIR / "modern_resume.tex"


def load_default_template() -> str:
    """Load the default LaTeX resume template"""
    if DEFAULT_TEMPLATE.exists():
        return DEFAULT_TEMPLATE.read_text(encoding="utf-8")
    # Fallback minimal template
    return r"""
\documentclass[11pt,a4paper]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{parskip}
\pagestyle{empty}

\begin{document}

\begin{center}
{\LARGE\textbf{Your Name}}\\[4pt]
email@example.com | +91-1234567890 | City, Country
\end{center}

\section*{Summary}
Write a brief professional summary here.

\section*{Experience}
\textbf{Job Title} \hfill \textit{Date Range}\\
\textit{Company Name}
\begin{itemize}
    \item Achievement or responsibility with metrics
    \item Another accomplishment
\end{itemize}

\section*{Education}
\textbf{Degree Name} \hfill \textit{Year}\\
\textit{University Name}

\section*{Skills}
Python, SQL, Data Analysis, Machine Learning

\end{document}
"""


# ============ Session Management ============

@router.post("/session/create", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest = SessionCreateRequest()):
    """Create a new resume builder session"""
    default_latex = request.default_latex or load_default_template()
    session_id = session_manager.create_session(default_latex)
    return SessionCreateResponse(
        session_id=session_id,
        message="Session created successfully"
    )


@router.get("/session/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """Get current session state"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionStateResponse(
        session_id=session.session_id,
        current_latex=session.current_latex,
        version_info={
            "current": session.current_version_index + 1,
            "total": len(session.version_history)
        },
        has_compiled_pdf=session.compiled_pdf_base64 is not None,
        last_compile_error=session.last_compile_error,
        selected_section=session.selected_section,
        chat_message_count=len(session.chat_messages),
        has_job_description=bool(session.job_description)
    )


# ============ LaTeX Management ============

@router.get("/session/{session_id}/latex")
async def get_latex(session_id: str):
    """Get current LaTeX source"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"latex": session.current_latex}


@router.put("/session/{session_id}/latex", response_model=LatexUpdateResponse)
async def update_latex(session_id: str, request: LatexUpdateRequest):
    """Update LaTeX source"""
    success = session_manager.update_latex(
        session_id, 
        request.latex, 
        request.save_version, 
        request.description
    )
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return LatexUpdateResponse(success=True, message="LaTeX updated")


@router.get("/session/{session_id}/undo/status")
async def can_undo(session_id: str):
    """Check if undo is available"""
    can_undo_flag = session_manager.can_undo(session_id)
    return {"can_undo": can_undo_flag}


@router.get("/session/{session_id}/redo/status")
async def can_redo(session_id: str):
    """Check if redo is available"""
    can_redo_flag = session_manager.can_redo(session_id)
    return {"can_redo": can_redo_flag}


@router.post("/session/{session_id}/undo")
async def undo(session_id: str):
    """Undo last change"""
    if not session_manager.can_undo(session_id):
        raise HTTPException(status_code=400, detail="Cannot undo - at oldest version")
    success = session_manager.undo(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot undo")
    session = session_manager.get_session(session_id)
    return {"success": True, "latex": session.current_latex}


@router.post("/session/{session_id}/redo")
async def redo(session_id: str):
    """Redo last undone change"""
    if not session_manager.can_redo(session_id):
        raise HTTPException(status_code=400, detail="Cannot redo - at newest version")
    success = session_manager.redo(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot redo")
    session = session_manager.get_session(session_id)
    return {"success": True, "latex": session.current_latex}


@router.get("/session/{session_id}/needs-recompile")
async def needs_recompile(session_id: str):
    """Check if LaTeX needs recompilation"""
    needs = session_manager.needs_recompile(session_id)
    return {"needs_recompile": needs}


# ============ PDF Compilation ============

@router.post("/session/{session_id}/compile", response_model=CompileResponse)
async def compile_pdf(session_id: str, request: CompileRequest = CompileRequest()):
    """Compile LaTeX to PDF"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    latex_source = request.latex or session.current_latex
    if not latex_source.strip():
        return CompileResponse(
            success=False,
            error="LaTeX source is empty",
            compile_time_ms=0
        )
    
    result = compile_latex_to_pdf(latex_source)
    
    if result.success and result.pdf_bytes:
        session_manager.set_compiled_pdf(session_id, result.pdf_bytes, result.compile_time_ms)
        pdf_base64 = base64.b64encode(result.pdf_bytes).decode('utf-8')
        return CompileResponse(
            success=True,
            pdf_base64=pdf_base64,
            compile_time_ms=result.compile_time_ms
        )
    else:
        session_manager.set_compile_error(session_id, result.error_message or "Unknown error")
        return CompileResponse(
            success=False,
            error=result.error_message or "Compilation failed",
            compile_time_ms=result.compile_time_ms
        )


@router.get("/session/{session_id}/pdf")
async def get_pdf(session_id: str):
    """Get compiled PDF as download"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.compiled_pdf:
        raise HTTPException(status_code=404, detail="No compiled PDF available")
    
    user_name = extract_name_from_latex(session.current_latex)
    filename = f"{sanitize_filename(user_name)}_resume.pdf"
    
    return Response(
        content=session.compiled_pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

