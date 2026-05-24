import os
import pickle
import json
import hashlib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import mlflow

from src.data_pipeline.features import BankMarketingFeaturePipeline
from src.data_pipeline.validate import DataValidator

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
os.makedirs(MODELS_DIR, exist_ok=True)

RAW_DATA_PATH = os.path.join(DATA_DIR, "bank_marketing_raw.csv")

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def run_training():
    print("Starting ML pipeline training...")
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Raw data file not found at {RAW_DATA_PATH}. Please run ingestion first.")

    # Load data
    # UCI bank-additional-full.csv uses semicolon delimiter by default
    try:
        df = pd.read_csv(RAW_DATA_PATH, sep=";")
        if len(df.columns) <= 1:
            df = pd.read_csv(RAW_DATA_PATH)
    except Exception as e:
        df = pd.read_csv(RAW_DATA_PATH)

    print(f"Loaded {len(df)} rows of training data.")

    # Validate data
    validation_report = DataValidator.validate_bank_marketing(df)
    print("Data Validation Report:", validation_report)
    if not validation_report["success"]:
        print("Warning: Data validation errors found:")
        for err in validation_report["errors"]:
            print(f"  - {err}")

    # Format absolute path as file URI to prevent KeyError on Windows
    tracking_uri = "file:///" + os.path.join(MODELS_DIR, "mlruns").replace("\\", "/")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("bank_marketing_campaign")

    # Map target 'y' to binary
    df["target"] = df["y"].map({"yes": 1, "no": 0})
    
    # Split
    X = df.drop(columns=["y", "target"])
    y = df["target"]
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Feature pipeline
    pipeline = BankMarketingFeaturePipeline()
    pipeline.fit(X_train)
    
    X_train_trans = pipeline.transform(X_train)
    X_val_trans = pipeline.transform(X_val)

    # Save pipeline candidate
    pipeline_path = os.path.join(MODELS_DIR, "candidate_pipeline.pkl")
    pipeline.save(pipeline_path)
    print(f"Saved feature pipeline candidate to {pipeline_path}")

    # Train Baseline Model (Logistic Regression)
    print("Training baseline model (Logistic Regression)...")
    baseline_model = LogisticRegression(max_iter=1000, random_state=42)
    
    with mlflow.start_run(run_name="baseline_logistic_regression"):
        baseline_model.fit(X_train_trans, y_train)
        
        # Predict
        y_val_pred = baseline_model.predict(X_val_trans)
        y_val_prob = baseline_model.predict_proba(X_val_trans)[:, 1]
        
        # Log params & metrics
        mlflow.log_param("model_type", "logistic_regression")
        mlflow.log_param("max_iter", 1000)
        mlflow.log_param("data_hash", get_file_hash(RAW_DATA_PATH))
        
        # Log to MLflow local artifacts
        mlflow.sklearn.log_model(baseline_model, "model")
        
        # Save baseline model file
        baseline_path = os.path.join(MODELS_DIR, "candidate_baseline.pkl")
        with open(baseline_path, "wb") as f:
            pickle.dump(baseline_model, f)
            
    print("Baseline model training completed.")

    # Train Challenger Model (Random Forest)
    print("Training challenger model (Random Forest)...")
    challenger_model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    
    with mlflow.start_run(run_name="challenger_random_forest"):
        challenger_model.fit(X_train_trans, y_train)
        
        # Log params & metrics
        mlflow.log_param("model_type", "random_forest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 12)
        mlflow.log_param("data_hash", get_file_hash(RAW_DATA_PATH))
        
        mlflow.sklearn.log_model(challenger_model, "model")
        
        # Save challenger model file
        challenger_path = os.path.join(MODELS_DIR, "candidate_challenger.pkl")
        with open(challenger_path, "wb") as f:
            pickle.dump(challenger_model, f)
            
    print("Challenger model training completed.")

if __name__ == "__main__":
    run_training()
