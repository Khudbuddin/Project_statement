import streamlit as st

def show():
    st.title("📂 History")

    history = st.session_state.get("history", [])

    if not history:
        st.info("No files analyzed yet")
        return

    # Unique files (extra safety)
    unique_files = list({item["file"] for item in history})

    st.metric("Total Files Analyzed", len(unique_files))

    st.subheader("Files")
    for file in unique_files:
        st.write(f"📁 {file}")