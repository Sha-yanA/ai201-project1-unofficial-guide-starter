"""
Embedding and retrieval pipeline.

Loads chunks from chunk_units(), embeds them with all-MiniLM-L6-v2 (local,
no API key), and stores them in a persistent ChromaDB collection.

Exposes:
    build_index()           — embed all chunks and persist to disk
    retrieve(query, k=5)    — return top-k chunks with distance scores

Run once to build the index:
    python embed.py

Then import retrieve() into generate.py:
    from embed import retrieve
"""

from pathlib import Path

from chunk import chunk_units
from ingest import ingest_documents

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "uf_dining"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def _get_collection(persist_dir: str = CHROMA_DIR):
    import chromadb

    client = chromadb.PersistentClient(path=persist_dir)
    return client, client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(persist_dir: str = CHROMA_DIR) -> int:
    """
    Embed all chunks and store them in a persistent ChromaDB collection.
    Skips the build if the collection already has documents.
    Returns the total number of chunks indexed.
    """
    from sentence_transformers import SentenceTransformer

    client, collection = _get_collection(persist_dir)

    if collection.count() > 0:
        print(f"Collection '{COLLECTION_NAME}' already has {collection.count()} chunks — skipping rebuild.")
        print("Delete the chroma_db/ folder and re-run to force a fresh index.")
        return collection.count()

    print("Loading chunks from ingestion + chunking pipeline...")
    units = ingest_documents()
    chunks = chunk_units(units)
    print(f"  {len(chunks)} chunks ready for embedding")

    print(f"Loading embedding model '{EMBEDDING_MODEL}'...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks (this takes ~10–20s on CPU)...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_list=True)

    # ChromaDB requires string IDs
    ids = [f"chunk_{i:04d}" for i in range(len(chunks))]

    # Compute per-document chunk position so attribution can cite "chunk 3 of 12 from <file>"
    doc_counters: dict[str, int] = {}
    doc_totals: dict[str, int] = {}
    for c in chunks:
        doc_totals[c["filename"]] = doc_totals.get(c["filename"], 0) + 1

    # Metadata dict must contain only str/int/float/bool values
    metadatas = []
    for c in chunks:
        fname = c["filename"]
        doc_counters[fname] = doc_counters.get(fname, 0) + 1
        metadatas.append(
            {
                "source": c["source"],
                "location": c["location"],
                "url": c["url"],
                "doc_type": c["doc_type"],
                "filename": fname,
                "chunk_index": doc_counters[fname] - 1,       # 0-based position within doc
                "chunk_total": doc_totals[fname],              # total chunks from this doc
            }
        )

    # Add in batches of 500 to avoid memory spikes on large collections
    batch_size = 500
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Stored chunks {start}–{min(end, len(chunks)) - 1}")

    print(f"\nIndex built: {collection.count()} chunks in '{COLLECTION_NAME}'")
    return collection.count()


def retrieve(query: str, k: int = 5, persist_dir: str = CHROMA_DIR) -> list[dict]:
    """
    Embed query and return the top-k most similar chunks.

    Each result dict contains:
        text         — the chunk text
        source       — e.g. "Reddit r/ufl"
        location     — e.g. "Gator Corner Dining Center"
        url          — source URL
        doc_type     — "review" | "article" | "reddit"
        filename     — original .txt file
        chunk_index  — 0-based position of this chunk within its source document
        chunk_total  — total chunks produced from that document
        distance     — cosine distance (lower = more similar; 0.0 is identical)
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode(query, convert_to_list=True)

    _, collection = _get_collection(persist_dir)

    if collection.count() == 0:
        raise RuntimeError(
            "ChromaDB collection is empty. Run `python embed.py` to build the index first."
        )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({"text": doc, **meta, "distance": round(dist, 4)})

    return chunks


if __name__ == "__main__":
    build_index()

    print("\n--- Retrieval smoke test ---")
    test_queries = [
        "What do students think about Gator Corner compared to Broward?",
        "Are there vegan options at UF dining halls?",
        "Is the UF meal plan worth buying?",
        "What food is available at the Reitz Union?",
        "Where can I eat after midnight near UF?",
    ]

    for query in test_queries:
        print(f"\nQ: {query}")
        hits = retrieve(query, k=3)
        for i, hit in enumerate(hits, 1):
            preview = hit["text"][:120].replace("\n", " ")
            print(f"  {i}. [{hit['source']} | {hit['location']}] dist={hit['distance']}")
            print(f"     {preview!r}")
