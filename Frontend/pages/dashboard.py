import streamlit as st
import pandas as pd
import os
from pathlib import Path
import pdfplumber

# Backend imports
from backend.Scripts.predicted import process_file
from backend.file_handler.loader import load_file


def show():

    # ---------------- USER NAME ----------------
    if st.session_state.get("user_info"):
        u_info = st.session_state.user_info
        email = u_info.get('email', 'User') if isinstance(u_info, dict) else u_info[1]
        user_name = email.split('@')[0].capitalize()
    else:
        user_name = "User"

    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 3rem;">Hi, {user_name}! 👋</h1>
            <p style="color: #94a3b8;">Upload and analyze your expenses</p>
        </div>
    """, unsafe_allow_html=True)

    # ---------------- INIT SESSION ----------------
    if "history" not in st.session_state:
        st.session_state["history"] = []

    # ---------------- UPLOAD CARD ----------------
    _, center_col, _ = st.columns([1, 3, 1])

    with center_col:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload PDF/CSV",
            type=["pdf", "csv"],
            label_visibility="collapsed"
        )

        pdf_password = None

        # ---------------- FILE READY ----------------
        if uploaded_file:

            st.success(f"{uploaded_file.name} ready")

            temp_path = f"temp_{uploaded_file.name}"

            # Save file temporarily
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 🔐 Detect password-protected PDF
            if uploaded_file.name.endswith(".pdf"):
                try:
                    with pdfplumber.open(temp_path) as pdf:
                        pass
                except Exception:
                    pdf_password = st.text_input("🔐 Enter PDF Password", type="password")

            # ---------------- ANALYZE BUTTON ----------------
            if st.button("🚀 Run Full Intelligence Analysis", use_container_width=True):

                try:
                    # 🔐 Validate password if PDF
                    if uploaded_file.name.endswith(".pdf"):
                        try:
                            if pdf_password:
                                with pdfplumber.open(temp_path, password=pdf_password) as pdf:
                                    pass
                            else:
                                with pdfplumber.open(temp_path) as pdf:
                                    pass
                        except Exception:
                            st.error("❌ Wrong password or unable to open PDF")
                            return

                    # ✅ MAIN BACKEND CALL
                    df, error = process_file(temp_path, password=pdf_password)

                    if error:
                        st.error(f"❌ {error}")
                        return

                    # ---------------- SUCCESS ----------------
                    st.success("✅ Analysis Completed")
                    st.dataframe(df, use_container_width=True)

                    # ✅ STORE FOR GRAPH PAGE
                    st.session_state["latest_df"] = df

                    # ✅ HISTORY TRACKING (NO DUPLICATES)
                    file_name = uploaded_file.name
                    existing_files = [item["file"] for item in st.session_state["history"]]

                    if file_name not in existing_files:
                        st.session_state["history"].append({
                            "file": file_name
                        })

                finally:
                    # Clean temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ---------------- OVERVIEW ----------------
    st.markdown("### 📊 Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Documents Analyzed", len(st.session_state.get("history", [])))
    col2.metric("Total Transactions", "Auto")
    col3.metric("Top Category", "Auto")

    # ---------------- RECENT FILES ----------------
    st.markdown("#### Recent Files")

    history = st.session_state.get("history", [])

    if history:
        for item in history[::-1][:3]:
            st.write(f"📁 {item['file']}")
    else:
        st.info("No files analyzed yet")