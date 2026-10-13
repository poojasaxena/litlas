"""Launch Streamlit without importing the app before its runner starts."""
from pathlib import Path
import sys

def main():
    from streamlit.web import cli as stcli
    app_file = Path(__file__).with_name('app.py')
    sys.argv = ['streamlit', 'run', str(app_file), '--server.headless', 'true']
    raise SystemExit(stcli.main())
