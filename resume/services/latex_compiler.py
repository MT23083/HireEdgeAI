# resume/services/latex_compiler.py
"""
LaTeX to PDF Compiler Service
Handles real-time compilation of LaTeX source to PDF
"""

from __future__ import annotations
import shutil
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import hashlib


@dataclass
class CompilationResult:
    """Result of LaTeX compilation"""
    success: bool
    pdf_bytes: Optional[bytes] = None
    error_message: Optional[str] = None
    error_line: Optional[int] = None
    compile_time_ms: int = 0


# Cache for compiled PDFs (avoid recompiling unchanged LaTeX)
_compile_cache: dict[str, bytes] = {}
_MAX_CACHE_SIZE = 10


def check_pdflatex_installed() -> tuple[bool, str]:
    """
    Check if pdflatex is available on the system.
    
    Returns:
        (is_installed, message)
    """
    exe = shutil.which("pdflatex")
    if exe:
        return True, f"pdflatex found at: {exe}"
    
    return False, (
        "⚠️ pdflatex not found. Please install a LaTeX distribution:\n"
        "• **Ubuntu/Debian**: `sudo apt-get install texlive-latex-base texlive-fonts-recommended`\n"
        "• **Windows**: Install [MiKTeX](https://miktex.org/download)\n"
        "• **macOS**: Install [MacTeX](https://www.tug.org/mactex/)"
    )


def _get_cache_key(latex_source: str) -> str:
    """Generate cache key from LaTeX source"""
    return hashlib.md5(latex_source.encode()).hexdigest()


def _parse_latex_error(log_output: str) -> tuple[Optional[str], Optional[int]]:
    """
    Parse LaTeX log output to extract user-friendly error message.
    
    Returns:
        (error_message, error_line_number)
    """
    lines = log_output.split('\n')
    error_msg = None
    error_line = None
    
    for i, line in enumerate(lines):
        # Look for error patterns
        if line.startswith('!'):
            error_msg = line[1:].strip()
            # Try to find line number
            for j in range(i, min(i + 5, len(lines))):
                if 'l.' in lines[j]:
                    try:
                        # Extract line number from "l.45" format
                        parts = lines[j].split('l.')
                        if len(parts) > 1:
                            line_part = parts[1].split()[0]
                            error_line = int(line_part)
                    except (ValueError, IndexError):
                        pass
                    break
            break
        
        # Alternative error format
        if 'LaTeX Error:' in line:
            error_msg = line.split('LaTeX Error:')[1].strip()
            break
        
        if 'Undefined control sequence' in line:
            error_msg = "Undefined command used. Check for typos in LaTeX commands."
            break
    
    if not error_msg:
        # Generic error
        if 'error' in log_output.lower():
            error_msg = "LaTeX compilation failed. Check your syntax."
    
    return error_msg, error_line


def compile_latex_to_pdf(
    latex_source: str,
    timeout_seconds: int = 30,
    use_cache: bool = True
) -> CompilationResult:
    """
    Compile LaTeX source to PDF.
    
    Args:
        latex_source: The LaTeX source code
        timeout_seconds: Maximum time for compilation
        use_cache: Whether to use caching for unchanged sources
        
    Returns:
        CompilationResult with PDF bytes or error info
    """
    import time
    start_time = time.time()
    
    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(latex_source)
        if cache_key in _compile_cache:
            return CompilationResult(
                success=True,
                pdf_bytes=_compile_cache[cache_key],
                compile_time_ms=0
            )
    
    # Check if pdflatex is installed
    is_installed, msg = check_pdflatex_installed()
    if not is_installed:
        return CompilationResult(
            success=False,
            error_message=msg
        )
    
    try:
        with tempfile.TemporaryDirectory(prefix="resume_latex_") as tmpdir:
            tmp_path = Path(tmpdir)
            tex_file = tmp_path / "resume.tex"
            pdf_file = tmp_path / "resume.pdf"
            log_file = tmp_path / "resume.log"
            
            # Write LaTeX source
            tex_file.write_text(latex_source, encoding="utf-8")
            
            # Compile (run twice for stable references like page numbers)
            pdflatex_cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory", str(tmp_path),
                str(tex_file)
            ]
            
            for run in range(2):
                proc = subprocess.run(
                    pdflatex_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=tmp_path,
                    text=True,
                    timeout=timeout_seconds
                )
                
                # Check for errors on first run
                if run == 0 and proc.returncode != 0:
                    log_content = ""
                    if log_file.exists():
                        log_content = log_file.read_text(encoding="utf-8", errors="ignore")
                    else:
                        log_content = proc.stdout or ""
                    
                    error_msg, error_line = _parse_latex_error(log_content)
                    
                    return CompilationResult(
                        success=False,
                        error_message=error_msg or "Compilation failed",
                        error_line=error_line,
                        compile_time_ms=int((time.time() - start_time) * 1000)
                    )
            
            # Check if PDF was created
            if not pdf_file.exists():
                return CompilationResult(
                    success=False,
                    error_message="PDF file was not generated",
                    compile_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Read PDF bytes
            pdf_bytes = pdf_file.read_bytes()
            
            # Cache the result
            if use_cache:
                cache_key = _get_cache_key(latex_source)
                if len(_compile_cache) >= _MAX_CACHE_SIZE:
                    # Remove oldest entry
                    oldest_key = next(iter(_compile_cache))
                    del _compile_cache[oldest_key]
                _compile_cache[cache_key] = pdf_bytes
            
            return CompilationResult(
                success=True,
                pdf_bytes=pdf_bytes,
                compile_time_ms=int((time.time() - start_time) * 1000)
            )
            
    except subprocess.TimeoutExpired:
        return CompilationResult(
            success=False,
            error_message=f"Compilation timed out after {timeout_seconds} seconds",
            compile_time_ms=timeout_seconds * 1000
        )
    except Exception as e:
        return CompilationResult(
            success=False,
            error_message=f"Unexpected error: {str(e)}",
            compile_time_ms=int((time.time() - start_time) * 1000)
        )


def clear_cache():
    """Clear the compilation cache"""
    global _compile_cache
    _compile_cache = {}

