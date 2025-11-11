# app.py
"""
AI Document Assistant (Resume, SOP, Cover Letter, Visa Cover Letter)
MVP: Streamlit + OpenAI + docxtpl + LaTeX + Razorpay Payment Links

Flow per document:
  Form -> AI draft preview (watermarked) -> Razorpay pay link (DOCX/PDF) ->
  Verify Payment ID -> Download final in chosen format
"""

from __future__ import annotations
import os
from pathlib import Path
import streamlit as st

from dotenv import load_dotenv
load_dotenv()  # local dev; on Streamlit Cloud use Secrets

# --- Local paths
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data" / "generated"
TEMPLATES_DIR = APP_DIR / "templates"

# --- Services
from services.llm import (
    ResumeForm, SopForm, CoverLetterForm, VisaCoverLetterForm,
    generate_resume_sections, generate_sop_text, generate_cover_letter_text, generate_visa_cover_letter_text
)
from services.render import (
    ensure_dirs, cleanup_old_files,
    # DOCX renderers
    render_resume_docx, render_sop_docx, render_cover_letter_docx, render_visa_cover_letter_docx,
    # LaTeX → PDF renderers
    render_resume_latex_pdf, render_sop_latex_pdf, render_cover_letter_latex_pdf, render_visa_cover_letter_latex_pdf
)
from services.payments import payment_links_config, verify_razorpay_payment, PaymentStatus


# ---------- App bootstrap ----------
ensure_dirs(DATA_DIR)
cleanup_old_files(DATA_DIR, older_than_hours=24)

st.set_page_config(
    page_title="AI Resume/SOP/Cover | Visa Cover Letter",
    page_icon="🧠",
    layout="wide",
)

links = payment_links_config()

# ---------- Helpers ----------
def _download_button(data_bytes: bytes, filename: str, label: str, mime: str):
    st.download_button(
        label=label,
        data=data_bytes,
        file_name=filename,
        mime=mime,
        use_container_width=True,
    )

def _verify_ui(product_label: str) -> bool:
    st.divider()
    st.markdown(f"#### ✅ Unlock Final {product_label}")
    st.write("If you’ve paid already, enter your **Razorpay Payment ID** (e.g., `pay_ABC123...`).")
    pid = st.text_input("Razorpay Payment ID", placeholder="pay_...", key=f"pid_{product_label}")
    verified = False
    if st.button("Verify Payment", use_container_width=True, type="primary", key=f"verify_{product_label}"):
        if not pid.strip():
            st.error("Enter a valid Payment ID.")
        else:
            status, raw = verify_razorpay_payment(pid.strip())
            if status == PaymentStatus.SUCCESS:
                st.success("Payment captured ✔️ — you can download your file now.")
                verified = True
            elif status == PaymentStatus.PENDING:
                st.warning("Payment found but not captured yet. Please wait 1–2 minutes and try again.")
            else:
                st.error("Payment not found or failed. If you paid just now, wait a moment and retry.")
            with st.expander("Payment lookup (debug)"):
                st.code(raw or "No response", language="json")
    return verified

def _format_selector(default_pdf: bool = False) -> tuple[str, bool]:
    """
    Returns (label, is_latex_pdf)
    """
    fmt = st.radio("Format", ["DOCX", "PDF (LaTeX)"], horizontal=True, index=1 if default_pdf else 0)
    return fmt, (fmt == "PDF (LaTeX)")


# ---------- Sidebar ----------
st.sidebar.markdown("### ⚙️ Settings")
st.sidebar.info("We show a **free preview** first. Pay only when you like it.")
st.sidebar.caption("Privacy: Files auto-delete within 24h. We don’t store your data by default.")

st.title("AI Document Assistant for Students & Professionals")
st.caption("Resume · SOP · Cover Letter · Visa Cover Letter (EU/Schengen format) — fast, clean, and affordable.")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["🧰 Resume", "🎓 SOP", "✉️ Cover Letter", "🌍 Visa Cover Letter"])

# =========================
# Resume
# =========================
with tab1:
    st.header("ATS-Ready Resume")
    st.caption("Fill minimal details → AI crafts metric-driven bullets → Preview → Pay → Download")

    with st.form("resume_form", clear_on_submit=False):
        full_name = st.text_input("Full Name *")
        email = st.text_input("Email *")
        phone = st.text_input("Phone", placeholder="+91-XXXXXXXXXX")
        location = st.text_input("Location", placeholder="New Delhi, IN")
        linkedin = st.text_input("LinkedIn", placeholder="https://linkedin.com/in/...")
        github = st.text_input("GitHub", placeholder="https://github.com/...")

        target_role = st.text_input("Target Role *", placeholder="Data Analyst / Backend Engineer / ...")
        experience_level = st.selectbox("Experience Level", ["Fresher", "1–3 years", "3–5 years", "5+ years"])
        skills = st.text_area("Skills (comma separated) *", placeholder="Python, SQL, Pandas, NLP, ...")

        st.markdown("**Experience**")
        e_title = st.text_input("Experience #1 — Title", placeholder="Data Analyst")
        e_company = st.text_input("Experience #1 — Company", placeholder="ABC Pvt Ltd")
        e_dates = st.text_input("Experience #1 — Dates", placeholder="Jan 2023 – Aug 2024")
        e_bullets = st.text_area("Experience #1 — Bullets (one per line)", height=100)

        st.markdown("**Projects**")
        p_name = st.text_input("Project #1 — Name", placeholder="Customer Churn Prediction")
        p_stack = st.text_input("Project #1 — Stack", placeholder="Python, XGBoost, Streamlit")
        p_bullets = st.text_area("Project #1 — Bullets (one per line)", height=90)

        st.markdown("**Education**")
        degree = st.text_input("Degree *", placeholder="M.Tech in CSE")
        institute = st.text_input("Institute *", placeholder="IIIT Delhi")
        score = st.text_input("CGPA/Percentage", placeholder="8.7/10")
        year = st.text_input("Year", placeholder="2025")

        r_submit = st.form_submit_button("⚡ Generate Resume Preview", type="primary", use_container_width=True)

    if r_submit:
        form = ResumeForm(
            full_name=full_name, email=email, phone=phone, location=location,
            linkedin=linkedin, github=github, target_role=target_role,
            experience_level=experience_level, skills=skills,
            experiences=[{
                "title": e_title, "company": e_company, "dates": e_dates,
                "bullets": [b.strip() for b in e_bullets.split("\n") if b.strip()]
            }],
            projects=[{
                "name": p_name, "stack": p_stack,
                "bullets": [b.strip() for b in p_bullets.split("\n") if b.strip()]
            }],
            education=[{
                "degree": degree, "institute": institute, "score": score, "year": year
            }],
        )
        with st.spinner("Creating ATS-friendly sections..."):
            draft = generate_resume_sections(form)

        st.success("Preview generated.")
        st.subheader("JSON Preview (watermarked)")
        st.json(draft, expanded=False)

        fmt, use_latex = _format_selector()

        if use_latex:
            try:
                preview_bytes = render_resume_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, draft, watermarked=True)
                _download_button(
                    preview_bytes,
                    f"{form.full_name.replace(' ','_')}_resume_PREVIEW.pdf",
                    label="⬇️ Download Watermarked Preview (PDF)",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF build error: {e}")
            st.link_button("Pay ₹399 for Resume (LaTeX PDF)", url=links["RESUME_LATEX"], use_container_width=True)

            if _verify_ui("Resume (LaTeX)"):
                try:
                    final_bytes = render_resume_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, draft, watermarked=False)
                    _download_button(
                        final_bytes,
                        f"{form.full_name.replace(' ','_')}_resume.pdf",
                        label="⬇️ Download Final (PDF)",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"PDF build error: {e}")
        else:
            preview_bytes = render_resume_docx(TEMPLATES_DIR, DATA_DIR, form, draft, watermarked=True)
            _download_button(
                preview_bytes,
                f"{form.full_name.replace(' ','_')}_resume_PREVIEW.docx",
                label="⬇️ Download Watermarked Preview (DOCX)",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.link_button("Pay ₹299 for Resume (DOCX)", url=links["RESUME"], use_container_width=True)

            if _verify_ui("Resume (DOCX)"):
                final_bytes = render_resume_docx(TEMPLATES_DIR, DATA_DIR, form, draft, watermarked=False)
                _download_button(
                    final_bytes,
                    f"{form.full_name.replace(' ','_')}_resume.docx",
                    label="⬇️ Download Final (DOCX)",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

# =========================
# SOP
# =========================
with tab2:
    st.header("Statement of Purpose (SOP)")
    st.caption("Clear, original, 900–1000 words; tailored to your program and university.")

    with st.form("sop_form", clear_on_submit=False):
        s_name = st.text_input("Full Name *", key="s_name")
        s_email = st.text_input("Email *", key="s_email")
        program = st.text_input("Target Program *", placeholder="MS in Data Science")
        university = st.text_input("University *", placeholder="University of Toronto")
        motivation = st.text_area("Motivation (why this field?)")
        background = st.text_area("Academic/Work Background")
        achievements = st.text_area("Achievements")
        goals = st.text_area("Career Goals")
        word_limit = st.slider("Word Limit", 800, 1200, 950, step=50)
        tone = st.selectbox("Tone", ["Academic", "Concise", "Story-driven"])
        s_submit = st.form_submit_button("⚡ Generate SOP Draft", type="primary", use_container_width=True)

    if s_submit:
        form = SopForm(
            full_name=s_name, email=s_email, target_program=program, university=university,
            motivation=motivation, background=background, achievements=achievements,
            goals=goals, word_limit=word_limit, tone=tone
        )
        with st.spinner("Drafting SOP..."):
            sop_text = generate_sop_text(form)

        st.success("Preview generated.")
        st.text_area("SOP Preview (watermarked)", sop_text, height=320)

        fmt, use_latex = _format_selector()

        if use_latex:
            try:
                preview_bytes = render_sop_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, sop_text, watermarked=True)
                _download_button(
                    preview_bytes,
                    f"{form.full_name.replace(' ','_')}_SOP_PREVIEW.pdf",
                    label="⬇️ Download Watermarked Preview (PDF)",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF build error: {e}")
            st.link_button("Pay ₹599 for SOP (LaTeX PDF)", url=links["SOP_LATEX"], use_container_width=True)

            if _verify_ui("SOP (LaTeX)"):
                try:
                    final_bytes = render_sop_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, sop_text, watermarked=False)
                    _download_button(
                        final_bytes,
                        f"{form.full_name.replace(' ','_')}_SOP.pdf",
                        label="⬇️ Download Final (PDF)",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"PDF build error: {e}")
        else:
            preview_bytes = render_sop_docx(TEMPLATES_DIR, DATA_DIR, form, sop_text, watermarked=True)
            _download_button(
                preview_bytes,
                f"{form.full_name.replace(' ','_')}_SOP_PREVIEW.docx",
                label="⬇️ Download Watermarked Preview (DOCX)",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.link_button("Pay ₹499 for SOP (DOCX)", url=links["SOP"], use_container_width=True)

            if _verify_ui("SOP (DOCX)"):
                final_bytes = render_sop_docx(TEMPLATES_DIR, DATA_DIR, form, sop_text, watermarked=False)
                _download_button(
                    final_bytes,
                    f"{form.full_name.replace(' ','_')}_SOP.docx",
                    label="⬇️ Download Final (DOCX)",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

# =========================
# Cover Letter
# =========================
with tab3:
    st.header("Job Cover Letter")
    st.caption("Tailored to your target role and company.")

    with st.form("cl_form", clear_on_submit=False):
        c_name = st.text_input("Full Name *", key="c_name")
        c_email = st.text_input("Email *", key="c_email")
        c_role = st.text_input("Target Role *")
        c_company = st.text_input("Company *", placeholder="e.g., TCS")
        c_high = st.text_area("Top achievements to mention (one per line)")
        c_tone = st.selectbox("Tone", ["Professional", "Warm", "Direct"])
        c_submit = st.form_submit_button("⚡ Generate Cover Letter", type="primary", use_container_width=True)

    if c_submit:
        form = CoverLetterForm(
            full_name=c_name, email=c_email, target_role=c_role, company=c_company,
            highlights=[h.strip() for h in c_high.split("\n") if h.strip()], tone=c_tone
        )
        with st.spinner("Drafting cover letter..."):
            cl_text = generate_cover_letter_text(form)

        st.success("Preview generated.")
        st.text_area("Cover Letter Preview (watermarked)", cl_text, height=280)

        fmt, use_latex = _format_selector()

        if use_latex:
            try:
                preview_bytes = render_cover_letter_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, cl_text, watermarked=True)
                _download_button(
                    preview_bytes,
                    f"{form.full_name.replace(' ','_')}_CoverLetter_PREVIEW.pdf",
                    label="⬇️ Download Watermarked Preview (PDF)",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF build error: {e}")
            st.link_button("Pay ₹249 for Cover Letter (LaTeX PDF)",
                           url=links["COVER_LETTER_LATEX"], use_container_width=True)

            if _verify_ui("Cover Letter (LaTeX)"):
                try:
                    final_bytes = render_cover_letter_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, cl_text, watermarked=False)
                    _download_button(
                        final_bytes,
                        f"{form.full_name.replace(' ','_')}_CoverLetter.pdf",
                        label="⬇️ Download Final (PDF)",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"PDF build error: {e}")
        else:
            preview_bytes = render_cover_letter_docx(TEMPLATES_DIR, DATA_DIR, form, cl_text, watermarked=True)
            _download_button(
                preview_bytes,
                f"{form.full_name.replace(' ','_')}_CoverLetter_PREVIEW.docx",
                label="⬇️ Download Watermarked Preview (DOCX)",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.link_button("Pay ₹199 for Cover Letter (DOCX)",
                           url=links["COVER_LETTER"], use_container_width=True)

            if _verify_ui("Cover Letter (DOCX)"):
                final_bytes = render_cover_letter_docx(TEMPLATES_DIR, DATA_DIR, form, cl_text, watermarked=False)
                _download_button(
                    final_bytes,
                    f"{form.full_name.replace(' ','_')}_CoverLetter.docx",
                    label="⬇️ Download Final (DOCX)",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

# =========================
# Visa Cover Letter (EU/Schengen format)
# =========================
with tab4:
    st.header("Visa Cover Letter (EU/Schengen)")
    st.caption("Conference / Study / Tourism — formal embassy format: Applicant → Date → Embassy → Subject → Body → Closing.")

    with st.form("visa_form", clear_on_submit=False):
        st.markdown("**Applicant**")
        v_name = st.text_input("Full Name *", key="v_name")
        v_email = st.text_input("Email *", key="v_email")
        v_phone = st.text_input("Phone", placeholder="+91-XXXXXXXXXX")
        v_addr = st.text_input("Address Line")
        v_citypin = st.text_input("City/State/PIN")

        st.markdown("**Embassy**")
        v_emb = st.text_input("Embassy Name", value="Embassy of the Hellenic Republic")
        v_emb_addr = st.text_input("Embassy Address", value="EP-32, Dr. S. Radhakrishnan Marg, Chanakyapuri, New Delhi, 110021")
        v_type = st.text_input("Visa Type", value="Schengen short-stay (C)")
        v_country = st.text_input("Country", value="Greece")

        st.markdown("**Trip**")
        v_purpose = st.text_area("Purpose (one line) *", placeholder="Attend and present a paper at INTERSPEECH 2024")
        v_dates = st.text_input("Stay Dates *", placeholder="30 Aug 2024 – 8 Sep 2024")
        v_dest = st.text_input("Destination City", value="Kos Island")
        v_entry = st.text_input("Entry Plan", placeholder="Initial entry via Frankfurt (layover)")
        v_accom = st.text_input("Accommodation", placeholder="Tropical Sol, Tigaki Beach, Kos 85300, Greece")
        v_sponsor = st.text_input("Sponsorship/Funding", placeholder="Father, Mr. Ajay Kumar Sharma")

        v_itin = st.text_area("Itinerary bullets (one per line, 2–6)", height=90,
                              placeholder="30 Aug: DEL→FRA; 31 Aug: FRA→KGS; 1–5 Sep: Conference at KICC; 7 Sep: KGS→ZRH; 8 Sep: ZRH→DEL")

        st.markdown("**Enclosures**")
        v_encl = st.multiselect(
            "Select attached documents",
            options=[
                "Application form", "Passport copy", "Visa refusal letter", "Sponsorship letter",
                "Bank statement", "No Objection Certificate (college/employer)",
                "Conference/University invitation letter", "Research paper/Acceptance",
                "Insurance", "Flight itinerary", "Hotel booking", "PAN", "AADHAAR", "Student ID"
            ],
            default=["Application form", "Passport copy", "Flight itinerary", "Hotel booking"]
        )

        v_ref = st.checkbox("Acknowledge previous refusal and respond?")
        v_ref_reason = st.text_area("Previous refusal reason (if applicable)", height=80) if v_ref else ""

        v_submit = st.form_submit_button("⚡ Generate Visa Cover Letter Preview", type="primary", use_container_width=True)

    if v_submit:
        form = VisaCoverLetterForm(
            full_name=v_name, email=v_email, phone=v_phone,
            address_line=v_addr, city_state_pin=v_citypin,
            embassy_name=v_emb, embassy_address=v_emb_addr,
            visa_type=v_type, country=v_country,
            purpose=v_purpose, stay_dates=v_dates, destination_city=v_dest,
            entry_plan=v_entry, accommodation=v_accom, sponsorship_by=v_sponsor,
            itinerary_points=[s.strip() for s in v_itin.split("\n") if s.strip()],
            enclosures=v_encl,
            acknowledge_prev_visa_refusal=v_ref,
            previous_refusal_reason=(v_ref_reason or None)
        )

        with st.spinner("Drafting visa cover letter..."):
            v_text = generate_visa_cover_letter_text(form)

        st.success("Preview generated.")
        st.text_area("Visa Cover Letter Preview (watermarked)", v_text, height=320)

        fmt, use_latex = _format_selector()

        if use_latex:
            try:
                v_preview = render_visa_cover_letter_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, v_text, watermarked=True)
                _download_button(
                    v_preview,
                    f"{form.full_name.replace(' ','_')}_VisaCover_PREVIEW.pdf",
                    label="⬇️ Download Watermarked Preview (PDF)",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF build error: {e}")
            st.link_button("Pay ₹349 to unlock Visa Cover Letter (LaTeX PDF)",
                           url=links["VISA_COVER_LETTER_LATEX"], use_container_width=True)

            if _verify_ui("Visa Cover Letter (LaTeX)"):
                try:
                    v_final = render_visa_cover_letter_latex_pdf(TEMPLATES_DIR, DATA_DIR, form, v_text, watermarked=False)
                    _download_button(
                        v_final,
                        f"{form.full_name.replace(' ','_')}_VisaCoverLetter.pdf",
                        label="⬇️ Download Final (PDF)",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"PDF build error: {e}")
        else:
            v_preview = render_visa_cover_letter_docx(TEMPLATES_DIR, DATA_DIR, form, v_text, watermarked=True)
            _download_button(
                v_preview,
                f"{form.full_name.replace(' ','_')}_VisaCover_PREVIEW.docx",
                label="⬇️ Download Watermarked Preview (DOCX)",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.link_button("Pay ₹299 to unlock Visa Cover Letter (DOCX)",
                           url=links["VISA_COVER_LETTER"], use_container_width=True)

            if _verify_ui("Visa Cover Letter (DOCX)"):
                v_final = render_visa_cover_letter_docx(TEMPLATES_DIR, DATA_DIR, form, v_text, watermarked=False)
                _download_button(
                    v_final,
                    f"{form.full_name.replace(' ','_')}_VisaCoverLetter.docx",
                    label="⬇️ Download Final (DOCX)",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

st.divider()
st.caption("© 2025 CVSarthi — Files auto-delete in 24h. We are not a visa advisory; review before submission.")
