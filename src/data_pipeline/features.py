import os
import pickle
import pandas as pd
import numpy as np

class BankMarketingFeaturePipeline:
    def __init__(self):
        self.fitted = False
        self.categorical_cols = [
            "job", "marital", "education", "default", "housing", "loan", 
            "contact", "month", "day_of_week", "poutcome"
        ]
        self.numerical_cols = [
            "age", "duration", "campaign", "pdays", "previous", 
            "emp.var.rate", "cons.price.idx", "cons.conf.idx", "euribor3m", "nr.employed"
        ]
        self.category_mappings = {}
        self.feature_columns_ = []
        self.numerical_means = {}
        self.numerical_stds = {}

    def fit(self, df: pd.DataFrame):
        # 1. Fit categorical mappings (One-Hot Columns list)
        self.category_mappings = {}
        feature_cols = []
        
        # We will use manual one-hot encoding representation to keep it light and serializable
        for col in self.categorical_cols:
            unique_vals = sorted(df[col].dropna().unique())
            self.category_mappings[col] = unique_vals
            for val in unique_vals:
                feature_cols.append(f"{col}_{val}")
        
        # Numerical columns
        for col in self.numerical_cols:
            self.numerical_means[col] = float(df[col].mean())
            self.numerical_stds[col] = float(df[col].std() if df[col].std() > 0 else 1.0)
            feature_cols.append(col)
            
        self.feature_columns_ = feature_cols
        self.fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.fitted:
            raise Exception("Pipeline is not fitted yet!")

        transformed_df = pd.DataFrame(index=df.index)
        
        # 1. Categorical one-hot encoding
        for col in self.categorical_cols:
            unique_vals = self.category_mappings.get(col, [])
            for val in unique_vals:
                # Fill 1 if value matches, else 0
                transformed_df[f"{col}_{val}"] = (df[col] == val).astype(int)

        # 2. Numerical features (with simple imputation + standardization)
        for col in self.numerical_cols:
            val = df[col].fillna(self.numerical_means[col])
            # Standardize
            mean = self.numerical_means[col]
            std = self.numerical_stds[col]
            transformed_df[col] = (val - mean) / std

        # Order columns to match the fitted feature column list exactly
        transformed_df = transformed_df[self.feature_columns_]
        return transformed_df

    def transform_single(self, record: dict) -> pd.DataFrame:
        """Transforms a single dictionary input (from serving API) to a 1-row DataFrame."""
        df = pd.DataFrame([record])
        # Ensure all columns exist, fill missing with defaults/nan
        for col in self.categorical_cols:
            if col not in df.columns:
                df[col] = "unknown"
        for col in self.numerical_cols:
            if col not in df.columns:
                df[col] = np.nan
        return self.transform(df)

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, "rb") as f:
            return pickle.load(f)


def clean_complaint_text(text: str) -> str:
    """Basic cleaning for complaint narrative text."""
    if not isinstance(text, str):
        return ""
    # Lowercase
    text = text.lower()
    # Simple character replacement for basic punctuation/noise removal
    # (keeps it dependency-free and fast)
    for char in [".", ",", "!", "?", ";", ":", "-", "_", "(", ")", "[", "]", "\"", "'", "*", "/", "\\"]:
        text = text.replace(char, " ")
    # Strip double spaces
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


def prepare_complaints_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses a complaints DataFrame in-place or returns a copy."""
    df_copy = df.copy()
    if "consumer_complaint_narrative" in df_copy.columns:
        df_copy["cleaned_narrative"] = df_copy["consumer_complaint_narrative"].apply(clean_complaint_text)
    return df_copy


if __name__ == "__main__":
    # Test block
    print("Testing Feature pipeline...")
    data = {
        "age": [30, 40],
        "job": ["admin.", "technician"],
        "marital": ["single", "married"],
        "education": ["basic.4y", "university.degree"],
        "default": ["no", "no"],
        "housing": ["yes", "no"],
        "loan": ["no", "no"],
        "contact": ["cellular", "cellular"],
        "month": ["may", "may"],
        "day_of_week": ["mon", "mon"],
        "duration": [200, 300],
        "campaign": [1, 2],
        "pdays": [999, 999],
        "previous": [0, 0],
        "poutcome": ["nonexistent", "nonexistent"],
        "emp.var.rate": [1.1, 1.4],
        "cons.price.idx": [93.994, 93.994],
        "cons.conf.idx": [-36.4, -36.4],
        "euribor3m": [4.857, 4.857],
        "nr.employed": [5191.0, 5191.0]
    }
    df = pd.DataFrame(data)
    pipeline = BankMarketingFeaturePipeline()
    pipeline.fit(df)
    trans = pipeline.transform(df)
    print("Transformed shape:", trans.shape)
    print("Columns:", list(trans.columns))
    
    single_record = {
        "age": 35,
        "job": "admin.",
        "marital": "single",
        "education": "university.degree",
        "default": "no",
        "housing": "yes",
        "loan": "no",
        "contact": "cellular",
        "month": "may",
        "day_of_week": "mon",
        "duration": 250,
        "campaign": 1,
        "pdays": 999,
        "previous": 0,
        "poutcome": "nonexistent",
        "emp.var.rate": 1.2,
        "cons.price.idx": 93.9,
        "cons.conf.idx": -36.0,
        "euribor3m": 4.8,
        "nr.employed": 5190.0
    }
    single_trans = pipeline.transform_single(single_record)
    print("Single record transformed shape:", single_trans.shape)
