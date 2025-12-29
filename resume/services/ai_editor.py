# resume/services/ai_editor.py
"""
AI-powered LaTeX Section Editor
Uses OpenAI to modify specific sections based on user instructions
"""

from __future__ import annotations
import os
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class EditResult:
    """Result of an AI edit operation"""
    success: bool
    new_content: str = ""
    explanation: str = ""
    error: Optional[str] = None


# Initialize OpenAI client
def _get_client() -> Optional[Any]:
    """Get OpenAI client if available"""
    if not OPENAI_AVAILABLE:
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    return OpenAI(api_key=api_key)


def _get_model() -> str:
    """Get the model to use"""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# System prompts
SECTION_EDIT_SYSTEM_PROMPT = """You are an expert LaTeX resume editor. Your job is to modify resume sections based on user instructions.

RULES:
1. ONLY modify the section content provided - do not add new sections
2. Keep the LaTeX syntax valid and properly formatted
3. Maintain consistent style with the original content
4. Use professional, action-oriented language for resume bullets
5. Include metrics and quantifiable achievements where appropriate
6. Return ONLY the modified LaTeX code, no explanations

FORMATTING GUIDELINES:
- Use \\textbf{} for bold text (job titles, company names)
- Use \\textit{} for italic text (dates)
- Use \\begin{itemize} ... \\end{itemize} for bullet lists
- Use \\item for each bullet point
- Escape special characters: % → \\%, $ → \\$, & → \\&
- Keep section headers as \\section*{Name}

When improving bullet points:
- Start with strong action verbs
- Include specific metrics (numbers, percentages, dollar amounts)
- Show impact and results
- Keep bullets concise (1-2 lines each)"""


FULL_RESUME_SYSTEM_PROMPT = """You are an expert LaTeX resume editor. Your job is to help users improve their entire resume based on their instructions.

RULES:
1. Make targeted changes based on user requests
2. Keep the LaTeX syntax valid and properly formatted  
3. Maintain the overall structure and style
4. Return the COMPLETE updated LaTeX document
5. Preserve all preamble, packages, and document structure

FORMATTING GUIDELINES:
- Use \\textbf{} for bold, \\textit{} for italic
- Use \\begin{itemize} for bullet lists
- Escape special characters: % → \\%, $ → \\$, & → \\&
- Keep proper LaTeX document structure"""


def edit_section(
    section_name: str,
    section_content: str,
    user_instruction: str,
    chat_history: Optional[List[Dict]] = None,
    job_description: Optional[str] = None
) -> EditResult:
    """
    Edit a specific section based on user instructions.
    
    Args:
        section_name: Name of the section being edited
        section_content: Current LaTeX content of the section
        user_instruction: What the user wants to change
        chat_history: Optional previous chat messages for context
        job_description: Optional job description for tailoring content
        
    Returns:
        EditResult with the modified content
    """
    client = _get_client()
    
    if not client:
        return EditResult(
            success=False,
            error="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )
    
    # Build system prompt with optional JD context
    system_prompt = SECTION_EDIT_SYSTEM_PROMPT
    if job_description and job_description.strip():
        system_prompt += f"""

TARGET JOB DESCRIPTION:
{job_description}

IMPORTANT: Tailor the resume content to match this job description. Emphasize relevant skills, experiences, and keywords that align with the job requirements."""
    
    # Build messages
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add chat history for context (last 15 messages for better memory)
    if chat_history:
        for msg in chat_history[-15:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current request
    user_message = f"""SECTION: {section_name}

CURRENT CONTENT:
```latex
{section_content}
```

USER REQUEST: {user_instruction}

Please modify the section according to the user's request. Return ONLY the modified LaTeX code."""

    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=_get_model(),
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        new_content = response.choices[0].message.content.strip()
        
        # Clean up the response - remove markdown code blocks if present
        new_content = _clean_latex_response(new_content)
        
        return EditResult(
            success=True,
            new_content=new_content,
            explanation=f"Modified {section_name} section based on your request."
        )
        
    except Exception as e:
        return EditResult(
            success=False,
            error=f"AI editing failed: {str(e)}"
        )


def edit_full_resume(
    full_latex: str,
    user_instruction: str,
    chat_history: Optional[List[Dict]] = None,
    job_description: Optional[str] = None
) -> EditResult:
    """
    Edit the entire resume based on user instructions.
    
    Args:
        full_latex: Complete LaTeX source
        user_instruction: What the user wants to change
        chat_history: Optional previous chat messages for context
        job_description: Optional job description for tailoring content
        
    Returns:
        EditResult with the modified LaTeX
    """
    client = _get_client()
    
    if not client:
        return EditResult(
            success=False,
            error="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )
    
    # Build system prompt with optional JD context
    system_prompt = FULL_RESUME_SYSTEM_PROMPT
    if job_description and job_description.strip():
        system_prompt += f"""

TARGET JOB DESCRIPTION:
{job_description}

IMPORTANT: Tailor the resume content to match this job description. Emphasize relevant skills, experiences, and keywords that align with the job requirements."""
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add chat history (last 15 messages for better memory)
    if chat_history:
        for msg in chat_history[-15:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    user_message = f"""CURRENT RESUME:
```latex
{full_latex}
```

USER REQUEST: {user_instruction}

Please modify the resume according to the user's request. Return the COMPLETE updated LaTeX document."""

    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=_get_model(),
            messages=messages,
            temperature=0.3,
            max_tokens=4000
        )
        
        new_content = response.choices[0].message.content.strip()
        new_content = _clean_latex_response(new_content)
        
        return EditResult(
            success=True,
            new_content=new_content,
            explanation="Modified resume based on your request."
        )
        
    except Exception as e:
        return EditResult(
            success=False,
            error=f"AI editing failed: {str(e)}"
        )


def suggest_improvements(
    section_name: str,
    section_content: str
) -> EditResult:
    """
    Get AI suggestions for improving a section.
    
    Args:
        section_name: Name of the section
        section_content: Current content
        
    Returns:
        EditResult with suggestions (not applied changes)
    """
    client = _get_client()
    
    if not client:
        return EditResult(
            success=False,
            error="OpenAI API key not configured."
        )
    
    messages = [
        {"role": "system", "content": "You are a resume expert. Analyze the section and provide specific, actionable suggestions for improvement. Be concise and practical."},
        {"role": "user", "content": f"""Analyze this {section_name} section and suggest improvements:

```latex
{section_content}
```

Provide 3-5 specific suggestions for making this section more impactful."""}
    ]
    
    try:
        response = client.chat.completions.create(
            model=_get_model(),
            messages=messages,
            temperature=0.5,
            max_tokens=500
        )
        
        suggestions = response.choices[0].message.content.strip()
        
        return EditResult(
            success=True,
            new_content=suggestions,
            explanation=f"Suggestions for {section_name}"
        )
        
    except Exception as e:
        return EditResult(
            success=False,
            error=f"Failed to get suggestions: {str(e)}"
        )


def _clean_latex_response(response: str) -> str:
    """
    Clean up AI response to extract pure LaTeX.
    Removes markdown code blocks and extra whitespace.
    """
    # Remove ```latex ... ``` blocks
    response = re.sub(r'^```latex\s*\n?', '', response)
    response = re.sub(r'^```tex\s*\n?', '', response)
    response = re.sub(r'^```\s*\n?', '', response)
    response = re.sub(r'\n?```$', '', response)
    
    # Remove any leading/trailing whitespace
    response = response.strip()
    
    return response


def is_api_configured() -> bool:
    """Check if OpenAI API is properly configured"""
    return OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY"))

