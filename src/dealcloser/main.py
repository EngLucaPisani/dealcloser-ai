"""
DealCloser – single-command entrypoint.
"""

def main() -> None:
    # Import inside to avoid import-time side effects
    from dealcloser import generator
    generator.generate()

if __name__ == "__main__":
    main()

