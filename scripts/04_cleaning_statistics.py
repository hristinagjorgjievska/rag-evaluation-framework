import json
from pathlib import Path

import pandas as pd

DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
RESULTS_FOLDER = DATA_FOLDER.parent / "results"

def count_words(folder, doc_id):
    with open(DATA_FOLDER / folder / f"{doc_id}.json", encoding="utf-8") as f:
        document = json.load(f)

    word_count = 0
    for page in document["pages"]:
        word_count += len(page.split())

    return word_count


manifest = pd.read_csv(DATA_FOLDER / "corpus_manifest.csv", dtype=str)

words_before = []
words_after = []
for doc_id in manifest["doc_id"]:
    words_before.append(count_words("extracted", doc_id))
    words_after.append(count_words("cleaned", doc_id))

manifest["пред чистење"] = words_before
manifest["по чистење"] = words_after

table = manifest.groupby("source_type")[["пред чистење", "по чистење"]].sum()
table.loc["ВКУПНО"] = table.sum()

removed = table["пред чистење"] - table["по чистење"]
table["избришани %"] = (100 * removed / table["пред чистење"]).round(1)

table.to_csv(RESULTS_FOLDER / "cleaning_statistics.csv")