import re
import cv2
import numpy as np

import pytesseract
from PIL import Image
import os

LOGO_DIR = "backend/logos"

# ✅ SET TESSERACT PATH (ONCE, GLOBAL FOR THIS MODULE)
pytesseract.pytesseract.tesseract_cmd = r"D:\smart-expense-categorizer\Tesser-OCR\tesseract.exe"

def extract_ifsc(text: str):
    text = text.upper()

    # 🔧 OCR normalization
    text = text.replace("O", "0")  # letter O → zero

    match = re.search(r'\b[A-Z]{4}0[A-Z0-9]{6}\b', text)
    return match.group(0) if match else None



def crop_top_region(image: Image.Image, ratio=0.35):
    """
    Crop top region of the page (default 35%)
    """
    width, height = image.size
    crop_box = (0, 0, width, int(height * ratio))
    return image.crop(crop_box)
def detect_bank_by_logo(image: Image.Image, threshold=0.7):
    """
    Detect bank by logo using OpenCV template matching
    """
    if not os.path.exists(LOGO_DIR):
        return None

    # Crop top 30% of page
    top = image.crop((0, 0, image.width, int(image.height * 0.3)))
    page_gray = cv2.cvtColor(np.array(top), cv2.COLOR_RGB2GRAY)

    best_match = None
    best_score = 0.0

    for file in os.listdir(LOGO_DIR):
        if not file.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        bank_code = file.split(".")[0]
        logo_path = os.path.join(LOGO_DIR, file)

        logo = cv2.imread(logo_path, cv2.IMREAD_GRAYSCALE)
        if logo is None:
            continue

        res = cv2.matchTemplate(page_gray, logo, cv2.TM_CCOEFF_NORMED)
        score = float(np.max(res))

        if score > best_score:
            best_score = score
            best_match = bank_code

    if best_score >= threshold:
        return {
            "method": "LOGO_MATCH",
            "bank_code": best_match,
            "confidence": round(best_score, 2)
        }

    return None


def detect_bank_from_image(image):
    """
    Detect bank using region-based OCR on top of page
    """

    # 1️⃣ Crop top region
    top_image = crop_top_region(image)

    # 2️⃣ OCR only top region
    text = pytesseract.image_to_string(top_image)
    
    print("===== OCR TEXT START =====")
    print(text)
    print("===== OCR TEXT END =====")

    # 3️⃣ Extract IFSC (BEST CASE)
    ifsc = extract_ifsc(text)
    if ifsc:
        return {
            "method": "IFSC_REGION_OCR",
            "ifsc": ifsc,
            "bank_code": ifsc[:4]
        }

    # 🆕 4️⃣ LOGO detection (SAFE ADDITION)
    logo_result = detect_bank_by_logo(image)
    if logo_result:
        return logo_result

    # 5️⃣ Fallback keyword detection (UNCHANGED)
    text_upper = text.upper()

    if "ICICI" in text_upper:
        return {"method": "KEYWORD", "bank_code": "ICICI"}
    if "CANARA" in text_upper:
        return {"method": "KEYWORD", "bank_code": "CNRB"}
    if "AXIS" in text_upper:
        return {"method": "KEYWORD", "bank_code": "UTIB"}

    return {
        "method": "UNKNOWN",
        "bank_code": None
    }
