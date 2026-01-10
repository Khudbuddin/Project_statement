import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# Import our custom modules
from styles import apply_custom_styles
from utils import parse_statement, create_pdf, smart_categorize

# 1. CONFIGURATION
st.set_page_config(page_title="ExpenseWise | Premium Finance", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")
apply_custom_styles()

# 2. SESSION STATE
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_page" not in st.session_state: st.session_state.current_page = "welcome"
if "user_name" not in st.session_state: st.session_state.user_name = "Yunus Ali"
if "db_data" not in st.session_state: st.session_state.db_data = pd.DataFrame(columns=["Date", "Description", "Amount", "Category"])
if "temp_transactions" not in st.session_state: st.session_state.temp_transactions = pd.DataFrame()
if "app_stage" not in st.session_state: st.session_state.app_stage = "📊 Dashboard"
if "past_months" not in st.session_state: st.session_state.past_months = {}
if "compare_past_df" not in st.session_state: st.session_state.compare_past_df = pd.DataFrame()
if "monthly_budget" not in st.session_state: st.session_state.monthly_budget = 50000

# 3. HELPER FUNCTIONS
def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# 4. PAGE ROUTING
# --- WELCOME PAGE ---
if st.session_state.current_page == "welcome":
    st.markdown("""
    <div class="hero-container">
        <div class="hero-text">
            <div class="hero-badge">Institutional Grade Security</div>
            <h1 class="hero-title">Master Your <span>Capital.</span></h1>
            <p class="hero-desc">The definitive workspace for private wealth management.</p>
            <div class="f-item"><i class="fas fa-shield-alt"></i> End-to-End Local Privacy</div>
            <div class="f-item"><i class="fas fa-bolt"></i> Instant AI Categorization</div>
        </div>
        <div class="auth-card">
            <div style="font-size: 1.8rem; font-weight: 800; color: #f8fafc; margin-bottom: 40px;">
                <i class="fas fa-wallet" style="color: #10b981;"></i> ExpenseWise
            </div>
            <p style="color:#cbd5e1; margin-bottom:20px;">Access your financial dashboard</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("🚀 Create Premium Account", type="primary", use_container_width=True):
            st.session_state.current_page = "signup"; st.rerun()
        if st.button("🔐 Sign In to Dashboard", type="secondary", use_container_width=True):
            st.session_state.current_page = "login"; st.rerun()

# --- SIGNUP/LOGIN PAGES (Combined Logic) ---
elif st.session_state.current_page in ["signup", "login"]:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(f'<div class="auth-form-card"><h3>{"Join ExpenseWise" if st.session_state.current_page=="signup" else "Welcome Back"}</h3>', unsafe_allow_html=True)
        with st.form("auth_form"):
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            submit = st.form_submit_button("Proceed", use_container_width=True)
            if submit and email and pwd:
                st.session_state.logged_in = True
                st.session_state.current_page = "dashboard"
                st.rerun()
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.current_page = "welcome"; st.rerun()

# --- DASHBOARD PAGE ---
elif st.session_state.current_page == "dashboard" and st.session_state.logged_in:
    # Header
    h_l, h_m, h_r = st.columns([1, 2.5, 1])
    with h_l: st.markdown('<div style="font-size: 1.5rem; font-weight: 800; color: white;">💎 ExpenseWise</div>', unsafe_allow_html=True)
    with h_m:
        st.session_state.app_stage = st.segmented_control("Nav", options=["📊 Dashboard", "📈 Comparing", "🔍 Review", "🤖 ML Suggestions", "📤 Upload"], default=st.session_state.app_stage, label_visibility="collapsed")
    with h_r: st.markdown(f'<div style="text-align: right; color: white;">{st.session_state.user_name}<span class="pro-badge">PRO</span></div>', unsafe_allow_html=True)
    st.divider()

    # Tab Logic
    if st.session_state.app_stage == "📤 Upload":
        uploaded_file = st.file_uploader("Upload Statement", type=["pdf", "csv", "xlsx"])
        if uploaded_file and st.button("Process"):
            new_df = parse_statement(uploaded_file)
            st.session_state.temp_transactions = new_df
            st.rerun()
        
        if not st.session_state.temp_transactions.empty:
            edited = st.data_editor(st.session_state.temp_transactions, use_container_width=True)
            if st.button("Save to Dashboard", type="primary"):
                st.session_state.db_data = pd.concat([st.session_state.db_data, edited], ignore_index=True)
                st.session_state.temp_transactions = pd.DataFrame()
                st.success("Data Saved!"); st.rerun()

    elif st.session_state.app_stage == "📊 Dashboard":
        if st.session_state.db_data.empty:
            st.info("No data yet. Go to Upload.")
        else:
            df = st.session_state.db_data
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Spent", f"₹{df['Amount'].sum():,.2f}")
            m2.metric("Remaining", f"₹{st.session_state.monthly_budget - df['Amount'].sum():,.2f}")
            
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(px.bar(df.groupby('Category')['Amount'].sum().reset_index(), x='Category', y='Amount', template='plotly_dark'))
            with c2: st.plotly_chart(px.pie(df, values='Amount', names='Category', hole=0.5, template='plotly_dark'))

    elif st.session_state.app_stage == "🔍 Review":
        if not st.session_state.db_data.empty:
            st.session_state.db_data = st.data_editor(st.session_state.db_data, use_container_width=True)
            pdf_b = create_pdf(st.session_state.db_data)
            st.download_button("📄 Download PDF", pdf_b, "Report.pdf", "application/pdf")
        else: st.warning("No data.")

    # Sidebar
    with st.sidebar:
        st.session_state.monthly_budget = st.number_input("Budget", value=st.session_state.monthly_budget)
        if st.button("🚪 Logout", use_container_width=True): logout()