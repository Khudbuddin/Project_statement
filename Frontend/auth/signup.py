import streamlit as st
from backend.Databases.database_manager import create_user

def show_signup():
    # 1. Create columns to center the card and prevent stretching
    empty_l, card_col, empty_r = st.columns([1, 2, 1])

    with card_col:
        # 2. Header Section (Centered)
        st.markdown("""
            <div class="centered-text">
                <p class="brand-text">STUDY SHARE</p>
                <h1 style="margin-top:0; color:white;">Create Account</h1>
                <p style="color:#94a3b8; margin-bottom:20px;">Join and start sharing study materials</p>
            </div>
        """, unsafe_allow_html=True)

        # 3. Signup Form (The Card)
        # border=False is used because our CSS handles the card border
        with st.form("signup_form", border=False):
            email = st.text_input("Email", placeholder="Enter your email")
            
            # Using placeholders for a cleaner look
            password = st.text_input("Password", type="password", placeholder="Create a strong password")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
            
            st.markdown('<br>', unsafe_allow_html=True)
            
            # Primary Blue Button
            submit = st.form_submit_button("Create Account", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please fill in all fields")
                elif password != confirm:
                    st.error("Passwords do not match")
                else:
                    success = create_user(email, password)
                    if success:
                        st.success("Account created successfully!")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error("User already exists")

        # 4. The "Login" Text Link
        st.markdown('<div class="centered-text">', unsafe_allow_html=True)
        if st.button("Already have an account? Login", key="login_link"):
            st.session_state.auth_mode = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)