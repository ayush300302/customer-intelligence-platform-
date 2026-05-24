import os
import json
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from src.data_pipeline.features import clean_complaint_text

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
os.makedirs(MODELS_DIR, exist_ok=True)

COMPLAINTS_CSV = os.path.join(DATA_DIR, "complaints_raw.csv")
INDEX_PATH = os.path.join(MODELS_DIR, "complaints_index.faiss")
METADATA_PATH = os.path.join(MODELS_DIR, "complaints_metadata.json")

def build_vector_index():
    print("Starting vector index building...")
    if not os.path.exists(COMPLAINTS_CSV):
        raise FileNotFoundError(f"Complaints file not found at {COMPLAINTS_CSV}. Please run ingestion first.")

    # Load complaints
    df = pd.read_csv(COMPLAINTS_CSV)
    print(f"Loaded {len(df)} raw complaints.")

    # Filter out empty narratives
    df = df.dropna(subset=["consumer_complaint_narrative"])
    df = df[df["consumer_complaint_narrative"].str.strip() != ""]
    print(f"Filtered to {len(df)} complaints with non-empty narratives.")

    if len(df) == 0:
        print("Warning: No complaints with narratives available to index.")
        # Create a dummy index & metadata
        dimension = 384
        index = faiss.IndexFlatIP(dimension)
        faiss.write_index(index, INDEX_PATH)
        with open(METADATA_PATH, "w") as f:
            json.dump([], f)
        print("Created empty index and metadata.")
        return

    # Keep only a maximum of 10,000 complaints to avoid high memory/CPU usage during local training
    if len(df) > 10000:
        df = df.sample(n=10000, random_state=42).reset_index(drop=True)
        print(f"Sampled down to {len(df)} complaints for fast local indexing.")

    # Clean text
    print("Cleaning narratives...")
    df["cleaned_narrative"] = df["consumer_complaint_narrative"].apply(clean_complaint_text)

    # Initialize SentenceTransformer
    print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Compute embeddings
    print(f"Encoding {len(df)} narratives (this may take a minute)...")
    texts = df["cleaned_narrative"].tolist()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    
    # Convert to float32
    embeddings = np.array(embeddings).astype('float32')
    
    # L2 normalize for cosine similarity (IndexFlatIP computes dot product,
    # which is equivalent to cosine similarity for normalized vectors)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10  # prevent division by zero
    embeddings = embeddings / norms
    
    dimension = embeddings.shape[1]
    print(f"Embedding shape: {embeddings.shape}, dimension: {dimension}")

    # Build FAISS index
    print("Building FAISS IndexFlatIP index...")
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save FAISS index
    faiss.write_index(index, INDEX_PATH)
    print(f"Saved FAISS index to {INDEX_PATH}")

    # Prepare and save metadata
    # Save the original fields so retrieve can return details and apply filters
    metadata_list = []
    for idx, row in df.iterrows():
        metadata_list.append({
            "index_id": int(idx),
            "complaint_id": str(row["complaint_id"]),
            "date_received": str(row["date_received"]),
            "product": str(row["product"]),
            "sub_product": str(row["sub_product"]) if pd.notna(row["sub_product"]) else "",
            "issue": str(row["issue"]),
            "sub_issue": str(row["sub_issue"]) if pd.notna(row["sub_issue"]) else "",
            "consumer_complaint_narrative": str(row["consumer_complaint_narrative"]),
            "company": str(row["company"]),
            "state": str(row["state"]) if pd.notna(row["state"]) else "",
            "zip_code": str(row["zip_code"]) if pd.notna(row["zip_code"]) else "",
            "company_response_to_consumer": str(row["company_response_to_consumer"]) if pd.notna(row["company_response_to_consumer"]) else ""
        })

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata_list, f, indent=4)
        
    print(f"Saved metadata mapping for {len(metadata_list)} documents to {METADATA_PATH}")
    print("Vector indexing completed successfully.")

if __name__ == "__main__":
    build_vector_index()
