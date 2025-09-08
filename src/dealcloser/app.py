# src/dealcloser/app.py
from __future__ import annotations

import os
import logging
from typing import Dict, Any

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# --- ENV loading robusto (funziona anche se avvii fuori dalla root) ---
dotenv_path = find_dotenv(usecwd=True) or ".env"
load_dotenv(dotenv_path=dotenv_path)

# --- Flask app ---
# Con templates/ in src/dealcloser/templates (accanto a questo file) non serve indicare template_folder
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "dev-secret")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# --- OpenAI client ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Non blocchiamo l'import dell'app (per /healthz), ma avviseremo a runtime
    app.logger.warning("OPENAI_API_KEY non impostata: la generazione AI fallirà.")
client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.DEBUG)


# ---------------------- Routes ----------------------
@app.route("/", methods=["GET"])
def home():
    """
    Mostra il form. 'result' None all'avvio.
    """
    return render_template("index.html", result=None)


@app.route("/generate", methods=["POST"])
def generate_view():
    """
    Legge i campi del form, costruisce il prompt in base al canale,
    chiama OpenAI e renderizza il risultato su index.html
    """
    # --- Pre-check chiave ---
    if not OPENAI_API_KEY:
        flash("Manca OPENAI_API_KEY nel tuo .env. Impostala e riprova.")
        return redirect(url_for("home"))

    # --- Lettura campi base ---
    channel = (request.form.get("channel") or "email").strip().lower()
    name = (request.form.get("name") or "").strip()
    pain_points = (request.form.get("pain_points") or "").strip()
    offer = (request.form.get("offer") or "").strip()
    benefits = (request.form.get("benefits") or "").strip()

    # --- Nuovi campi per DM / Telegram / Instagram / WhatsApp ---
    handle = (request.form.get("handle") or "").strip()            # @username o url
    objective = (request.form.get("objective") or "").strip()      # es. "collaborazione", "demo", "call"
    use_emojis = bool(request.form.get("use_emojis"))
    use_linebreaks = bool(request.form.get("use_linebreaks"))

    # --- Regole specifiche per canale ---
    channel_rules: Dict[str, Dict[str, str]] = {
        "email": {
            "style": "tono professionale, soggetto chiaro, paragrafi brevi",
            "length": "max 130 parole",
            "cta": "chiudi con una call-to-action chiara (es. 'Posso mostrarti una demo di 10 minuti?')",
        },
        "whatsapp": {
            "style": "conversazionale, diretto, evita muri di testo",
            "length": "max 6-8 righe",
            "cta": "chiedi conferma rapida (sì/no)",
        },
        "telegram": {
            "style": "conciso, amichevole, evita formattazioni troppo complesse",
            "length": "max 8-10 righe",
            "cta": "invita a una breve call o reply veloce",
        },
        "instagram": {
            "style": "tono umano, prima riga forte, 1-2 emoji rilevanti",
            "length": "DM breve (max 500 caratteri)",
            "cta": "chiedi un semplice 'ti va?' o 'posso mandarti 2 righe?'",
        },
        "dm": {
            "style": "neutro per DM su piattaforme varie",
            "length": "breve e leggibile su mobile",
            "cta": "domanda a risposta facile",
        },
    }
    rules = channel_rules.get(channel, channel_rules["dm"])

    # --- Helper formattazione ---
    lb = "\n" if use_linebreaks else " "
    emoji_hint = (
        "Puoi usare 1-2 emoji pertinenti (non forzate)."
        if use_emojis
        else "Non usare emoji."
    )

    # Normalizzazione handle (soft)
    if handle and not handle.startswith("@") and "instagram.com" not in handle.lower():
        handle = "@" + handle.lstrip("@")

    # Obiettivo di default soft
    if channel in ("telegram", "instagram", "whatsapp", "dm") and not objective:
        objective = "aprire una breve conversazione e fissare una micro-call"

    handle_hint = f"Destinatario/Profilo: {handle}." if handle else "Destinatario/Profilo: non specificato."

    # --- Prompt ---
    prompt = (
        f"Sei un copywriter. Genera un messaggio per il canale fallo sempre in inglese qualsiasi cosa scrivi, sempre in inglese: {channel}.{lb}"
        f"{handle_hint}{lb}"
        f"Obiettivo: {objective or 'non specificato'}.{lb}"
        f"Persona destinataria: {name or 'non specificata'}.{lb}"
        f"Dolori: {pain_points or 'non specificati'}.{lb}"
        f"Offerta: {offer or 'non specificata'}.{lb}"
        f"Benefici: {benefits or 'non specificati'}.{lb}{lb}"
        f"Regole di stile: {rules['style']}; {rules['length']}; {rules['cta']}. {emoji_hint}{lb}"
        f"Formattazione: usa righe corte pensate per smartphone. Evita frasi lunghe. Evita gergo eccessivo.{lb}"
        f"Output: fornisci SOLO il testo finale da inviare, senza preamboli o titoli."
        f" Se canale=instagram, inizia con un gancio forte (prima riga)."
        f" Se canale=telegram/whatsapp, rendi semplice rispondere."
        f"{lb}{lb}"
        f"Quando utile, separa con a-capo per leggibilità su mobile."
    )

    app.logger.debug(
        f"[GEN] channel={channel} name={name!r} handle={handle!r} "
        f"use_emojis={use_emojis} use_linebreaks={use_linebreaks}"
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": "Sei un assistente di scrittura conciso e pratico."},
                {"role": "user", "content": prompt},
            ],
        )
        ai_text = (resp.choices[0].message.content or "").strip()
        app.logger.debug(f"[GEN] AI OUTPUT (inizio): {ai_text[:200]}")
    except Exception as e:
        app.logger.exception("Errore durante la generazione AI")
        flash(f"Errore durante la generazione: {e}")
        return redirect(url_for("home"))

    # --- Render con i campi utili per riempire di nuovo il form (quality-of-life) ---
    ctx: Dict[str, Any] = {
        "result": ai_text,
        "channel": channel,
        "name": name,
        "pain_points": pain_points,
        "offer": offer,
        "benefits": benefits,
        "handle": handle,
        "objective": objective,
        "use_emojis": use_emojis,
        "use_linebreaks": use_linebreaks,
    }
    return render_template("index.html", **ctx)


@app.route("/healthz", methods=["GET"])
def healthz():
    """
    Sonda semplice per verificare che l'app sia su.
    """
    return {"ok": True, "has_key": bool(OPENAI_API_KEY)}, 200


# --- Entrypoint locale ---
if __name__ == "__main__":
    # Avvio comodo con: PYTHONPATH=src python -m dealcloser.app
    # oppure: export PYTHONPATH=src; export FLASK_APP=dealcloser.app; flask run --debug
    app.run(host="0.0.0.0", port=5000, debug=True)
