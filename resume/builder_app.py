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
    add_chat_message, get_chat_messages, clear_chat_messages, get_recent_chat_context,
    set_job_description, get_job_description, clear_job_description, has_job_description
)
from resume.services.latex_parser import parse_latex_sections, replace_section_content
from resume.services.ai_editor import edit_section, edit_full_resume, is_api_configured
from resume.utils.file_handlers import create_download_buttons, extract_name_from_latex
from resume.services.document_converter import convert_document, get_supported_formats


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
    """Display PDF in an iframe with large responsive height"""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'''
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" 
            style="height: 85vh; min-height: 600px; border: 1px solid #ddd; border-radius: 0.5em; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
            type="application/pdf">
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


def get_section_buttons_data():
    """Get section data for rendering buttons dynamically"""
    latex_source = get_current_latex()
    sections = parse_latex_sections(latex_source)
    return sections


def render_section_buttons():
    """Render section buttons that add @section to query box"""
    sections = get_section_buttons_data()
    
    if not sections:
        return
    
    # Initialize query prefix in session state
    if "query_prefix" not in st.session_state:
        st.session_state.query_prefix = ""
    
    # Build section list
    all_items = [("Full Resume", get_current_latex())]
    for section in sections:
        all_items.append((section.name, section.content))
    
    # Show only first 4 sections in main row
    main_count = 4
    cols = st.columns(main_count)
    for i, (name, content) in enumerate(all_items[:main_count]):
        with cols[i]:
            short_name = name[:8] + ".." if len(name) > 8 else name
            if st.button(f"@{short_name}", key=f"sec_{i}", help=f"Edit {name}", use_container_width=True):
                st.session_state.query_prefix = f"@{name}: "
                set_selected_section(name if name != "Full Resume" else "__full__", content)
    
    # Put remaining sections in expander
    if len(all_items) > main_count:
        with st.expander(f"📑 More ({len(all_items) - main_count})"):
            cols2 = st.columns(3)
            for i, (name, content) in enumerate(all_items[main_count:]):
                with cols2[i % 3]:
                    if st.button(f"@{name}", key=f"sec_more_{i}", use_container_width=True):
                        st.session_state.query_prefix = f"@{name}: "
                        set_selected_section(name, content)


def render_chat_interface():
    """Render chat interface: History → Sections → Query box"""
    selected_name, selected_content = get_selected_section()
    
    # Initialize query prefix
    if "query_prefix" not in st.session_state:
        st.session_state.query_prefix = ""
    
    st.markdown("##### 💬 AI Editor")
    
    # 1. CHAT HISTORY FIRST - scrollable container
    messages = get_chat_messages()
    chat_container = st.container(height=250)
    with chat_container:
        if not messages:
            st.caption("Your conversation will appear here...")
        else:
            for msg in messages[-20:]:  # Show last 20 messages
                if msg["role"] == "user":
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**🤖:** {msg['content']}")
    
    st.markdown("---")
    
    # 2. JOB DESCRIPTION (collapsible)
    jd_set = has_job_description()
    jd_label = "📋 Job Description ✓" if jd_set else "📋 Add Job Description (optional)"
    with st.expander(jd_label, expanded=False):
        current_jd = get_job_description()
        jd_input = st.text_area(
            "Job Description",
            value=current_jd,
            height=80,
            max_chars=5000,  # ~1000 words
            placeholder="Paste job description here to tailor your resume...",
            label_visibility="collapsed"
        )
        # Word count and buttons in one row
        word_count = len(jd_input.split()) if jd_input.strip() else 0
        st.caption(f"{word_count}/1000 words")
        
        # Use single row with buttons side by side
        if st.button("💾 Save JD", key="save_jd"):
            if word_count <= 1000:
                set_job_description(jd_input)
                st.success("Saved!")
                st.rerun()
            else:
                st.error("Max 1000 words")
        if jd_set:
            if st.button("🗑️ Clear JD", key="clear_jd"):
                clear_job_description()
                st.rerun()
    
    # 3. SECTION BUTTONS
    st.caption("📑 Click section to edit:")
    render_section_buttons()
    
    # 3. QUERY INPUT BOX at bottom
    prefix = st.session_state.query_prefix
    default_value = prefix if prefix else ""
    
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input(
            "Query",
            value=default_value,
            placeholder="Type your request here...",
            key="main_query",
            label_visibility="collapsed"
        )
    with col2:
        send_clicked = st.button("📤", type="primary", use_container_width=True)
    
    # Clear prefix after showing
    if prefix:
        st.session_state.query_prefix = ""
    
    # Process input
    if send_clicked and user_input.strip():
        # Parse @section from input
        if user_input.startswith("@"):
            parts = user_input.split(":", 1)
            if len(parts) == 2:
                section_ref = parts[0][1:].strip()  # Remove @
                instruction = parts[1].strip()
                # Find section content
                if section_ref == "Full Resume":
                    set_selected_section("__full__", get_current_latex())
                else:
                    sections = parse_latex_sections(get_current_latex())
                    for s in sections:
                        if s.name.lower() == section_ref.lower():
                            set_selected_section(s.name, s.content)
                            break
                selected_name, selected_content = get_selected_section()
                process_chat_input(instruction, selected_name, selected_content)
            else:
                process_chat_input(user_input, selected_name, selected_content)
        else:
            process_chat_input(user_input, selected_name, selected_content)
    
    # API warning at bottom
    if not is_api_configured():
        st.caption("⚠️ Set OPENAI_API_KEY to enable AI")


def process_chat_input(user_input: str, selected_name: str, selected_content: str):
    """Process user chat input and apply AI edits"""
    
    # Add user message to history
    add_chat_message("user", user_input, selected_name)
    
    # Get job description for context (persistent, not affected by chat limit)
    jd = get_job_description()
    
    with st.spinner("🤖 AI is thinking..."):
        if selected_name == "__full__":
            # Edit full resume
            result = edit_full_resume(
                full_latex=get_current_latex(),
                user_instruction=user_input,
                chat_history=get_recent_chat_context(),
                job_description=jd
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
                chat_history=get_recent_chat_context(),
                job_description=jd
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
                chat_history=get_recent_chat_context(),
                job_description=jd
            )
            
            if result.success:
                update_latex(result.new_content, save_version=True, description=f"AI: {user_input[:50]}")
                add_chat_message("assistant", f"✅ Done! {result.explanation}")
            else:
                add_chat_message("assistant", f"❌ Error: {result.error}")
    
    st.rerun()


def render_sidebar():
    """Render compact sidebar with file upload and options"""
    with st.sidebar:
        st.markdown("#### 📁 Options")
        
        # Compact file upload - supports TEX, PDF, DOCX
        uploaded_file = st.file_uploader(
            "Upload Resume",
            type=["tex", "pdf", "docx"],
            key="resume_upload",
            label_visibility="collapsed",
            help="Upload .tex, .pdf, or .docx files"
        )
        
        if uploaded_file is not None:
            file_content = uploaded_file.read()
            filename = uploaded_file.name
            
            # Convert to LaTeX using document_converter
            with st.spinner(f"Converting {filename}..."):
                result = convert_document(file_content, filename)
            
            if result.success:
                update_latex(result.latex_content, save_version=True, description=f"Uploaded: {filename}")
                st.success(f"✅ {filename}")
                
                # Show warnings if any
                if result.warnings:
                    for warning in result.warnings:
                        st.warning(f"⚠️ {warning}")
                
                st.rerun()
            else:
                st.error(f"❌ Conversion failed: {result.error_message}")
        
        # New resume button
        if st.button("🆕 New", use_container_width=True):
            st.session_state.pop("resume_builder", None)
            st.rerun()
        
        st.divider()
        
        # Compact undo/redo
        col1, col2 = st.columns(2)
        with col1:
            if st.button("↩️", disabled=not can_undo(), use_container_width=True, help="Undo"):
                undo()
                st.rerun()
        with col2:
            if st.button("↪️", disabled=not can_redo(), use_container_width=True, help="Redo"):
                redo()
                st.rerun()
        
        current_ver, total_ver = get_version_info()
        st.caption(f"v{current_ver}/{total_ver}")
        
        st.divider()
        
        # Compact download buttons
        user_name = extract_name_from_latex(get_current_latex())
        pdf_bytes = get_compiled_pdf()
        
        if pdf_bytes:
            st.download_button(
                label="⬇️ PDF",
                data=pdf_bytes,
                file_name=f"{user_name.replace(' ', '_')}_resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        st.download_button(
            label="⬇️ LaTeX",
            data=get_current_latex(),
            file_name=f"{user_name.replace(' ', '_')}_resume.tex",
            mime="text/x-tex",
            use_container_width=True
        )


def main():
    """Main entry point for the Resume Builder app"""
    
    # ============ PAGE CONFIG ============
    st.set_page_config(
        page_title="Resume Builder | HireEdgeAI",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed"  # Hidden by default, hamburger menu to open
    )
    
    # ============ CUSTOM CSS - OVERLAY SIDEBAR ============
    st.markdown("""
        <style>
        /* ===== SIDEBAR AS OVERLAY (floats on top, solid background) ===== */
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100% !important;
            z-index: 999999 !important;
            min-width: 18% !important;
            max-width: 18% !important;
            background-color: #0e1117 !important;  /* Solid dark background */
            box-shadow: 4px 0 15px rgba(0,0,0,0.5) !important;
            transition: transform 0.3s ease-in-out !important;
        }
        
        /* Inner content also solid background */
        [data-testid="stSidebar"] > div {
            background-color: #0e1117 !important;
        }
        [data-testid="stSidebarContent"] {
            background-color: #0e1117 !important;
        }
        
        /* Hide sidebar when collapsed (slide out) */
        [data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(-100%) !important;
        }
        
        /* Compact sidebar content */
        [data-testid="stSidebar"] .block-container {
            padding: 3% !important;
        }
        [data-testid="stSidebar"] h4 {
            font-size: 0.9em !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
            font-size: 0.8em !important;
        }
        [data-testid="stSidebar"] button {
            font-size: 0.75em !important;
        }
        
        /* ===== REMOVE SIDEBAR RESERVED SPACE ===== */
        [data-testid="stSidebarCollapsedControl"] {
            position: fixed !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
            z-index: 1000000 !important;
        }
        
        /* ===== MAIN CONTENT - FULL WIDTH & CENTERED ===== */
        .main .block-container {
            max-width: 95% !important;
            width: 95% !important;
            padding-left: 2.5% !important;
            padding-right: 2.5% !important;
            margin: 0 auto !important;
        }
        
        /* Remove default left margin that accommodates sidebar */
        .main {
            width: 100% !important;
            margin-left: 0 !important;
            padding-left: 0 !important;
        }
        
        [data-testid="stAppViewContainer"] {
            width: 100% !important;
            margin-left: 0 !important;
        }
        
        [data-testid="stAppViewContainer"] > .main {
            margin-left: 0 !important;
        }
        
        /* Remove the sidebar width placeholder */
        [data-testid="stSidebarUserContent"] {
            width: 100% !important;
        }
        
        /* Header centering */
        .main h1 {
            text-align: center !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ============ CHECK PDFLATEX ============
    is_installed, install_msg = check_pdflatex_installed()
    
    if not is_installed:
        st.error("⚠️ pdflatex is not installed")
        st.markdown(install_msg)
        st.stop()
    
    # ============ INITIALIZE SESSION ============
    default_latex = load_default_template()
    init_session_state(default_latex)
    
    # ============ SIDEBAR ============
    render_sidebar()
    
    # ============ HEADER (compact, big font) ============
    st.markdown("""
        <style>
            .main > div:first-child { padding-top: 0 !important; }
            header { display: none !important; }
            .block-container { padding-top: 0.5rem !important; }
        </style>
        <h2 style='text-align: center; margin: 0; padding: 0.3rem 0; color: #1E88E5; font-size: 1.5rem;'>
            📄 Resume Builder
        </h2>
    """, unsafe_allow_html=True)
    
    
    # ============ MAIN LAYOUT: PDF (left) | Chat (right) ============
    left_col, right_col = st.columns([1.2, 1], gap="large")
    
    # ---------- LEFT: PDF PREVIEW ONLY ----------
    with left_col:
        st.markdown("### 👁️ Resume Preview")
        
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
            st.info("📄 Your resume preview will appear here")
    
    # ---------- RIGHT: AI CHAT WITH SECTION BUTTONS ----------
    with right_col:
        render_chat_interface()
    
    # ============ FOOTER ============
    st.divider()
    st.caption(
        "💡 **Tip:** Select a section, then ask AI to improve it. "
        "Changes are applied automatically to your resume."
    )


# Entry point
if __name__ == "__main__":
    main()
