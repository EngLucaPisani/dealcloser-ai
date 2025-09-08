"""
DealCloser — message generation from templates & YAML, with optional LLM refinement.

This module provides two entry points:
- render_message(...): returns the generated text (used by the Flask UI)
- generate(...): reads YAML, writes out/<channel>.txt (used by the CLI)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import os
import yaml
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

# OpenAI SDK (>=1.x). Import protetto per evitare errori se non installato.
try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


# ----------------------------------
# Config & helpers
# ----------------------------------

CHANNEL_TPL: Dict[str, str] = {
    "email": "email.j2",
    "linkedin": "linkedin.j2",
    "telegram": "telegram.j2",
    "instagram": "instagram_dm.j2",
}


def _project_root() -> Path:
    """
    Returns the project root directory:
    <repo_root> / src / dealcloser / generator.py  -> parents[2] = <repo_root>
    """
    return Path(__file__).resolve().parents[2]


def _load_env() -> None:
    """
    Load .env from the project root using an absolute path so it also works
    when the app is launched via Flask (different working dir / autoreload).
    """
    env_path = _project_root() / ".env"
    # override=False: non sovrascrive variabili già presenti nell'ambiente
    load_dotenv(dotenv_path=str(env_path), override=False)


def _template_env() -> Environment:
    """
    Prepare a Jinja2 environment pointing to src/dealcloser/templates.
    """
    base_path = Path(__file__).resolve().parent
    template_path = base_path / "templates"
    return Environment(loader=FileSystemLoader(str(template_path)))


def _render_template(channel: str, context: Dict[str, Any]) -> str:
    """
    Render the appropriate template for the channel with the provided context.
    """
    env = _template_env()
    tpl_name = CHANNEL_TPL[channel]
    template = env.get_template(tpl_name)
    return template.render(**context)


def _llm_refine(draft: str, channel: str, model: str, temperature: float) -> str:
    """
    Refine a draft using an OpenAI chat model (concise US business tone, 1 CTA).
    """
    if OpenAI is None:
        raise RuntimeError("openai package not available. Install it and retry.")
    client = OpenAI()

    system = (
        "You refine outreach copy. Keep it concise, use a US business tone, "
        "include one clear CTA, and follow the etiquette of the specified channel."
    )
    user = (
        f"Channel: {channel}\n"
        "Refine the following outreach draft. Keep key details. Improve clarity and flow.\n"
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


# ----------------------------------
# Public API for the Flask UI
# ----------------------------------

def render_message(
    channel: str,
    name: str,
    pain_points: List[str],
    offer: str,
    benefits: List[str],
    use_llm: bool = False,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> str:
    """
    Render a message directly from form fields (no YAML files).
    Returns the final text (optionally refined by LLM).
    """
    channel = channel.lower().strip()
    if channel not in CHANNEL_TPL:
        raise ValueError(f"Unsupported channel '{channel}'. Use one of: {', '.join(CHANNEL_TPL)}")

    # Make sure .env is loaded even when called from Flask
    _load_env()

    context: Dict[str, Any] = {
        "name": name or "there",
        "pain_points": pain_points or [],
        "offer": offer or "our solution",
        "benefits": benefits or [],
    }

    # 1) Draft via template (offline)
    draft = _render_template(channel, context)

    # 2) Optional LLM refinement
    if use_llm:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set. Put it in a .env file at project root.")
        draft = _llm_refine(draft, channel, model, temperature)

    return draft


# ----------------------------------
# Public API for the CLI
# ----------------------------------

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
    CLI entrypoint:
    - Reads ICP & Offer from YAML files
    - Renders the message from a Jinja2 template
    - Optionally refines with the LLM
    - Writes the result to out/<channel>.txt
    """
    channel = channel.lower().strip()
    if channel not in CHANNEL_TPL:
        raise ValueError(f"Unsupported channel '{channel}'. Use one of: {', '.join(CHANNEL_TPL)}")

    # Ensure .env is available (for --use-llm)
    _load_env()

    # Load YAML data
    with icp_path.open("r", encoding="utf-8") as f:
        icp = yaml.safe_load(f) or {}
    with offer_path.open("r", encoding="utf-8") as f:
        offer = yaml.safe_load(f) or {}

    context: Dict[str, Any] = {
        "name": icp.get("name", "there"),
        "pain_points": icp.get("pain_points", []),
        "offer": offer.get("offer", "our solution"),
        "benefits": offer.get("benefits", []),
    }

    # 1) Draft via template (offline)
    draft = _render_template(channel, context)

    # 2) Optional LLM refinement
    if use_llm:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set. Put it in a .env file at project root.")
        draft = _llm_refine(draft, channel, model, temperature)

    # Write to file
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{channel}.txt"
    out_file.write_text(draft, encoding="utf-8")
    print(f"✅ {channel.capitalize()} draft generated at {out_file} (LLM={'on' if use_llm else 'off'})")
