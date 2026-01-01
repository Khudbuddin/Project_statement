import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import re
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import time

# ============================================
# 1. APP CONFIGURATION & SESSION STATE
# ============================================
st.set_page_config(
    page_title="ExpenseWise | Premium Finance",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize ALL session states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "welcome"  # welcome, login, signup, dashboard
if "user_name" not in st.session_state:
    st.session_state.user_name = "Yunus Ali"
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "db_data" not in st.session_state:
    st.session_state.db_data = pd.DataFrame(columns=["Date", "Description", "Amount", "Category"])
if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = 50000
if "temp_transactions" not in st.session_state:
    st.session_state.temp_transactions = pd.DataFrame()
if "app_stage" not in st.session_state:
    st.session_state.app_stage = "📊 Dashboard"
if "past_months" not in st.session_state:
    st.session_state.past_months = {}
if "compare_past_df" not in st.session_state:
    st.session_state.compare_past_df = pd.DataFrame()

# ============================================
# 2. SHARED CSS & STYLES (ALL YOUR ORIGINAL CSS)
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    /* Deep Background with subtle slate gradient */
    [data-testid="stAppViewContainer"] {
        background-color: #0a0c10;
        background-image: 
            radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(30, 41, 59, 0.2) 0px, transparent 50%);
    }

    .block-container { padding-top: 2rem; }
    
    .hero-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;
        gap: 80px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .hero-text { flex: 1.2; }
    
    .hero-badge {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.2);
        margin-bottom: 24px;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .hero-title {
        font-size: 4.5rem;
        font-weight: 800;
        line-height: 1;
        color: #f8fafc;
        margin-bottom: 25px;
    }
    
    .hero-title span { 
        color: #10b981;
    }
    
    .hero-desc {
        font-size: 1.25rem;
        color: #94a3b8;
        line-height: 1.6;
        margin-bottom: 35px;
        max-width: 550px;
    }
    
    .auth-card {
        width: 420px;
        background: #111827;
        padding: 50px;
        border-radius: 20px;
        border: 1px solid #1f2937;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        text-align: center;
    }
    
    .auth-card-small {
        width: 440px;
        background: #111827;
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #1f2937;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        text-align: center;
        margin: 0 auto;
    }
    
    .auth-form-card {
        background: #111827;
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #1f2937;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    }
    
    .btn {
        display: block;
        padding: 16px;
        border-radius: 10px;
        font-weight: 700;
        text-decoration: none !important;
        margin-bottom: 12px;
        transition: 0.2s ease-in-out;
        text-align: center;
        font-size: 1rem;
        cursor: pointer;
        border: none;
        width: 100%;
    }
    
    .btn-primary { 
        background: #10b981; 
        color: #064e3b !important;
    }
    
    .btn-secondary { 
        background: transparent; 
        color: #f8fafc !important; 
        border: 1px solid #334155; 
    }
    
    .btn:hover { 
        transform: translateY(-2px); 
        filter: brightness(1.1);
        border-color: #10b981;
    }
    
    .pro-badge {
        background: linear-gradient(90deg, #10b981, #3b82f6);
        color: black; padding: 2px 10px; border-radius: 20px;
        font-size: 10px; font-weight: 800; margin-left: 10px;
    }
    
    .f-list { display: flex; flex-direction: column; gap: 12px; margin-top: 25px; }
    .f-item { color: #cbd5e1; font-size: 0.95rem; display: flex; align-items: center; gap: 10px; }
    .f-item i { color: #10b981; font-size: 1.1rem; }
    
    .form-input {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 16px !important;
    }
    
    .form-input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2) !important;
    }
    
    .security-box {
        background: rgba(16, 185, 129, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(16, 185, 129, 0.1);
        margin: 20px 0;
    }
    
    @media (max-width: 900px) {
        .hero-container { flex-direction: column; text-align: center; }
        .hero-title { font-size: 3rem; }
        .f-list { align-items: center; }
    }
    
    .stButton > button {
        border-radius: 10px;
        transition: 0.3s;
        border: none;
        font-weight: 700;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
    }
    
    .stButton > button[kind="primary"] {
        background: #10b981;
        color: #064e3b;
    }
    
    .stButton > button[kind="secondary"] {
        background: transparent;
        color: #f8fafc;
        border: 1px solid #334155;
    }
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)

# ============================================
# 3. SHARED FUNCTIONS (ALL YOUR ORIGINAL FUNCTIONS)
# ============================================
def logout():
    """Clear session and return to welcome page"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.authenticated = False
    st.session_state.current_page = "welcome"
    st.session_state.logged_in = False
    st.rerun()

def create_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "ExpenseWise - Expense Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    
    for _, row in df.iterrows():
        line = f"{row['Date']} | {row['Description']} | Rs. {row['Amount']} | {row['Category']}"
        safe_line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, safe_line)
    
    return pdf.output(dest="S").encode("latin-1")

def smart_categorize(desc):
    """ML function - your backend friend will improve this"""
    desc = desc.upper()
    if any(x in desc for x in ['ZOMATO', 'SWIGGY', 'RESTAURANT', 'FOOD', 'HOTEL', 'EAT', 'DOMINOS', 'PIZZA', 'CAFE']): 
        return "Food"
    if any(x in desc for x in ['UBER', 'OLA', 'RAPIDO', 'FUEL', 'PETROL', 'IRCTC', 'RAILWAY', 'METRO', 'BUS', 'AUTO', 'CAB']): 
        return "Travel"
    if any(x in desc for x in ['AMAZON', 'FLIPKART', 'MYNTRA', 'SHOP', 'RETAIL', 'AJIO', 'BIGBASKET', 'GROCERY', 'MART']): 
        return "Shopping"
    if any(x in desc for x in ['RENT', 'MAINTENANCE', 'SOCIETY', 'OWNER', 'HOUSE', 'APARTMENT']): 
        return "Housing"
    if any(x in desc for x in ['BILL', 'RECHARGE', 'JIO', 'AIRTEL', 'VI', 'BSNL', 'ELECTRIC', 'EBILL', 'INSURANCE', 'GAS', 'WATER']): 
        return "Bills"
    if any(x in desc for x in ['CHG', 'SMS CHG', 'MIN BAL', 'ATM CHG', 'SERVICE CHG', 'FEE', 'PENALTY']): 
        return "Bank Charges"
    if any(x in desc for x in ['SALARY', 'CREDIT', 'DEPOSIT', 'INCOME', 'REFUND']): 
        return "Income"
    return "Miscellaneous"

def parse_statement(file):
    """Your original parse_statement function"""
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
                                    "Description": desc,
                                    "Amount": amt,
                                    "Category": smart_categorize(desc)
                                })
        elif file.type in ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            df = pd.read_csv(file) if file.type == "text/csv" else pd.read_excel(file)
            df["Category"] = df["Description"].apply(smart_categorize)
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            extracted = df.to_dict('records')
        return pd.DataFrame(extracted)
    except Exception as e:
        st.error(f"Error reading file: {e}. Ensure the file is from a supported Indian bank format.")
        return pd.DataFrame()

def process_with_ml(uploaded_file):
    """ML processing placeholder"""
    with st.spinner("🤖 ML Backend: Analyzing transaction patterns..."):
        time.sleep(2)
        data = {
            "Date": ["2025-12-01", "2025-12-05", "2025-12-10"],
            "Description": ["Zomato Delivery", "Uber Ride", "Netflix Subscription"],
            "Amount": [450.0, 120.5, 799.0],
            "Category": ["Food", "Travel", "Bills"]
        }
        return pd.DataFrame(data)

# ============================================
# 4. PAGE ROUTING - WELCOME PAGE (YOUR ORIGINAL DESIGN)
# ============================================
if st.session_state.current_page == "welcome":
    st.markdown("""
    <div class="hero-container">
        <div class="hero-text">
            <div class="hero-badge">Institutional Grade Security</div>
            <h1 class="hero-title">Master Your <span>Capital.</span></h1>
            <p class="hero-desc">The definitive workspace for private wealth management. Turn raw transaction data into strategic financial intelligence.</p>
            <div class="f-list">
                <div class="f-item"><i class="fas fa-shield-alt"></i> End-to-End Local Privacy</div>
                <div class="f-item"><i class="fas fa-bolt"></i> Instant AI Categorization</div>
                <div class="f-item"><i class="fas fa-layer-group"></i> Multi-Account Consolidation</div>
            </div>
        </div>
        <div class="auth-card">
            <div style="font-size: 1.8rem; font-weight: 800; color: #f8fafc; margin-bottom: 40px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                <i class="fas fa-wallet" style="color: #10b981;"></i> ExpenseWise
            </div>
            <p style="margin-bottom:25px; color:#cbd5e1;">Access your financial dashboard</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the buttons
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        # Sign Up Button
        if st.button("🚀 Create Premium Account", type="primary", use_container_width=True):
            st.session_state.current_page = "signup"
            st.rerun()
        
        # Login Button
        if st.button("🔐 Sign In to Dashboard", type="secondary", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()
        
        st.markdown('<p style="text-align:center; color:#64748b; margin-top:20px;">Regulated-ready encryption</p>', unsafe_allow_html=True)

# ============================================
# 5. SIGNUP PAGE - PROFESSIONAL DESIGN
# ============================================
elif st.session_state.current_page == "signup":
    # Center the layout
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 8px 16px; border-radius: 6px; display: inline-block; font-weight: 700; margin-bottom: 20px; letter-spacing: 1px;">
                PREMIUM ACCOUNT
            </div>
            <h1 style="font-size: 2.5rem; font-weight: 800; color: white; margin-bottom: 10px;">Join ExpenseWise</h1>
            <p style="color: #94a3b8; font-size: 1.1rem;">Start your journey to financial mastery</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Signup Form in Card
        st.markdown("""
        <div class="auth-form-card">
            <div style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin-bottom: 30px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                <i class="fas fa-user-plus" style="color: #10b981;"></i> Create Your Account
            </div>
        """, unsafe_allow_html=True)
        
        # Form
        with st.form("signup_form"):
            # Two-column layout for name and email
            col_name, col_email = st.columns(2)
            with col_name:
                full_name = st.text_input(
                    "Full Name",
                    placeholder="John Smith",
                    key="signup_name"
                )
            with col_email:
                email = st.text_input(
                    "Email Address",
                    placeholder="you@company.com",
                    key="signup_email"
                )
            
            # Two-column layout for passwords
            col_pass, col_confirm = st.columns(2)
            with col_pass:
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 8 characters",
                    key="signup_pass"
                )
            with col_confirm:
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter password",
                    key="signup_confirm"
                )
            
            # Security features box
            st.markdown("""
            <div class="security-box">
                <div style="color: #10b981; font-weight: 600; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                    <i class="fas fa-shield-alt"></i> Security Features
                </div>
                <div style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;"><i class="fas fa-lock" style="color: #10b981;"></i> End-to-end encryption</div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;"><i class="fas fa-building" style="color: #10b981;"></i> Bank-grade security</div>
                    <div style="display: flex; align-items: center; gap: 8px;"><i class="fas fa-user-shield" style="color: #10b981;"></i> GDPR compliant</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Terms checkbox
            terms = st.checkbox(
                "I agree to ExpenseWise Terms of Service and Privacy Policy",
                key="signup_terms"
            )
            
            # Submit button
            submit = st.form_submit_button(
                "🚀 Create Premium Account",
                type="primary",
                use_container_width=True
            )
            
            if submit:
                if not all([full_name, email, password, confirm_password]):
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters")
                elif not terms:
                    st.error("Please agree to the terms and conditions")
                else:
                    # In production, this would connect to backend
                    st.session_state.user_name = full_name
                    st.session_state.user_email = email
                    st.session_state.logged_in = True
                    st.session_state.current_page = "dashboard"
                    st.success("Account created successfully!")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Login link
        st.markdown('<div style="text-align:center; margin-top:20px; color:#94a3b8;">Already have an account?</div>', unsafe_allow_html=True)
        if st.button("Sign In Instead", type="secondary", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()
        
        # Back button
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.current_page = "welcome"
            st.rerun()

# ============================================
# 6. LOGIN PAGE - PROFESSIONAL DESIGN
# ============================================
elif st.session_state.current_page == "login":
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 8px 16px; border-radius: 6px; display: inline-block; font-weight: 700; margin-bottom: 20px; letter-spacing: 1px;">
                INSTITUTIONAL ACCESS
            </div>
            <h1 style="font-size: 2.5rem; font-weight: 800; color: white; margin-bottom: 10px;">Welcome Back</h1>
            <p style="color: #94a3b8; font-size: 1.1rem;">Sign in to your ExpenseWise dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login Form in Card
        st.markdown("""
        <div class="auth-form-card">
            <div style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin-bottom: 30px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                <i class="fas fa-sign-in-alt" style="color: #10b981;"></i> Secure Sign In
            </div>
        """, unsafe_allow_html=True)
        
        # Login Form
        with st.form("login_form"):
            email = st.text_input(
                "Email Address",
                placeholder="you@company.com",
                key="login_email"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_pass"
            )
            
            # Remember me and Forgot password
            col_remember, col_forgot = st.columns([2, 1])
            with col_remember:
                remember = st.checkbox("Remember this device", key="login_remember")
            with col_forgot:
                st.markdown('<div style="text-align: right; margin-top: 8px;"><a href="#" style="color: #10b981; text-decoration: none; font-size: 0.9rem;">Forgot password?</a></div>', unsafe_allow_html=True)
            
            # Security notice
            st.markdown("""
            <div style="background: rgba(59, 130, 246, 0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.1); margin: 20px 0;">
                <div style="color: #3b82f6; font-size: 0.9rem; display: flex; align-items: center; gap: 8px;">
                    <i class="fas fa-info-circle"></i>
                    <span>Your credentials are encrypted and never stored in plain text</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            submit = st.form_submit_button(
                "🔐 Sign In to Dashboard",
                type="primary",
                use_container_width=True
            )
            
            if submit:
                if email and password:
                    # Simple validation - backend will implement proper auth
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.current_page = "dashboard"
                    st.success("Welcome back!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Please enter both email and password")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Signup link
        st.markdown('<div style="text-align:center; margin-top:20px; color:#94a3b8;">Don\'t have an account?</div>', unsafe_allow_html=True)
        if st.button("Create Premium Account", type="secondary", use_container_width=True):
            st.session_state.current_page = "signup"
            st.rerun()
        
        # Back button
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.current_page = "welcome"
            st.rerun()

# ============================================
# 7. DASHBOARD PAGE (YOUR COMPLETE ORIGINAL DASHBOARD)
# ============================================
elif st.session_state.current_page == "dashboard" and st.session_state.logged_in:
    
    # Navigation Bar (YOUR ORIGINAL)
    header_l, header_m, header_r = st.columns([1, 2.5, 1])

    with header_l:
        st.markdown('<div style="font-size: 1.5rem; font-weight: 800; color: white;">💎 ExpenseWise</div>', unsafe_allow_html=True)

    with header_m:
        st.session_state.app_stage = st.segmented_control(
            "Navigation",
            options=["📊 Dashboard", "📈 Comparing", "🔍 Review", "🤖 ML Suggestions", "📤 Upload"],
            default=st.session_state.app_stage,
            label_visibility="collapsed"
        )

    with header_r:
        # FIXED: Now it shows the actual user name from session state
        st.markdown(f"""
            <div style="text-align: right;">
                <span style="color: white; font-weight: 600;">{st.session_state.user_name}</span><span class="pro-badge">PRO</span><br>
                <span style="color: #6b7280; font-size: 12px;">Indian Bank Holder</span>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # =============== UPLOAD TAB ===============
    if st.session_state.app_stage == "📤 Upload":
        st.subheader("Import Bank Statement")
        col1, col2 = st.columns([2,1])
        with col1:
            uploaded_file = st.file_uploader("Upload Indian Bank Statement (PDF/CSV/Excel)", type=["pdf", "csv", "xlsx"])
            selected_month = st.selectbox("Select Month for This Upload", 
                                          options=[f"{datetime.now().year}-{str(i).zfill(2)}" for i in range(1, 13)], 
                                          index=datetime.now().month - 1)
            if uploaded_file and st.button("Process Statement", type="primary", use_container_width=True):
                with st.spinner("AI is analyzing Indian bank transactions..."):
                    new_df = parse_statement(uploaded_file)
                    if not new_df.empty:
                        new_df["Month"] = selected_month
                        st.session_state.temp_transactions = new_df
                        st.success("Processing complete! Review and edit categories below before saving.")
                    else:
                        st.error("Could not find transactions. Ensure the file is from a supported Indian bank format.")
        
        # Display editable table for review/corrections
        if not st.session_state.temp_transactions.empty:
            st.markdown("### Review & Edit Transactions")
            st.info("AI has categorized these. Check and edit categories if needed, then save.")
            
            edited_df = st.data_editor(
                st.session_state.temp_transactions,
                column_config={
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=["Food", "Travel", "Shopping", "Housing", "Bills", "Bank Charges", "Income", "Miscellaneous"],
                        required=True
                    )
                },
                use_container_width=True,
                num_rows="dynamic"
            )
            
            col_save, col_discard = st.columns(2)
            with col_save:
                if st.button("Save to Backend", type="primary", use_container_width=True):
                    if selected_month in st.session_state.past_months:
                        st.session_state.past_months[selected_month] = pd.concat([st.session_state.past_months[selected_month], edited_df], ignore_index=True)
                    else:
                        st.session_state.past_months[selected_month] = edited_df
                    
                    st.session_state.db_data = pd.concat(list(st.session_state.past_months.values()), ignore_index=True)
                    st.session_state.temp_transactions = pd.DataFrame()
                    st.success("Saved! Data is now in your dashboard.")
                    st.rerun()
            
            with col_discard:
                if st.button("Discard & Re-upload", use_container_width=True):
                    st.session_state.temp_transactions = pd.DataFrame()
                    st.rerun()
    
    # =============== DASHBOARD TAB ===============
    elif st.session_state.app_stage == "📊 Dashboard":
        if st.session_state.db_data.empty:
            st.info("No data available. Please upload your Indian bank statement.")
        else:
            df = st.session_state.db_data
            total = df['Amount'].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Spent", f"₹{total:,.2f}")
            m2.metric("Remaining Budget", f"₹{st.session_state.monthly_budget - total:,.2f}")
            m3.metric("Bank Charges Identified", f"₹{df[df['Category']=='Bank Charges']['Amount'].sum():,.2f}")

            c1, c2 = st.columns([1.5, 1])
            with c1:
                fig = px.bar(df.groupby('Category')['Amount'].sum().reset_index(), 
                             x='Category', y='Amount', template='plotly_dark', color='Category')
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig_pie = px.pie(df, values='Amount', names='Category', hole=0.5, template='plotly_dark')
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # =============== COMPARING TAB ===============
    elif st.session_state.app_stage == "📈 Comparing":
        st.subheader("Compare Past Months")
        st.markdown("Upload a past month's statement to compare with your recent data.")
        
        past_file = st.file_uploader("Upload Past Month Statement (PDF/CSV/Excel)", type=["pdf", "csv", "xlsx"], key="past_upload")
        if past_file and st.button("Process Past Month for Comparison", type="primary"):
            with st.spinner("Processing past month data..."):
                past_df = parse_statement(past_file)
                if not past_df.empty:
                    past_df["Period"] = "Past Month"
                    st.session_state.compare_past_df = past_df
                    st.success("Past month processed! Now comparing with recent data.")
                else:
                    st.error("Could not process past month file.")
        
        if not st.session_state.compare_past_df.empty and not st.session_state.db_data.empty:
            recent_df = st.session_state.db_data.copy()
            recent_df["Period"] = "Recent Month"
            
            comp_df = pd.concat([st.session_state.compare_past_df, recent_df], ignore_index=True)
            
            comp_metrics = comp_df.groupby("Period").agg({"Amount": "sum"}).reset_index()
            st.subheader("Spend Comparison: Past vs Recent")
            fig_comp = px.bar(comp_metrics, x="Period", y="Amount", color="Period", template="plotly_dark")
            st.plotly_chart(fig_comp, use_container_width=True)
            
            st.subheader("Category Trends: Past vs Recent")
            cat_comp = comp_df.groupby(["Period", "Category"])["Amount"].sum().reset_index()
            fig_cat = px.bar(cat_comp, x="Category", y="Amount", color="Period", barmode="group", template="plotly_dark")
            st.plotly_chart(fig_cat, use_container_width=True)
        elif st.session_state.compare_past_df.empty:
            st.info("Upload a past month file to start comparing.")
        else:
            st.info("No recent data available. Upload current data first.")
    
    # =============== ML SUGGESTIONS TAB ===============
    elif st.session_state.app_stage == "🤖 ML Suggestions":
        st.subheader("Smart AI Advisor")
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 5px solid #10b981; padding: 20px; border-radius: 8px;">
            <h4 style="color: #10b981; margin-top:0;">🤖 Indian Bank Optimization</h4>
            We noticed frequent <b>SMS Charges</b> and <b>Minimum Balance</b> alerts. 
            Maintaining an extra ₹2,000 could save you ₹150 in monthly bank fees.
        </div>
        """, unsafe_allow_html=True)
    
    # =============== REVIEW TAB ===============
    elif st.session_state.app_stage == "🔍 Review":
        st.subheader("Edit & Export Transactions")

        if not st.session_state.db_data.empty:
            st.session_state.db_data = st.data_editor(
                st.session_state.db_data,
                use_container_width=True
            )

            col1, col2 = st.columns(2)

            with col1:
                csv = st.session_state.db_data.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "Indian_Bank_Expense_Report.csv",
                    "text/csv",
                    use_container_width=True
                )

            with col2:
                pdf_file = create_pdf(st.session_state.db_data)
                st.download_button(
                    "📄 Download PDF",
                    pdf_file,
                    "Indian_Bank_Expense_Report.pdf",
                    "application/pdf",
                    use_container_width=True
                )
        else:
            st.warning("No data to review.")
    
    # =============== SIDEBAR SETTINGS ===============
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.session_state.monthly_budget = st.number_input("Monthly Budget (₹)", value=st.session_state.monthly_budget)
        
        if st.button("Reset Everything", use_container_width=True):
            st.session_state.db_data = pd.DataFrame(columns=["Date", "Description", "Amount", "Category"])
            st.session_state.past_months = {}
            st.session_state.temp_transactions = pd.DataFrame()
            st.session_state.compare_past_df = pd.DataFrame()
            st.rerun()
        
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            logout()

# ============================================
# 8. ACCESS CONTROL
# ============================================
elif st.session_state.current_page == "dashboard" and not st.session_state.logged_in:
    st.warning("Please login to access the dashboard")
    st.session_state.current_page = "login"
    st.rerun()