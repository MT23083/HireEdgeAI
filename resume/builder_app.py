# resume/builder_app.py
"""
Real-time LaTeX Resume Builder with Live PDF Preview
Main Streamlit application with section-based AI editing
"""

from __future__ import annotations
import base64
from pathlib import Path
import sys

# Add parent directory to path for imports
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

# Import services
from resume.services.latex_compiler import compile_latex_to_pdf, check_pdflatex_installed
from resume.services.session_manager import (
    init_session_state, get_current_latex, update_latex,
    undo, redo, can_undo, can_redo,
    get_compiled_pdf, set_compiled_pdf, set_compile_error, get_compile_error,
    needs_recompile, get_version_info,
    set_selected_section, get_selected_section, clear_selected_section,
    add_chat_message, get_chat_messages, clear_chat_messages, get_recent_chat_context
)
from resume.services.latex_parser import parse_latex_sections, replace_section_content
from resume.services.ai_editor import edit_section, edit_full_resume, is_api_configured
from resume.utils.file_handlers import create_download_buttons, extract_name_from_latex


# ============ CONFIGURATION ============
TEMPLATES_DIR = APP_DIR / "templates"
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


def display_pdf_preview(pdf_bytes: bytes) -> None:
    """Display PDF in an iframe"""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'''
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" 
            height="600px" 
            type="application/pdf"
            style="border: 1px solid #ddd; border-radius: 4px;">
        </iframe>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)


def display_error_preview(error_message: str) -> None:
    """Display compilation error in preview area"""
    st.error("⚠️ LaTeX Compilation Error")
    st.code(error_message, language="text")
    st.info("💡 **Tip:** Check for missing braces, undefined commands, or special characters that need escaping (like % → \\%)")


def compile_and_update() -> None:
    """Compile current LaTeX and update session state"""
    latex_source = get_current_latex()
    
    if not latex_source.strip():
        set_compile_error("LaTeX source is empty")
        return
    
    result = compile_latex_to_pdf(latex_source)
    
    if result.success and result.pdf_bytes:
        set_compiled_pdf(result.pdf_bytes, result.compile_time_ms)
    else:
        set_compile_error(result.error_message or "Unknown compilation error")


def render_section_selector():
    """Render the section selector in sidebar"""
    st.sidebar.markdown("## 📑 Sections")
    st.sidebar.caption("Click a section to edit with AI")
    
    latex_source = get_current_latex()
    sections = parse_latex_sections(latex_source)
    
    if not sections:
        st.sidebar.info("No sections found in document")
        return
    
    selected_name, _ = get_selected_section()
    
    # Add "Full Resume" option
    if st.sidebar.button(
        "📄 Full Resume",
        use_container_width=True,
        type="primary" if selected_name == "__full__" else "secondary"
    ):
        set_selected_section("__full__", latex_source)
        st.rerun()
    
    st.sidebar.divider()
    
    # Section buttons
    for section in sections:
        icon = "📝" if section.section_type == "header" else "📌"
        is_selected = selected_name == section.name
        
        if st.sidebar.button(
            f"{icon} {section.name}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
            key=f"section_{section.name}"
        ):
            set_selected_section(section.name, section.content)
            st.rerun()
    
    # Clear selection button
    if selected_name:
        st.sidebar.divider()
        if st.sidebar.button("❌ Clear Selection", use_container_width=True):
            clear_selected_section()
            st.rerun()


def render_chat_interface():
    """Render the AI chat interface"""
    selected_name, selected_content = get_selected_section()
    
    st.markdown("### 💬 AI Editor")
    
    # Show API status
    if not is_api_configured():
        st.warning("⚠️ OpenAI API key not configured. Set `OPENAI_API_KEY` in your environment.")
        return
    
    # Show selected section context
    if selected_name:
        if selected_name == "__full__":
            st.info("🎯 **Context:** Editing full resume")
        else:
            st.info(f"🎯 **Context:** Editing **{selected_name}** section")
            with st.expander("View selected content", expanded=False):
                st.code(selected_content, language="latex")
    else:
        st.caption("💡 Select a section from the sidebar to focus your edits, or ask about the full resume.")
    
    # Chat history display
    messages = get_chat_messages()
    chat_container = st.container(height=300)
    
    with chat_container:
        if not messages:
            st.markdown("*Start a conversation by typing below...*")
        else:
            for msg in messages:
                if msg["role"] == "user":
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**🤖 AI:** {msg['content']}")
    
    # Chat input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="e.g., 'Add more metrics to the bullets' or 'Make this more professional'",
            key="chat_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_clicked = st.button("Send 📤", use_container_width=True, type="primary")
    
    # Process user input
    if send_clicked and user_input.strip():
        process_chat_input(user_input.strip(), selected_name, selected_content)
    
    # Clear chat button
    if messages:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            clear_chat_messages()
            st.rerun()


def process_chat_input(user_input: str, selected_name: str, selected_content: str):
    """Process user chat input and apply AI edits"""
    
    # Add user message to history
    add_chat_message("user", user_input, selected_name)
    
    with st.spinner("🤖 AI is thinking..."):
        if selected_name == "__full__":
            # Edit full resume
            result = edit_full_resume(
                full_latex=get_current_latex(),
                user_instruction=user_input,
                chat_history=get_recent_chat_context()
            )
            
            if result.success:
                update_latex(result.new_content, save_version=True, description=f"AI: {user_input[:50]}")
                add_chat_message("assistant", f"✅ Done! {result.explanation}")
            else:
                add_chat_message("assistant", f"❌ Error: {result.error}")
                
        elif selected_name and selected_content:
            # Edit specific section
            result = edit_section(
                section_name=selected_name,
                section_content=selected_content,
                user_instruction=user_input,
                chat_history=get_recent_chat_context()
            )
            
            if result.success:
                # Get the section object to replace
                sections = parse_latex_sections(get_current_latex())
                target_section = None
                for s in sections:
                    if s.name == selected_name:
                        target_section = s
                        break
                
                if target_section:
                    new_latex = replace_section_content(
                        get_current_latex(),
                        target_section,
                        result.new_content
                    )
                    update_latex(new_latex, save_version=True, description=f"AI edit: {selected_name}")
                    
                    # Update selected section content
                    set_selected_section(selected_name, result.new_content)
                    
                add_chat_message("assistant", f"✅ Updated **{selected_name}** section!")
            else:
                add_chat_message("assistant", f"❌ Error: {result.error}")
        else:
            # No section selected - edit full resume
            result = edit_full_resume(
                full_latex=get_current_latex(),
                user_instruction=user_input,
                chat_history=get_recent_chat_context()
            )
            
            if result.success:
                update_latex(result.new_content, save_version=True, description=f"AI: {user_input[:50]}")
                add_chat_message("assistant", f"✅ Done! {result.explanation}")
            else:
                add_chat_message("assistant", f"❌ Error: {result.error}")
    
    st.rerun()


def main():
    """Main entry point for the Resume Builder app"""
    
    # ============ PAGE CONFIG ============
    st.set_page_config(
        page_title="Resume Builder | HireEdgeAI",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # ============ CHECK PDFLATEX ============
    is_installed, install_msg = check_pdflatex_installed()
    
    if not is_installed:
        st.error("⚠️ pdflatex is not installed")
        st.markdown(install_msg)
        st.stop()
    
    # ============ INITIALIZE SESSION ============
    default_latex = load_default_template()
    init_session_state(default_latex)
    
    # ============ SIDEBAR: SECTION SELECTOR ============
    render_section_selector()
    
    # ============ HEADER ============
    st.markdown("""
        <h1 style='text-align: center; color: #1E88E5;'>
            📄 Resume Builder
        </h1>
        <p style='text-align: center; color: #666;'>
            Select a section → Ask AI to edit → See changes in real-time
        </p>
    """, unsafe_allow_html=True)
    
    # ============ TOOLBAR ============
    toolbar_cols = st.columns([1, 1, 1, 1, 2, 2])
    
    with toolbar_cols[0]:
        if st.button("↩️ Undo", disabled=not can_undo(), use_container_width=True):
            undo()
            st.rerun()
    
    with toolbar_cols[1]:
        if st.button("↪️ Redo", disabled=not can_redo(), use_container_width=True):
            redo()
            st.rerun()
    
    with toolbar_cols[2]:
        if st.button("🔄 Compile", type="primary", use_container_width=True):
            with st.spinner("Compiling..."):
                compile_and_update()
            st.rerun()
    
    with toolbar_cols[3]:
        if st.button("🔃 Reset", use_container_width=True):
            st.session_state.pop("resume_builder", None)
            st.rerun()
    
    with toolbar_cols[4]:
        current_ver, total_ver = get_version_info()
        st.caption(f"📝 Version {current_ver} of {total_ver}")
    
    with toolbar_cols[5]:
        error = get_compile_error()
        if error:
            st.caption("❌ Compilation failed")
        elif get_compiled_pdf():
            st.caption("✅ Compiled successfully")
        else:
            st.caption("⏳ Not compiled yet")
    
    st.divider()
    
    # ============ MAIN LAYOUT ============
    # Three columns: Editor | Preview | Chat
    left_col, middle_col, right_col = st.columns([2, 2, 1.5], gap="medium")
    
    # ---------- LEFT: LATEX EDITOR ----------
    with left_col:
        st.markdown("### 📝 LaTeX Editor")
        
        current_latex = get_current_latex()
        
        new_latex = st.text_area(
            label="LaTeX Source",
            value=current_latex,
            height=550,
            key="latex_editor",
            label_visibility="collapsed",
            help="Edit your LaTeX resume here. Click 'Compile' to see changes."
        )
        
        if new_latex != current_latex:
            update_latex(new_latex, save_version=True, description="Manual edit")
    
    # ---------- MIDDLE: PDF PREVIEW ----------
    with middle_col:
        st.markdown("### 👁️ PDF Preview")
        
        # Auto-compile if needed
        if needs_recompile() or get_compiled_pdf() is None:
            with st.spinner("Compiling LaTeX..."):
                compile_and_update()
        
        pdf_bytes = get_compiled_pdf()
        error = get_compile_error()
        
        if pdf_bytes:
            display_pdf_preview(pdf_bytes)
        elif error:
            display_error_preview(error)
        else:
            st.info("Click 'Compile' to generate PDF preview")
    
    # ---------- RIGHT: AI CHAT ----------
    with right_col:
        render_chat_interface()
    
    # ============ DOWNLOAD SECTION ============
    st.divider()
    st.markdown("### 📥 Download")
    
    user_name = extract_name_from_latex(get_current_latex())
    
    create_download_buttons(
        latex_source=get_current_latex(),
        pdf_bytes=get_compiled_pdf(),
        user_name=user_name,
        show_zip=True
    )
    
    # ============ FOOTER ============
    st.divider()
    st.caption(
        "💡 **Tips:** Select a section from the sidebar, then ask AI to improve it. "
        "Use `\\%` for percent signs, `\\$` for dollar signs in LaTeX."
    )


# Entry point
if __name__ == "__main__":
    main()
