import joblib
import pandas as pd
import re
import sys
from pathlib import Path
from rapidfuzz import process  # pip install rapidfuzz

# Fix pathing: Set BASE_DIR to project root
BASE_DIR = Path(__file__).resolve().parent.parent 
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Import your specific rules and preprocessing logic
from rules.category_rules import CATEGORY_RULES
from file_handler.loader import load_file
from Scripts.preprocess import clean_text  # Using your specific NLTK-based cleaner

# 1. LOAD ML ASSETS
MODEL_PATH = BASE_DIR / "ml" / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "ml" / "vectorizer.pkl"

try:
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    print("🤖 ML Model & Vectorizer loaded successfully.")
except Exception as e:
    model, vectorizer = None, None
    print(f"⚠️ ML Model fallback disabled. Error: {e}")

def predict_single(raw_text):
    """
    Classification Waterfall: 
    Preprocess -> Exact Rules -> Fuzzy Matching -> ML Model
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "Others", "N/A"
    
    # --- STEP 0: PREPROCESSING (Using your NLTK logic) ---
    # This removes 'upi', 'rs', 'txn', and stopwords like 'the', 'is'
    text_clean = clean_text(raw_text)
    
    if not text_clean:
        return "Others", "No Clean Text"

    # --- STAGE 1: EXACT RULE MATCHING ---
    for category, keywords in CATEGORY_RULES.items():
        # Check if any keyword exists in the cleaned text
        if any(kw.lower() in text_clean for kw in keywords):
            return category, "Exact Rules"

    # --- STAGE 2: FUZZY MATCHING ---
    # Catches typos like 'zomto' or 'swiggi'
    flattened_rules = {kw.lower(): cat for cat, kws in CATEGORY_RULES.items() for kw in kws}
    fuzzy_match = process.extractOne(text_clean, flattened_rules.keys(), score_cutoff=85)
    
    if fuzzy_match:
        matched_keyword = fuzzy_match[0]
        return flattened_rules[matched_keyword], "Fuzzy Match"

    # --- STAGE 3: MACHINE LEARNING ---
    if model and vectorizer:
        try:
            vec_text = vectorizer.transform([text_clean])
            prediction = model.predict(vec_text)[0]
            return prediction, "ML Model"
        except:
            pass
    
    return "Others", "Default"

def run_batch_test(file_name):
    """Full workflow: Load -> Clean -> Categorize -> Summary"""
    input_path = BASE_DIR / "data" / file_name
    output_path = BASE_DIR / "data" / "final_categorized_results.csv"
    
    if not input_path.exists():
        print(f"❌ Error: {file_name} not found.")
        return

    # Use your smart loader (pdfplumber + OCR)
    df = load_file(str(input_path))
    
    if df.empty:
        print("❌ No data found.")
        return
    
    print(f"⚙️ Processing {len(df)} transactions...")

    # Apply categorization
    results = df['Description'].apply(lambda x: predict_single(x))
    df[['Predicted_Category', 'Method']] = pd.DataFrame(results.tolist(), index=df.index)

    # Save
    df.to_csv(output_path, index=False)
    
    print("\n" + "="*40)
    print(f"📊 SUMMARY FOR: {file_name}")
    print("-" * 40)
    print(f"✅ Rules/Fuzzy/ML Coverage: {((df['Method'] != 'Default').mean()*100):.1f}%")
    print(f"\n📂 Top Categories:\n{df['Predicted_Category'].value_counts().head()}")
    print(f"\n🛠️ Logic Breakdown:\n{df['Method'].value_counts()}")
    print("="*40)

if __name__ == "__main__":
    # Ensure this file exists in your /data/ folder
    run_batch_test("batch_results.csv")