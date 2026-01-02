import pdfplumber, pandas as pd, re, pytesseract

pytesseract.pytesseract.tesseract_cmd = r'D:\smart-expense-categorizer\Tesser-OCR\tesseract.exe'

def extract_location(all_text):
    """Extract location (city, state) from PDF text."""
    # Example: Extract address from text
    address_match = re.search(r'Branch:\s*([^,]+),\s*([^)]+)', all_text, re.IGNORECASE)
    if address_match:
        city = address_match.group(1).strip()
        state = address_match.group(2).strip()
        return f"{city}, {state}"
    # Fallback: General location pattern
    general_match = re.search(r'([A-Z][a-z]+),\s*([A-Z][a-z]+)', all_text)
    if general_match:
        return f"{general_match.group(1)}, {general_match.group(2)}"
    return None  # No location found

def load_pdf(file_path, password=None):
    all_rows, all_text = [], []
    try:
        with pdfplumber.open(file_path, password=password) as pdf:
            print(f"PDF has {len(pdf.pages)} pages.")
            for page in pdf.pages:
                table = page.extract_table()
                if table: 
                    all_rows.extend(table)
                    print(f"Table found on page {page.page_number} with {len(table)} rows.")
                
                text = page.extract_text()
                if text:
                    all_text.append(text)
                    print(f"Text extracted from page {page.page_number}: {text[:100]}...")
                else:
                    print(f"No text on page {page.page_number}, attempting OCR...")
                    image = page.to_image(resolution=300).original
                    ocr_text = pytesseract.image_to_string(image)
                    if ocr_text.strip():
                        all_text.append(ocr_text)
                        print(f"OCR extracted: {ocr_text[:100]}...")
                    else:
                        print("OCR failed to extract text.")
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return pd.DataFrame(columns=["Description"])

    print(f"Total all_rows: {len(all_rows)}, Total all_text: {len(all_text)}")

    # Extract location from all_text
    location = extract_location("\n".join(all_text))
    print(f"Extracted Location: {location}")

    if all_rows:
        df = pd.DataFrame(all_rows).replace(r'\n', ' ', regex=True)
        print(f"Raw table DF shape: {df.shape}")
        
        # Find column using keywords or content signatures
        headers = ['remarks', 'particulars', 'description', 'narration', 'details']
        patterns = ['upi/', 'cash', 'chq', 'transfer', 'neft', 'rtgs']
        
        target_idx = next((i for i, c in enumerate(df.iloc[0]) if any(k in str(c).lower() for k in headers)), None)
        if target_idx is None:
            target_idx = next((i for i in range(len(df.columns)) if any(p in " ".join(df.iloc[:5, i].astype(str)).lower() for p in patterns)), None)

        print(f"Target column index: {target_idx}")

        if target_idx is not None:
            date_regex = r'\b(?:\d{1,2} \w{3}|\w{3} \d{1,2}), \d{4}\b'
            final, current = [], ""
            for _, row in df.iterrows():
                val = str(row[target_idx]).strip()
                if val.lower() in headers: continue
                if re.search(date_regex, " ".join(row.astype(str))):
                    if current: final.append(current)
                    current = val
                else: current += " " + val
            if current: final.append(current)
            result_df = pd.DataFrame(final, columns=["Description"]).query("Description.str.len() > 5")
            print(f"Extracted {len(result_df)} descriptions from tables.")
            
            # NEW: If no descriptions extracted, fall back to text parsing
            if len(result_df) == 0:
                print("No descriptions from tables. Falling back to text parsing...")
                return parse_text_for_descriptions(all_text, location)

            # Add Location column
            result_df['Location'] = location
            return result_df

    print("No tables found. Parsing text...")
    return parse_text_for_descriptions(all_text, location)

def parse_text_for_descriptions(all_text, location=None):
    print(f"Parsing all_text with {len(all_text)} items.")
    pattern = r'\b(?:\d{1,2} \w{3}|\w{3} \d{1,2}), \d{4}\b'
    data, current = [], ""
    for line in "\n".join(all_text).split('\n'):
        if len(line) < 10: continue
        if re.search(pattern, line):
            if current:
                # Extract Type and Amount for the current description
                transaction_type, amount = extract_type_and_amount(current)
                data.append({'Description': current, 'Type': transaction_type, 'Amount': amount})
            current = re.sub(pattern, '', line).strip()
        else: current += " " + line
    if current:
        transaction_type, amount = extract_type_and_amount(current)
        data.append({'Description': current, 'Type': transaction_type, 'Amount': amount})
    result_df = pd.DataFrame(data).reset_index(drop=True)
    # Add Location column
    result_df['Location'] = location
    print(f"Extracted {len(result_df)} descriptions from text/OCR.")
    return result_df

def extract_type_and_amount(description):
    # Extract Type: CREDIT or DEBIT from text
    if 'CREDIT' in description.upper():
        transaction_type = 'CREDIT'
    elif 'DEBIT' in description.upper():
        transaction_type = 'DEBIT'
    else:
        transaction_type = 'UNKNOWN'
    
    # Extract Amount: Look for ₹ followed by number
    amount_match = re.search(r'₹([\d,]+(?:\.\d{2})?)', description)
    amount = amount_match.group(1) if amount_match else '0'
    
    return transaction_type, amount