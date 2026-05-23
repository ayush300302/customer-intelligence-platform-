import os
import pickle
import json
import datetime
import hashlib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, f1_score, accuracy_score, confusion_matrix, brier_score_loss

# Paths
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
RAW_DATA_PATH = os.path.join(DATA_DIR, "bank_marketing_raw.csv")

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def compute_metrics(y_true, y_prob):
    # Determine threshold based on F1 maximization
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_prob)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
    best_idx = np.argmax(f1_scores)
    best_threshold = float(thresholds[best_idx]) if best_idx < len(thresholds) else 0.5
    
    # Calculate metrics with threshold 0.5 for baseline comparison, or best_threshold
    y_pred = (y_prob >= 0.5).astype(int)
    
    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(auc(recalls, precisions))
    f1 = float(f1_score(y_true, y_pred))
    acc = float(accuracy_score(y_true, y_pred))
    brier = float(brier_score_loss(y_true, y_prob))
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "f1": f1,
        "accuracy": acc,
        "brier_score": brier,
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        },
        "opt_threshold": best_threshold
    }

def run_evaluation():
    print("Starting ML model evaluation and promotion gate...")
    
    # Load candidate artifacts
    pipeline_path = os.path.join(MODELS_DIR, "candidate_pipeline.pkl")
    baseline_path = os.path.join(MODELS_DIR, "candidate_baseline.pkl")
    challenger_path = os.path.join(MODELS_DIR, "candidate_challenger.pkl")
    
    if not (os.path.exists(pipeline_path) and os.path.exists(baseline_path) and os.path.exists(challenger_path)):
        raise FileNotFoundError("Candidate artifacts not found. Please run train.py first.")
        
    with open(pipeline_path, "rb") as f:
        pipeline = pickle.load(f)
    with open(baseline_path, "rb") as f:
        baseline_model = pickle.load(f)
    with open(challenger_path, "rb") as f:
        challenger_model = pickle.load(f)

    # Load and split raw data exactly like in train.py
    try:
        df = pd.read_csv(RAW_DATA_PATH, sep=";")
        if len(df.columns) <= 1:
            df = pd.read_csv(RAW_DATA_PATH)
    except Exception:
        df = pd.read_csv(RAW_DATA_PATH)

    df["target"] = df["y"].map({"yes": 1, "no": 0})
    X = df.drop(columns=["y", "target"])
    y = df["target"]
    
    _, X_val, _, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Transform validation split
    X_val_trans = pipeline.transform(X_val)
    
    # Predict probabilities
    prob_baseline = baseline_model.predict_proba(X_val_trans)[:, 1]
    prob_challenger = challenger_model.predict_proba(X_val_trans)[:, 1]
    
    # Compute metrics
    metrics_baseline = compute_metrics(y_val, prob_baseline)
    metrics_challenger = compute_metrics(y_val, prob_challenger)
    
    print("\n--- Baseline Model Metrics (Logistic Regression) ---")
    print(json.dumps(metrics_baseline, indent=2))
    
    print("\n--- Challenger Model Metrics (Random Forest) ---")
    print(json.dumps(metrics_challenger, indent=2))
    
    # Gate rules:
    # 1. Challenger PR-AUC must beat baseline by at least 2 percentage points (0.02)
    # 2. Challenger F1 drops by no more than 1 percentage point (0.01)
    
    pr_auc_diff = metrics_challenger["pr_auc"] - metrics_baseline["pr_auc"]
    f1_diff = metrics_baseline["f1"] - metrics_challenger["f1"] # lower F1 is positive drop
    
    pr_auc_passed = pr_auc_diff >= 0.02
    f1_passed = f1_diff <= 0.01 # challenger F1 is not worse by more than 0.01
    
    promoted = pr_auc_passed and f1_passed
    
    print("\n--- Promotion Gate Checking ---")
    print(f"PR-AUC Challenger: {metrics_challenger['pr_auc']:.4f} vs Baseline: {metrics_baseline['pr_auc']:.4f} (Diff: {pr_auc_diff:+.4f}) -> Passed: {pr_auc_passed}")
    print(f"F1 Challenger: {metrics_challenger['f1']:.4f} vs Baseline: {metrics_baseline['f1']:.4f} (Drop: {f1_diff:+.4f}) -> Passed: {f1_passed}")
    
    # Set promoted model type
    if promoted:
        print("\nSUCCESS: Challenger model meets promotion criteria. Promoting challenger!")
        promoted_model_name = "challenger_random_forest"
        promoted_model = challenger_model
    else:
        print("\nRETAINED: Challenger model did NOT meet promotion criteria. Retaining baseline.")
        promoted_model_name = "baseline_logistic_regression"
        promoted_model = baseline_model
        
    # Save promoted artifacts
    promoted_model_path = os.path.join(MODELS_DIR, "promoted_model.pkl")
    final_pipeline_path = os.path.join(MODELS_DIR, "pipeline.pkl")
    
    with open(promoted_model_path, "wb") as f:
        pickle.dump(promoted_model, f)
    with open(final_pipeline_path, "wb") as f:
        pickle.dump(pipeline, f)
        
    # Write registry metadata
    metadata = {
        "model_version": "1.0.0" if not promoted else "1.1.0",
        "model_type": promoted_model_name,
        "training_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_hash": get_file_hash(RAW_DATA_PATH),
        "gate_evaluation": {
            "pr_auc_difference": pr_auc_diff,
            "f1_drop": f1_diff,
            "pr_auc_gate_passed": bool(pr_auc_passed),
            "f1_gate_passed": bool(f1_passed),
            "is_challenger_promoted": bool(promoted)
        },
        "metrics": {
            "baseline": metrics_baseline,
            "challenger": metrics_challenger,
            "promoted": metrics_challenger if promoted else metrics_baseline
        }
    }
    
    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Saved promoted model registry metadata to {metadata_path}")
    print("Model evaluation and promotion completed successfully.")

if __name__ == "__main__":
    run_evaluation()
