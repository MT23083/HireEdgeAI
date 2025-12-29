# resume/services/session_manager.py
"""
Session State Manager for Resume Builder
Handles LaTeX source, version history, and editor state
"""

from __future__ import annotations
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import streamlit as st


@dataclass
class VersionEntry:
    """A single version in the history"""
    latex: str
    timestamp: datetime
    description: str = ""


def init_session_state(default_latex: str = "") -> None:
    """
    Initialize session state for the resume builder.
    Call this at the start of the app.
    """
    if "resume_builder" not in st.session_state:
        st.session_state.resume_builder = {
            # Current LaTeX source
            "current_latex": default_latex,
            
            # Version history for undo/redo
            "version_history": [],
            "current_version_index": -1,
            
            # Last compiled PDF
            "compiled_pdf": None,
            "last_compile_time_ms": 0,
            "last_compile_error": None,
            
            # Editor settings
            "editor_theme": "monokai",
            "editor_font_size": 14,
            "auto_compile": True,
            
            # Compilation status
            "is_compiling": False,
            "needs_recompile": True,
            
            # Section selection
            "selected_section": None,
            "selected_section_content": None,
            
            # Chat messages
            "chat_messages": [],
            
            # Job Description (persistent context)
            "job_description": "",
        }
        
        # Save initial version
        if default_latex:
            _save_version(default_latex, "Initial template")
    
    # Ensure chat_messages exists (for backward compatibility)
    if "chat_messages" not in st.session_state.resume_builder:
        st.session_state.resume_builder["chat_messages"] = []
    
    # Ensure section selection exists
    if "selected_section" not in st.session_state.resume_builder:
        st.session_state.resume_builder["selected_section"] = None
        st.session_state.resume_builder["selected_section_content"] = None


def get_current_latex() -> str:
    """Get the current LaTeX source"""
    if "resume_builder" not in st.session_state:
        return ""
    return st.session_state.resume_builder.get("current_latex", "")


def update_latex(new_latex: str, save_version: bool = True, description: str = "") -> None:
    """
    Update the current LaTeX source.
    
    Args:
        new_latex: The new LaTeX source code
        save_version: Whether to save this as a new version (for undo)
        description: Description of the change
    """
    if "resume_builder" not in st.session_state:
        init_session_state(new_latex)
        return
    
    old_latex = st.session_state.resume_builder["current_latex"]
    
    # Only update if changed
    if new_latex != old_latex:
        st.session_state.resume_builder["current_latex"] = new_latex
        st.session_state.resume_builder["needs_recompile"] = True
        
        if save_version:
            _save_version(new_latex, description)


def _save_version(latex: str, description: str = "") -> None:
    """Save a version to history"""
    state = st.session_state.resume_builder
    current_idx = state["current_version_index"]
    
    # Remove any versions after current (if we're in middle of undo chain)
    if current_idx >= 0 and current_idx < len(state["version_history"]) - 1:
        state["version_history"] = state["version_history"][:current_idx + 1]
    
    # Add new version
    version = VersionEntry(
        latex=latex,
        timestamp=datetime.now(),
        description=description
    )
    state["version_history"].append(version)
    state["current_version_index"] = len(state["version_history"]) - 1
    
    # Limit history size (keep last 50 versions)
    if len(state["version_history"]) > 50:
        state["version_history"] = state["version_history"][-50:]
        state["current_version_index"] = len(state["version_history"]) - 1


def undo() -> bool:
    """
    Undo to previous version.
    
    Returns:
        True if undo was successful, False if at oldest version
    """
    if "resume_builder" not in st.session_state:
        return False
    
    state = st.session_state.resume_builder
    if state["current_version_index"] > 0:
        state["current_version_index"] -= 1
        version = state["version_history"][state["current_version_index"]]
        state["current_latex"] = version.latex
        state["needs_recompile"] = True
        return True
    return False


def redo() -> bool:
    """
    Redo to next version.
    
    Returns:
        True if redo was successful, False if at newest version
    """
    if "resume_builder" not in st.session_state:
        return False
    
    state = st.session_state.resume_builder
    if state["current_version_index"] < len(state["version_history"]) - 1:
        state["current_version_index"] += 1
        version = state["version_history"][state["current_version_index"]]
        state["current_latex"] = version.latex
        state["needs_recompile"] = True
        return True
    return False


def can_undo() -> bool:
    """Check if undo is available"""
    if "resume_builder" not in st.session_state:
        return False
    return st.session_state.resume_builder["current_version_index"] > 0


def can_redo() -> bool:
    """Check if redo is available"""
    if "resume_builder" not in st.session_state:
        return False
    state = st.session_state.resume_builder
    return state["current_version_index"] < len(state["version_history"]) - 1


def get_compiled_pdf() -> Optional[bytes]:
    """Get the last compiled PDF bytes"""
    if "resume_builder" not in st.session_state:
        return None
    return st.session_state.resume_builder.get("compiled_pdf")


def set_compiled_pdf(pdf_bytes: bytes, compile_time_ms: int = 0) -> None:
    """Store the compiled PDF"""
    if "resume_builder" not in st.session_state:
        return
    st.session_state.resume_builder["compiled_pdf"] = pdf_bytes
    st.session_state.resume_builder["last_compile_time_ms"] = compile_time_ms
    st.session_state.resume_builder["last_compile_error"] = None
    st.session_state.resume_builder["needs_recompile"] = False


def set_compile_error(error: str) -> None:
    """Store a compilation error"""
    if "resume_builder" not in st.session_state:
        return
    st.session_state.resume_builder["last_compile_error"] = error
    st.session_state.resume_builder["compiled_pdf"] = None


def get_compile_error() -> Optional[str]:
    """Get the last compilation error"""
    if "resume_builder" not in st.session_state:
        return None
    return st.session_state.resume_builder.get("last_compile_error")


def needs_recompile() -> bool:
    """Check if LaTeX source has changed since last compile"""
    if "resume_builder" not in st.session_state:
        return True
    return st.session_state.resume_builder.get("needs_recompile", True)


def get_version_info() -> tuple[int, int]:
    """
    Get version history info.
    
    Returns:
        (current_index, total_versions)
    """
    if "resume_builder" not in st.session_state:
        return (0, 0)
    state = st.session_state.resume_builder
    return (
        state["current_version_index"] + 1,  # 1-indexed for display
        len(state["version_history"])
    )


# ============ Section Selection ============

def set_selected_section(section_name: Optional[str], section_content: Optional[str] = None) -> None:
    """
    Set the currently selected section for AI editing.
    
    Args:
        section_name: Name of the section (e.g., "Experience")
        section_content: LaTeX content of the section
    """
    if "resume_builder" not in st.session_state:
        return
    st.session_state.resume_builder["selected_section"] = section_name
    st.session_state.resume_builder["selected_section_content"] = section_content


def get_selected_section() -> tuple[Optional[str], Optional[str]]:
    """
    Get the currently selected section.
    
    Returns:
        (section_name, section_content) or (None, None) if no selection
    """
    if "resume_builder" not in st.session_state:
        return None, None
    state = st.session_state.resume_builder
    return (
        state.get("selected_section"),
        state.get("selected_section_content")
    )


def clear_selected_section() -> None:
    """Clear the section selection"""
    set_selected_section(None, None)


# ============ Chat History ============

@dataclass
class ChatMessage:
    """A single chat message"""
    role: str  # "user" or "assistant"
    content: str
    section_context: Optional[str] = None  # Which section this was about


def add_chat_message(role: str, content: str, section_context: Optional[str] = None) -> None:
    """
    Add a message to chat history.
    
    Args:
        role: "user" or "assistant"
        content: The message content
        section_context: Optional section name this message relates to
    """
    if "resume_builder" not in st.session_state:
        return
    
    message = {
        "role": role,
        "content": content,
        "section_context": section_context
    }
    st.session_state.resume_builder["chat_messages"].append(message)
    
    # Limit chat history to last 50 messages
    if len(st.session_state.resume_builder["chat_messages"]) > 50:
        st.session_state.resume_builder["chat_messages"] = \
            st.session_state.resume_builder["chat_messages"][-50:]


def get_chat_messages() -> List[dict]:
    """Get all chat messages"""
    if "resume_builder" not in st.session_state:
        return []
    return st.session_state.resume_builder.get("chat_messages", [])


def clear_chat_messages() -> None:
    """Clear all chat messages"""
    if "resume_builder" not in st.session_state:
        return
    st.session_state.resume_builder["chat_messages"] = []


def get_recent_chat_context(n_messages: int = 10) -> List[dict]:
    """
    Get recent chat messages for AI context.
    
    Args:
        n_messages: Number of recent messages to return
        
    Returns:
        List of recent messages
    """
    messages = get_chat_messages()
    return messages[-n_messages:] if messages else []


# ============ Job Description (Persistent Context) ============

def set_job_description(jd: str) -> None:
    """
    Store job description in session.
    This persists across all messages and is not affected by chat history limits.
    
    Args:
        jd: The job description text
    """
    if "resume_builder" not in st.session_state:
        return
    st.session_state.resume_builder["job_description"] = jd


def get_job_description() -> str:
    """
    Get the stored job description.
    
    Returns:
        Job description string, or empty string if not set
    """
    if "resume_builder" not in st.session_state:
        return ""
    return st.session_state.resume_builder.get("job_description", "")


def clear_job_description() -> None:
    """Clear the stored job description"""
    if "resume_builder" not in st.session_state:
        return
    st.session_state.resume_builder["job_description"] = ""


def has_job_description() -> bool:
    """Check if a job description is set"""
    return bool(get_job_description().strip())

