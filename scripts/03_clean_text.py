import json
import re
import unicodedata
from pathlib import Path

DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
EXTRACTED_FOLDER = DATA_FOLDER / "extracted"
HEADERS_FILE = DATA_FOLDER / "headers_approved.json"
CLEANED_FOLDER = DATA_FOLDER / "cleaned"


LINES_TO_CHECK = 4

def normalize_unicode(text):
    return unicodedata.normalize("NFKC", text)


def replace_numbers(line):
    line = line.strip()
    return re.sub(r"\d+", "NUMBER", line)


def build_vocabulary():
    all_text = ""
    for file in EXTRACTED_FOLDER.glob("*.txt"):
        with open(file, encoding="utf-8") as f:
            all_text += f.read() + " "

    all_text = normalize_unicode(all_text).lower()
    words = re.findall(r"\w+", all_text)
    return set(words)


def remove_headers(page, header_keys):
    if len(header_keys) == 0:
        return page

    lines = []
    for line in page.splitlines():
        if line.strip() != "":
            lines.append(line)

    kept_lines = []
    for i in range(len(lines)):
        line = lines[i]
        is_top = i < LINES_TO_CHECK
        is_bottom = i >= len(lines) - LINES_TO_CHECK

        if (is_top or is_bottom) and replace_numbers(line) in header_keys:
            continue

        kept_lines.append(line)

    return "\n".join(kept_lines)


def join_word(match):
    word = match.group(1) + match.group(2)

    if word.lower() in VOCABULARY:
        return word

    return match.group(0)


def fix_hyphenation(page):
    return re.sub(r"(\w+)-\n(\w+)", join_word, page)


def remove_noise(page):
    page = re.sub(r"[\ue000-\uf8ff]", "", page)

    kept_lines = []
    for line in page.splitlines():
        if re.search(r"[A-Za-z]", line):
            kept_lines.append(line)

    return "\n".join(kept_lines)

with open(HEADERS_FILE, encoding="utf-8") as f:
    approved_headers = json.load(f)

VOCABULARY = build_vocabulary()

for file in sorted(EXTRACTED_FOLDER.glob("*.json")):
    with open(file, encoding="utf-8") as f:
        document = json.load(f)
    doc_id = document["doc_id"]

    if doc_id in approved_headers:
        header_keys = set(approved_headers[doc_id])
    else:
        header_keys = set()

    cleaned_pages = []
    for page in document["pages"]:
        page = normalize_unicode(page)
        page = remove_headers(page, header_keys)
        page = fix_hyphenation(page)
        page = remove_noise(page)
        cleaned_pages.append(page)

    output = {"doc_id": doc_id, "pages": cleaned_pages}
    with open(CLEANED_FOLDER / f"{doc_id}.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    text = ""
    page_number = 1
    for page in cleaned_pages:
        text += f"---------- страница {page_number} ----------\n{page}\n\n"
        page_number += 1

    with open(CLEANED_FOLDER / f"{doc_id}.txt", "w", encoding="utf-8") as f:
        f.write(text)