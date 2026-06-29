"""One-time Google Sheets OAuth — run this once in the terminal to create token.json.

Usage:
    python3 scripts/auth_sheets.py

After completing the browser flow, token.json is saved at the project root.
The Flask server then reuses this token automatically on every approve.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from src.config import PROJECT_ROOT

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
TOKEN_PATH = PROJECT_ROOT / "token.json"


def main():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        print("token.json already valid — no auth needed.")
        return

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        print("Token refreshed.")
    else:
        client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("Client_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("Client_Secret")
        if not client_id or not client_secret:
            print("ERROR: Set GOOGLE_CLIENT_ID / Client_ID and GOOGLE_CLIENT_SECRET / Client_Secret in .env")
            sys.exit(1)

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }

        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        # Opens browser — complete sign-in, then paste the code back here
        creds = flow.run_local_server(port=8090)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    print(f"token.json saved to: {TOKEN_PATH}")
    print("Sheets export will now work automatically on every approval.")


if __name__ == "__main__":
    main()
