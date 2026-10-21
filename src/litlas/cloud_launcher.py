"""Launch Litlas locally using the PostgreSQL backend."""

import os
import subprocess
import tomllib
from pathlib import Path

from litlas.processing.paths import PROJECT_ROOT


def main():
    secrets_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"

    with secrets_path.open("rb") as file:
        secrets = tomllib.load(file)

    env = os.environ.copy()
    env["DATABASE_URL"] = secrets["DATABASE_URL"]
    env["LITLAS_DB_BACKEND"] = "postgres"

    subprocess.run(
        ["litlas"],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )