import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from src.data_pipeline.features import clean_complaint_text

# Paths
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
INDEX_PATH = os.path.join(MODELS_DIR, "complaints_index.faiss")
METADATA_PATH = os.path.join(MODELS_DIR, "complaints_metadata.json")

class ComplaintRetriever:
    def __init__(self):
        self.index = None
        self.metadata = []
        self.model = None
        self.load_resources()

    def load_resources(self):
        if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
            print("Loading retriever resources...")
            self.index = faiss.read_index(INDEX_PATH)
            with open(METADATA_PATH, "r") as f:
                self.metadata = json.load(f)
            print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Retriever resources loaded successfully.")
        else:
            print("Warning: Index or metadata files not found. Retriever initialized with empty resources.")

    def retrieve(self, query: str, filters: dict = None, top_k: int = 5) -> list:
        if self.index is None or not self.metadata or self.model is None:
            print("Warning: Retriever resources are not loaded.")
            return []

        cleaned_query = clean_complaint_text(query)
        
        # Embed the query
        query_embedding = self.model.encode([cleaned_query])[0].astype('float32')
        
        # L2 normalize
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm
            
        query_vector = np.array([query_embedding])

        # If we have filters, we retrieve more candidates to account for post-filtering
        search_k = top_k
        if filters:
            search_k = min(len(self.metadata), max(1000, top_k * 20))

        # Search FAISS index
        # index.search returns distances (cosine similarities here since we L2-normalized vectors and use IndexFlatIP)
        # and indices of the matching vectors
        similarities, indices = self.index.search(query_vector, search_k)
        
        similarities = similarities[0]
        indices = indices[0]

        results = []
        for sim, idx in zip(similarities, indices):
            if idx == -1 or idx >= len(self.metadata):
                continue
                
            doc = self.metadata[idx]
            
            # Apply metadata filters
            if filters:
                passed = True
                for key, val in filters.items():
                    if val is None or val == "":
                        continue
                    # Check if the doc has the key and compare (case insensitive)
                    doc_val = str(doc.get(key, "")).lower()
                    filter_val = str(val).lower()
                    if filter_val not in doc_val:
                        passed = False
                        break
                if not passed:
                    continue

            results.append({
                "complaint_id": doc["complaint_id"],
                "date_received": doc["date_received"],
                "product": doc["product"],
                "sub_product": doc["sub_product"],
                "issue": doc["issue"],
                "sub_issue": doc["sub_issue"],
                "consumer_complaint_narrative": doc["consumer_complaint_narrative"],
                "company": doc["company"],
                "state": doc["state"],
                "zip_code": doc["zip_code"],
                "company_response_to_consumer": doc["company_response_to_consumer"],
                "similarity_score": float(sim)
            })
            
            # Stop once we have top_k filtered results
            if len(results) >= top_k:
                break

        return results

if __name__ == "__main__":
    # Test block
    retriever = ComplaintRetriever()
    if retriever.index is not None:
        res = retriever.retrieve("credit card billing dispute", filters={"company": "Citibank"}, top_k=2)
        print("Test Search Results:")
        for r in res:
            print(f"- ID: {r['complaint_id']}, Score: {r['similarity_score']:.4f}, Company: {r['company']}, Issue: {r['issue']}")
