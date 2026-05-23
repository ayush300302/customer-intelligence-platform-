import pytest
from pydantic import ValidationError
from src.serving.schemas import CustomerFeatures, AskComplaintsRequest, CustomerIntelRequest

def test_customer_features_valid():
    payload = {
        "age": 30,
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
        "emp.var.rate": 1.1,
        "cons.price.idx": 93.994,
        "cons.conf.idx": -36.4,
        "euribor3m": 4.857,
        "nr.employed": 5191.0
    }
    features = CustomerFeatures(**payload)
    assert features.age == 30
    assert features.job == "admin."

def test_customer_features_invalid():
    # Missing required field
    payload = {
        "age": 30,
        "job": "admin."
    }
    with pytest.raises(ValidationError):
        CustomerFeatures(**payload)

def test_ask_complaints_schema():
    payload = {
        "question": "What is the status of my claim?",
        "company": "Equifax"
    }
    req = AskComplaintsRequest(**payload)
    assert req.question == "What is the status of my claim?"
    assert req.company == "Equifax"
    assert req.product is None
