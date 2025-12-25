import os, getpass, pandas as pd
from .pdf_load import load_pdf
from .csv_load import load_csv

def load_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    password = getpass.getpass("PDF Password (blank if none): ") if ext == '.pdf' else None
    
    if ext == '.csv': return load_csv(file_path)
    if ext == '.pdf': return load_pdf(file_path, password)
    return pd.DataFrame(columns=["Description"])

if __name__ == "__main__":
    df = load_file('data/Raw.csv') # Replace with your test file
    print(df.head())