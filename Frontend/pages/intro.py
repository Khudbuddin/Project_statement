import streamlit as st

def show():
    st.set_page_config(layout="wide")

    # Clean spacing
    st.write("")
    st.write("")

    left, right = st.columns([1.2, 1])

    # ===== LEFT SIDE: Persuasive Text =====
    with left:
        st.markdown(
            """
            <h1 style='font-size:52px; font-weight:800; line-height:1.1; color: #f8fafc;'>
            Smart Expense <span style='color:#38bdf8;'>Categorizer</span>,<br>
            Built for Financial Clarity
            </h1>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div style='color:#94a3b8; font-size:20px; margin-top:25px; line-height:1.6; max-width: 90%;'>
            Transform your raw financial data into actionable insights. Our secure platform automates organization and analysis—letting you focus on optimizing your growth.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")
        
        # Professional UI Bullets
        st.markdown("<div style='color:#38bdf8; font-size:18px; margin-bottom:10px;'>✦ <span style='color:#cbd5e1; margin-left:10px;'>Instant PDF & CSV bank statement processing</span></div>", unsafe_allow_html=True)
        st.markdown("<div style='color:#38bdf8; font-size:18px; margin-bottom:10px;'>✦ <span style='color:#cbd5e1; margin-left:10px;'>90% accurate automated classification engine</span></div>", unsafe_allow_html=True)
        st.markdown("<div style='color:#38bdf8; font-size:18px; margin-bottom:10px;'>✦ <span style='color:#cbd5e1; margin-left:10px;'>Interactive analytics and data-driven suggestions</span></div>", unsafe_allow_html=True)

        st.write("")
        st.write("")

        col1, col2 = st.columns([0.8, 1])

        with col1:
            if st.button("Login", type="primary", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

        with col2:
            if st.button("Create Account", type="secondary", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()

    # ===== RIGHT SIDE: Professional Image Insertion =====
    with right:
        # Using a professional high-tech analytics image URL
        image_url = "https://img.freepik.com/free-vector/financial-analytics-concept-illustration_114360-5153.jpg"
        
        st.markdown(
            f"""
            <div style='
                background: rgba(15, 23, 42, 0.6);
                height: 450px;
                border-radius: 32px;
                display:flex;
                flex-direction:column;
                align-items:center;
                justify-content:center;
                border: 1px solid rgba(56, 189, 248, 0.2);
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                overflow: hidden;
            '>
                <img src="{image_url}" style='width: 100%; height: auto; object-fit: cover; opacity: 0.9;'>
                <div style='position: absolute; bottom: 20px; color:#f8fafc; font-size:18px; font-weight:700; letter-spacing:2px; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 10px;'>
                    SMART ANALYTICS ENGINE
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )