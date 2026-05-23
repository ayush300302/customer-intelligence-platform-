# Post-Project Reflections

This document answers the reflection prompts specified in Section 12 of the mini-project description.

## 1. Model Family & Threshold Choice
- **Model Family**: We selected a **Random Forest Classifier** as the challenger model, comparing it against a **Logistic Regression** baseline. Random Forests handle non-linear decision boundaries, interaction terms, and mixed categorical/numerical types exceptionally well without requiring complex polynomial transformations.
- **Threshold**: We utilized a default classification threshold of `0.5`, but the evaluation script automatically tracks and logs the **optimal F1 threshold** based on the Precision-Recall curve. This allows the API to adjust decision thresholds dynamically if the business prioritizes precision over recall (or vice-versa).

## 2. What Broke First & What We Changed
- **What Broke**: The very first operation (downloading the UCI dataset) failed with an `SSLCertVerificationError` because the SSL certificate on `archive.ics.uci.edu` was expired or could not be verified by the local SSL context.
- **What We Changed**: We updated `src/data_pipeline/ingest.py` to use `verify=False` in `requests.get` calls and added `urllib3.disable_warnings` to prevent logs from being flooded with insecure request warnings.

## 3. Gate Margin & Tightening Consequences
- **Gate Margin**: The promotion gate requires the challenger model to beat the baseline PR-AUC by at least **2 percentage points** (0.02) and keep F1 drops within **1 percentage point** (0.01).
- **Tightening Consequences**: If we tightened the PR-AUC requirement by another 2 points (total 4%), the challenger model would fail to promote. Because the bank marketing target class is highly imbalanced, a 4% absolute gain in PR-AUC is a very high bar that would require extensive feature engineering (e.g. target encoding, macroeconomics trend features) beyond standard scaling and encoding.

## 4. RAG Failure & Refusal Execution
- **RAG Failure Case**: When asked an out-of-domain query like *"Why is the sky blue and what are the best investments in the stock market?"*, the retriever fetched credit card billing complaints containing keywords like "market" or "stock".
- **Refusal Resolution**: Because these complaints had very low relevance to the question, the highest similarity score returned by FAISS was `0.26`. Since this is well below our safety threshold of `0.42`, the answering engine successfully refused to answer (*"I cannot answer this question because no relevant complaints were found..."*), preventing a financial advice hallucination.

## 5. Major Risk Remaining for Production
- **Remaining Risk**: Configuration and secret management. If the `GEMINI_API_KEY` is misconfigured or missing in production, the application will silently fall back to Mock LLM mode rather than throwing a hard startup error. In a live customer deployment, this could result in customers receiving static, pre-defined templates. A startup check should be added to fail fast if keys are missing in a production profile.

## 6. Senior MLOps Engineer Critique
- **The Critique**: *"Post-filtering metadata is a scaling bottleneck."*
- **Why**: Currently, metadata filtering is implemented by retrieving 200 documents via FAISS and post-filtering them in memory using Pandas. If a filter is highly restrictive (e.g. a specific company with only 2 complaints in the database), the top 200 similarity search might not even contain those records, causing empty results. We should use a database that supports **native metadata filtering** (e.g. PGVector, Chroma, or Azure AI Search) to combine vector search and relational filters in a single step.
