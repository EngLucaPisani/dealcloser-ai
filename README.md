# DealCloser AI

DealCloser AI is a simple MVP tool that generates **outreach emails in English** for founders and businesses.

## Features
- Web form built with Flask + Jinja2
- Two modes:
  - **Template**: fast, no API required
  - **GPT-powered**: more personalized (requires OpenAI API key)
- Save and download output as `.txt`
- Responsive, lightweight UI

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python src/dealcloser/app.py --host 0.0.0.0 --debug
# open http://127.0.0.1:5000
