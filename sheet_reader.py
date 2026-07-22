import csv
import io
import re
import requests

CSV_EXPORT_URL = "https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=0"

USERNAME_FROM_URL = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")
USERNAME_FROM_TITLE = re.compile(r"@([A-Za-z0-9_.]+)")

def fetch_raw_csv(spreadsheet_id: str) -> str:
    url = CSV_EXPORT_URL.format(spreadsheet_id=spreadsheet_id)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text

def extract_username(cell_value: str) -> str | None:
    if not cell_value:
        return None
    m = USERNAME_FROM_URL.search(cell_value)
    if m:
        return m.group(1).rstrip("/")
    m = USERNAME_FROM_TITLE.search(cell_value)
    if m:
        return m.group(1)
    return None

def load_blogger_usernames(spreadsheet_id: str) -> list[str]:
    raw = fetch_raw_csv(spreadsheet_id)
    reader = csv.reader(io.StringIO(raw))
    usernames = []
    for row in reader:
        if len(row) < 2:
            continue
        username = extract_username(row[1])
        if username and username not in usernames:
            usernames.append(username)
    return usernames
