# services/llm.py
from __future__ import annotations
import os, json
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator
from openai import OpenAI

# OpenAI client
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ----------------------------
# Schemas
# ----------------------------
class ResumeForm(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    target_role: str
    experience_level: str
    skills: str  # comma separated
    experiences: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)

    @validator("skills")
    def _normalize(cls, v: str) -> str:
        return ", ".join([s.strip() for s in v.split(",") if s.strip()])

class SopForm(BaseModel):
    full_name: str
    email: str
    target_program: str
    university: str
    motivation: str
    background: str
    achievements: str
    goals: str
    word_limit: int = 950
    tone: str = "Academic"

class CoverLetterForm(BaseModel):
    full_name: str
    email: str
    target_role: str
    company: str
    highlights: List[str]
    tone: str = "Professional"

class VisaCoverLetterForm(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    address_line: str | None = None
    city_state_pin: str | None = None
    embassy_name: str = "Embassy of the Hellenic Republic"
    embassy_address: str = "EP-32, Dr. S. Radhakrishnan Marg, Chanakyapuri, New Delhi, 110021"
    visa_type: str = "Schengen short-stay (C)"
    country: str = "Greece"
    purpose: str
    entry_plan: str | None = None
    stay_dates: str
    destination_city: str = "Kos Island"
    itinerary_points: list[str] = []
    sponsorship_by: str | None = None
    accommodation: str | None = None
    enclosures: list[str] = []
    acknowledge_prev_visa_refusal: bool = False
    previous_refusal_reason: str | None = None
    closing_line: str = "I will adhere to visa conditions and depart before visa expiry."

# ----------------------------
# Chat helper
# ----------------------------
def _chat(messages: list[dict], max_tokens: int, temperature: float = 0.4) -> str:
    resp = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

# ----------------------------
# Generators
# ----------------------------
def generate_resume_sections(form: ResumeForm) -> Dict[str, Any]:
    sys = (
        "You are an expert Indian careers resume writer. "
        "Create concise, metric-driven, ATS-friendly output."
    )
    user = {
        "target_role": form.target_role,
        "experience_level": form.experience_level,
        "skills": form.skills,
        "experiences": form.experiences,
        "projects": form.projects,
        "education": form.education
    }
    messages = [
        {"role": "system", "content": sys},
        {"role": "user", "content":
            "Return ONLY JSON in this schema:\n"
            "{"
            '"summary": "string",'
            '"skills": ["string"],'
            '"experience": [{"title":"","company":"","dates":"","bullets":["",""]}],'
            '"projects": [{"name":"","stack":"","bullets":["",""]}],'
            '"education": [{"degree":"","institute":"","score":"","year":""}]'
            "}\n"
            f"User data:\n{json.dumps(user, ensure_ascii=False)}\n"
            "Bullets must include ACTION + METRIC + IMPACT."
        }
    ]
    text = _chat(messages, max_tokens=1100)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass
    return {
        "summary": text[:300],
        "skills": [s.strip() for s in form.skills.split(",")],
        "experience": form.experiences,
        "projects": form.projects,
        "education": form.education
    }

def generate_sop_text(form: SopForm) -> str:
    sys = ("You write original, plagiarism-free SOPs for Indian students. "
           "900–1000 words; clear structure; avoid clichés.")
    messages = [
        {"role": "system", "content": sys},
        {"role": "user", "content":
            f"Name: {form.full_name}\nEmail: {form.email}\nProgram: {form.target_program}\n"
            f"University: {form.university}\nMotivation: {form.motivation}\nBackground: {form.background}\n"
            f"Achievements: {form.achievements}\nGoals: {form.goals}\n"
            f"Word limit: {form.word_limit}\nTone: {form.tone}\n"
            "Structure: Intro; Academic foundation; Projects/Research; Work; Why this program/university; Goals; Closing.\n"
            "Return plain text only."
        }
    ]
    return _chat(messages, max_tokens=1600, temperature=0.5)

def generate_cover_letter_text(form: CoverLetterForm) -> str:
    sys = "You craft crisp, professional cover letters tailored to Indian recruiters."
    messages = [
        {"role": "system", "content": sys},
        {"role": "user", "content":
            f"Applicant: {form.full_name} ({form.email})\nTarget role: {form.target_role}\n"
            f"Company: {form.company}\nHighlights: {', '.join(form.highlights)}\n"
            f"Tone: {form.tone}\nLength: 250–350 words. Strong opening + clear closing."
        }
    ]
    return _chat(messages, max_tokens=700, temperature=0.45)

def generate_visa_cover_letter_text(form: VisaCoverLetterForm) -> str:
    sys = (
        "You draft formal visa cover letters for Indian applicants to EU embassies. "
        "Format strictly: Applicant block; Date; Embassy address; Subject; Salutation "
        "('Respected Visa Officer,'); Purpose; Itinerary/entry plan; Accommodation & Funding/Sponsorship; "
        "Return compliance; Thank you; Signature."
    )
    subject = f"Application for {form.visa_type} to {form.country} — {form.purpose}"
    if form.acknowledge_prev_visa_refusal and form.previous_refusal_reason:
        subject += " (response to previous refusal)"

    itinerary_text = ""
    if form.itinerary_points:
        itinerary_text = "Itinerary summary:\n" + "\n".join([f"- {p}" for p in form.itinerary_points])

    encl_text = ""
    if form.enclosures:
        encl_text = "Enclosures:\n" + "\n".join([f"• {e}" for e in form.enclosures])

    user = f"""
Applicant: {form.full_name}, {form.email}, {form.phone or ""}, {form.address_line or ""}, {form.city_state_pin or ""}
Embassy: {form.embassy_name}, {form.embassy_address}
Subject: {subject}

Purpose of travel: {form.purpose}
Travel window: {form.stay_dates}; Destination: {form.destination_city}
Entry plan: {form.entry_plan or "—"}
Accommodation: {form.accommodation or "—"}
Funding/Sponsorship: {form.sponsorship_by or "self-funded"}

{itinerary_text}

Return intent: {form.closing_line}

{encl_text}
"""
    messages = [
        {"role": "system", "content": sys},
        {"role": "user", "content":
            "Write a concise embassy cover letter (250–400 words). Maintain formal tone and structure. "
            "Return plain text only.\n"
            f"Applicant data:\n{user}"
        }
    ]
    return _chat(messages, max_tokens=900, temperature=0.3)
