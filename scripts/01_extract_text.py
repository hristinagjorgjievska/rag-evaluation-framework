import json
import re
from pathlib import Path

import pandas as pd
import pymupdf
from bs4 import BeautifulSoup

DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"

def extract_pdf_document(path):
    pdf = pymupdf.open(path)
    pages = []

    for page in pdf:
        text = page.get_text()
        pages.append(text)

    pdf.close()
    return pages

def extract_html_document(path):
    article = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").find("article")

    for tag in article.select("script, style, a.headerlink"):
        tag.decompose()

    for tag in article.find_all(["p", "li", "dt", "dd", "pre", "div", "h1", "h2", "h3", "h4"]):
        tag.insert_after("\n")

    return [re.sub(r"\s*\n\s*\n\s*", "\n\n", article.get_text()).strip()]

for doc in pd.read_csv(DATA_FOLDER / "corpus_manifest.csv", dtype=str).itertuples():
    extract = extract_pdf_document if doc.format == "pdf" else extract_html_document

    pages = extract(DATA_FOLDER / "raw" / doc.filename)
    out = {"doc_id": doc.doc_id, "pages": pages}
    (DATA_FOLDER / "extracted" / f"{doc.doc_id}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    text = ""
    for number, page in enumerate(pages, start=1):
        text += f"====== страница {number} ======\n{page}\n\n"
    (DATA_FOLDER / "extracted" / f"{doc.doc_id}.txt").write_text(text, encoding="utf-8")

    print(doc.doc_id, len(pages), "стр.", sum(len(p.split()) for p in pages), "збора")