import joblib
import re
import sys
import pandas as pd
from pathlib import Path

# Fix for the Line 3 error: allow Python to see the 'ml' and 'rules' folders
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from rules.category_rules import CATEGORY_RULES

# ---------------------------
# Step 1: Rule-based matching
# ---------------------------
def rule_based_category(text):
    if not isinstance(text, str): return None
    text = text.lower()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in text:
                return category
    return None

# ---------------------------
# 🚀 BATCH PROCESSING WORKFLOW (Using Pathlib)
# ---------------------------
def run_batch_test(file_name):
    # Construct paths using Pathlib '/' operator
    input_path = BASE_DIR / "data" / file_name
    output_path = BASE_DIR / "data" / "batch_results.csv"
    
    if not input_path.exists():
        print(f"❌ Error: {file_name} not found in {input_path.parent}")
        return

    # 1. Load the CSV
    df = pd.read_csv(input_path)
    
    # 2. Identify the column
    possible_cols = ['Transaction Description', 'description', 'Details', 'Narration']
    col_name = next((c for c in possible_cols if c in df.columns), df.columns[0])
    
    print(f"⚙️  Starting Batch Processing: {file_name}")

    # 3. Apply rules to the WHOLE file at once (Pandas Batching)
    df['Predicted_Category'] = df[col_name].apply(rule_based_category)

    # 4. Save results
    df.to_csv(output_path, index=False)
    
    # 5. Show Batch Summary
    total = len(df)
    matched = df['Predicted_Category'].notna().sum()
    print("-" * 30)
    print(f"✅ Success: Processed {total} rows.")
    print(f"📊 Rules Matched: {matched} | Coverage: {(matched/total)*100:.1f}%")
    print(f"💾 Results saved to: {output_path.name}")
    print("-" * 30)

if __name__ == "__main__":
    # Ensure this name matches your file in the /data/ folder
    run_batch_test("bank_statement.csv")