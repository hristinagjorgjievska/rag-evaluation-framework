import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROCESSED_FOLDER = ROOT / "data" / "processed"


CHUNK_SIZES = [(300, 45), (600, 90)]
CHUNKS_FOLDER = ROOT / "data" / "chunks"

def get_word_positions(text):
    return [(m.group(), m.start(), m.end()) for m in re.finditer(r"\S+", text)]

def build_chunks(doc_id, text, chunk_size, overlap):
    word_positions = get_word_positions(text)
    chunks = []

    start = 0
    chunk_num = 0

    while start < len(word_positions):
        end = start + chunk_size
        window = word_positions[start:end]

        chunk_text_value = text[window[0][1] : window[-1][2]]

        chunks.append({
            "chunk_id": f"{doc_id}_c{chunk_num:03d}",
            "doc_id": doc_id,
            "text": chunk_text_value,
            "char_start": window[0][1],
            "char_end": window[-1][2]
        })

        chunk_num += 1
        start = start + chunk_size - overlap

    return chunks

def save_chunks_preview(chunks, out_path):
    lines = []
    for c in chunks:
        lines.append(f"=== {c['chunk_id']} (doc {c['doc_id']}) ===")
        lines.append(c["text"])
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")

def process_all_documents():

    for chunk_size, overlap in CHUNK_SIZES:
        all_chunks = []

        for json_file in sorted(PROCESSED_FOLDER.glob("*.json")):
            doc = json.loads(json_file.read_text(encoding="UTF-8"))
            chunks = build_chunks(doc["doc_id"], doc["text"], chunk_size, overlap)
            all_chunks.extend(chunks)

        processed_path = CHUNKS_FOLDER / f"chunks_{chunk_size}.json"
        processed_path.write_text(
            json.dumps(all_chunks, ensure_ascii=False, indent=2),
            encoding="UTF-8"
        )

        preview_path = CHUNKS_FOLDER / f"chunks_{chunk_size}_preview.txt"
        save_chunks_preview(all_chunks, preview_path)

        print(f"chunk_size={chunk_size}: {len(all_chunks)} chunks " f"-> {processed_path.name}")


process_all_documents()