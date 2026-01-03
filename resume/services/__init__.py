# resume/services/__init__.py
"""
Resume builder services
"""

from .latex_compiler import compile_latex_to_pdf, check_pdflatex_installed, CompilationResult
from .session_manager import SessionManager, session_manager, Session, VersionEntry
from .latex_parser import (
    parse_latex_sections, get_section_by_name, replace_section_content,
    get_section_names, LatexSection
)
from .ai_editor import (
    edit_section, edit_full_resume, suggest_improvements,
    is_api_configured, EditResult
)

__all__ = [
    # Compiler
    "compile_latex_to_pdf",
    "check_pdflatex_installed",
    "CompilationResult",
    # Session Manager (FastAPI implementation)
    "SessionManager",
    "session_manager",
    "Session",
    "VersionEntry",
    # LaTeX Parser
    "parse_latex_sections",
    "get_section_by_name",
    "replace_section_content",
    "get_section_names",
    "LatexSection",
    # AI Editor
    "edit_section",
    "edit_full_resume",
    "suggest_improvements",
    "is_api_configured",
    "EditResult",
]

