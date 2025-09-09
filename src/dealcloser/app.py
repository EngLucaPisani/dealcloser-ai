from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import os

# --- Setup base / ENV ---
load_dotenv()  # carica .env in locale; su Render userai le Environment Variables

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")

# Client OpenAI compatibile con sk-proj + org + project
client = (
    OpenAI(
        api_key=OPENAI_API_KEY,
        organization=OPENAI_ORG_ID,
        project=OPENAI_PROJECT_ID,
    )
    if OPENAI_API_KEY
    else None
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "CHANGE_ME"

BASE_PATH = Path(__file__).resolve().parent
TEMPLATES_PATH = BASE_PATH / "templates"
OUT_PATH = BASE_PATH.parent.parent / "out"
OUT_PATH.mkdir(parents=True, exist_ok=True)

# Jinja2 per modalità "template"
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_PATH)),
    autoescape=select_autoescape(["html", "xml", "j2"])
)

# --- Render con Jinja2 (senza AI) ---
def render_email_template(recipient_name, company, pain_points, offer, benefits, tone, sender_name):
    template = env.get_template("email.j2")
    pp = [p.strip() for p in pain_points.split("\n") if p.strip()]
    bn = [b.strip() for b in benefits.split("\n") if b.strip()]
    return template.render(
        recipient_name=(recipient_name or "there").strip(),
        company=(company or "your company").strip(),
        pain_points=pp,
        offer=(offer or "AI-powered outreach system to remove busywork").strip(),
        benefits=bn,
        tone=(tone or "professional").strip(),
        sender_name=(sender_name or "Luca").strip(),
    )

# --- Render con GPT (AI) ---
def render_email_gpt(recipient_name, company, pain_points, offer, benefits, tone, sender_name):
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env")

    pp = [p.strip() for p in pain_points.split("\n") if p.strip()]
    bn = [b.strip() for b in benefits.split("\n") if b.strip()]

    system = (
        "You are a senior sales copywriter who writes crisp, clean outreach emails in English. "
        "Keep it human, specific, and under 800 words. Use a clear subject line. "
        "Tone options: professional, friendly, concise, persuasive. "
        "Length: 800-850 words."
    )
    user = f"""
Write an outreach email in English.

Context:
- Recipient name: {recipient_name or 'there'}
- Company: {company or 'your company'}
- Pain points (bulleted): - Expand each pain point into 2–3 lines of explanation. {pp if pp else ['Manual busywork', 'Low reply rates', 'Messy CRM handoff']}
- Offer (one-liner): {offer or 'AI-powered outreach that drafts tailored emails and syncs to CRM'}
- Expected outcomes/benefits: {bn if bn else ['Save 10+ hours/week', '+15–30% reply rate', 'Clean CRM handoff']}
- Tone: {tone or 'professional'}
- Sender name: {sender_name or 'Luca'}

Constraints:
- Subject line + body
- No buzzwords, no fluff
- Make it actionable; propose a 15-min call this week
"""

    
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content.strip()

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", has_api=bool(OPENAI_API_KEY))

@app.route("/generate", methods=["POST"])
def generate():
    try:
        mode = request.form.get("mode", "template")  # "template" | "gpt"
        recipient_name = request.form.get("recipient_name", "").strip()
        company = request.form.get("company", "").strip()
        pain_points = request.form.get("pain_points", "").strip()
        offer = request.form.get("offer", "").strip()
        benefits = request.form.get("benefits", "").strip()
        tone = request.form.get("tone", "professional").strip()
        sender_name = request.form.get("sender_name", "Luca").strip()  # <-- aggiunta necessaria

        if not offer or not benefits:
            flash("Please provide at least the Offer and the Benefits.", "warning")
            return redirect(url_for("index"))

        if mode == "gpt":
            email_text = render_email_gpt(
                recipient_name, company, pain_points, offer, benefits, tone, sender_name
            )
        else:
            email_text = render_email_template(
                recipient_name, company, pain_points, offer, benefits, tone, sender_name
            )

        filename = f"dealcloser_email_{mode}_{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.txt"
        (OUT_PATH / filename).write_text(email_text, encoding="utf-8")
        return render_template("result.html", email_text=email_text, filename=filename, mode=mode)
    except Exception as e:
        flash(f"Unexpected error: {e}", "danger")
        return redirect(url_for("index"))

@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    return send_from_directory(str(OUT_PATH), filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
