"""
Generate messages from templates and YAML data, optionally refined by an LLM.
"""
from pathlib import Path
import os
import yaml
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

# OpenAI SDK (>=1.x). Import protetto per non rompere se non installato.
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

CHANNEL_TPL = {
    "email": "email.j2",
    "linkedin": "linkedin.j2",
    "telegram": "telegram.j2",
    "instagram": "instagram_dm.j2",
}

def _render_template(channel: str, template_path: Path, context: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(template_path)))
    template = env.get_template(CHANNEL_TPL[channel])
    return template.render(**context)

def _llm_refine(draft: str, channel: str, model: str, temperature: float) -> str:
    """
    Refine the draft with an LLM (concise US business tone, 1 CTA).
    """
    if OpenAI is None:
        raise RuntimeError("openai package not available. Install it and retry.")
    client = OpenAI()

    system = (
        "You refine outreach copy. Keep it concise, US business tone, "
        "one clear CTA, and adapt to the channel etiquette."
    )
    user = (
        f"Channel: {channel}\n"
        "Refine the following outreach draft. Keep key details. Improve clarity.\n"
        "---\n"
        f"{draft}\n"
        "---\n"
        "Return only the improved message."
    )

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()

def generate(
    channel: str,
    icp_path: Path,
    offer_path: Path,
    out_dir: Path,
    use_llm: bool = False,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> None:
    """
    Main entry: render with Jinja2; optionally refine with LLM.
    """
    channel = channel.lower().strip()
    if channel not in CHANNEL_TPL:
        raise ValueError(f"Unsupported channel '{channel}'. Use one of: {', '.join(CHANNEL_TPL)}")

    # carica .env per OPENAI_API_KEY (se presente)
    load_dotenv()

    base_path = Path(__file__).resolve().parent
    template_path = base_path / "templates"

    with icp_path.open("r", encoding="utf-8") as f:
        icp = yaml.safe_load(f) or {}
    with offer_path.open("r", encoding="utf-8") as f:
        offer = yaml.safe_load(f) or {}

    context = {
        "name": icp.get("name", "there"),
        "pain_points": icp.get("pain_points", []),
        "offer": offer.get("offer", "our solution"),
        "benefits": offer.get("benefits", []),
    }

    # 1) Draft via template (offline)
    draft = _render_template(channel, template_path, context)

    # 2) AI refinement (se richiesto)
    if use_llm:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set. Put it in a .env file.")
        draft = _llm_refine(draft, channel, model, temperature)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{channel}.txt"
    out_file.write_text(draft, encoding="utf-8")
    print(f"✅ {channel.capitalize()} draft generated at {out_file} (LLM={'on' if use_llm else 'off'})")
