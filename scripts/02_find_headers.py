import json
import re
from pathlib import Path

DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
EXTRACTED_FOLDER = DATA_FOLDER / "extracted"

MIN_PAGES = 5
MIN_SHARE = 0.4
LINES_TO_CHECK = 4


def replace_numbers(line):
    line = line.strip()
    return re.sub(r"\d+", "NUMBER", line)


for file in sorted(EXTRACTED_FOLDER.glob("*.json")):
    with open(file, encoding="utf-8") as f:
        document = json.load(f)
    pages = document["pages"]

    line_counts = {}

    for page in pages:
        lines = []
        for line in page.splitlines():
            if line.strip() != "":
                lines.append(line)

        top_and_bottom = lines[:LINES_TO_CHECK] + lines[-LINES_TO_CHECK:]

        lines_on_page = set()
        for line in top_and_bottom:
            lines_on_page.add(replace_numbers(line))

        for line in lines_on_page:
            if line in line_counts:
                line_counts[line] += 1
            else:
                line_counts[line] = 1

    headers = []
    if len(pages) >= MIN_PAGES:
        for line in sorted(line_counts):
            if line_counts[line] >= MIN_SHARE * len(pages):
                headers.append((line, line_counts[line]))

    print(file.stem, headers)