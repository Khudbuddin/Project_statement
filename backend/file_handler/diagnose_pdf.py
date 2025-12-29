import pdfplumber

file_path = 'data/canara_epassbook.pdf'  # Adjust if needed
try:
    with pdfplumber.open(file_path) as pdf:
        print(f"PDF opened successfully. Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages[:2]):  # Check first 2 pages
            print(f"\n--- Page {i+1} ---")
            table = page.extract_table()
            if table:
                print(f"Table found: {len(table)} rows")
                print("First 3 rows:", table[:3])
            else:
                print("No table found.")
            text = page.extract_text()
            if text:
                print(f"Raw text (first 300 chars): {text[:300]}...")
            else:
                print("No text extracted (likely image-based or scanned).")
except Exception as e:
    print(f"Error: {e} (Check file path or if PDF is password-protected.)")