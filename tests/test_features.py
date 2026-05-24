import pytest
import pandas as pd
import numpy as np
from src.data_pipeline.features import clean_complaint_text, BankMarketingFeaturePipeline

def test_clean_complaint_text():
    raw_text = "I have a billing dispute!! Experian's credit report contains error; (ID: 12345)."
    expected = "i have a billing dispute experian s credit report contains error id 12345"
    assert clean_complaint_text(raw_text) == expected

def test_feature_pipeline_fit_transform():
    data = {
        "age": [25, 45, 60],
        "job": ["admin.", "technician", "blue-collar"],
        "marital": ["single", "married", "divorced"],
        "education": ["university.degree", "basic.4y", "high.school"],
        "default": ["no", "no", "unknown"],
        "housing": ["yes", "no", "yes"],
        "loan": ["no", "no", "no"],
        "contact": ["cellular", "telephone", "cellular"],
        "month": ["may", "jun", "jul"],
        "day_of_week": ["mon", "tue", "wed"],
        "duration": [120, 240, 360],
        "campaign": [1, 2, 3],
        "pdays": [999, 999, 6],
        "previous": [0, 0, 1],
        "poutcome": ["nonexistent", "nonexistent", "failure"],
        "emp.var.rate": [1.1, -1.8, -1.2],
        "cons.price.idx": [93.994, 92.893, 92.431],
        "cons.conf.idx": [-36.4, -46.2, -30.1],
        "euribor3m": [4.857, 1.258, 0.819],
        "nr.employed": [5191.0, 5099.1, 5017.5]
    }
    df = pd.DataFrame(data)
    
    pipeline = BankMarketingFeaturePipeline()
    pipeline.fit(df)
    
    assert pipeline.fitted
    
    transformed_df = pipeline.transform(df)
    
    # Check shape
    assert transformed_df.shape[0] == 3
    assert "age" in transformed_df.columns
    assert "duration" in transformed_df.columns
    assert "job_admin." in transformed_df.columns
    
    # Check single transform to ensure no train-serving skew
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
        "duration": 200,
        "campaign": 1,
        "pdays": 999,
        "previous": 0,
        "poutcome": "nonexistent",
        "emp.var.rate": 1.1,
        "cons.price.idx": 93.994,
        "cons.conf.idx": -36.4,
        "euribor3m": 4.857,
        "nr.employed": 5191.0
    }
    
    single_trans = pipeline.transform_single(single_record)
    assert single_trans.shape[0] == 1
    assert list(single_trans.columns) == list(transformed_df.columns)
