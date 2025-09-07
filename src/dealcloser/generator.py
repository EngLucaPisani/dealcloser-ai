"""
Generate messages from templates and YAML data.
"""
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader


def generate():
    # .../src/dealcloser
    base_path = Path(__file__).resolve().parent
    data_path = base_path / "data"
    template_path = base_path / "templates"

    # Load YAML inputs
    with open(data_path / "icp_example.yaml", "r", encoding="utf-8") as f:
        icp = yaml.safe_load(f) or {}
    with open(data_path / "offer_example.yaml", "r", encoding="utf-8") as f:
        offer = yaml.safe_load(f) or {}

    # Prepare Jinja2
    env = Environment(loader=FileSystemLoader(str(template_path)))
    template = env.get_template("email.j2")

    # Safe context
    context = {
        "name": icp.get("name", "there"),
        "pain_points": icp.get("pain_points", []),
        "offer": offer.get("offer", "our solution"),
        "benefits": offer.get("benefits", []),
    }

    # Render
    output = template.render(**context)

    # Write to out/email.txt
    out_dir = base_path.parent.parent / "out"  # .../out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "email.txt"
    out_path.write_text(output, encoding="utf-8")
    print(f"✅ Email generated at {out_path}")
