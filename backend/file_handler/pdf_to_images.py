from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
import os

POPPLER_PATH = r"D:\smart-expense-categorizer\poppler-25.12.0\Library\bin"


def pdf_to_images(pdf_path, dpi=300, password=None):
    """
    Convert PDF to images.
    Supports both password-protected and normal PDFs.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    for attempt in range(3):
        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                poppler_path=POPPLER_PATH,
                userpw=password,
                ownerpw=password
            )
            return images

        except PDFPageCountError:
            # Wrong or missing password
            if password is None:
                password = input("🔐 Enter PDF password: ").strip()
                password = password if password else None
            else:
                print("❌ Incorrect password.")
                password = input("🔐 Re-enter PDF password: ").strip()
                password = password if password else None

        except Exception as e:
            raise RuntimeError(f"PDF conversion failed: {e}")

    raise RuntimeError("❌ Failed to open PDF after 3 password attempts")
