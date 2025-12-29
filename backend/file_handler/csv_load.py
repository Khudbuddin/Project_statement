import pandas as pd
import regex as re
def load_csv(file_path):
    df = pd.read_csv(file_path)
    df.columns = [str(c).lower().strip() for c in df.columns]
    print(f"CSV loaded with {len(df)} rows. Columns: {list(df.columns)}")
    
    headers = ['description', 'particulars', 'remarks', 'narration', 'details', 'transaction description']  # Added your column
    patterns = ['upi/', '/inf/', 'transfer', 'chq', 'cash', 'neft']
    
    # Identify column
    target = next((c for c in df.columns if any(k in c for k in headers)), None)
    if not target:
        target = next((c for c in df.columns if any(p in " ".join(df[c].head(5).astype(str)).lower() for p in patterns)), None)
    
    print(f"Target column: {target}")
    
    if target:
        df = df.rename(columns={target: "Description"})
        # Flexible date filtering: Try multiple patterns, and if none match, skip filtering
        date_patterns = [r'\d{2}[/-]\d{2}[/-]\d{4}', r'\d{4}[/-]\d{2}[/-]\d{2}', r'\d{1,2} \w{3} \d{4}']  # DD/MM/YYYY, YYYY-MM-DD, DD Mon YYYY
        mask = df.apply(lambda r: any(re.search(p, str(r)) for p in date_patterns), axis=1)
        filtered_df = df[mask] if mask.any() else df  # If no dates found, use all rows
        print(f"Rows after date filtering: {len(filtered_df)}")
        return filtered_df[["Description"]].reset_index(drop=True)
    
    print("No suitable column found.")
    return pd.DataFrame(columns=["Description"])