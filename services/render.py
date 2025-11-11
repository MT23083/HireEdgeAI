# services/render.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta
import os
import shutil
import subprocess
import tempfile

from docxtpl import DocxTemplate
from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.llm import ResumeForm, SopForm, CoverLetterForm, VisaCoverLetterForm


# -----------------------------
# Common utils
# -----------------------------
def ensure_dirs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

def cleanup_old_files(out_dir: Path, older_than_hours: int = 24) -> int:
    cutoff = datetime.now() - timedelta(hours=older_than_hours)
    count = 0
    for p in list(out_dir.glob("*.docx")) + list(out_dir.glob("*.pdf")):
        try:
            if datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
                p.unlink()
                count += 1
        except Exception:
            pass
    return count

def _safe_filename(stem: str) -> str:
    return "".join(c if c.isalnum() or c in ("_", "-", ".") else "_" for c in stem)

def _check_pdflatex() -> str:
    exe = shutil.which("pdflatex")
    if not exe:
        raise RuntimeError(
            "pdflatex not found. Install a LaTeX distribution and ensure 'pdflatex' is on PATH.\n"
            "Windows: MiKTeX (https://miktex.org/download)\n"
            "Ubuntu: sudo apt-get install texlive-full\n"
            "macOS: MacTeX."
        )
    return exe

def _jinja_env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=(), default_for_string=False)
    )

def _latex_compile(tex_source: str, out_dir: Path, outfile_name: str) -> bytes:
    """
    Compile a LaTeX source string to PDF using pdflatex in a temp directory.
    Returns the compiled PDF bytes saved as out_dir/outfile_name.
    """
    ensure_dirs(out_dir)
    _check_pdflatex()
    with tempfile.TemporaryDirectory(prefix="latex_build_") as tmpdir:
        tmp = Path(tmpdir)
        tex_path = tmp / "doc.tex"
        tex_path.write_text(tex_source, encoding="utf-8")

        cmd = [_check_pdflatex(), "-interaction=nonstopmode", "-halt-on-error", str(tex_path)]
        # Run twice for stable refs
        for _ in range(2):
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=tmp, text=True)
            if proc.returncode != 0:
                raise RuntimeError("LaTeX compilation failed:\n\n" + proc.stdout)

        built_pdf = tmp / "doc.pdf"
        if not built_pdf.exists():
            raise FileNotFoundError("LaTeX did not produce doc.pdf")

        final_pdf = out_dir / outfile_name
        shutil.copyfile(built_pdf, final_pdf)
        return final_pdf.read_bytes()


# -----------------------------
# Shared resume context (used by DOCX + LaTeX)
# -----------------------------
def _resume_context(form: ResumeForm, sections: Dict[str, Any], watermarked: bool) -> Dict[str, Any]:
    return {
        "watermark": "PREVIEW" if watermarked else "",
        "watermark_text": "PREVIEW" if watermarked else "",
        "full_name": form.full_name,
        "email": form.email,
        "phone": form.phone or "",
        "location": form.location or "",
        "linkedin": form.linkedin or "",
        "github": form.github or "",
        "target_role": form.target_role,
        "summary": sections.get("summary", ""),
        "skills": ", ".join(sections.get("skills", [])),
        "experience_items": sections.get("experience", []),
        "project_items": sections.get("projects", []),
        "education_items": sections.get("education", []),
        "today": datetime.now().strftime("%B %d, %Y"),
    }


# ===== Resume: DOCX =====
def render_resume_docx(templates_dir: Path, out_dir: Path,
                       form: ResumeForm, sections: Dict[str, Any],
                       watermarked: bool) -> bytes:
    tpl_path = templates_dir / "resume_template.docx"
    if not tpl_path.exists():
        raise FileNotFoundError(f"Template missing: {tpl_path}")
    tpl = DocxTemplate(str(tpl_path))
    tpl.render(_resume_context(form, sections, watermarked))
    out = out_dir / f"{_safe_filename(form.full_name)}_resume{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()

# ===== Resume: LaTeX → PDF =====
def render_resume_latex_pdf(templates_dir: Path, out_dir: Path,
                            form: ResumeForm, sections: Dict[str, Any],
                            watermarked: bool) -> bytes:
    env = _jinja_env(templates_dir)
    tex_tmpl = templates_dir / "resume_template.tex"
    if not tex_tmpl.exists():
        raise FileNotFoundError(f"LaTeX template missing: {tex_tmpl}")
    tex = env.get_template("resume_template.tex").render(**_resume_context(form, sections, watermarked))
    return _latex_compile(
        tex,
        out_dir,
        f"{_safe_filename(form.full_name)}_resume{'_PREVIEW' if watermarked else ''}.pdf"
    )


# ===== SOP: DOCX =====
def render_sop_docx(templates_dir: Path, out_dir: Path,
                    form: SopForm, sop_text: str, watermarked: bool) -> bytes:
    tpl_path = templates_dir / "sop_template.docx"
    if not tpl_path.exists():
        raise FileNotFoundError(f"Template missing: {tpl_path}")
    tpl = DocxTemplate(str(tpl_path))
    tpl.render({
        "watermark": "PREVIEW" if watermarked else "",
        "full_name": form.full_name,
        "email": form.email,
        "program": form.target_program,
        "university": form.university,
        "body": sop_text,
    })
    out = out_dir / f"{_safe_filename(form.full_name)}_SOP{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()

# ===== SOP: LaTeX → PDF =====
def render_sop_latex_pdf(templates_dir: Path, out_dir: Path,
                         form: SopForm, sop_text: str, watermarked: bool) -> bytes:
    env = _jinja_env(templates_dir)
    tex_tmpl = templates_dir / "sop_template.tex"
    if not tex_tmpl.exists():
        raise FileNotFoundError(f"LaTeX template missing: {tex_tmpl}")
    tex = env.get_template("sop_template.tex").render(
        full_name=form.full_name,
        email=form.email,
        program=form.target_program,
        university=form.university,
        body=sop_text,
        watermark_text="PREVIEW" if watermarked else "",
        today=datetime.now().strftime("%B %d, %Y"),
    )
    return _latex_compile(
        tex,
        out_dir,
        f"{_safe_filename(form.full_name)}_SOP{'_PREVIEW' if watermarked else ''}.pdf"
    )


# ===== Cover Letter: DOCX =====
def render_cover_letter_docx(templates_dir: Path, out_dir: Path,
                             form: CoverLetterForm, cl_text: str, watermarked: bool) -> bytes:
    tpl_path = templates_dir / "cover_letter_template.docx"
    if not tpl_path.exists():
        raise FileNotFoundError(f"Template missing: {tpl_path}")
    tpl = DocxTemplate(str(tpl_path))
    tpl.render({
        "watermark": "PREVIEW" if watermarked else "",
        "full_name": form.full_name,
        "email": form.email,
        "role": form.target_role,
        "company": form.company,
        "body": cl_text,
    })
    out = out_dir / f"{_safe_filename(form.full_name)}_CoverLetter{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()

# ===== Cover Letter: LaTeX → PDF =====
def render_cover_letter_latex_pdf(templates_dir: Path, out_dir: Path,
                                  form: CoverLetterForm, cl_text: str, watermarked: bool) -> bytes:
    env = _jinja_env(templates_dir)
    tex_tmpl = templates_dir / "cover_letter_template.tex"
    if not tex_tmpl.exists():
        raise FileNotFoundError(f"LaTeX template missing: {tex_tmpl}")
    tex = env.get_template("cover_letter_template.tex").render(
        full_name=form.full_name,
        email=form.email,
        role=form.target_role,
        company=form.company,
        body=cl_text,
        watermark_text="PREVIEW" if watermarked else "",
        today=datetime.now().strftime("%B %d, %Y"),
    )
    return _latex_compile(
        tex,
        out_dir,
        f"{_safe_filename(form.full_name)}_CoverLetter{'_PREVIEW' if watermarked else ''}.pdf"
    )


# ===== Visa Cover Letter: DOCX =====
def render_visa_cover_letter_docx(templates_dir: Path, out_dir: Path,
                                  form: VisaCoverLetterForm, body_text: str,
                                  watermarked: bool) -> bytes:
    tpl_path = templates_dir / "visa_cover_letter_template.docx"
    if not tpl_path.exists():
        raise FileNotFoundError(f"Template missing: {tpl_path}")
    tpl = DocxTemplate(str(tpl_path))

    applicant_block = "\n".join(filter(None, [
        form.full_name,
        (form.address_line or ""),
        (form.city_state_pin or ""),
        (f"Contact: {form.phone}" if form.phone else ""),
        (f"Email: {form.email}" if form.email else ""),
    ])).strip()
    embassy_block = "\n".join([form.embassy_name, form.embassy_address]).strip()
    subject = f"Application for {form.visa_type} to {form.country} — {form.purpose}"

    tpl.render({
        "watermark": "PREVIEW" if watermarked else "",
        "date": datetime.now().strftime("%B %d, %Y"),
        "applicant_block": applicant_block,
        "embassy_block": embassy_block,
        "subject": subject,
        "body": body_text,
        "sign_name": form.full_name,
    })

    out = out_dir / f"{_safe_filename(form.full_name)}_VisaCoverLetter{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()

# ===== Visa Cover Letter: LaTeX → PDF =====
def render_visa_cover_letter_latex_pdf(templates_dir: Path, out_dir: Path,
                                       form: VisaCoverLetterForm, body_text: str,
                                       watermarked: bool) -> bytes:
    env = _jinja_env(templates_dir)
    tex_tmpl = templates_dir / "visa_cover_letter_template.tex"
    if not tex_tmpl.exists():
        raise FileNotFoundError(f"LaTeX template missing: {tex_tmpl}")

    applicant_block = "\n".join(filter(None, [
        form.full_name,
        (form.address_line or ""),
        (form.city_state_pin or ""),
        (f"Contact: {form.phone}" if form.phone else ""),
        (f"Email: {form.email}" if form.email else ""),
    ])).strip()
    embassy_block = "\n".join([form.embassy_name, form.embassy_address]).strip()
    subject = f"Application for {form.visa_type} to {form.country} — {form.purpose}"

    tex = env.get_template("visa_cover_letter_template.tex").render(
        applicant_block=applicant_block,
        date=datetime.now().strftime("%B %d, %Y"),
        embassy_block=embassy_block,
        subject=subject,
        body=body_text,
        sign_name=form.full_name,
        watermark_text="PREVIEW" if watermarked else "",
    )
    return _latex_compile(
        tex,
        out_dir,
        f"{_safe_filename(form.full_name)}_VisaCoverLetter{'_PREVIEW' if watermarked else ''}.pdf"
    )
