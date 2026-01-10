import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
        
        [data-testid="stAppViewContainer"] {
            background-color: #0a0c10;
            background-image: 
                radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(30, 41, 59, 0.2) 0px, transparent 50%);
        }

        .block-container { padding-top: 2rem; }
        .hero-container { display: flex; align-items: center; justify-content: center; padding: 80px 20px; gap: 80px; max-width: 1200px; margin: 0 auto; }
        .hero-badge { background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px 14px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; margin-bottom: 24px; display: inline-block; text-transform: uppercase; }
        .hero-title { font-size: 4.5rem; font-weight: 800; line-height: 1; color: #f8fafc; margin-bottom: 25px; }
        .hero-title span { color: #10b981; }
        .hero-desc { font-size: 1.25rem; color: #94a3b8; line-height: 1.6; margin-bottom: 35px; max-width: 550px; }
        .auth-card, .auth-form-card { background: #111827; padding: 40px; border-radius: 20px; border: 1px solid #1f2937; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); }
        .pro-badge { background: linear-gradient(90deg, #10b981, #3b82f6); color: black; padding: 2px 10px; border-radius: 20px; font-size: 10px; font-weight: 800; margin-left: 10px; }
        .f-item { color: #cbd5e1; font-size: 0.95rem; display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
        .f-item i { color: #10b981; }
        .security-box { background: rgba(16, 185, 129, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.1); margin: 20px 0; }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    """, unsafe_allow_html=True)