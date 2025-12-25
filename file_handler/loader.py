import pdfplumber
import pandas as pd
import re
import pytesseract
from PIL import Image
import os  # For file extension check
import getpass  # For secure password input

# Set Tesseract path (update this to your exact path, e.g., D:\smart-expense-categorizer\tesseract.exe)
pytesseract.pytesseract.tesseract_cmd = r'D:\smart-expense-categorizer\tesseract.exe'

def load_file(file_path, password=None):
    print(f"Loading {file_path}...")
    
    # Check file extension
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.csv':
        return load_csv(file_path)
    elif file_extension.lower() == '.pdf':
        return load_pdf(file_path, password)
    else:
        print(f"Unsupported file type: {file_extension}. Only .pdf and .csv are supported.")
        return pd.DataFrame(columns=["Description"])

def load_pdf(file_path, password=None):
    all_rows = []
    all_text = []
    
    try:
        with pdfplumber.open(file_path, password=password) as pdf:  # Added password support
            print(f"PDF has {len(pdf.pages)} pages.")
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    print(f"Table found on page {page.page_number} with {len(table)} rows.")
                    all_rows.extend(table)
                text = page.extract_text()
                if text:
                    all_text.append(text)
                    print(f"Text extracted from page {page.page_number}.")
                else:
                    # OCR fallback for image-based pages
                    print(f"No text on page {page.page_number}. Attempting OCR...")
                    image = page.to_image(resolution=300).original  # High res for better OCR
                    ocr_text = pytesseract.image_to_string(image)
                    if ocr_text.strip():
                        all_text.append(ocr_text)
                        print("OCR extracted text.")
                    else:
                        print("OCR failed to extract text.")
    except Exception as e:
        print(f"Error opening PDF: {e}")
        if "password" in str(e).lower():
            print("This PDF is password-protected. Please provide the password.")
        return pd.DataFrame(columns=["Description"])
    
    if not all_rows and not all_text:
        print("No tables or text extracted.")
        return pd.DataFrame(columns=["Description"])
    
    # Process tables if available
    if all_rows:
        raw_df = pd.DataFrame(all_rows).replace(r'\n', ' ', regex=True)
        if len(raw_df) <= 1:
            print("Table has no data rows. Falling back to text/OCR parsing.")
            return parse_text_for_descriptions(all_text)
        
        # Column detection
        target_idx = None
        known_headers = ['remarks', 'particulars', 'description', 'narration', 'details', 'transaction details']
        banking_patterns = ['upi/', 'cash', 'chq', 'transfer', 'neft', 'rtgs', 'atm', 'debit', 'credit', 'payment', 'withdrawal', 'deposit']
        
        for i, col_val in enumerate(raw_df.iloc[0]):
            if any(key in str(col_val).lower() for key in known_headers):
                target_idx = i
                print(f"Header match: Column {i} ({col_val})")
                break
        
        if target_idx is None:
            for col_idx in range(len(raw_df.columns)):
                sample_text = " ".join(raw_df.iloc[:min(10, len(raw_df)), col_idx].astype(str)).lower()
                if any(p in sample_text for p in banking_patterns):
                    target_idx = col_idx
                    print(f"Content match: Column {col_idx}")
                    break
        
        if target_idx is None:
            print("No description column. Falling back to text/OCR parsing.")
            return parse_text_for_descriptions(all_text)
        
        # Extraction & merging
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b|\b\d{1,2} \w{3} \d{4}\b'
        final_data = []
        current_desc = ""
        
        for _, row in raw_df.iterrows():
            row_content = " ".join(row.astype(str))
            is_new_txn = re.search(date_pattern, row_content)
            val_desc = str(row[target_idx]).strip()
            
            if val_desc.lower() in known_headers:
                continue
            
            if is_new_txn:
                if current_desc:
                    final_data.append(current_desc)
                current_desc = val_desc
            else:
                if val_desc and val_desc.lower() != 'none' and val_desc != "":
                    current_desc += " " + val_desc
        
        if current_desc:
            final_data.append(current_desc)
        
        df = pd.DataFrame(final_data, columns=["Description"])
        df = df[df['Description'].str.len() > 5]
        print(f"Extracted {len(df)} descriptions from tables.")
        
        # If no descriptions extracted, fall back to text/OCR
        if len(df) == 0:
            print("No descriptions from tables. Falling back to text/OCR parsing.")
            return parse_text_for_descriptions(all_text)
        
        return df.reset_index(drop=True)
    
    # Fallback to text/OCR parsing
    print("Parsing text/OCR for descriptions...")
    return parse_text_for_descriptions(all_text)

def load_csv(file_path):
    df = pd.read_csv(file_path)
    df.columns = [str(c).lower().strip() for c in df.columns]

    target_col = None
    # 1. Header Keyword Check
    known_headers = ['description', 'particulars', 'remarks', 'narration', 'details']
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

def parse_text_for_descriptions(all_text):
    final_data = []
    date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b|\b\d{1,2} \w{3} \d{4}\b'
    current_desc = ""
    
    for page_text in all_text:
        lines = page_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            is_new_txn = re.search(date_pattern, line)
            if is_new_txn:
                if current_desc:
                    final_data.append(current_desc)
                current_desc = re.sub(date_pattern, '', line).strip()
            else:
                if any(keyword in line.lower() for keyword in ['upi', 'cash', 'chq', 'transfer', 'neft', 'rtgs', 'atm', 'debit', 'credit', 'payment']):
                    if current_desc:
                        final_data.append(current_desc)
                    current_desc = line
                else:
                    current_desc += " " + line
    
    if current_desc:
        final_data.append(current_desc)
    
    df = pd.DataFrame(final_data, columns=["Description"])
    df = df[df['Description'].str.len() > 5]
    print(f"Extracted {len(df)} descriptions from text/OCR.")
    if len(df) == 0:
        print("No transaction descriptions found. The PDF may be empty or OCR failed.")
    return df.reset_index(drop=True)

def main():
    # Adjust the file path as needed (e.g., 'data/canara_epassbook.pdf' or 'data/Raw.csv')
    file_path = 'data/Op.pdf'  # Change this to the file you want to load
    
    # Prompt for password if it's a PDF
    password = None
    if file_path.lower().endswith('.pdf'):
        password = getpass.getpass("Enter PDF password (leave blank if none): ")
        if not password:
            password = None
    
    df = load_file(file_path, password)
    print("Final DataFrame:")
    print(df)
    # Optional: Save to CSV for further use
    if not df.empty:
        df.to_csv('output_descriptions.csv', index=False)
        print("Descriptions saved to output_descriptions.csv")

if __name__ == "__main__":
    main()