import pdfplumber
import pandas as pd
import re
import pytesseract

from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfplumber.utils.exceptions import PdfminerException
from PIL import Image, ImageFilter

# Import local modules
from .bank_templates import BANK_TEMPLATES, get_dynamic_fallback_template
from .bank_detector import detect_bank_from_image


# -------------------- CONFIG --------------------
pytesseract.pytesseract.tesseract_cmd = r"D:\smart-expense-categorizer\Tesser-OCR\tesseract.exe"


# -------------------- HELPERS --------------------
# def get_pdf_with_password(file_path):
#     for _ in range(3):
#         try:
#             password = input("🔐 Enter PDF password (press Enter if none): ")
#             return pdfplumber.open(
#                 file_path,
#                 password=password if password else None
#             )
#         except (PDFPasswordIncorrect, PdfminerException):
#             print("❌ Incorrect password.")
#     return None


def clean_amount(text):
    """Robust cleaner for OCR amounts that handles noise and trailing dots."""
    if not text:
        return 0.0

    cleaned = re.sub(r'[^0-9.,]', '', text).strip('.')

    if not cleaned:
        return 0.0

    try:
        return float(cleaned.replace(",", ""))
    except:
        return 0.0


def crop_column(image, x1, x2, y1, y2):
    w, h = image.size
    return image.crop((
        max(0, x1),
        max(0, y1),
        min(w, x2),
        min(h, y2)
    ))


# -------------------- UNIVERSAL ROW DETECTION --------------------
def detect_amount_layout(image):
    width, height = image.size

    header_img = image.crop((
        int(width * 0.30),
        int(height * 0.12),
        int(width * 0.95),
        int(height * 0.22)
    ))

    header_img = header_img.convert("L").filter(ImageFilter.MedianFilter(3))

    text = pytesseract.image_to_string(
        header_img,
        config="--psm 6"
    ).upper()

    split_keywords = ["DEPOSIT", "WITHDRAWAL", "DEBITS", "CREDITS"]
    merged_keywords = ["WITHDRAWAL(DR)", "DEPOSIT(CR)", "DR/CR", "DR", "CR"]

    if sum(1 for k in split_keywords if k in text) >= 2:
        return "split"

    if sum(1 for k in merged_keywords if k in text) >= 1:
        return "merged"

    return "split"


def detect_row_anchors(date_img, offset_y):
    """Universal: Finds dates or serials to use as row starting points."""
    date_img = date_img.filter(
        ImageFilter.MedianFilter(size=3)
    ).convert("L")

    data = pytesseract.image_to_data(
        date_img,
        output_type=pytesseract.Output.DICT,
        config="--psm 4"
    )

    anchors = []
    _, img_h = date_img.size
    min_row_gap = img_h * 0.005

    for i, text in enumerate(data["text"]):
        text = text.strip()

        if int(data["conf"][i]) < 15 or not text:
            continue

        y_top = data["top"][i] + offset_y
        h = data["height"][i]

        # Updated Regex to support: 24-12-2024, 24/12/24, and Dec 24, 2024
        # Support: 24-12-2024, 24/12/24, AND Dec 24, 2024
        is_date = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|([A-Z][a-z]{2}\s+\d{1,2}(,?\s+\d{4})?)", text)
        is_serial = text.isdigit() and len(text) <= 3

        if is_date or is_serial:
            if not anchors or abs(anchors[-1][1] - y_top) > min_row_gap:
                anchors.append((text, y_top, y_top + h))

    return anchors


def expand_row_bounds(anchors, page_height):
    """Calculates dynamic boxes for each transaction based on the distance between anchors."""
    if not anchors:
        return []

    anchors.sort(key=lambda x: x[1])

    heights = [
        anchors[i + 1][1] - anchors[i][1]
        for i in range(len(anchors) - 1)
    ]

    avg_h = sum(heights) / len(heights) if heights else 70

    blocks = []

    for i in range(len(anchors)):
        ref_text, y1, y2 = anchors[i]
        box_start = y1 - (avg_h * 0.1)

        if i + 1 < len(anchors):
            box_end = anchors[i + 1][1] - 2
        else:
            box_end = min(y1 + (avg_h * 3), page_height)

        blocks.append((ref_text, box_start, box_end))

    return blocks


# -------------------- EXTRACTION LOGIC --------------------
def extract_single_transaction(image, template, date, y1, y2):
    """Universal extraction using PSM 4 for multi-line support."""
    d_c = template["columns"]["description"]

    desc_img = crop_column(image, d_c[0], d_c[1], y1, y2)

    description = pytesseract.image_to_string(
        desc_img,
        config="--psm 4"
    ).strip()

    description = " ".join(description.split())

    amt = 0.0
    tx_type = "UNKNOWN"

    if template["amount_mode"] == "split":
        deb_c = template["columns"]["debit"]
        cre_c = template["columns"]["credit"]

        deb_val = clean_amount(
            pytesseract.image_to_string(
                crop_column(image, deb_c[0], deb_c[1], y1, y2),
                config="--psm 4"
            )
        )

        cre_val = clean_amount(
            pytesseract.image_to_string(
                crop_column(image, cre_c[0], cre_c[1], y1, y2),
                config="--psm 4"
            )
        )

        if cre_val > 0:
            amt, tx_type = cre_val, "CREDIT"
        elif deb_val > 0:
            amt, tx_type = deb_val, "DEBIT"

    elif template["amount_mode"] == "amount_type":
        amt_c = template["columns"]["amount"]
        type_c = template["columns"]["type"]

        amt_text = pytesseract.image_to_string(
            crop_column(image, amt_c[0], amt_c[1], y1, y2),
            config="--psm 4"
        ).upper()

        amt = clean_amount(amt_text)

        type_text = pytesseract.image_to_string(
            crop_column(image, type_c[0], type_c[1], y1, y2),
            config="--psm 4"
        ).upper()

        if "CR" in type_text or "CREDIT" in type_text:
            tx_type = "CREDIT"
        elif "DR" in type_text or "DEBIT" in type_text:
            tx_type = "DEBIT"
        else:
            if amt > 0:
                tx_type = "DEBIT"
            else:
                tx_type = "UNKNOWN"

    else:
        amt_c = template["columns"]["amount"]

        amt_text = pytesseract.image_to_string(
            crop_column(image, amt_c[0], amt_c[1], y1, y2),
            config="--psm 4"
        ).upper()

        amt = clean_amount(amt_text)

        if "CR" in amt_text:
            tx_type = "CREDIT"
        elif "DR" in amt_text:
            tx_type = "DEBIT"

    return {
        "Date": date,
        "Description": description,
        "Type": tx_type,
        "Amount": amt
    }


def find_table_header_y(image):
    width, height = image.size

    scan_img = image.crop((
        0,
        0,
        width,
        int(height * 0.4)
    )).convert("L").filter(ImageFilter.MedianFilter(3))

    data = pytesseract.image_to_data(
        scan_img,
        output_type=pytesseract.Output.DICT,
        config="--psm 6"
    )

    for i, text in enumerate(data["text"]):
        if any(kw in text.upper() for kw in ["TRANSACTION", "VALUE", "DATE", "S NO"]):
            return data["top"][i] + data["height"][i] + 10

    return int(height * 0.25)


def extract_rows_from_page(image, template, page_number):
    all_rows = []

    img_w, img_h = image.size

    table_top = (
        find_table_header_y(image)
        if page_number == 1
        else template.get("other_pages_start_y", 300)
    )

    if template.get("is_fallback"):
        date_col_img = crop_column(image, 0, img_w, table_top, img_h - 100)
    else:
        date_c = template["columns"]["date"]
        date_col_img = crop_column(image, date_c[0], date_c[1], table_top, img_h - 100)

    raw_anchors = detect_row_anchors(date_col_img, table_top)

    print(f"🔍 Page {page_number}: Found {len(raw_anchors)} potential anchors.")

    blocks = expand_row_bounds(raw_anchors, img_h)

    for i, (date, y1, y2) in enumerate(blocks):
        row_data = extract_single_transaction(
            image,
            template,
            date,
            max(0, y1),
            min(y2, img_h)
        )

        if row_data["Amount"] > 0 or len(row_data["Description"]) > 5:
            all_rows.append(row_data)
            print(
                f"   ✅ [ROW {i+1}] {date} | "
                f"{row_data['Amount']} | "
                f"{row_data['Description'][:30]}..."
            )

    return all_rows


# -------------------- MAIN LOADING --------------------
# At the top of pdf_load.py, ensure you import the new function

def load_pdf(file_path, password=None):
    try:
        pdf = pdfplumber.open(file_path, password=password)
    except Exception as e:
        print(f"❌ PDF open failed: {e}")
        return pd.DataFrame()
    if not pdf: return pd.DataFrame()

    all_data = []
    current_template = None

    with pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            image = page.to_image(resolution=300).original

            if idx == 1 or current_template is None:
                bank_info = detect_bank_from_image(image)
                bank_code = bank_info.get("bank_code")

                # 🟢 LOGIC 1: Use Existing Templates
                if bank_code in BANK_TEMPLATES:
                    bank_template = BANK_TEMPLATES[bank_code]
                    if "variants" in bank_template:
                        layout = detect_amount_layout(image)
                        current_template = bank_template["variants"].get(
                            layout, list(bank_template["variants"].values())[0]
                        )
                    else:
                        current_template = bank_template
                
                # 🔴 LOGIC 2: Fallback System for Unknown Banks
                else:
                    print(f"🚀 Unknown Bank ({bank_code}). Generating Dynamic Template...")
                    current_template = get_dynamic_fallback_template(image)
                    # We still use your existing find_table_header_y logic for the Y offset
                    current_template["page1_start_y"] = find_table_header_y(image)

            print(f"📄 Processing Page {idx}...")
            rows = extract_rows_from_page(image, current_template, idx)
            all_data.extend(rows)

    return pd.DataFrame(all_data)