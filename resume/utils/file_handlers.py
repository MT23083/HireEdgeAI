# resume/utils/file_handlers.py
"""
File handling utilities for Resume Builder
Download buttons, ZIP creation, file naming
"""

from __future__ import annotations
import io
import zipfile
from typing import Optional
import streamlit as st


def sanitize_filename(name: str) -> str:
    """
    Create a safe filename from a name string.
    
    Args:
        name: The name to sanitize (e.g., "Sarthak Sharma")
        
    Returns:
        Safe filename (e.g., "Sarthak_Sharma")
    """
    # Replace spaces with underscores
    safe = name.replace(" ", "_")
    # Remove any characters that aren't alphanumeric, underscore, or hyphen
    safe = "".join(c for c in safe if c.isalnum() or c in ("_", "-"))
    return safe or "resume"


def create_download_buttons(
    latex_source: str,
    pdf_bytes: Optional[bytes],
    user_name: str = "Resume",
    show_zip: bool = True
) -> None:
    """
    Create download buttons for TEX, PDF, and optionally ZIP.
    
    Args:
        latex_source: The LaTeX source code
        pdf_bytes: The compiled PDF bytes (None if compilation failed)
        user_name: Name to use in filename
        show_zip: Whether to show the ZIP download option
    """
    safe_name = sanitize_filename(user_name)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📥 Download .tex",
            data=latex_source,
            file_name=f"{safe_name}_resume.tex",
            mime="text/x-tex",
            use_container_width=True,
            help="Download the LaTeX source file"
        )
    
    with col2:
        if pdf_bytes:
            st.download_button(
                label="📥 Download .pdf",
                data=pdf_bytes,
                file_name=f"{safe_name}_resume.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Download the compiled PDF"
            )
        else:
            st.button(
                label="📥 Download .pdf",
                disabled=True,
                use_container_width=True,
                help="Fix LaTeX errors to enable PDF download"
            )
    
    with col3:
        if show_zip and pdf_bytes:
            zip_bytes = create_zip_download(latex_source, pdf_bytes, safe_name)
            st.download_button(
                label="📥 Download ZIP",
                data=zip_bytes,
                file_name=f"{safe_name}_resume.zip",
                mime="application/zip",
                use_container_width=True,
                help="Download both TEX and PDF in a ZIP file"
            )
        elif show_zip:
            st.button(
                label="📥 Download ZIP",
                disabled=True,
                use_container_width=True,
                help="Fix LaTeX errors to enable ZIP download"
            )


def create_zip_download(
    latex_source: str,
    pdf_bytes: bytes,
    base_name: str = "resume"
) -> bytes:
    """
    Create a ZIP file containing both TEX and PDF.
    
    Args:
        latex_source: The LaTeX source code
        pdf_bytes: The compiled PDF bytes
        base_name: Base name for files (without extension)
        
    Returns:
        ZIP file as bytes
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add LaTeX file
        zf.writestr(f"{base_name}_resume.tex", latex_source)
        # Add PDF file
        zf.writestr(f"{base_name}_resume.pdf", pdf_bytes)
    
    return zip_buffer.getvalue()


def extract_name_from_latex(latex_source: str) -> str:
    """
    Try to extract the user's name from LaTeX source.
    
    Looks for common patterns like:
    - \\textbf{\\Large NAME}
    - {\\Large NAME}
    - \\name{NAME}
    
    Args:
        latex_source: The LaTeX source code
        
    Returns:
        Extracted name or "Resume" if not found
    """
    import re
    
    patterns = [
        r'\\textbf\{\\Large\s+([^}]+)\}',  # \textbf{\Large Name}
        r'\\textbf\{\\huge\s+([^}]+)\}',   # \textbf{\huge Name}
        r'\{\\Large\s+([^}]+)\}',           # {\Large Name}
        r'\{\\huge\s+([^}]+)\}',            # {\huge Name}
        r'\\name\{([^}]+)\}',               # \name{Name}
        r'\\author\{([^}]+)\}',             # \author{Name}
    ]
    
    for pattern in patterns:
        match = re.search(pattern, latex_source)
        if match:
            name = match.group(1).strip()
            # Clean up any remaining LaTeX commands
            name = re.sub(r'\\[a-zA-Z]+', '', name)
            name = name.strip()
            if name and len(name) > 2:
                return name
    
    return "Resume"

