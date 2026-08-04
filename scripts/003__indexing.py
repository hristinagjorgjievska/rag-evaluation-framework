import re
import json
from pathlib import Path
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).parent.parent
CHUNKS_FOLDER = ROOT / "data" / "chunks"

def tokenize(text):
    text_lowercase = text.lower()
    words = re.findall(r"\w+", text_lowercase)

    return words

def load_chunks(chunk_size):
    file_path = CHUNKS_FOLDER / f"chunks_{chunk_size}.json"
    text = file_path.read_text(encoding="UTF-8")
    chunks = json.loads(text)

    return chunks

def tokenize_all_chunks(chunks):
    tokenized_list = []
    for chunk in chunks:

        words = tokenize(chunk["text"])
        tokenized_list.append(words)

    return tokenized_list

def make_bm25_index(tokenized_chunks):
    bm25 = BM25Okapi(tokenized_chunks)
    return bm25

def search(bm25, chunks, query, top_k):
    query_words = tokenize(query)
    scores = bm25.get_scores(query_words)

    paired = []
    i = 0
    while i < len(chunks):
        pair = (chunks[i], scores[i])
        paired.append(pair)
        i = i + 1

    paired.sort(key=lambda pair: pair[1], reverse=True)

    return paired[:top_k]

chunks = load_chunks(chunk_size=300)
tokenized_chunks = tokenize_all_chunks(chunks)
bm25 = make_bm25_index(tokenized_chunks)

results = search(bm25, chunks, "Колку кредити треба за докторски студии?", top_k=3)

for chunk, score in results:
    print("score:", score)
    print("chunk_id:", chunk["chunk_id"])
    print("текст:", chunk["text"][:100])
    print()

