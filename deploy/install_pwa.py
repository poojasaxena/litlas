"""Install Litlas's manifest and icons in the self-hosted Streamlit frontend."""

import json
from pathlib import Path
from shutil import copyfile

import streamlit


def main() -> None:
    frontend = Path(streamlit.__file__).resolve().parent / "static"
    index = frontend / "index.html"
    html = index.read_text(encoding="utf-8")
    head = "<head>"
    if html.count(head) != 1 or 'rel="manifest"' in html:
        raise RuntimeError("The Streamlit frontend changed. Check the manifest link.")

    project = Path(__file__).resolve().parents[1]
    artwork = project / "data" / "assets" / "illustrations"
    manifest_path = Path(__file__).with_name("litlas.webmanifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for icon in manifest["icons"]:
        filename = icon["src"].removeprefix("/")
        copyfile(artwork / filename, frontend / filename)

    copyfile(manifest_path, frontend / manifest_path.name)
    html = html.replace(
        head, f'{head}\n    <link rel="manifest" href="/{manifest_path.name}" />', 1
    )
    index.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
