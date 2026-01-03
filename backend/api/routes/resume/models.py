"""
Pydantic models for Resume Builder API
Request and Response models
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SessionCreateRequest(BaseModel):
    default_latex: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    message: str


class LatexUpdateRequest(BaseModel):
    latex: str
    save_version: bool = True
    description: str = ""


class LatexUpdateResponse(BaseModel):
    success: bool
    message: str


class CompileRequest(BaseModel):
    latex: Optional[str] = None  # If None, uses session's current_latex


class CompileResponse(BaseModel):
    success: bool
    pdf_base64: Optional[str] = None
    error: Optional[str] = None
    compile_time_ms: int = 0


class SectionListResponse(BaseModel):
    sections: List[Dict[str, Any]]


class SectionEditRequest(BaseModel):
    section_name: str
    instruction: str


class SectionEditResponse(BaseModel):
    success: bool
    new_latex: str
    explanation: str
    error: Optional[str] = None


class FullResumeEditRequest(BaseModel):
    instruction: str


class ChatMessageRequest(BaseModel):
    message: str
    section_name: Optional[str] = None  # If provided, edits that section


class ChatMessageResponse(BaseModel):
    success: bool
    new_latex: Optional[str] = None
    response: str
    error: Optional[str] = None


class JobDescriptionRequest(BaseModel):
    job_description: str


class ScoreRequest(BaseModel):
    latex: Optional[str] = None  # If None, uses session's current_latex
    job_description: Optional[str] = None  # For ATS JD score


class ScoreResponse(BaseModel):
    ats_universal: Optional[Dict] = None
    hbps: Optional[Dict] = None
    ats_jd: Optional[Dict] = None


class SessionStateResponse(BaseModel):
    session_id: str
    current_latex: str
    version_info: Dict[str, int]
    has_compiled_pdf: bool
    last_compile_error: Optional[str] = None
    selected_section: Optional[str] = None
    chat_message_count: int
    has_job_description: bool

