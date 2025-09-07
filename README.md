# DealCloser AI

DealCloser is a CLI tool that generates personalized outreach messages (Email, LinkedIn, Telegram, Instagram) using **YAML data** + **Jinja2 templates**.

## Features
- CLI built with [Typer](https://typer.tiangolo.com/)
- Reads Ideal Customer Profile (ICP) + Offer from YAML files
- Generates ready-to-send outreach drafts
- Supports multiple channels (email, LinkedIn, IG, Telegram)
- Outputs stored in the `out/` folder

## Quick Start
```bash
git clone https://github.com/EngLucaPisani/dealcloser-ai.git
cd dealcloser-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
dealcloser
