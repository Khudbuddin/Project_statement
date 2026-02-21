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
import requests  # For Google Maps API
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

# Google Maps API Key (Replace with your key)
GOOGLE_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"  # Get from Google Cloud Console

def extract_location_from_pdf(pdf_text):
    """Extract location (city, state) from PDF text."""
    # Look for patterns like "Branch: Mumbai, Maharashtra" or "Delhi, India"
    address_match = re.search(r'Branch:\s*([^,]+),\s*([^)]+)', pdf_text, re.IGNORECASE)
    if address_match:
        city = address_match.group(1).strip()
        state = address_match.group(2).strip()
        return f"{city}, {state}"
    # Fallback: General location
    general_match = re.search(r'([A-Z][a-z]+),\s*([A-Z][a-z]+)', pdf_text)
    if general_match:
        return f"{general_match.group(1)}, {general_match.group(2)}"
    return None  # No location found

def check_business_with_maps(name, location):
    """Query Google Maps to check if name is a business."""
    if not GOOGLE_API_KEY or not location:
        return None  # Skip if no key or location
    
    query = f"{name} store in {location}"  # e.g., "gaurav store in Delhi"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={GOOGLE_API_KEY}"
    
    try:
        response = requests.get(url, timeout=5).json()
        if response.get('results'):
            place = response['results'][0]
            # Check if it's a business (types include 'store', 'restaurant', etc.)
            types = place.get('types', [])
            rating = place.get('rating', 0)
            if any(t in types for t in ['store', 'restaurant', 'food', 'grocery', 'shop']) or rating > 4:
                # Map to category based on types
                if 'restaurant' in types or 'food' in types:
                    return "Food & Dining"
                elif 'store' in types or 'grocery' in types:
                    return "Shopping & E-commerce"
                elif 'hospital' in types or 'health' in types:
                    return "Health & Wellness"
                else:
                    return "Shopping & E-commerce"  # Default for businesses
    except Exception as e:
        print(f"Google Maps API error: {e}")
    return None  # Not a business or error

def predict_single(raw_text, pdf_text=None):
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
    prediction, method = "Others", "Default"
    confidence = 0
    if model and vectorizer:
        try:
            vec_text = vectorizer.transform([text_clean])
            prediction = model.predict(vec_text)[0]
            # Assuming model has predict_proba; if not, skip confidence
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(vec_text)[0]
                confidence = max(proba)
            method = "ML Model"
        except:
            pass
    
    # NEW: Stage 4: Google Maps Override for Ambiguous Cases
    if prediction == "Transfers (Personal/UPI)" and confidence < 0.8 and pdf_text:
        location = extract_location_from_pdf(pdf_text)
        name = raw_text.split()[0] if raw_text else ""  # Extract name (e.g., "gaurav")
        maps_category = check_business_with_maps(name, location)
        if maps_category:
            prediction = maps_category
            method = "Google Maps Override"
    
    return prediction, method

def run_batch_test(file_name):
    input_path = BASE_DIR / "data" / file_name
    output_path = BASE_DIR / "data" / "final_categorized_results.csv"
    
    if not input_path.exists():
        print(f"❌ Error: {file_name} not found.")
        return

    # Load PDF and extract text for location
    pdf_text = ""
    try:
        import pdfplumber
        with pdfplumber.open(str(input_path)) as pdf:
            pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except:
        pass  # Fallback if PDF loading fails
    
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

    # Pass pdf_text to predict_single for Maps integration
    results = df['Description'].apply(lambda x: predict_single(x, pdf_text))
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