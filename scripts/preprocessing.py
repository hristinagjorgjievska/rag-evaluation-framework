import unicodedata
import re
import pdfplumber
import pandas as pd
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
RAW_FOLDER = ROOT / "data" / "raw"
PROCESSED_FOLDER = ROOT / "data" / "processed"
corpus_manifest = ROOT / "data" / "corpus_manifest.csv"

df = pd.read_csv(corpus_manifest, dtype=str)

MIN_LINE_LENGTH = 2
MAX_HF_LEN = 120
HF_RATIO = 0.3
HF_MIN_PAGES = 5
NAV_RATIO = 0.4

PAGE_NUMBER_RE = re.compile(r"^(page|стр\.?|страна)?\s*\d{1,4}(\s*/\s*\d{1,4})?$", re.I)
SUPERSCRIPT_RE = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]")
LINK_RE = re.compile(r"\((?:/|https?://)[^)]*\)?", re.I)

def find_documents():
    rows = []
    for row in df.itertuples():
        row_root = ROOT / "data" / "raw" / row.filename
        rows.append(row_root)
    return rows

def extract_pages(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as doc:
        for page in doc.pages:
            text = page.extract_text(x_tolerance=2)
            if text:
                pages.append(text)
            else:
                pages.append("")
    return pages

def build_corpus():
    corpus = {}
    for doc in find_documents():
        corpus[doc.name] = extract_pages(doc)
    return corpus

def normalize_page(text):
    text = SUPERSCRIPT_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    return text

def strip_links(line):
    stripped = LINK_RE.sub("", line)
    stripped = stripped.strip()
    stripped = re.sub(r"\s{2,}", " ", stripped)

    is_navigation = len(stripped) < len(line) * NAV_RATIO
    return stripped, is_navigation

def find_headers_and_footers(pages):
    n = len(pages)

    if n < HF_MIN_PAGES:
        return set()

    counts = Counter()

    for page in pages:
        lines_on_page = set()
        for line in page.splitlines():
            line = line.strip()
            if line:
                lines_on_page.add(line)

        for line in lines_on_page:
            counts[line] = counts[line] + 1

    threshold = max(2, int(HF_RATIO * n))

    headers = set()
    for line in counts:
        if counts[line] >= threshold and len(line) <= MAX_HF_LEN:
            headers.add(line)

    return headers

def clean_pages(text, headers):
    kept = []
    for line in text.splitlines():
        line = line.strip()

        if len(line) < MIN_LINE_LENGTH:
            continue

        if line in headers:
            continue

        if PAGE_NUMBER_RE.match(line):
            continue

        line, is_navigation = strip_links(line)
        if is_navigation:
            continue

        if len(line) < MIN_LINE_LENGTH:
            continue

        kept.append(line)

    cleaned_text = "\n".join(kept)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()
    return cleaned_text

def clean_document(pdf_path):
    raw_pages = extract_pages(pdf_path)

    normalized_pages = []
    for page in raw_pages:
        normalized_pages.append(normalize_page(page))

    headers = find_headers_and_footers(normalized_pages)

    cleaned_pages = []
    for page in normalized_pages:
        cleaned_pages.append(clean_pages(page, headers))

    return cleaned_pages

def save_processed_documents():

    for row in df.itertuples():
        pdf_path = RAW_FOLDER / row.filename

        cleaned_pages = clean_document(pdf_path)

        full_text = "\n\n".join(cleaned_pages)

        processed_path = PROCESSED_FOLDER / (row.doc_id + ".txt")
        processed_path.write_text(full_text, encoding="UTF-8")

        print(f"{row.doc_id} {len(cleaned_pages):>3} pages and {len(full_text):>7} characters " 
              f"{row.filename}")

save_processed_documents()