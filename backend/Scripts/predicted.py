import sys
from pathlib import Path
import os
import warnings
import logging
from io import StringIO
from dotenv import load_dotenv
from tabulate import tabulate

# Suppress all UserWarnings including FontBBox from pdfplumber
warnings.simplefilter("ignore", UserWarning)

# Suppress logging messages from pdfplumber and pdfminer
logging.getLogger("pdfplumber").setLevel(logging.ERROR)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# Set BASE_DIR and sys.path FIRST (before any imports)
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load environment variables
load_dotenv()

# Now imports
import joblib
import pandas as pd
import re
import requests
from rapidfuzz import process, fuzz  # Import fuzz for partial_ratio

from rules.category_rules import CATEGORY_RULES
from file_handler.loader import load_file
from Scripts.preprocess import clean_text

# Load ML Pipeline
MODEL_PATH = BASE_DIR / "Scripts" / "model.pkl"

try:
    model = joblib.load(MODEL_PATH)
    print("🤖 ML Pipeline loaded successfully.")
except Exception as e:
    model = None
    print(f"⚠️ ML Model fallback disabled. Error: {e}")

# Google Maps API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("⚠️ Google Maps API key not found in .env. Google Maps integration disabled.")
else:
    print("✅ Google Maps API key loaded successfully.")

def extract_location_from_pdf(pdf_text):
    # Primary: Look for branch/address patterns
    address_match = re.search(r'Branch:\s*([^,]+),\s*([^)]+)', pdf_text, re.IGNORECASE)
    if address_match:
        city = address_match.group(1).strip()
        state = address_match.group(2).strip()
        return f"{city}, {state}"
    
    # Secondary: General location pattern
    general_match = re.search(r'([A-Z][a-z]+),\s*([A-Z][a-z]+)', pdf_text)
    if general_match:
        return f"{general_match.group(1)}, {general_match.group(2)}"
    
    # NEW: Fallback - Scan for common Indian cities in the text
    common_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Pune', 'Hyderabad', 'Ahmedabad']
    for city in common_cities:
        if city.lower() in pdf_text.lower():
            return city  # Return the first match found
    
    return None  # Will default to "Mumbai" in predict_single

def extract_business_name(raw_text):
    """Extract business name from description (handles UPI and non-UPI patterns, more aggressive)."""
    # Primary: UPI pattern
    match = re.search(r'UPI/([^/]+)', raw_text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        # Clean up common suffixes
        name = re.sub(r'/\w+', '', name).strip()
        return name
    
    # Non-UPI patterns (e.g., "Paid to NAME", "Received from NAME", "Transfer to NAME")
    patterns = [
        r'Paid to\s+([A-Z\s]+?)(?:\s+DEBIT|\s+₹|$)',  # "Paid to KIRTISH TABIYAR"
        r'Received from\s+([A-Z\s]+?)(?:\s+CREDIT|\s+₹|$)',  # "Received from GAGANDEEP"
        r'Transfer to\s+([A-Z\s]+?)(?:\s+DEBIT|\s+₹|$)',  # "Transfer to XXXXXXXXXXX0141"
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Remove numbers/masked chars if present (e.g., ******9006 -> skip or clean)
            name = re.sub(r'\*+', '', name).strip()
            if len(name) > 2:  # Avoid very short names
                return name
    
    # Aggressive fallback: Find capitalized words (potential names), skip keywords
    words = raw_text.split()
    skip_keywords = ['paid', 'received', 'transfer', 'upi', 'debit', 'credit', 'transaction', 'id', 'utr', 'no', 'by', 'to', 'from']
    for word in words:
        if word.istitle() and word.lower() not in skip_keywords and len(word) > 2 and not word.isdigit():
            return word  # Return first valid capitalized word
    
    # Final fallback: First word if not a keyword
    first_word = words[0] if words else ""
    if first_word.lower() not in skip_keywords:
        return first_word
    return ""  # Return empty if no good name found

def check_business_with_maps(name, location):
    if not GOOGLE_API_KEY or not location or not name:
        return None
    
    query = f"{name} in {location}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={GOOGLE_API_KEY}"
    
    try:
        response = requests.get(url, timeout=5).json()
        print(f"🔍 Google Maps Query: {query}")
        if response.get('results'):
            place = response['results'][0]
            types = place.get('types', [])
            rating = place.get('rating', 0)
            name_match = place.get('name', '').lower()
            # Updated: Use partial_ratio and lower threshold/rating for noisy UPI names
            if rating >= 3.0 and fuzz.partial_ratio(name.lower(), name_match) > 60:
                if 'restaurant' in types or 'food' in types:
                    return "Food & Dining"
                elif 'gas_station' in types or 'fuel' in types:
                    return "Utilities & Bills"
                elif 'hospital' in types or 'health' in types:
                    return "Health & Wellness"
                elif 'store' in types or 'grocery' in types:
                    return "Shopping & E-commerce"
                # No generic fallback
        print("ℹ️ No strong business match in Google Maps.")
    except Exception as e:
        print(f"❌ Google Maps API error: {e}")
    return None

def predict_single(raw_text, pdf_text=None, amount=0):
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "Others", "N/A", 0
    
    text_clean = clean_text(raw_text)
    
    if not text_clean:
        return "Others", "No Clean Text", 0

    # Strict Pipeline with Voting Ensemble: Exact Rules -> Fuzzy -> ML -> Google Maps
    opinions = []

    # --- Engine A: Exact Rules ---
    for category, keywords in CATEGORY_RULES.items():
        if any(re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_clean) for kw in keywords):
            opinions.append({"cat": category, "score": 0.95, "method": "Exact Rules"})
            break  # Only one exact match

    # --- Engine B: Fuzzy Matching ---
    flattened_rules = {kw.lower(): cat for cat, kws in CATEGORY_RULES.items() for kw in kws}
    fuzzy_match = process.extractOne(text_clean, flattened_rules.keys(), score_cutoff=85)
    if fuzzy_match:
        opinions.append({"cat": flattened_rules[fuzzy_match[0]], "score": 0.80, "method": "Fuzzy Match"})

    # --- Engine C: ML Model ---
    if model:
        try:
            input_df = pd.DataFrame({'Description': [text_clean], 'Amount': [amount]})
            ml_cat = model.predict(input_df)[0]
            ml_score = max(model.predict_proba(input_df)[0]) if hasattr(model, 'predict_proba') else 0.7
            if ml_score > 0.5:
                opinions.append({"cat": ml_cat, "score": ml_score, "method": "ML Model"})
        except Exception as e:
            print(f"⚠️ ML prediction error: {e}")

   # --- Engine D: Google Maps (Highest score, more aggressive) ---
    name = extract_business_name(raw_text)
    if len(name) > 3 and not any(p in name.lower() for p in ["khan", "mushir", "mohd", "noor", "anil", "rahul", "saquib", "ashraf", "manish", "dipit", "mohammed", "y", "z", "ir", "rai", "vege", "ahamd", "nair", "snac", "nadir", "kesha", "rama", "luck", "ind", "ahm", "moh", "arif", "zubair", "ansari"]):
        location = extract_location_from_pdf(pdf_text) or "Mumbai"
        maps_cat = check_business_with_maps(name, location)
        if maps_cat:
            opinions.append({"cat": maps_cat, "score": 0.99, "method": "Google Maps Override"})  # Highest score

    # Agreement Boost: If multiple engines agree on a category, boost score by 0.2
    final_cats = [o['cat'] for o in opinions]
    for op in opinions:
        if final_cats.count(op['cat']) > 1:
            op['score'] += 0.2

    # Maps Tie-Breaker: If Maps disagrees with Rules, give Maps priority
    rules_cats = [o['cat'] for o in opinions if o['method'] == "Exact Rules"]
    maps_op = next((o for o in opinions if o['method'] == "Google Maps Override"), None)
    if maps_op and rules_cats and maps_op['cat'] not in rules_cats:
        maps_op['score'] += 0.1

    # MASTER LOGIC: Pick the opinion with the highest score
    if not opinions:
        return "Others", "Default", 0

    best_opinion = max(opinions, key=lambda x: x['score'])
    
    return best_opinion['cat'], best_opinion['method'], best_opinion['score']

# ✅ ADD THIS FUNCTION (NEW — DO NOT REMOVE ANYTHING ELSE)

def process_file(file_path, password=None):
    """
    This is the bridge between frontend and backend.
    Handles password-protected PDFs + runs full pipeline.
    """

    import pdfplumber

    pdf_text = ""

    # ---------------- PDF TEXT EXTRACTION ----------------
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path, password=password) as pdf:
                pdf_text = "\n".join(
                    page.extract_text(layout=False) or "" 
                    for page in pdf.pages
                )
    except Exception as e:
        return None, f"PDF Error: {e}"

    # ---------------- LOAD FILE (IMPORTANT FIX) ----------------
    try:
        df_full = load_file(file_path, password=password)   # ✅ FIXED
    except TypeError:
        # fallback if loader not updated yet
        df_full = load_file(file_path)

    if df_full is None or df_full.empty:
        return None, "No data found"

    df = df_full.copy()

    # ---------------- PREDICTION ----------------
    try:
        if 'Amount' in df.columns:
            results = df.apply(
                lambda row: predict_single(
                    row.get('Description', ''),
                    pdf_text,
                    row.get('Amount', 0)
                ),
                axis=1
            )
        else:
            results = df['Description'].apply(
                lambda x: predict_single(x, pdf_text)
            )

        df[['Predicted_Category', 'Method', 'Confidence']] = pd.DataFrame(
            results.tolist(), index=df.index
        )

    except Exception as e:
        return None, f"Prediction Error: {e}"

    return df, None

def run_batch_test(file_name):
    input_path = BASE_DIR / "data" / file_name
    output_path = BASE_DIR / "data" / "final_categorized_results_with_corrections.csv"
    
    if not input_path.exists():
        print(f"❌ Error: {file_name} not found.")
        return

    pdf_text = ""
    try:
        import pdfplumber
        # Added: Handle password-protected PDFs (prompt for password if needed)
        password = None
        try:
            with pdfplumber.open(str(input_path)) as pdf:
                pdf_text = "\n".join(page.extract_text(layout=False) or "" for page in pdf.pages)
        except pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect:
            password = input("Enter PDF password: ")
            with pdfplumber.open(str(input_path), password=password) as pdf:
                pdf_text = "\n".join(page.extract_text(layout=False) or "" for page in pdf.pages)
        # Added: Extract tables with rows/columns (from old code)
        all_rows = []
        all_text = []
        with pdfplumber.open(str(input_path), password=password) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        all_rows.extend(table)
                all_text.append(page.extract_text(layout=False) or "")
        pdf_text = "\n".join(all_text)
        print(f"Total all_rows: {len(all_rows)}, Total all_text: {len(all_text)}")
    except Exception as e:
        print(f"⚠️ PDF text extraction error: {e}")
    
    df_full = load_file(str(input_path), password=password)  # Integrated file_handler.loader
    
    print(f"Loaded DataFrame columns: {df_full.columns.tolist()}")
    print(f"Sample data:\n{df_full.head()}")
    
    if df_full.empty:
        print("❌ No data found.")
        return
    
    if 'Type' in df_full.columns and 'Amount' in df_full.columns:
        df_full['Amount'] = df_full['Amount'].astype(str).str.replace('₹', '').str.replace(',', '').astype(float)
        total_credit = df_full[df_full['Type'] == 'CREDIT']['Amount'].sum()
        total_debit = df_full[df_full['Type'] == 'DEBIT']['Amount'].sum()
        net_balance = total_credit - total_debit
        net_status = "Surplus (Positive Rupees)" if net_balance > 0 else "Deficit (Negative Rupees)" if net_balance < 0 else "Balanced"
    else:
        total_credit = total_debit = net_balance = 0
        net_status = "Data unavailable (missing Type/Amount columns)"
    
    # Process all transactions (both DEBIT and CREDIT)
    df = df_full.copy()
    
    if df.empty:
        print("⚠️ No DEBIT transactions found for categorization.")
        return
    
    print(f"⚙️ Processing {len(df)} expense transactions...")

    # Pass Amount to predict_single if available
    if 'Amount' in df.columns:
        results = df.apply(lambda row: predict_single(row['Description'], pdf_text, row['Amount']), axis=1)
    else:
        results = df['Description'].apply(lambda x: predict_single(x, pdf_text))
    
    df[['Predicted_Category', 'Method', 'Confidence']] = pd.DataFrame(results.tolist(), index=df.index)
    
    # Add User_Corrected_Category column (for Streamlit app)
    df['User_Corrected_Category'] = None
    
    # Save full results to CSV (no console prompts)
    df.to_csv(output_path, index=False)
    
    # Print table in readable format
    print("\n" + "="*80)
    print(f"📊 DETAILED RESULTS TABLE FOR: {file_name}")
    print("="*80)
    table_data = df[['Date','Description', 'Predicted_Category', 'Method', 'Confidence', 'User_Corrected_Category']].head(20)
    print(tabulate(table_data, headers='keys', tablefmt='grid', showindex=False))
    if len(df) > 20:
        print(f"... and {len(df) - 20} more rows. Full data saved to {output_path}")
    
    print("\n" + "-"*40)
    print(f"✅ Rules/Fuzzy/ML Coverage: {((df['Method'] != 'Default').mean()*100):.1f}%")
    print(f"\n📂 Top Expense Categories:\n{df['Predicted_Category'].value_counts().head()}")
    print(f"\n🛠️ Logic Breakdown:\n{df['Method'].value_counts()}")
    print(f"\n💰 Financial Summary:")
    print(f"Total Income (CREDIT): ₹{total_credit:,.2f}")
    print(f"Total Expenses (DEBIT): ₹{total_debit:,.2f}")
    print(f"Net Balance: ₹{net_balance:,.2f} ({net_status})")
    print("="*80)

if __name__ == "__main__":
    run_batch_test("canara_epassbook.pdf")