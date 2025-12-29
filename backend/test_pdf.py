import pdfplumber
import getpass
from pathlib import Path

# Correct path to PDF from backend folder
pdf_path = Path(__file__).resolve().parent.parent / "backend" / "data" / "hibasstatement.pdf"  # Goes up to root, then to data

password = getpass.getpass("Enter password: ")
try:
    with pdfplumber.open(str(pdf_path), password=password) as pdf:
        print(f"PDF opened successfully. Pages: {len(pdf.pages)}")
        for page in pdf.pages[:2]:  # Check first 2 pages
            text = page.extract_text()
            if text:
                print(f"Page {page.page_number}: {text[:200]}...")
            else:
                print(f"Page {page.page_number}: No text (may need OCR)")
except Exception as e:
    print(f"Error: {e}")