import streamlit as st
from backend.Databases.database_manager import verify_user

def show_login():
    # 1. Create 3 columns. The middle one (width 2) is our card area.
    empty_l, card_col, empty_r = st.columns([1, 2, 1])

    with card_col:
        # 2. Header (Centered)
        st.markdown("""
            <div class="centered-text">
                <p style="color:#0ea5e9; font-weight:bold; margin-bottom:0;">STUDY SHARE</p>
                <h1 style="margin-top:0; color:white;">Welcome Back</h1>
                <p style="color:#94a3b8;">Login to access your study materials</p>
            </div>
        """, unsafe_allow_html=True)

        # 3. The Form (Styled as a card in CSS)
        with st.form("login_form", border=False):
            email = st.text_input("Email / Phone / Username", placeholder="Enter your credentials")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                user = verify_user(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        # 4. Link-style button centered below
        st.markdown('<div class="centered-text">', unsafe_allow_html=True)
        if st.button("Don't have an account? Sign up", key="signup_link"):
            st.session_state.auth_mode = "signup"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)