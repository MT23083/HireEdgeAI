# services/render.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

from docxtpl import DocxTemplate

from services.llm import ResumeForm, SopForm, CoverLetterForm, VisaCoverLetterForm


def ensure_dirs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

def cleanup_old_files(out_dir: Path, older_than_hours: int = 24) -> int:
    cutoff = datetime.now() - timedelta(hours=older_than_hours)
    count = 0
    for p in out_dir.glob("*.docx"):
        try:
            if datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
                p.unlink(); count += 1
        except Exception:
            pass
    return count

# ---------- Resume ----------
def _resume_context(form: ResumeForm, sections: Dict[str, Any], watermarked: bool) -> Dict[str, Any]:
    return {
        "watermark": "PREVIEW" if watermarked else "",
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
    }

def render_resume_docx(templates_dir: Path, out_dir: Path,
                       form: ResumeForm, sections: Dict[str, Any],
                       watermarked: bool) -> bytes:
    tpl_path = templates_dir / "resume_template.docx"
    tpl = DocxTemplate(str(tpl_path))
    tpl.render(_resume_context(form, sections, watermarked))
    out = out_dir / f"{form.full_name.replace(' ','_')}_resume{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()

# ---------- SOP ----------
def render_sop_docx(templates_dir: Path, out_dir: Path,
                    form: SopForm, sop_text: str, watermarked: bool) -> bytes:
    tpl_path = templates_dir / "sop_template.docx"
    tpl = DocxTemplate(str(tpl_path))
    tpl.render({
        "watermark": "PREVIEW" if watermarked else "",
        "full_name": form.full_name,
        "email": form.email,
        "program": form.target_program,
        "university": form.university,
        "body": sop_text,
    })
    out = out_dir / f"{form.full_name.replace(' ','_')}_SOP{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()

# ---------- Cover Letter ----------
def render_cover_letter_docx(templates_dir: Path, out_dir: Path,
                             form: CoverLetterForm, cl_text: str, watermarked: bool) -> bytes:
    tpl_path = templates_dir / "cover_letter_template.docx"  # dedicated template
    tpl = DocxTemplate(str(tpl_path))
    tpl.render({
        "watermark": "PREVIEW" if watermarked else "",
        "full_name": form.full_name,
        "email": form.email,
        "role": form.target_role,
        "company": form.company,
        "body": cl_text,
    })
    out = out_dir / f"{form.full_name.replace(' ','_')}_CoverLetter{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()

# ---------- Visa Cover Letter ----------
def render_visa_cover_letter_docx(templates_dir: Path, out_dir: Path,
                                  form: VisaCoverLetterForm, body_text: str,
                                  watermarked: bool) -> bytes:
    tpl_path = templates_dir / "visa_cover_letter_template.docx"
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

    out = out_dir / f"{form.full_name.replace(' ','_')}_VisaCoverLetter{'_PREVIEW' if watermarked else ''}.docx"
    tpl.save(str(out))
    return out.read_bytes()
