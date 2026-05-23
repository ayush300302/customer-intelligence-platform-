import os
import pandas as pd
import numpy as np

class DataValidator:
    @staticmethod
    def validate_bank_marketing(df: pd.DataFrame) -> dict:
        errors = []
        
        # 1. Schema Check: Required columns
        required_cols = [
            "age", "job", "marital", "education", "default", "housing", "loan", 
            "contact", "month", "day_of_week", "duration", "campaign", "pdays", 
            "previous", "poutcome", "emp.var.rate", "cons.price.idx", 
            "cons.conf.idx", "euribor3m", "nr.employed", "y"
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns in Bank Marketing dataset: {missing_cols}")
            return {"success": False, "errors": errors, "num_records": len(df)}

        # 2. Check for missing values in critical fields (e.g., target 'y', age)
        null_target = df["y"].isnull().sum()
        if null_target > 0:
            errors.append(f"Target column 'y' has {null_target} missing values.")

        null_age = df["age"].isnull().sum()
        if null_age > 0:
            errors.append(f"Age column has {null_age} missing values.")

        # Business Rule 1: Age must be positive and reasonable (e.g., between 15 and 120)
        invalid_age = df[(df["age"] < 15) | (df["age"] > 120)]
        if not invalid_age.empty:
            errors.append(f"Business Rule Failure: Found {len(invalid_age)} records with age outside [15, 120] range.")

        # Business Rule 2: Duration of contact must be non-negative
        invalid_duration = df[df["duration"] < 0]
        if not invalid_duration.empty:
            errors.append(f"Business Rule Failure: Found {len(invalid_duration)} records with negative contact duration.")

        # Business Rule 3: Number of contacts in this campaign must be at least 1
        invalid_campaign = df[df["campaign"] < 1]
        if not invalid_campaign.empty:
            errors.append(f"Business Rule Failure: Found {len(invalid_campaign)} records with campaign contacts < 1.")

        # Business Rule 4: Target variable 'y' must only contain 'yes' or 'no'
        invalid_y = df[~df["y"].isin(["yes", "no"])]
        if not invalid_y.empty:
            errors.append(f"Business Rule Failure: Target 'y' contains invalid values: {invalid_y['y'].unique()}")

        # Business Rule 5: pdays (days since last contact) must be -1, 999, or positive.
        # Note: In UCI Bank Marketing, 999 means client was not previously contacted.
        invalid_pdays = df[(df["pdays"] < 0) & (df["pdays"] != -1) & (df["pdays"] != 999)]
        if not invalid_pdays.empty:
            errors.append(f"Business Rule Failure: Found {len(invalid_pdays)} records with invalid pdays values.")

        success = len(errors) == 0
        return {
            "success": success,
            "errors": errors,
            "num_records": len(df),
            "duplicate_records": int(df.duplicated().sum())
        }

    @staticmethod
    def validate_complaints(df: pd.DataFrame) -> dict:
        errors = []
        
        # 1. Schema Check: Required columns
        required_cols = [
            "complaint_id", "date_received", "product", "issue", "consumer_complaint_narrative"
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns in Complaints dataset: {missing_cols}")
            return {"success": False, "errors": errors, "num_records": len(df)}

        # 2. Check for empty narratives
        null_narratives = df["consumer_complaint_narrative"].isnull().sum()
        empty_narratives = (df["consumer_complaint_narrative"] == "").sum()
        total_empty_narratives = null_narratives + empty_narratives
        if total_empty_narratives > 0:
            errors.append(f"Found {total_empty_narratives} complaints with missing/empty consumer narrative.")

        # Business Rule 1: Complaint IDs must be unique
        duplicate_ids = df["complaint_id"].duplicated().sum()
        if duplicate_ids > 0:
            errors.append(f"Business Rule Failure: Found {duplicate_ids} duplicate complaint IDs.")

        # Business Rule 2: Date Received must be non-null and format parseable
        try:
            pd.to_datetime(df["date_received"])
        except Exception as e:
            errors.append(f"Business Rule Failure: 'date_received' contains unparseable dates: {str(e)}")

        success = len(errors) == 0
        return {
            "success": success,
            "errors": errors,
            "num_records": len(df)
        }

if __name__ == "__main__":
    # Test script if files exist
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    bm_file = os.path.join(data_dir, "bank_marketing_raw.csv")
    comp_file = os.path.join(data_dir, "complaints_raw.csv")
    
    if os.path.exists(bm_file):
        df_bm = pd.read_csv(bm_file, sep=";")
        if "y" not in df_bm.columns and ";" not in df_bm.columns:
            # Let's check delimiter
            df_bm = pd.read_csv(bm_file)
        print("Bank Marketing Validation:", DataValidator.validate_bank_marketing(df_bm))
        
    if os.path.exists(comp_file):
        df_comp = pd.read_csv(comp_file)
        print("Complaints Validation:", DataValidator.validate_complaints(df_comp))
