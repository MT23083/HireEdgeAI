"""
Section Management, AI Chat, and Job Description Routes
"""

from fastapi import APIRouter, HTTPException, Form
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from resume.services.latex_parser import parse_latex_sections, replace_section_content
from resume.services.ai_editor import edit_section, edit_full_resume
from resume.services.session_manager import session_manager
from .models import (
    SectionListResponse, SectionEditRequest, SectionEditResponse,
    ChatMessageRequest, ChatMessageResponse, JobDescriptionRequest
)

router = APIRouter()


# ============ Section Management ============

@router.get("/session/{session_id}/sections", response_model=SectionListResponse)
async def get_sections(session_id: str):
    """Get all sections from LaTeX"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sections = parse_latex_sections(session.current_latex)
    sections_data = [
        {
            "name": s.name,
            "type": s.section_type,
            "start_line": s.start_line,
            "end_line": s.end_line,
            "preview": s.preview,
            "content": s.content
        }
        for s in sections
    ]
    
    return SectionListResponse(sections=sections_data)


@router.post("/session/{session_id}/sections/select")
async def set_selected_section(
    session_id: str,
    section_name: str = Form(...),
    section_content: str = Form(...)
):
    """Set selected section for editing"""
    session_manager.set_selected_section(session_id, section_name, section_content)
    return {"success": True, "message": f"Section '{section_name}' selected"}


@router.get("/session/{session_id}/sections/selected")
async def get_selected_section(session_id: str):
    """Get currently selected section"""
    section_name, section_content = session_manager.get_selected_section(session_id)
    if section_name is None:
        return {"selected": False, "section_name": None, "section_content": None}
    return {
        "selected": True,
        "section_name": section_name,
        "section_content": section_content
    }


@router.delete("/session/{session_id}/sections/selected")
async def clear_selected_section(session_id: str):
    """Clear selected section"""
    session_manager.clear_selected_section(session_id)
    return {"success": True, "message": "Section selection cleared"}


@router.post("/session/{session_id}/sections/edit", response_model=SectionEditResponse)
async def edit_section_content(session_id: str, request: SectionEditRequest):
    """Edit a specific section using AI"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Find the section
    sections = parse_latex_sections(session.current_latex)
    target_section = None
    for s in sections:
        if s.name.lower() == request.section_name.lower():
            target_section = s
            break
    
    if not target_section:
        raise HTTPException(status_code=404, detail=f"Section '{request.section_name}' not found")
    
    # Get chat history using helper method
    chat_history = session_manager.get_recent_chat_context(session_id, limit=15)
    
    # Edit section
    result = edit_section(
        section_name=target_section.name,
        section_content=target_section.content,
        user_instruction=request.instruction,
        chat_history=chat_history,
        job_description=session.job_description
    )
    
    if not result.success:
        return SectionEditResponse(
            success=False,
            new_latex=session.current_latex,
            explanation="",
            error=result.error
        )
    
    # Replace section in LaTeX
    new_latex = replace_section_content(
        session.current_latex,
        target_section,
        result.new_content
    )
    
    # Update session
    session_manager.update_latex(
        session_id,
        new_latex,
        save_version=True,
        description=f"AI edit: {target_section.name}"
    )
    
    # Add to chat history
    session_manager.add_chat_message(session_id, "user", request.instruction, target_section.name)
    session_manager.add_chat_message(session_id, "assistant", result.explanation)
    
    return SectionEditResponse(
        success=True,
        new_latex=new_latex,
        explanation=result.explanation
    )


# ============ AI Chat ============

@router.post("/session/{session_id}/chat", response_model=ChatMessageResponse)
async def chat(session_id: str, request: ChatMessageRequest):
    """Chat with AI to edit resume"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message
    session_manager.add_chat_message(session_id, "user", request.message, request.section_name)
    
    # Get chat history using helper method
    chat_history = session_manager.get_recent_chat_context(session_id, limit=15)
    
    # Get selected section if any
    selected_name, selected_content = session_manager.get_selected_section(session_id)
    
    # Determine if editing section or full resume
    # Priority: request.section_name > selected section > full resume
    edit_section_name = request.section_name or selected_name
    edit_section_content = selected_content if edit_section_name == selected_name else None
    
    if edit_section_name and edit_section_name != "__full__":
        # Edit specific section
        if not edit_section_content:
            # Need to find section content
            sections = parse_latex_sections(session.current_latex)
            target_section = None
            for s in sections:
                if s.name.lower() == edit_section_name.lower():
                    target_section = s
                    edit_section_content = s.content
                    break
        else:
            target_section = None
            for s in parse_latex_sections(session.current_latex):
                if s.name.lower() == edit_section_name.lower():
                    target_section = s
                    break
        
        if target_section or edit_section_content:
            section_name_to_use = edit_section_name
            section_content_to_use = edit_section_content or (target_section.content if target_section else "")
            
            result = edit_section(
                section_name=section_name_to_use,
                section_content=section_content_to_use,
                user_instruction=request.message,
                chat_history=chat_history,
                job_description=session.job_description
            )
            
            if result.success:
                # Need to find section object for replacement
                if not target_section:
                    sections = parse_latex_sections(session.current_latex)
                    for s in sections:
                        if s.name.lower() == section_name_to_use.lower():
                            target_section = s
                            break
                
                if target_section:
                    new_latex = replace_section_content(
                        session.current_latex,
                        target_section,
                        result.new_content
                    )
                else:
                    # Fallback: just update LaTeX directly
                    new_latex = result.new_content
                
                session_manager.update_latex(
                    session_id,
                    new_latex,
                    save_version=True,
                    description=f"AI edit: {section_name_to_use}"
                )
                # Update selected section content
                session_manager.set_selected_section(session_id, section_name_to_use, result.new_content)
                session_manager.add_chat_message(session_id, "assistant", f"✅ Updated {section_name_to_use} section!")
                return ChatMessageResponse(
                    success=True,
                    new_latex=new_latex,
                    response=f"✅ Updated {section_name_to_use} section!"
                )
            else:
                session_manager.add_chat_message(session_id, "assistant", f"❌ Error: {result.error}")
                return ChatMessageResponse(
                    success=False,
                    new_latex=session.current_latex,
                    response=f"❌ Error: {result.error}",
                    error=result.error
                )
    
    # Edit full resume
    result = edit_full_resume(
        full_latex=session.current_latex,
        user_instruction=request.message,
        chat_history=chat_history,
        job_description=session.job_description
    )
    
    if result.success:
        session_manager.update_latex(
            session_id,
            result.new_content,
            save_version=True,
            description=f"AI: {request.message[:50]}"
        )
        session_manager.add_chat_message(session_id, "assistant", f"✅ Done! {result.explanation}")
        return ChatMessageResponse(
            success=True,
            new_latex=result.new_content,
            response=f"✅ Done! {result.explanation}"
        )
    else:
        session_manager.add_chat_message(session_id, "assistant", f"❌ Error: {result.error}")
        return ChatMessageResponse(
            success=False,
            new_latex=session.current_latex,
            response=f"❌ Error: {result.error}",
            error=result.error
        )


@router.get("/session/{session_id}/chat/history")
async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat message history"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"messages": session.chat_messages[-limit:]}


@router.get("/session/{session_id}/chat/context")
async def get_chat_context(session_id: str, limit: int = 15):
    """Get recent chat context for AI editing (formatted for AI)"""
    context = session_manager.get_recent_chat_context(session_id, limit)
    return {"context": context}


@router.delete("/session/{session_id}/chat/history")
async def clear_chat_history(session_id: str):
    """Clear chat history"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.chat_messages = []
    return {"success": True, "message": "Chat history cleared"}


# ============ Job Description ============

@router.put("/session/{session_id}/job-description")
async def set_job_description(session_id: str, request: JobDescriptionRequest):
    """Set job description for context"""
    session_manager.set_job_description(session_id, request.job_description)
    return {"success": True, "message": "Job description saved"}


@router.get("/session/{session_id}/job-description")
async def get_job_description(session_id: str):
    """Get job description"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"job_description": session.job_description}


@router.delete("/session/{session_id}/job-description")
async def clear_job_description(session_id: str):
    """Clear job description"""
    session_manager.set_job_description(session_id, "")
    return {"success": True, "message": "Job description cleared"}

