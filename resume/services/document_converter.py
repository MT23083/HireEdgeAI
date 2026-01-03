# resume/services/document_converter.py
"""
Document Converter Service
Converts PDF and DOCX files to LaTeX format for the Resume Builder.

Supported conversions:
- DOCX → LaTeX (via pypandoc/Pandoc)
- PDF → DOCX → LaTeX (via pdf2docx + pypandoc)
- TEX → TEX (passthrough, just decode bytes)
"""

from __future__ import annotations
import tempfile
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union
import io
from resume.services.ai_editor import is_api_configured


@dataclass
class ConversionResult:
    """Result of a document conversion operation"""
    success: bool
    latex_content: str = ""
    error_message: str = ""
    source_format: str = ""
    warnings: list[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def _check_pandoc_installed() -> tuple[bool, str]:
    """Check if Pandoc is installed on the system"""
    try:
        import pypandoc
        version = pypandoc.get_pandoc_version()
        return True, f"Pandoc {version} is installed"
    except OSError:
        return False, (
            "Pandoc is not installed. Install it with:\n"
            "  - Ubuntu/Debian: `sudo apt-get install pandoc`\n"
            "  - macOS: `brew install pandoc`\n"
            "  - Windows: Download from https://pandoc.org/installing.html"
        )
    except ImportError:
        return False, "pypandoc is not installed. Run: `pip install pypandoc`"


def _check_pdf2docx_installed() -> tuple[bool, str]:
    """Check if pdf2docx is installed"""
    try:
        from pdf2docx import Converter
        return True, "pdf2docx is installed"
    except ImportError:
        return False, "pdf2docx is not installed. Run: `pip install pdf2docx`"


def convert_docx_to_latex(
    file_content: bytes,
    filename: str = "document.docx"
) -> ConversionResult:
    """
    Convert DOCX file content to LaTeX using pypandoc.
    
    Args:
        file_content: Raw bytes of the DOCX file
        filename: Original filename for reference
        
    Returns:
        ConversionResult with LaTeX content or error
    """
    # Check dependencies
    is_installed, msg = _check_pandoc_installed()
    if not is_installed:
        return ConversionResult(
            success=False,
            error_message=msg,
            source_format="docx"
        )
    
    try:
        import pypandoc
        
        # Write to temporary file (pypandoc needs a file path)
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        try:
            # Convert DOCX to LaTeX
            latex_content = pypandoc.convert_file(
                tmp_path,
                'latex',
                format='docx',
                extra_args=[
                    '--standalone',  # Include preamble
                    '--wrap=none',   # Don't wrap lines
                ]
            )
            
            # Post-process the LaTeX
            latex_content = _postprocess_pandoc_latex(latex_content)
            
            # Clean up with LLM if available
            latex_content = _cleanup_latex_with_llm(latex_content)
            
            return ConversionResult(
                success=True,
                latex_content=latex_content,
                source_format="docx",
                warnings=_get_conversion_warnings(latex_content)
            )
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        return ConversionResult(
            success=False,
            error_message=f"DOCX conversion failed: {str(e)}",
            source_format="docx"
        )


def convert_pdf_to_latex(
    file_content: bytes,
    filename: str = "document.pdf"
) -> ConversionResult:
    """
    Convert PDF to LaTeX using a two-step pipeline: PDF → DOCX → LaTeX.
    
    Uses pdf2docx to convert PDF to DOCX (preserves layout/formatting),
    then pypandoc to convert DOCX to LaTeX (proper LaTeX structure).
    
    Args:
        file_content: Raw bytes of the PDF file
        filename: Original filename for reference
        
    Returns:
        ConversionResult with LaTeX content or error
    """
    # Check dependencies
    pdf2docx_ok, pdf2docx_msg = _check_pdf2docx_installed()
    if not pdf2docx_ok:
        return ConversionResult(
            success=False,
            error_message=pdf2docx_msg,
            source_format="pdf"
        )
    
    pandoc_ok, pandoc_msg = _check_pandoc_installed()
    if not pandoc_ok:
        return ConversionResult(
            success=False,
            error_message=pandoc_msg,
            source_format="pdf"
        )
    
    try:
        from pdf2docx import Converter
        import pypandoc
        
        # Create temp files for the conversion pipeline
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_tmp:
            pdf_tmp.write(file_content)
            pdf_path = pdf_tmp.name
        
        docx_path = pdf_path.replace('.pdf', '.docx')
        
        try:
            # Step 1: PDF → DOCX
            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()
            
            # Check if DOCX was created
            if not os.path.exists(docx_path):
                return ConversionResult(
                    success=False,
                    error_message="PDF to DOCX conversion failed - no output file created.",
                    source_format="pdf"
                )
            
            # Step 2: DOCX → LaTeX
            latex_content = pypandoc.convert_file(
                docx_path,
                'latex',
                format='docx',
                extra_args=['--standalone', '--wrap=none']
            )
            
            # Post-process the LaTeX
            latex_content = _postprocess_pandoc_latex(latex_content)
            
            # Clean up with LLM if available
            latex_content = _cleanup_latex_with_llm(latex_content)
            
            # Check if we got valid content
            if not latex_content or len(latex_content.strip()) < 50:
                return ConversionResult(
                    success=False,
                    error_message="PDF conversion produced minimal output. The PDF may be image-based (scanned) or corrupted.",
                    source_format="pdf"
                )
            
            return ConversionResult(
                success=True,
                latex_content=latex_content,
                source_format="pdf",
                warnings=_get_conversion_warnings(latex_content)
            )
            
        finally:
            # Clean up temp files
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
            if os.path.exists(docx_path):
                os.unlink(docx_path)
            
    except Exception as e:
        return ConversionResult(
            success=False,
            error_message=f"PDF conversion failed: {str(e)}",
            source_format="pdf"
        )


def read_tex_file(
    file_content: bytes,
    filename: str = "document.tex"
) -> ConversionResult:
    """
    Read TEX file - just decode bytes to string (no conversion needed).
    
    Args:
        file_content: Raw bytes of the TEX file
        filename: Original filename for reference
        
    Returns:
        ConversionResult with LaTeX content
    """
    try:
        # Decode bytes to string (UTF-8 first, latin-1 fallback)
        try:
            latex_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            latex_content = file_content.decode('latin-1')
        
        return ConversionResult(
            success=True,
            latex_content=latex_content,
            source_format="tex"
        )
        
    except Exception as e:
        return ConversionResult(
            success=False,
            error_message=f"Failed to read TEX file: {str(e)}",
            source_format="tex"
        )


def convert_document(
    file_content: bytes,
    filename: str
) -> ConversionResult:
    """
    Main entry point: Convert any supported document to LaTeX.
    
    Supported formats:
    - .docx (Microsoft Word)
    - .pdf (PDF documents)
    - .tex (LaTeX - passthrough)
    
    Args:
        file_content: Raw bytes of the file
        filename: Original filename (used to determine format)
        
    Returns:
        ConversionResult with LaTeX content or error
    """
    ext = Path(filename).suffix.lower()
    
    if ext == '.docx':
        return convert_docx_to_latex(file_content, filename)
    elif ext == '.pdf':
        return convert_pdf_to_latex(file_content, filename)
    elif ext == '.tex':
        return read_tex_file(file_content, filename)
    else:
        return ConversionResult(
            success=False,
            error_message=f"Unsupported file format: {ext}. Supported formats: .docx, .pdf, .tex",
            source_format=ext.lstrip('.')
        )


def _cleanup_latex_with_llm(latex: str) -> str:
    """
    Use LLM to clean up and restructure converted LaTeX into proper resume format.
    
    This function takes messy Pandoc-converted LaTeX and transforms it into
    clean, resume-appropriate LaTeX structure.
    
    Args:
        latex: Raw converted LaTeX from Pandoc
        
    Returns:
        Cleaned and restructured LaTeX, or original if LLM is not available
    """
    if not is_api_configured():
        return latex  # Skip if OpenAI API key not configured
    
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        system_prompt = """You are a LaTeX expert specializing in resume formatting. 
Your task is to convert messy, auto-generated LaTeX (from PDF/DOCX conversion) into clean, professional resume LaTeX.

Key requirements:
1. Remove unnecessary environments (quote, longtable, minipage where not needed)
2. Convert to clean section/item structures
3. Preserve all content (text, dates, descriptions)
4. Use standard resume formatting (sections, items, proper spacing)
5. Keep the document class as article (don't change to resume-specific classes)
6. Remove excessive packages and preamble complexity
7. Maintain professional formatting with proper spacing
8. Keep hyperref and basic formatting packages only

Output ONLY the cleaned LaTeX code, no explanations."""
        
        user_prompt = f"""Clean and restructure this converted LaTeX resume into proper resume format:

{latex}

Provide the cleaned LaTeX code:"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        cleaned_latex = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if cleaned_latex.startswith("```"):
            lines = cleaned_latex.split("\n")
            # Remove first line (```latex or ```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_latex = "\n".join(lines)
        
        return cleaned_latex.strip()
        
    except Exception as e:
        # If LLM cleanup fails, return original
        print(f"Warning: LLM cleanup failed: {e}")
        return latex


def _postprocess_pandoc_latex(latex: str) -> str:
    """
    Post-process LaTeX generated by Pandoc to clean it up.
    
    - Removes excessive whitespace
    - Fixes common Pandoc artifacts
    - Handles image references (removes or comments them out)
    """
    import re
    
    # Remove multiple blank lines
    latex = re.sub(r'\n{3,}', '\n\n', latex)
    
    # Remove tightlist command if not defined (Pandoc adds this)
    if '\\tightlist' in latex and '\\providecommand{\\tightlist}' not in latex:
        # Add the definition at the start of the preamble
        latex = latex.replace(
            '\\begin{document}',
            '\\providecommand{\\tightlist}{\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}}\n\\begin{document}'
        )
    
    # Handle image references - replace with placeholder text since images don't exist
    # Pattern: \includegraphics[...]{...}
    def replace_image(match):
        # Extract the image path (group 1 is the path in braces)
        img_path = match.group(1) if match.group(1) else 'image'
        # Extract just the filename
        img_name = img_path.split('/')[-1].split('\\')[-1]
        return f'[Image: {img_name}]'
    
    # Replace \includegraphics commands with placeholder text
    latex = re.sub(
        r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',
        replace_image,
        latex
    )
    
    return latex.strip()


def _get_conversion_warnings(latex: str) -> list[str]:
    """
    Analyze converted LaTeX and return warnings about potential issues.
    """
    warnings = []
    
    # Check for common issues
    if '\\includegraphics' in latex:
        warnings.append("Document contains images. Images may not display correctly and might need manual adjustment.")
    
    if '\\begin{table}' in latex:
        warnings.append("Document contains tables. Table formatting may need adjustment.")
    
    if len(latex) < 200:
        warnings.append("Converted content is very short. Some content may not have been extracted properly.")
    
    # Check for unbalanced braces
    open_braces = latex.count('{')
    close_braces = latex.count('}')
    if open_braces != close_braces:
        warnings.append(f"Unbalanced braces detected ({open_braces} open, {close_braces} close). LaTeX may have compilation errors.")
    
    return warnings


def get_supported_formats() -> list[str]:
    """Return list of supported file extensions"""
    return ['.docx', '.pdf', '.tex']


def check_conversion_dependencies() -> dict[str, tuple[bool, str]]:
    """
    Check if all conversion dependencies are installed.
    
    Returns:
        Dict mapping format to (is_installed, message)
    """
    return {
        'docx': _check_pandoc_installed(),
        'pdf': _check_pdf2docx_installed(),
        'tex': (True, "No dependencies required")
    }

