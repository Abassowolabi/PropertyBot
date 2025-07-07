import argparse
import subprocess

def run_module(module_name):
    subprocess.run(["python", "-m", f"scrapers.{module_name}"], check=True)

def run_all():
    # REDACTED: Add all scrapers here
    run_module("SCRAPER_1")
    run_module("SCRAPER_2")
    run_module("SCRAPER_3")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PropertyBot demo scrapers via modules.")
    parser.add_argument(
        "script",
        choices=["scraper1", "scraper2", "scraper3", "all"],
        help="Which scraper to run"
    )

    args = parser.parse_args()

    if args.script == "scraper1":
        run_module("SCRAPER_1")
    elif args.script == "scraper2":
        run_module("SCRAPER_2")
    elif args.script == "scraper3":
        run_module("SCRAPER_3")
    elif args.script == "all":
        run_all()
