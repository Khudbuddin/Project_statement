import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
import pdfplumber

# --- PAGE CONFIG ---
st.set_page_config(page_title="FinScan Pro", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Bold & Professional) ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F4F8; }
    h1, h2, h3 { color: #1A365D !important; font-weight: 800 !important; }
    .stButton>button { 
        background-color: #1A365D; color: white; 
        font-weight: 700; border-radius: 8px; border: none;
    }
    .google-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: white; border: 2px solid #D1D5DB;
        padding: 12px; border-radius: 8px; font-weight: 800; cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF PROCESSING FUNCTION ---
def extract_data_from_pdf(pdf_file):
    all_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                # Pehle row ko header maan kar baaki data lena
                df_page = pd.DataFrame(table[1:], columns=table[0])
                all_data.append(df_page)
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # Safai: Column names clean karna aur dummy amount set karna agar empty ho
        final_df.columns = [str(c).replace('\n', ' ') for c in final_df.columns]
        return final_df
    return None

# --- APP LOGIC ---
if 'step' not in st.session_state: st.session_state.step = 'Intro'

# --- 1. INTRO PAGE ---
if st.session_state.step == 'Intro':
    st.markdown("<h1 style='font-size: 50px; text-align:center;'>FinScan AI: PDF Analyzer</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://illustrations.popsy.co/white/finance-analysis.svg")
        st.markdown("""
        - **BOLD INSIGHTS:** Har transaction ka hisaab.
        - **PDF SUPPORT:** Direct bank statement upload karein.
        - **MUTABLE DATA:** Galtiyaan khud sahi karein.
        """)
        if st.button("GET STARTED ➔"):
            st.session_state.step = 'Login'
            st.rerun()

# --- 2. LOGIN PAGE ---
elif st.session_state.step == 'Login':
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='background:white; padding:30px; border-radius:15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>Sign In</h2>", unsafe_allow_html=True)
        st.text_input("**Email**")
        st.text_input("**Password**", type="password")
        if st.button("LOGIN"):
            st.session_state.step = 'Dashboard'
            st.rerun()
        
        # Proper Google Button Logic
        st.markdown('<div class="google-btn"><img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" width="20" style="margin-right:10px;"> CONTINUE WITH GOOGLE</div>', unsafe_allow_html=True)
        if st.button("Confirm Google Auth"): # Clickable trigger for demo
            st.session_state.step = 'Dashboard'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 3. DASHBOARD ---
elif st.session_state.step == 'Dashboard':
    st.sidebar.title("FinScan Pro")
    if st.sidebar.button("Logout"):
        st.session_state.step = 'Intro'
        st.rerun()

    st.markdown("<h1>Your Dashboard</h1>", unsafe_allow_html=True)
    
    # PDF UPLOADER
    uploaded_pdf = st.file_uploader("**Upload your Bank Statement (PDF)**", type="pdf")
    
    if uploaded_pdf:
        with st.spinner("Extracting data from PDF..."):
            df = extract_data_from_pdf(uploaded_pdf)
            
            if df is not None:
                st.success("PDF Data Extracted Successfully!")
                
                # Metrics (Dummy for now based on extracted data)
                st.metric("Total Transactions Found", len(df))
                
                # MUTABLE TABLE
                st.markdown("### **📝 Review & Edit Data**")
                st.info("Aap niche table mein kisi bhi cell par click karke use sahi kar sakte hain.")
                edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
                
                # Dummy Graph (Agar 'Amount' column mil jaye)
                try:
                    # 'Amount' column ko numeric banane ki koshish
                    edited_df['Amount'] = pd.to_numeric(edited_df.iloc[:, -1].astype(str).str.replace(',', ''), errors='coerce')
                    fig = px.bar(edited_df, title="Spending Overview", template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    st.warning("Amount column format automatic detect nahi ho paya, manually edit karein.")
                
                st.download_button("**📥 Download Analyzed PDF**", "PDF Content", "Report.pdf")
            else:
                st.error("Is PDF se data extract nahi ho pa raha. Please clean PDF upload karein.")