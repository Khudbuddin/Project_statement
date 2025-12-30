import sys
from pathlib import Path

# Set BASE_DIR and sys.path FIRST (before any imports)
BASE_DIR = Path(__file__).resolve().parent.parent  # Project root
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))  # Use insert(0) for priority

# Now imports will work
import joblib
import pandas as pd
import re
from rapidfuzz import process

from rules.category_rules import CATEGORY_RULES
from file_handler.loader import load_file
from Scripts.preprocess import clean_text

# Load ML
MODEL_PATH = BASE_DIR / "Scripts" / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "Scripts" / "vectorizer.pkl"

try:
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    print("🤖 ML Model & Vectorizer loaded successfully.")
except Exception as e:
    model, vectorizer = None, None
    print(f"⚠️ ML Model fallback disabled. Error: {e}")

def predict_single(raw_text):
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "Others", "N/A"
    
    text_clean = clean_text(raw_text)
    
    if not text_clean:
        return "Others", "No Clean Text"

    # Stage 1: Exact Rules
    for category, keywords in CATEGORY_RULES.items():
        if any(kw.lower() in text_clean for kw in keywords):
            return category, "Exact Rules"

    # Stage 2: Fuzzy Matching
    flattened_rules = {kw.lower(): cat for cat, kws in CATEGORY_RULES.items() for kw in kws}
    fuzzy_match = process.extractOne(text_clean, flattened_rules.keys(), score_cutoff=85)
    
    if fuzzy_match:
        matched_keyword = fuzzy_match[0]
        return flattened_rules[matched_keyword], "Fuzzy Match"

    # Stage 3: ML
    if model and vectorizer:
        try:
            vec_text = vectorizer.transform([text_clean])
            prediction = model.predict(vec_text)[0]
            return prediction, "ML Model"
        except:
            pass
    
    return "Others", "Default"

def run_batch_test(file_name):
    input_path = BASE_DIR / "data" / file_name
    output_path = BASE_DIR / "data" / "final_categorized_results.csv"
    
    if not input_path.exists():
        print(f"❌ Error: {file_name} not found.")
        return

    df_full = load_file(str(input_path))
    
    # DEBUG: Print DataFrame info
    print(f"Loaded DataFrame columns: {df_full.columns.tolist()}")
    print(f"Sample data:\n{df_full.head()}")
    
    if df_full.empty:
        print("❌ No data found.")
        return
    
    # Financial Summaries
    if 'Type' in df_full.columns and 'Amount' in df_full.columns:
        df_full['Amount'] = df_full['Amount'].astype(str).str.replace('₹', '').str.replace(',', '').astype(float)
        total_credit = df_full[df_full['Type'] == 'CREDIT']['Amount'].sum()
        total_debit = df_full[df_full['Type'] == 'DEBIT']['Amount'].sum()
        net_balance = total_credit - total_debit
        net_status = "Surplus (Positive Rupees)" if net_balance > 0 else "Deficit (Negative Rupees)" if net_balance < 0 else "Balanced"
    else:
        total_credit = total_debit = net_balance = 0
        net_status = "Data unavailable (missing Type/Amount columns)"
    
    # Filter to DEBIT for expenses
    if 'Type' in df_full.columns:
        df = df_full[df_full['Type'] == 'DEBIT'].copy()
    else:
        df = df_full.copy()  # Fallback if no Type column
    
    if df.empty:
        print("⚠️ No DEBIT transactions found for categorization.")
        return
    
    print(f"⚙️ Processing {len(df)} expense transactions...")

    results = df['Description'].apply(lambda x: predict_single(x))
    df[['Predicted_Category', 'Method']] = pd.DataFrame(results.tolist(), index=df.index)

    df.to_csv(output_path, index=False)
    
    print("\n" + "="*40)
    print(f"📊 SUMMARY FOR: {file_name}")
    print("-" * 40)
    print(f"✅ Rules/Fuzzy/ML Coverage: {((df['Method'] != 'Default').mean()*100):.1f}%")
    print(f"\n📂 Top Expense Categories:\n{df['Predicted_Category'].value_counts().head()}")
    print(f"\n🛠️ Logic Breakdown:\n{df['Method'].value_counts()}")
    print(f"\n💰 Financial Summary:")
    print(f"Total Income (CREDIT): ₹{total_credit:,.2f}")
    print(f"Total Expenses (DEBIT): ₹{total_debit:,.2f}")
    print(f"Net Balance: ₹{net_balance:,.2f} ({net_status})")
    print("="*40)

if __name__ == "__main__":
    run_batch_test("zahir.pdf")