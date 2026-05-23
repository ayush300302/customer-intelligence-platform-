# System Architecture

The Customer Intelligence Platform combines a classic Machine Learning pipeline and a Large Language Model RAG pipeline under a single FastAPI-powered application layer. 

## High-Level Architecture

```mermaid
graph TD
    %% Datasets
    subgraph Data Layer
        UCI[UCI Bank Marketing Data]
        CFPB[CFPB Consumer Complaints]
    end

    %% ML Pipeline
    subgraph ML Pipeline (Model Lane)
        ingest_ml[ingest.py] --> val_ml[validate.py]
        val_ml --> feat_ml[features.py]
        feat_ml --> train_ml[train.py]
        train_ml --> eval_ml[evaluate.py]
        eval_ml --> gate_decision{Relative Promotion Gate}
    end

    %% RAG Pipeline
    subgraph RAG Pipeline (LLM Lane)
        ingest_rag[ingest.py] --> build_rag[build_index.py]
        build_rag --> vector_index[FAISS Index]
        build_rag --> doc_meta[Complaints Metadata]
    end

    %% Registry / Store
    subgraph Registry / Artifact Store
        mlflow_store[MLflow Tracker]
        model_reg[promoted_model.pkl]
        pipeline_reg[pipeline.pkl]
        meta_reg[model_metadata.json]
    end

    %% API Layer
    subgraph FastAPI Spine
        app[serve.py]
        schemas[schemas.py]
        loader[model_loader.py]
    end

    %% Connections
    UCI --> ingest_ml
    CFPB --> ingest_rag
    
    train_ml -.-> mlflow_store
    
    gate_decision -->|Promoted| model_reg
    gate_decision -->|Promoted| pipeline_reg
    gate_decision -->|Log Decision| meta_reg
    
    loader -->|Loads| model_reg
    loader -->|Loads| pipeline_reg
    loader -->|Loads| meta_reg
    loader -->|Loads| vector_index
    loader -->|Loads| doc_meta
    
    app --> loader
    app --> schemas
    
    %% API Endpoints
    client[API Client / Frontend] -->|GET /health| app
    client -->|POST /predict| app
    client -->|POST /batch-score| app
    client -->|POST /ask-complaints| app
    client -->|POST /customer-intel| app
    client -->|GET /metrics| app

    %% Monitoring & Retraining
    subgraph Monitoring & Ops
        ml_drift[ml_drift.py] -->|Generates| drift_rep[ml_drift_report.html]
        rag_mon[rag_monitor.py]
        app -->|Telemetry Logs| ml_drift
        app -->|Telemetry Logs| rag_mon
        ml_drift -->|Triggers Drift Alert| retrain[Retrain Trigger]
        retrain -.->|Runs| train_ml
    end
```

## Component Breakdown

1. **FastAPI Serving Spine**:
   - Acts as the unified gateway for all downstream logic.
   - Decoupled into `schemas.py` (Pydantic payload definitions) and `model_loader.py` (cache layer for system models and vector index).
2. **ML Lane**:
   - Predicts term-deposit conversion using client demographic and economic indicators.
   - Enforces a **Relative Promotion Gate**: New challenger models must beat the current baseline's PR-AUC by at least 2 percentage points, and have an F1 score drop of no more than 1 point.
3. **RAG Lane**:
   - Uses `SentenceTransformer` (`all-MiniLM-L6-v2`) locally to compute 384-dimensional dense vectors from complaint narratives.
   - Indexes and retrieves vectors using in-process **FAISS** (utilizing inner product similarity, equivalent to cosine similarity for L2-normalized vectors).
   - Serves grounded answers using Gemini Pro (via API key) or falls back to a rule-based mock QA engine.
4. **Monitoring & MLOps**:
   - **Evidently AI** evaluates features for statistical drift, comparing live scoring inputs with the training data distribution.
   - Memory-based telemetry monitors endpoint latencies, request distributions, and RAG retrieval quality metrics.
