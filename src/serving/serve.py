import os
import time
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict, Any, List

from src.serving.schemas import (
    HealthResponse, CustomerFeatures, PredictionResponse,
    BatchScoreRequest, BatchScoreResponse,
    AskComplaintsRequest, AskComplaintsResponse,
    CustomerIntelRequest, CustomerIntelResponse, ThemeDetail,
    MetricsResponse
)
from src.serving.model_loader import get_resources
from src.rag.answer import ComplaintAnsweringEngine
from src.rag.retrieve import ComplaintRetriever

app = FastAPI(
    title="Customer Intelligence Platform API",
    description="Combined ML predictions and LLM/RAG complaint intelligence engine.",
    version="1.1.0"
)

# Initialize resources
resources = get_resources()
answering_engine = None
retriever = None

# Telemetry Metrics Store
telemetry = {
    "request_count": 0,
    "error_count": 0,
    "latencies": {
        "predict": [],
        "batch_score": [],
        "ask_complaints": [],
        "customer_intel": []
    },
    "prediction_distribution": {
        "0": 0,
        "1": 0
    },
    "rag_retrieval_stats": {
        "total_queries": 0,
        "hits": 0,
        "refusals": 0,
        "similarity_sum": 0.0
    }
}

@app.on_event("startup")
def startup_event():
    global answering_engine, retriever
    resources.reload()
    retriever = ComplaintRetriever()
    answering_engine = ComplaintAnsweringEngine(retriever=retriever)
    print("API Application startup: resources successfully loaded.")

@app.get("/health", response_model=HealthResponse)
def health():
    model_ver = resources.model_metadata.get("model_version", "1.0.0")
    # Set a dummy vector index version
    vector_ver = "1.0.0" if resources.faiss_index is not None else "0.0.0"
    return {
        "status": "healthy",
        "model_version": model_ver,
        "vector_index_version": vector_ver
    }

@app.post("/predict", response_model=PredictionResponse)
def predict(payload: CustomerFeatures):
    start_time = time.time()
    telemetry["request_count"] += 1
    
    if resources.ml_model is None or resources.pipeline is None:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=503, detail="ML model or pipeline is not loaded.")
        
    try:
        # Convert Pydantic payload to dictionary, using aliases to match original feature names (e.g. emp.var.rate)
        record = payload.model_dump(by_alias=True)
        
        # Transform single record
        transformed_df = resources.pipeline.transform_single(record)
        
        # Predict
        prob = float(resources.ml_model.predict_proba(transformed_df)[:, 1][0])
        
        # Threshold decision (e.g. 0.5 threshold)
        pred = int(prob >= 0.5)
        decision = "subscribe" if pred == 1 else "no_subscribe"
        
        # Track distribution and latency
        telemetry["prediction_distribution"][str(pred)] += 1
        latency = time.time() - start_time
        telemetry["latencies"]["predict"].append(latency)
        
        return {
            "prediction": pred,
            "probability": prob,
            "threshold_decision": decision,
            "model_version": resources.model_metadata.get("model_version", "1.1.0")
        }
    except Exception as e:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/batch-score", response_model=BatchScoreResponse)
def batch_score(payload: BatchScoreRequest):
    start_time = time.time()
    telemetry["request_count"] += 1
    
    if resources.ml_model is None or resources.pipeline is None:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=503, detail="ML model or pipeline is not loaded.")
        
    input_path = payload.input_file
    output_path = payload.output_file or input_path.replace(".csv", "_scored.csv")
    
    if not os.path.exists(input_path):
        telemetry["error_count"] += 1
        raise HTTPException(status_code=400, detail=f"Input file not found at {input_path}")
        
    try:
        # Load batch CSV
        try:
            df = pd.read_csv(input_path, sep=";")
            if len(df.columns) <= 1:
                df = pd.read_csv(input_path)
        except Exception:
            df = pd.read_csv(input_path)
            
        # Check targets if they exist in CSV
        X_batch = df.copy()
        if "y" in X_batch.columns:
            X_batch = X_batch.drop(columns=["y"])
        if "target" in X_batch.columns:
            X_batch = X_batch.drop(columns=["target"])
            
        # Apply transformation
        transformed_df = resources.pipeline.transform(X_batch)
        
        # Predict
        probs = resources.ml_model.predict_proba(transformed_df)[:, 1]
        preds = (probs >= 0.5).astype(int)
        
        # Append predictions to dataframe
        df["conversion_probability"] = probs
        df["conversion_prediction"] = preds
        df["conversion_band"] = pd.cut(
            df["conversion_probability"],
            bins=[-0.01, 0.3, 0.7, 1.01],
            labels=["low", "medium", "high"]
        )
        
        # Save scored file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        # Band counts
        band_counts = df["conversion_band"].value_counts().to_dict()
        # format key names
        counts = {
            "low": int(band_counts.get("low", 0)),
            "medium": int(band_counts.get("medium", 0)),
            "high": int(band_counts.get("high", 0))
        }
        
        # Update metrics
        for pred in preds:
            telemetry["prediction_distribution"][str(pred)] += 1
            
        latency = time.time() - start_time
        telemetry["latencies"]["batch_score"].append(latency)
        
        return {
            "scored_file_path": output_path,
            "counts_by_conversion_band": counts
        }
    except Exception as e:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=500, detail=f"Batch scoring failed: {str(e)}")

@app.post("/ask-complaints", response_model=AskComplaintsResponse)
def ask_complaints(payload: AskComplaintsRequest):
    start_time = time.time()
    telemetry["request_count"] += 1
    
    if answering_engine is None:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=503, detail="RAG Answering Engine is not loaded.")
        
    try:
        # Build filters dictionary
        filters = {}
        if payload.product:
            filters["product"] = payload.product
        if payload.company:
            filters["company"] = payload.company
        if payload.date_received:
            filters["date_received"] = payload.date_received
        if payload.issue:
            filters["issue"] = payload.issue
            
        # Get answer
        result = answering_engine.answer_question(payload.question, filters=filters)
        
        # Update RAG metrics
        telemetry["rag_retrieval_stats"]["total_queries"] += 1
        if result["refused"]:
            telemetry["rag_retrieval_stats"]["refusals"] += 1
        else:
            telemetry["rag_retrieval_stats"]["hits"] += 1
            telemetry["rag_retrieval_stats"]["similarity_sum"] += result["top_score"]
            
        latency = time.time() - start_time
        telemetry["latencies"]["ask_complaints"].append(latency)
        
        return {
            "answer": result["answer"],
            "retrieved_evidence_ids": result["retrieved_evidence_ids"],
            "evidence_sufficiency_note": result["evidence_sufficiency_note"],
            "prompt_version": result["prompt_version"]
        }
    except Exception as e:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@app.post("/customer-intel", response_model=CustomerIntelResponse)
def customer_intel(payload: CustomerIntelRequest):
    start_time = time.time()
    telemetry["request_count"] += 1
    
    if resources.ml_model is None or resources.pipeline is None or retriever is None:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=503, detail="ML Model or Retriever is not loaded.")
        
    try:
        # 1. Predict conversion probability
        record = payload.customer_features.model_dump(by_alias=True)
        transformed_df = resources.pipeline.transform_single(record)
        prob = float(resources.ml_model.predict_proba(transformed_df)[:, 1][0])
        
        if prob >= 0.70:
            band = "high"
        elif prob >= 0.30:
            band = "medium"
        else:
            band = "low"
            
        # 2. Retrieve top complaints matching filters (e.g. for complaint themes)
        filters = {}
        if payload.product:
            filters["product"] = payload.product
        if payload.company:
            filters["company"] = payload.company
        if payload.date_received:
            filters["date_received"] = payload.date_received
        if payload.issue:
            filters["issue"] = payload.issue
            
        # Construct query based on issue/product or use a default segment scan
        query = payload.issue or payload.product or "billing account service management"
        
        retrieved_docs = retriever.retrieve(query, filters=filters, top_k=3)
        
        themes = []
        for doc in retrieved_docs:
            themes.append(ThemeDetail(
                complaint_id=doc["complaint_id"],
                company=doc["company"],
                issue=doc["issue"],
                similarity_score=doc["similarity_score"]
            ))
            
        # Update metrics
        pred = int(prob >= 0.5)
        telemetry["prediction_distribution"][str(pred)] += 1
        
        latency = time.time() - start_time
        telemetry["latencies"]["customer_intel"].append(latency)
        
        return {
            "conversion_probability": prob,
            "conversion_band": band,
            "complaint_themes": themes
        }
    except Exception as e:
        telemetry["error_count"] += 1
        raise HTTPException(status_code=500, detail=f"Customer intelligence mapping failed: {str(e)}")

@app.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    # Calculate average latencies
    avg_latencies = {}
    for key, vals in telemetry["latencies"].items():
        avg_latencies[key] = float(np.mean(vals)) if vals else 0.0
        
    # Calculate RAG stats
    rag_total = telemetry["rag_retrieval_stats"]["total_queries"]
    hit_rate = float(telemetry["rag_retrieval_stats"]["hits"] / rag_total) if rag_total > 0 else 0.0
    refusal_rate = float(telemetry["rag_retrieval_stats"]["refusals"] / rag_total) if rag_total > 0 else 0.0
    avg_top_score = float(telemetry["rag_retrieval_stats"]["similarity_sum"] / telemetry["rag_retrieval_stats"]["hits"]) if telemetry["rag_retrieval_stats"]["hits"] > 0 else 0.0
    
    return {
        "latency": avg_latencies,
        "request_count": telemetry["request_count"],
        "error_count": telemetry["error_count"],
        "prediction_distribution": telemetry["prediction_distribution"],
        "rag_retrieval_stats": {
            "hit_rate": hit_rate,
            "refusal_rate": refusal_rate,
            "avg_top_k_score": avg_top_score,
            "total_tokens": rag_total * 300  # simulated token usage estimate
        }
    }
