# DealCloser AI

DealCloser AI is a **Python CLI tool** that leverages **AI + Jinja2 templates** to generate personalized multi-channel outreach messages (Email, LinkedIn, Telegram, Instagram) from structured **YAML data**.

## Features
- **AI-enhanced copy generation** (ready to integrate with OpenAI or other LLMs)
- CLI built with [Typer](https://typer.tiangolo.com/)
- Reads Ideal Customer Profile (ICP) + Offer from YAML files
- Generates personalized, ready-to-send outreach drafts
- Supports multiple channels (Email, LinkedIn, IG, Telegram)
- Outputs stored in the `out/` folder

## Quick Start
```bash
git clone https://github.com/EngLucaPisani/dealcloser-ai.git
cd dealcloser-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
dealcloser
