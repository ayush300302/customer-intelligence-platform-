from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

# --- Health Endpoint Schemas ---
class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    model_version: str = Field(..., example="1.1.0")
    vector_index_version: str = Field(..., example="1.0.0")

# --- Predict Endpoint Schemas ---
class CustomerFeatures(BaseModel):
    age: int = Field(..., example=30)
    job: str = Field(..., example="admin.")
    marital: str = Field(..., example="single")
    education: str = Field(..., example="university.degree")
    default: str = Field(..., example="no")
    housing: str = Field(..., example="yes")
    loan: str = Field(..., example="no")
    contact: str = Field(..., example="cellular")
    month: str = Field(..., example="may")
    day_of_week: str = Field(..., example="mon")
    duration: int = Field(..., example=250)
    campaign: int = Field(..., example=1)
    pdays: int = Field(..., example=999)
    previous: int = Field(..., example=0)
    poutcome: str = Field(..., example="nonexistent")
    emp_var_rate: float = Field(..., alias="emp.var.rate", example=1.1)
    cons_price_idx: float = Field(..., alias="cons.price.idx", example=93.994)
    cons_conf_idx: float = Field(..., alias="cons.conf.idx", example=-36.4)
    euribor3m: float = Field(..., example=4.857)
    nr_employed: float = Field(..., alias="nr.employed", example=5191.0)

    class Config:
        populate_by_name = True

class PredictionResponse(BaseModel):
    prediction: int = Field(..., example=1)
    probability: float = Field(..., example=0.85)
    threshold_decision: str = Field(..., example="subscribe")
    model_version: str = Field(..., example="1.1.0")

# --- Batch Score Endpoint Schemas ---
class BatchScoreRequest(BaseModel):
    input_file: str = Field(..., example="data/batch_input.csv")
    output_file: Optional[str] = Field(None, example="data/batch_output.csv")

class BatchScoreResponse(BaseModel):
    scored_file_path: str = Field(..., example="data/batch_output.csv")
    counts_by_conversion_band: Dict[str, int] = Field(..., example={"high": 12, "medium": 45, "low": 150})

# --- Ask Complaints Endpoint Schemas ---
class AskComplaintsRequest(BaseModel):
    question: str = Field(..., example="What are the common issues reported against Equifax?")
    product: Optional[str] = Field(None, example="Credit card")
    company: Optional[str] = Field(None, example="Equifax")
    date_received: Optional[str] = Field(None, example="2026-05-20")
    issue: Optional[str] = Field(None, example="Billing dispute")

class AskComplaintsResponse(BaseModel):
    answer: str = Field(..., example="Equifax credit reporting issues involve...")
    retrieved_evidence_ids: List[str] = Field(..., example=["123456", "789012"])
    evidence_sufficiency_note: str = Field(..., example="Strong evidence found.")
    prompt_version: str = Field(..., example="v1.1_gemini_pro")

# --- Customer Intel Endpoint Schemas ---
class CustomerIntelRequest(BaseModel):
    customer_features: CustomerFeatures
    product: Optional[str] = Field(None, example="Credit card")
    company: Optional[str] = Field(None, example="Citibank")
    date_received: Optional[str] = Field(None, example="2026-05-20")
    issue: Optional[str] = Field(None, example="Billing dispute")

class ThemeDetail(BaseModel):
    complaint_id: str
    company: str
    issue: str
    similarity_score: float

class CustomerIntelResponse(BaseModel):
    conversion_probability: float = Field(..., example=0.62)
    conversion_band: str = Field(..., example="medium")
    complaint_themes: List[ThemeDetail]

# --- Metrics Endpoint Schemas ---
class MetricsResponse(BaseModel):
    latency: Dict[str, float] = Field(..., example={"predict": 0.015, "ask_complaints": 0.450, "customer_intel": 0.465})
    request_count: int = Field(..., example=120)
    error_count: int = Field(..., example=2)
    prediction_distribution: Dict[str, int] = Field(..., example={"0": 98, "1": 22})
    rag_retrieval_stats: Dict[str, Any] = Field(..., example={
        "hit_rate": 0.92,
        "refusal_rate": 0.08,
        "avg_top_k_score": 0.65,
        "total_tokens": 12450
    })
