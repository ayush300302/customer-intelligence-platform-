import os
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def validate_bank_data():
    bank_csv = os.path.join(DATA_DIR, "bank-additional-full.csv")
    if not os.path.exists(bank_csv):
        # Fallback to bank-additional.csv or just bank.csv if full is not there
        bank_csv = os.path.join(DATA_DIR, "bank-additional", "bank-additional-full.csv")
        if not os.path.exists(bank_csv):
            print(f"File not found: {bank_csv}")
            return False

    print(f"Validating {bank_csv}...")
    df = pd.read_csv(bank_csv, sep=";")
    
    schema = DataFrameSchema({
        "age": Column(int, Check.ge(17)),
        "job": Column(str),
        "marital": Column(str),
        "education": Column(str),
        "default": Column(str, Check.isin(["no", "yes", "unknown"])),
        "housing": Column(str, Check.isin(["no", "yes", "unknown"])),
        "loan": Column(str, Check.isin(["no", "yes", "unknown"])),
        "y": Column(str, Check.isin(["no", "yes"]))
    })
    
    try:
        schema.validate(df)
        print("Bank Marketing Data Validated Successfully.")
        return True
    except pa.errors.SchemaError as e:
        print(f"Validation failed for Bank Data: {e}")
        return False

def validate_complaints_data():
    complaints_csv = os.path.join(DATA_DIR, "complaints_sample.csv")
    if not os.path.exists(complaints_csv):
        print(f"File not found: {complaints_csv}")
        return False

    print(f"Validating {complaints_csv}...")
    df = pd.read_csv(complaints_csv)

    schema = DataFrameSchema({
        "product": Column(str, nullable=True),
        "issue": Column(str, nullable=True),
        "company": Column(str, nullable=True),
        "date_received": Column(str, nullable=True),
        # Assuming narrative field could be 'complaint_what_happened' or similar, let's keep it loose
    })
    
    try:
        schema.validate(df)
        print("Complaints Data Validated Successfully.")
        return True
    except pa.errors.SchemaError as e:
        print(f"Validation failed for Complaints Data: {e}")
        return False

if __name__ == "__main__":
    bank_valid = validate_bank_data()
    complaints_valid = validate_complaints_data()
    
    if not bank_valid or not complaints_valid:
        print("Data Validation Failed.")
        exit(1)
    else:
        print("All data validated.")
