import polars as pl
import streamlit as st

from utils.config import DATE
from utils.data import get_df_turnover, load_data

st.set_page_config(layout="wide", page_title="Inventory", page_icon="📦")
st.title("Inventory")

df_raw = load_data()
year = DATE.year
month = DATE.month

with st.expander("Trunover Analysis", expanded=True):
    with st.columns(2)[0]:
        n_month = st.slider(
            "Based on Number of Past Months", min_value=1, max_value=DATE.month, value=3
        )
        subcat_list = sorted(df_raw["CategoryName"].unique().to_list())
        subcat = st.selectbox("Category", subcat_list)

    # ------------------------------
    # Column Names
    # ------------------------------
    sales_col = f"Sales({n_month}M)"
    avg_sales_col = f"AvgSales({n_month}M)"
    quantity_col = f"Quantity({n_month}M)"
    avg_quantity_col = f"AvgQuantity({n_month}M)"
    avg_quantity_col_rename = f"AvgUnitSold({n_month}M)"

    group_cat = "BrandName"
    turnover_cat = "DollarTurnover"
    cols_cat = [
        group_cat,
        sales_col,
        avg_sales_col,
        avg_quantity_col,
        "StockValue",
        "Stock",
        turnover_cat,
        "TurnoverStatus",
    ]
    group_brand = "ProductName"
    turnover_brand = "Turnover"
    cols_brand = [
        group_brand,
        avg_sales_col,
        quantity_col,
        avg_quantity_col,
        "Stock",
        turnover_brand,
        "TurnoverStatus",
    ]

    # ------------------------------
    # Category Turnover
    # ------------------------------
    df_cat = df_raw.filter(pl.col("CategoryName") == subcat).filter(
        (pl.col("OrderDate") >= pl.date(year, month - n_month + 1, 1))
    )

    df_cat_turnover = (
        get_df_turnover(df_cat, group_cat, turnover_cat, n_month)
        .select(cols_cat)
        .with_columns(pl.col(avg_quantity_col).round(1))
    )

    st.dataframe(
        df_cat_turnover,
        column_config={
            "DollarTurnover": st.column_config.NumberColumn("Turnover"),
            sales_col: st.column_config.LineChartColumn(width="meidum", y_min=0.0),
            avg_sales_col: st.column_config.NumberColumn(format="$%d"),
            avg_quantity_col: st.column_config.NumberColumn(avg_quantity_col_rename),
            "StockValue": st.column_config.NumberColumn(format="$%d"),
        },
    )

    # ------------------------------
    # Brand Turnover
    # ------------------------------
    with st.columns(2)[0]:
        brand = st.selectbox("Brand", sorted(df_cat["BrandName"].unique().to_list()))
        # sort_by_sales_brand = st.checkbox("Sort by Sales", value=True)

    df_brand = df_cat.filter(pl.col("BrandName") == brand)
    df_brand_turnover = (
        get_df_turnover(df_brand, group_brand, turnover_brand, n_month)
        # .sort(
        #     avg_sales_col if sort_by_sales_brand else "ProductName",
        #     descending=sort_by_sales_brand,
        # )
        .select(cols_brand)
    )
    st.dataframe(
        df_brand_turnover,
        column_config={
            quantity_col: st.column_config.LineChartColumn(width="meidum", y_min=0.0),
            avg_quantity_col: st.column_config.NumberColumn(avg_quantity_col_rename),
            "Stock": st.column_config.NumberColumn(format="%d"),
        },
    )
