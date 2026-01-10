import pandas as pd
import pdfplumber
import re
from fpdf import FPDF
from datetime import datetime
import streamlit as st

def smart_categorize(desc):
    desc = desc.upper()
    if any(x in desc for x in ['ZOMATO', 'SWIGGY', 'RESTAURANT', 'FOOD', 'DOMINOS']): return "Food"
    if any(x in desc for x in ['UBER', 'OLA', 'FUEL', 'PETROL', 'METRO']): return "Travel"
    if any(x in desc for x in ['AMAZON', 'FLIPKART', 'GROCERY', 'MART']): return "Shopping"
    if any(x in desc for x in ['RENT', 'HOUSE', 'SOCIETY']): return "Housing"
    if any(x in desc for x in ['BILL', 'RECHARGE', 'JIO', 'ELECTRIC']): return "Bills"
    if any(x in desc for x in ['CHG', 'SMS CHG', 'FEE']): return "Bank Charges"
    if any(x in desc for x in ['SALARY', 'CREDIT', 'INCOME']): return "Income"
    return "Miscellaneous"

def parse_statement(file):
    extracted = []
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split('\n'):
                            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", line)
                            amounts = re.findall(r"(\d+\.\d{2})", line)
                            if amounts and date_match:
                                date_str = date_match.group(1)
                                amt = float(amounts[-1])
                                desc = re.sub(r"\d{2}/\d{2}/\d{4}", "", line).strip()[:50]
                                extracted.append({
                                    "Date": datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d"),
                                    "Description": desc, "Amount": amt, "Category": smart_categorize(desc)
                                })
        elif file.type in ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            df = pd.read_csv(file) if file.type == "text/csv" else pd.read_excel(file)
            df["Category"] = df["Description"].apply(smart_categorize)
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            extracted = df.to_dict('records')
        return pd.DataFrame(extracted)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def create_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "ExpenseWise - Report", ln=True, align="C")
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        line = f"{row['Date']} | {row['Description']} | Rs. {row['Amount']} | {row['Category']}"
        pdf.multi_cell(0, 8, line.encode("latin-1", "replace").decode("latin-1"))
    return pdf.output(dest="S").encode("latin-1")