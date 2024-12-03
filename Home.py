import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Vipshop Sales and Inventory Manage System",
    page_icon="🚀",
)
st.title("Welcome to Vipshop Sales and Inventory Management System")
st.page_link("pages/1_🎨_Overview.py", label="Overview", icon="🎨")
st.page_link("pages/2_📊_Sales.py", label="Sales", icon="📊")
st.page_link("pages/3_📦_Inventory.py", label="Inventory", icon="📦")
