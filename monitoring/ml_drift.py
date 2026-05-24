import os
import pandas as pd
import numpy as np
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
os.makedirs(DOCS_DIR, exist_ok=True)

RAW_DATA_PATH = os.path.join(DATA_DIR, "bank_marketing_raw.csv")
DRIFT_REPORT_HTML = os.path.join(DOCS_DIR, "ml_drift_report.html")

def generate_drift_report():
    print("Starting ML data drift simulation and report generation...")
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Raw data file not found at {RAW_DATA_PATH}. Please run ingestion first.")

    # Load raw data
    try:
        df = pd.read_csv(RAW_DATA_PATH, sep=";")
        if len(df.columns) <= 1:
            df = pd.read_csv(RAW_DATA_PATH)
    except Exception:
        df = pd.read_csv(RAW_DATA_PATH)

    # Reference dataset: clean sample of original data
    reference_data = df.sample(n=2000, random_state=42).reset_index(drop=True)
    
    # Current dataset: simulate feature drift
    # Let's shift some features:
    # 1. Shift age: add 15 years to all customers in the current dataset (demographic shift)
    # 2. Shift duration: multiply duration by 1.5 (longer call durations in recent campaigns)
    # 3. Shift euribor3m: increase interest rates by 1.2 points (macroeconomic shift)
    current_data = df.sample(n=2000, random_state=100).reset_index(drop=True)
    current_data["age"] = current_data["age"] + 15
    current_data["duration"] = current_data["duration"] * 1.5
    current_data["euribor3m"] = current_data["euribor3m"] + 1.2

    # Drop target column to analyze feature drift
    if "y" in reference_data.columns:
        reference_data = reference_data.drop(columns=["y"])
    if "y" in current_data.columns:
        current_data = current_data.drop(columns=["y"])

    print("Running Evidently DataDriftPreset Report...")
    # Generate Evidently report
    data_drift_report = Report(metrics=[
        DataDriftPreset()
    ])

    data_drift_report.run(reference_data=reference_data, current_data=current_data)
    
    # Save HTML report
    data_drift_report.save_html(DRIFT_REPORT_HTML)
    print(f"ML drift report saved to {DRIFT_REPORT_HTML}")
    
    # Extract some simple metrics to display in console
    report_dict = data_drift_report.as_dict()
    metrics = report_dict.get("metrics", [])
    
    drift_share = 0.0
    number_of_drifted_features = 0
    total_features = 0
    
    for metric in metrics:
        if metric.get("metric") == "DatasetDriftMetric":
            result = metric.get("result", {})
            drift_share = result.get("drift_share", 0.0)
            number_of_drifted_features = result.get("number_of_drifted_features", 0)
            total_features = result.get("number_of_features", 0)
            break
            
    print("\n--- Drift Summary ---")
    print(f"Drifted Features: {number_of_drifted_features} / {total_features}")
    print(f"Drift Share: {drift_share * 100:.1f}%")
    print(f"Dataset Drift Detected: {drift_share >= 0.5}")
    print("---------------------")

if __name__ == "__main__":
    generate_drift_report()
