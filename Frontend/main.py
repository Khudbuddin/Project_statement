import streamlit as st
from streamlit_option_menu import option_menu
import sys
from pathlib import Path

# ---------------------------------------------------
# 1️⃣ Path Setup & Database Connection
# ---------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Import your colleague's database logic
from backend.Databases.database_manager import verify_user, save_for_backend
# ---------------------------------------------------
# 2️⃣ Page Config & Professional CSS
# ---------------------------------------------------
st.set_page_config(
    page_title="SmartSpend AI",
    page_icon="💸",
    layout="wide"
)

def apply_custom_css():
    css_path = ROOT_DIR / "Frontend" / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------
# 3️⃣ Routing Logic (The "Switchboard")
# ---------------------------------------------------
def render_page(page_name):
    """Dynamically imports and shows the selected page content"""
    if page_name == "Dashboard":
        from Frontend.pages import dashboard
        dashboard.show()
    elif page_name == "upload Statement":
        from Frontend.pages import upload
        upload.show()
    elif page_name == "Graph":
        from Frontend.pages import graph
        graph.show()
    elif page_name == "History":
        from Frontend.pages import history
        history.show()
    elif page_name == "Comparison":
        from Frontend.pages import comparison
        comparison.show()
    elif page_name == "Insights":
        from Frontend.pages import insights
        insights.show()
    elif page_name == "Profile":
        from Frontend.pages import profile
        profile.show()

# ---------------------------------------------------
# 4️⃣ Main App Controller
# ---------------------------------------------------
def main():
    apply_custom_css()

    # Session State Initialization
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "landing"
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

    # Force Sidebar to be hidden everywhere
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

    # --- PHASE A: Authentication ---
    if not st.session_state.logged_in:
        if st.session_state.auth_mode == "landing":
            from Frontend.pages import intro
            intro.show()
        elif st.session_state.auth_mode == "login":
            from Frontend.auth.login import show_login
            show_login()
        elif st.session_state.auth_mode == "signup":
            from Frontend.auth.signup import show_signup
            show_signup()

    # --- PHASE B: Full Application (Top Nav Design) ---
    else:
        # Create a 3-column header for the Navigation
        # Col 1: Profile | Col 2: Navigation | Col 3: Logout
        header_col1, header_col2, header_col3 = st.columns([1, 4, 1], gap="small")

        with header_col1:
            if st.session_state.user_info:
                u_info = st.session_state.user_info
                email = u_info.get('email', 'User') if isinstance(u_info, dict) else u_info[1]
                initial = email[0].upper()
                st.markdown(f'<div class="profile-circle">{initial}</div>', unsafe_allow_html=True)

        with header_col2:
            # Horizontal Option Menu
            selected = option_menu(
                menu_title=None,
                options=["Dashboard","Upload", "Graph", "History", "Comparison", "Insights"],
                icons=["house", "cloud-upload", "clock-history", "bar-chart-steps", "lightbulb"],
                menu_icon="cast",
                default_index=0,
                orientation="horizontal",
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "#1e293b"},
                    "nav-link-selected": {"background-color": "#0ea5e9"},
                }
            )

        with header_col3:
            if st.button("Log out", key="nav_logout"):
                st.session_state.logged_in = False
                st.session_state.user_info = None
                st.rerun()

        st.divider()

        # Trigger the dynamic routing
        # Note: Map "Upload" from menu to "Upload Statement" page
        page_map = {"Upload": "Upload Statement"}
        render_page(page_map.get(selected, selected))
if __name__ == "__main__":
    main()