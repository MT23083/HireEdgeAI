# resume/services/session_manager.py
"""
Session State Manager for Resume Builder (FastAPI implementation)
Handles LaTeX source, version history, and editor state
"""

from __future__ import annotations
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import base64


@dataclass
class VersionEntry:
    """A single version in the history"""
    latex: str
    timestamp: datetime
    description: str = ""
    
    def to_dict(self):
        return {
            "latex": self.latex,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description
        }


@dataclass
class Session:
    """User session state"""
    session_id: str
    current_latex: str = ""
    version_history: List[VersionEntry] = field(default_factory=list)
    current_version_index: int = -1
    compiled_pdf: Optional[bytes] = None
    compiled_pdf_base64: Optional[str] = None  # For JSON responses
    last_compile_time_ms: int = 0
    last_compile_error: Optional[str] = None
    needs_recompile: bool = True
    selected_section: Optional[str] = None
    selected_section_content: Optional[str] = None
    chat_messages: List[Dict] = field(default_factory=list)
    job_description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "current_latex": self.current_latex,
            "version_history": [v.to_dict() for v in self.version_history],
            "current_version_index": self.current_version_index,
            "compiled_pdf_base64": self.compiled_pdf_base64,
            "last_compile_time_ms": self.last_compile_time_ms,
            "last_compile_error": self.last_compile_error,
            "needs_recompile": self.needs_recompile,
            "selected_section": self.selected_section,
            "selected_section_content": self.selected_section_content,
            "chat_messages": self.chat_messages,
            "job_description": self.job_description,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
        }


class SessionManager:
    """Manages user sessions for Resume Builder"""
    
    def __init__(self, expiry_hours: int = 24):
        self.sessions: Dict[str, Session] = {}
        self.expiry_hours = expiry_hours
    
    def create_session(self, default_latex: str = "") -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id, current_latex=default_latex)
        
        # Save initial version
        if default_latex:
            session.version_history.append(
                VersionEntry(latex=default_latex, timestamp=datetime.now(), description="Initial template")
            )
            session.current_version_index = 0
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID, return None if not found or expired"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Check expiry
        if datetime.now() - session.last_accessed > timedelta(hours=self.expiry_hours):
            del self.sessions[session_id]
            return None
        
        session.last_accessed = datetime.now()
        return session
    
    def init_session_state(self, session_id: str, default_latex: str = "") -> bool:
        """
        Initialize session state for the resume builder.
        Creates session if it doesn't exist.
        
        Returns:
            True if session was created/initialized, False on error
        """
        session = self.get_session(session_id)
        if session:
            return True  # Session already exists
        
        # Create new session
        new_session_id = self.create_session(default_latex)
        return new_session_id == session_id or False
    
    def get_current_latex(self, session_id: str) -> str:
        """Get the current LaTeX source"""
        session = self.get_session(session_id)
        if not session:
            return ""
        return session.current_latex
    
    def update_latex(
        self, 
        session_id: str,
        new_latex: str, 
        save_version: bool = True, 
        description: str = ""
    ) -> bool:
        """
        Update the current LaTeX source.
        
        Args:
            session_id: Session ID
            new_latex: The new LaTeX source code
            save_version: Whether to save this as a new version (for undo)
            description: Description of the change
            
        Returns:
            True if update was successful, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        old_latex = session.current_latex
        
        # Only update if changed
        if new_latex != old_latex:
            session.current_latex = new_latex
            session.needs_recompile = True
            
            if save_version:
                self._save_version(session, new_latex, description)
        
        return True
    
    def _save_version(self, session: Session, latex: str, description: str = "") -> None:
        """Save a version to history"""
        current_idx = session.current_version_index
        
        # Remove any versions after current (if we're in middle of undo chain)
        if current_idx >= 0 and current_idx < len(session.version_history) - 1:
            session.version_history = session.version_history[:current_idx + 1]
        
        # Add new version
        version = VersionEntry(
            latex=latex,
            timestamp=datetime.now(),
            description=description
        )
        session.version_history.append(version)
        session.current_version_index = len(session.version_history) - 1
        
        # Limit history size (keep last 50 versions)
        if len(session.version_history) > 50:
            session.version_history = session.version_history[-50:]
            session.current_version_index = len(session.version_history) - 1
    
    def undo(self, session_id: str) -> bool:
        """
        Undo to previous version.
        
        Returns:
            True if undo was successful, False if at oldest version or session not found
        """
        session = self.get_session(session_id)
        if not session or session.current_version_index <= 0:
            return False
        
        session.current_version_index -= 1
        version = session.version_history[session.current_version_index]
        session.current_latex = version.latex
        session.needs_recompile = True
        return True
    
    def redo(self, session_id: str) -> bool:
        """
        Redo to next version.
        
        Returns:
            True if redo was successful, False if at newest version or session not found
        """
        session = self.get_session(session_id)
        if not session or session.current_version_index >= len(session.version_history) - 1:
            return False
        
        session.current_version_index += 1
        version = session.version_history[session.current_version_index]
        session.current_latex = version.latex
        session.needs_recompile = True
        return True
    
    def can_undo(self, session_id: str) -> bool:
        """Check if undo is available"""
        session = self.get_session(session_id)
        if not session:
            return False
        return session.current_version_index > 0
    
    def can_redo(self, session_id: str) -> bool:
        """Check if redo is available"""
        session = self.get_session(session_id)
        if not session:
            return False
        return session.current_version_index < len(session.version_history) - 1
    
    def get_compiled_pdf(self, session_id: str) -> Optional[bytes]:
        """Get the last compiled PDF bytes"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.compiled_pdf
    
    def set_compiled_pdf(self, session_id: str, pdf_bytes: bytes, compile_time_ms: int):
        """Store compiled PDF"""
        session = self.get_session(session_id)
        if not session:
            return
        
        session.compiled_pdf = pdf_bytes
        session.compiled_pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        session.last_compile_time_ms = compile_time_ms
        session.last_compile_error = None
        session.needs_recompile = False
    
    def set_compile_error(self, session_id: str, error: str):
        """Store compilation error"""
        session = self.get_session(session_id)
        if not session:
            return
        
        session.last_compile_error = error
        session.compiled_pdf = None
        session.compiled_pdf_base64 = None
    
    def get_compile_error(self, session_id: str) -> Optional[str]:
        """Get the last compilation error"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.last_compile_error
    
    def needs_recompile(self, session_id: str) -> bool:
        """Check if recompile is needed"""
        session = self.get_session(session_id)
        if not session:
            return False
        return session.needs_recompile or session.compiled_pdf_base64 is None
    
    def get_version_info(self, session_id: str) -> tuple[int, int]:
        """
        Get version history info.
        
        Returns:
            (current_index, total_versions) - both 1-indexed for display
        """
        session = self.get_session(session_id)
        if not session:
            return (0, 0)
        return (
            session.current_version_index + 1,  # 1-indexed for display
            len(session.version_history)
        )
    
    # ============ Section Selection ============
    
    def set_selected_section(self, session_id: str, section_name: str, section_content: str):
        """Set selected section"""
        session = self.get_session(session_id)
        if not session:
            return
        session.selected_section = section_name
        session.selected_section_content = section_content
    
    def get_selected_section(self, session_id: str) -> tuple[Optional[str], Optional[str]]:
        """
        Get the currently selected section.
        
        Returns:
            (section_name, section_content) or (None, None) if no selection or session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None, None
        return (
            session.selected_section,
            session.selected_section_content
        )
    
    def clear_selected_section(self, session_id: str):
        """Clear selected section"""
        session = self.get_session(session_id)
        if not session:
            return
        session.selected_section = None
        session.selected_section_content = None
    
    # ============ Chat History ============
    
    def add_chat_message(self, session_id: str, role: str, content: str, section: Optional[str] = None):
        """Add chat message to history"""
        session = self.get_session(session_id)
        if not session:
            return
        
        session.chat_messages.append({
            "role": role,
            "content": content,
            "section": section,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limit chat history
        if len(session.chat_messages) > 100:
            session.chat_messages = session.chat_messages[-100:]
    
    def get_chat_messages(self, session_id: str) -> List[dict]:
        """Get all chat messages"""
        session = self.get_session(session_id)
        if not session:
            return []
        return session.chat_messages
    
    def clear_chat_messages(self, session_id: str):
        """Clear all chat messages"""
        session = self.get_session(session_id)
        if not session:
            return
        session.chat_messages = []
    
    def get_recent_chat_context(self, session_id: str, limit: int = 15) -> List[Dict]:
        """Get recent chat messages for context"""
        session = self.get_session(session_id)
        if not session:
            return []
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session.chat_messages[-limit:]
        ]
    
    # ============ Job Description (Persistent Context) ============
    
    def set_job_description(self, session_id: str, jd: str):
        """Set job description"""
        session = self.get_session(session_id)
        if not session:
            return
        session.job_description = jd
    
    def get_job_description(self, session_id: str) -> str:
        """
        Get the stored job description.
        
        Returns:
            Job description string, or empty string if not set or session not found
        """
        session = self.get_session(session_id)
        if not session:
            return ""
        return session.job_description
    
    def clear_job_description(self, session_id: str):
        """Clear job description"""
        session = self.get_session(session_id)
        if not session:
            return
        session.job_description = ""
    
    def has_job_description(self, session_id: str) -> bool:
        """Check if a job description is set"""
        return bool(self.get_job_description(session_id).strip())
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_accessed > timedelta(hours=self.expiry_hours)
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)


# Global session manager instance
session_manager = SessionManager()
