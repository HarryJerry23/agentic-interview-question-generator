"""Google Sheets Writer — writes CuratedOutput to a Google Sheet using OAuth."""

import os
import json
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from src.models import CuratedOutput, QualityReport
from src.config import PROJECT_ROOT
from datetime import datetime


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

FEEDBACK_OPTIONS = ["Good", "Remove", "Wrong Topic", "Too Easy", "Too Hard"]
TOKEN_PATH = PROJECT_ROOT / "token.json"


def _get_gspread_client() -> gspread.Client:
    """Authenticate with Google Sheets API using OAuth (client ID + secret from .env)."""
    creds = None

    # Check for cached token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # If no valid creds, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("Client_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("Client_Secret")

            if not client_id or not client_secret:
                raise ValueError(
                    "Google OAuth credentials must be set in .env "
                    "(GOOGLE_CLIENT_ID / Client_ID and GOOGLE_CLIENT_SECRET / Client_Secret)"
                )

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
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return gspread.authorize(creds)


def write_to_sheets(
    output: CuratedOutput,
    report: QualityReport,
    session_name: str,
    run_id: str,
) -> str:
    """Write CuratedOutput to a new Google Sheet. Returns the Sheet URL."""
    client = _get_gspread_client()

    # Create new spreadsheet
    title = f"InterviewQ - {session_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    spreadsheet = client.create(title)

    # --- Tab 1: QuestionDetails ---
    ws_qd = spreadsheet.sheet1
    ws_qd.update_title("QuestionDetails")

    qd_headers = [
        "question_id", "category", "content", "topic", "sub_topic",
        "difficulty", "asked_in_company", "source", "kp_label",
        "expected_answer", "feedback",
    ]
    qd_rows = [qd_headers]
    for q in output.question_details:
        qd_rows.append([
            q.question_id, q.category, q.content, q.topic,
            q.sub_topic or "", q.difficulty or "", q.asked_in_company or "",
            q.source, q.kp_label or "", q.expected_answer or "", "",
        ])

    if qd_rows:
        ws_qd.update(range_name="A1", values=qd_rows)

    # Add feedback dropdown validation
    _add_dropdown_validation(ws_qd, col_index=11, row_count=len(output.question_details))

    # --- Tab 2: CodingQuestion (only if coding questions exist) ---
    if output.coding_questions:
        ws_cq = spreadsheet.add_worksheet(
            title="CodingQuestion",
            rows=len(output.coding_questions) + 1,
            cols=12,
        )

        cq_headers = [
            "id", "category", "title", "content", "topic", "sub_topic",
            "difficulty", "language", "asked_in_company", "source",
            "expected_answer", "feedback",
        ]
        cq_rows = [cq_headers]
        for q in output.coding_questions:
            cq_rows.append([
                q.id, q.category, q.title, q.content[:1000], q.topic,
                q.sub_topic or "", q.difficulty or "", q.language,
                q.asked_in_company or "", q.source,
                q.expected_answer or "", "",
            ])

        ws_cq.update(range_name="A1", values=cq_rows)
        _add_dropdown_validation(ws_cq, col_index=12, row_count=len(output.coding_questions))

    # --- Tab 3: CodeSnippet (only if snippets exist) ---
    if output.code_snippets:
        ws_cs = spreadsheet.add_worksheet(
            title="CodeSnippet",
            rows=len(output.code_snippets) + 1,
            cols=3,
        )

        cs_headers = ["code_id", "code_content", "Language"]
        cs_rows = [cs_headers]
        for s in output.code_snippets:
            cs_rows.append([s.code_id, s.code_content[:1000], s.language])

        ws_cs.update(range_name="A1", values=cs_rows)

    return spreadsheet.url


def _add_dropdown_validation(worksheet, col_index: int, row_count: int):
    """Add data validation dropdown to the feedback column."""
    if row_count == 0:
        return
    try:
        from gspread.utils import rowcol_to_a1
        start = rowcol_to_a1(2, col_index)
        end = rowcol_to_a1(row_count + 1, col_index)
        rule = gspread.worksheet.DataValidationRule(
            gspread.worksheet.BooleanCondition("ONE_OF_LIST", FEEDBACK_OPTIONS),
            showCustomUi=True,
        )
        worksheet.set_data_validation(f"{start}:{end}", rule)
    except Exception:
        pass
