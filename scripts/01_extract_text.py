import json
import re
from pathlib import Path

import pandas as pd
import pymupdf
from bs4 import BeautifulSoup

DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
RAW_FOLDER = DATA_FOLDER / "raw"
EXTRACTED_FOLDER = DATA_FOLDER / "extracted"


def extract_pdf_document(filename):
    pdf = pymupdf.open(filename)
    pages = []

    for page in pdf:
        text = page.get_text()
        pages.append(text)

    pdf.close()
    return pages


def extract_html_document(filename):
    html = filename.read_text(encoding="utf-8")
    article = BeautifulSoup(html, "html.parser").find("article")

    for tag in article.select("script, style, a.headerlink"):
        tag.decompose()

    for tag in article.find_all(["p", "li", "dt", "dd", "pre", "div", "h1", "h2", "h3", "h4"]):
        tag.insert_after("\n")

    article_text = article.get_text()
    article_text = re.sub(r"\s*\n\s*\n\s*", "\n\n", article_text)
    article_text = article_text.strip()
    return [article_text]


manifest = pd.read_csv(DATA_FOLDER / "corpus_manifest.csv", dtype=str)
for doc in manifest.itertuples():
    file = RAW_FOLDER / doc.filename

    if doc.format == "pdf":
        pages = extract_pdf_document(file)
    else:
        pages = extract_html_document(file)

    output = {"doc_id": doc.doc_id, "pages": pages}

    with open(EXTRACTED_FOLDER / f"{doc.doc_id}.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    text = ""
    page_number = 1
    for page in pages:
        text += f"---------- страница {page_number} ----------\n{page}\n\n"
        page_number += 1

    with open(EXTRACTED_FOLDER / f"{doc.doc_id}.txt", "w", encoding="utf-8") as f:
        f.write(text)

    word_count = 0
    for page in pages:
        word_count += len(page.split())

    print(doc.doc_id, len(pages), "стр.", word_count, "зборови")