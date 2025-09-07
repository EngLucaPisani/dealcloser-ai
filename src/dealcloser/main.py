"""
DealCloser CLI (single-command) with optional AI refinement.
"""
from pathlib import Path
import argparse
from dealcloser import generator

# Defaults
_base = Path(__file__).resolve().parent
DEFAULT_ICP = _base / "data" / "icp_example.yaml"
DEFAULT_OFFER = _base / "data" / "offer_example.yaml"
DEFAULT_OUT = _base.parent.parent / "out"
CHANNELS = ["email", "linkedin", "telegram", "instagram"]

def main() -> None:
    p = argparse.ArgumentParser(description="DealCloser – outreach generator")
    p.add_argument("-c", "--channel", choices=CHANNELS, default="email", help="Channel to generate")
    p.add_argument("--icp", default=str(DEFAULT_ICP), help="Path to ICP YAML")
    p.add_argument("--offer", default=str(DEFAULT_OFFER), help="Path to Offer YAML")
    p.add_argument("--out", dest="outdir", default=str(DEFAULT_OUT), help="Output directory")
    p.add_argument("--all", action="store_true", help="Generate all channels")

    # AI flags
    p.add_argument("--use-llm", action="store_true", help="Use AI to refine the copy")
    p.add_argument("--model", default="gpt-4o-mini", help="OpenAI model id")
    p.add_argument("--temperature", type=float, default=0.7, help="Creativity 0-1")

    args = p.parse_args()

    icp_path = Path(args.icp)
    offer_path = Path(args.offer)
    out_dir = Path(args.outdir)

    def run_one(ch: str):
        generator.generate(
            channel=ch,
            icp_path=icp_path,
            offer_path=offer_path,
            out_dir=out_dir,
            use_llm=args.use_llm,
            model=args.model,
            temperature=args.temperature,
        )

    if args.all:
        for ch in CHANNELS:
            run_one(ch)
        print(f"✅ All drafts generated in {out_dir}")
    else:
        run_one(args.channel)
