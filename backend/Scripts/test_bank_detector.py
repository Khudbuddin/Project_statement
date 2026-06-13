from backend.file_handler.pdf_to_images import pdf_to_images
from backend.file_handler.bank_detector import detect_bank_from_image
import getpass

PDF_PATH = r"D:\smart-expense-categorizer\backend\data\Phonepe.pdf"

def main():
    # 🔐 Always ask for password
    password = getpass.getpass("🔐 Enter PDF password (press Enter if none): ")

    try:
        pages = pdf_to_images(PDF_PATH, password=password or None)
        print(f"📄 Total pages: {len(pages)}")

        first_page = pages[0]
        bank_info = detect_bank_from_image(first_page)

        print("🏦 Bank Detection Result:")
        print(bank_info)

    except ValueError as e:
        print("❌ PDF Error:", str(e))

if __name__ == "__main__":
    main()
