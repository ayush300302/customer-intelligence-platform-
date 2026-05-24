# Decision Log

This document records the architectural choices, trade-offs, and rejected approaches during the development of the Customer Intelligence Platform.

## 1. Vector Search: FAISS vs. Chroma
- **Decision**: In-process FAISS (`IndexFlatIP`).
- **Rationale**: FAISS-cpu is highly performant and runs completely in-process. Since we are sampling 5,000 to 10,000 complaints, an in-memory flat index is lightweight, has near-zero latency, and avoids the overhead of managing a separate database daemon like Chroma or Qdrant. 
- **Rejected Alternatives**: Chroma DB. Chroma is great for document storage but introduces unnecessary dependencies and larger disk footprint for a small local development sample.

## 2. LLM Engine: Gemini API with Mock Fallback
- **Decision**: Implemented a dual-mode engine. If `GEMINI_API_KEY` is present in the environment or `.env` file, the system uses the real Gemini API (`gemini-1.5-flash`). Otherwise, it falls back to a deterministic, rule-based Mock LLM.
- **Rationale**: Enables the test suite and evaluation pipeline to run out of the box in zero-cost environments (like automated CI pipelines or local setups without keys) while still testing the full RAG pipeline structure.
- **Rejected Alternatives**: High-overhead local models (e.g. Llama-3 running via llama.cpp) which would take gigabytes of space and stall execution on CPU-only laptops.

## 3. Embedding Model: SentenceTransformers vs. External API
- **Decision**: Local `sentence-transformers` using the `all-MiniLM-L6-v2` model.
- **Rationale**: Generates high-quality 384-dimensional embeddings locally at zero cost and fast speed. Fits perfectly within CPU limits, ensuring that the vector indexing pipeline remains reproducible and doesn't require paid OpenAI/Gemini embedding API calls.
- **Rejected Alternatives**: Paid embedding APIs. Bypassing them ensures compliance with the "run for zero rupees" rule.

## 4. Relative Model Promotion Gate
- **Decision**: PR-AUC difference >= 2% AND F1 score drop <= 1%.
- **Rationale**: Imbalanced datasets (like campaign conversion, which has a low positive class rate) make accuracy a misleading metric. Using PR-AUC and F1 ensures that we prioritize precision and recall on the positive class. The relative gate ensures we only deploy a model if it represents a meaningful improvement.
- **Rejected Alternatives**: Accuracy-based gating. Rejects models that just predict the majority class.
