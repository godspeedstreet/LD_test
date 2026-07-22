"""
Чтение исходной таблицы с блогерами.

Таблица открыта на просмотр по ссылке ("Все, у кого есть ссылка — Читатель"),
поэтому для чтения не нужен ни API-ключ, ни service account — Google Sheets
отдаёт публичные листы как обычный CSV по прямой ссылке экспорта.

Если бы таблицу нужно было ЗАПИСЫВАТЬ (а не только читать), потребовался бы
либо OAuth2, либо service account с доступом Editor — см. README, раздел
"Про доступ к таблице".
"""

import csv
import io
import re
import requests

CSV_EXPORT_URL = "https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=0"

# В таблице попадаются не только чистые ссылки instagram.com/username,
# но и сохранённые заголовки страниц вида
# "ИМЯ (@username) • Instagram photos and videos" — их тоже нужно разобрать.
USERNAME_FROM_URL = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")
USERNAME_FROM_TITLE = re.compile(r"@([A-Za-z0-9_.]+)")


def fetch_raw_csv(spreadsheet_id: str) -> str:
    url = CSV_EXPORT_URL.format(spreadsheet_id=spreadsheet_id)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_username(cell_value: str) -> str | None:
    """Достаёт username из ссылки или из скопированного заголовка страницы."""
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
    """
    Возвращает список уникальных username блогеров из колонки B таблицы.
    Пустые строки (в таблице между записями есть визуальные разрывы) пропускаются.
    """
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


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    import os

    load_dotenv()
    sid = os.getenv("SPREADSHEET_ID") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not sid:
        raise SystemExit("Укажи SPREADSHEET_ID в .env или первым аргументом")
    names = load_blogger_usernames(sid)
    print(f"Найдено блогеров: {len(names)}")
    for n in names:
        print(" -", n)
