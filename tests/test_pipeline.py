import os
import pytest
from src.data_pipeline.validate import validate_bank_data, validate_complaints_data

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def test_data_directory_exists():
    assert os.path.exists(DATA_DIR), f"Data directory not found at {DATA_DIR}"

def test_bank_data_validation():
    # Verify that the bank marketing data exists and validates successfully
    bank_csv = os.path.join(DATA_DIR, "bank-additional-full.csv")
    if not os.path.exists(bank_csv):
        bank_csv = os.path.join(DATA_DIR, "bank-additional", "bank-additional-full.csv")
    
    assert os.path.exists(bank_csv), f"Bank marketing data file not found at {bank_csv}"
    assert validate_bank_data() is True, "Bank marketing data validation failed"

def test_complaints_data_validation():
    # Verify that complaints sample file exists and validates successfully
    complaints_csv = os.path.join(DATA_DIR, "complaints_sample.csv")
    assert os.path.exists(complaints_csv), f"Complaints sample data file not found at {complaints_csv}"
    assert validate_complaints_data() is True, "Complaints data validation failed"
