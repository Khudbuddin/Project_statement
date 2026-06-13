import streamlit as st

def show():

    st.title("📊 Category Insights")

    if "latest_df" not in st.session_state:
        st.warning("⚠️ No data available. Please upload and analyze first.")
        return

    df = st.session_state["latest_df"]

    st.subheader("Category Distribution")
    st.bar_chart(df['Predicted_Category'].value_counts())