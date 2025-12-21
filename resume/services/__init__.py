# resume/services/__init__.py
"""
Resume builder services
"""

from .latex_compiler import compile_latex_to_pdf, check_pdflatex_installed, CompilationResult
from .session_manager import (
    init_session_state, get_current_latex, update_latex,
    undo, redo, can_undo, can_redo,
    get_compiled_pdf, set_compiled_pdf, set_compile_error, get_compile_error,
    needs_recompile, get_version_info,
    # Section selection
    set_selected_section, get_selected_section, clear_selected_section,
    # Chat history
    add_chat_message, get_chat_messages, clear_chat_messages, get_recent_chat_context
)
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
    # Session Manager
    "init_session_state",
    "get_current_latex",
    "update_latex",
    "undo",
    "redo", 
    "can_undo",
    "can_redo",
    "get_compiled_pdf",
    "set_compiled_pdf",
    "set_compile_error",
    "get_compile_error",
    "needs_recompile",
    "get_version_info",
    # Section selection
    "set_selected_section",
    "get_selected_section", 
    "clear_selected_section",
    # Chat history
    "add_chat_message",
    "get_chat_messages",
    "clear_chat_messages",
    "get_recent_chat_context",
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

