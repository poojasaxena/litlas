import argparse
import subprocess
import sys
from pathlib import Path
from importlib.metadata import version


def main():
    parser = argparse.ArgumentParser(
        prog="litlas",
        description="Litlas — explore the world through literature."
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Litlas {version('litlas')}"
    )

    parser.parse_args()

    app_path = Path(__file__).resolve().parent / "app.py"

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        check=True,
    )


if __name__ == "__main__":
    main()