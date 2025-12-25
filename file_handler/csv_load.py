import pandas as pd
import re

def load_csv(file_path):
    df = pd.read_csv(file_path)
    df.columns = [str(c).lower().strip() for c in df.columns]

    target_col = None
    # 1. Header Keyword Check
    known_headers = ['description', 'particulars', 'remarks', 'narration', 'details',]
    for col in df.columns:
        if any(key in col for key in known_headers):
            target_col = col
            break

    # 2. Content Fingerprinting (Fallback)
    if target_col is None:
        banking_patterns = ['upi/', '/inf/', 'transfer', 'chq', 'cash', 'neft', 'rtgs']
        for col in df.columns:
            sample_data = " ".join(df[col].head(5).astype(str)).lower()
            if any(pattern in sample_data for pattern in banking_patterns):
                target_col = col
                break

    if target_col:
        df = df.rename(columns={target_col: "Description"})
        date_pattern = r'\d{2}[/-]\d{2}[/-]\d{4}'
        # Clean rows that don't look like transactions
        for col in df.columns:
            if df[col].astype(str).str.contains(date_pattern).any():
                df = df[df[col].astype(str).str.contains(date_pattern, na=False)]
                break
        return df[["Description"]].reset_index(drop=True)
    
    return pd.DataFrame(columns=["Description"])