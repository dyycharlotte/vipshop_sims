import polars as pl
import streamlit as st

from utils.config import CAT, CAT_MAP, DATE, DATE_MAX, DATE_MIN
from utils.data import (
    get_df_ov,
    get_monthly_ov_heatmap,
    get_sub_td_metric,
    get_td_filters,
    get_td_metric,
    load_data,
)

st.set_page_config(layout="wide", page_title="Sales", page_icon="📊")
st.title("Sales")
df_raw = load_data()


with st.expander("Sales Decomposition", expanded=True):
    # ------------------------------
    # Filter by Date and Category
    # ------------------------------
    cols_filter = st.columns(3)
    with cols_filter[0]:
        date = st.date_input("As of Date", DATE, min_value=DATE_MIN, max_value=DATE_MAX)
        year = date.year
        month = date.month
        day = date.day
        quarter = (month - 1) // 3 + 1

    with cols_filter[1]:
        cat_sel = st.radio("Display by", CAT, horizontal=True)
        cat = CAT_MAP.get(cat_sel)

    with cols_filter[2]:
        subcat_list = sorted(df_raw[cat].unique().to_list())
        subcat = st.selectbox(f"Select {cat_sel}", subcat_list)

    df = df_raw.filter(pl.col(cat) == subcat)

    filters = get_td_filters(year, month, quarter, day)
    df_sales = get_td_metric(df, "Sales", filters)
    df_profit = get_td_metric(df, "Profit", filters)
    df_cost = get_td_metric(df, "Cost", filters)

    # ------------------------------
    # Total Sales and Gross Profit
    # ------------------------------
    st.subheader(f"As of {date}")
    cols_growth = st.columns(2)
    with cols_growth[0]:
        st.caption(f"Total Sales of {cat_sel} - {subcat}")
        st.dataframe(
            df_sales,
            column_config={
                "CurrentPeriod": st.column_config.NumberColumn(format="$%d"),
                "LastPeriod": st.column_config.NumberColumn(format="$%d"),
                "Growth": st.column_config.ProgressColumn(),
            },
        )

    with cols_growth[1]:
        st.caption(f"Gross Profit of {cat_sel} - {subcat}")
        st.dataframe(
            df_profit,
            column_config={
                "CurrentPeriod": st.column_config.NumberColumn(format="$%d"),
                "LastPeriod": st.column_config.NumberColumn(format="$%d"),
                "Growth": st.column_config.ProgressColumn(),
            },
        )

    # ------------------------------
    # Total Sales by Subcategory
    # ------------------------------
    ytd_filter, qtd_filter, mtd_filter, lytd_filter, lqtd_filter, lmtd_filter = filters
    col_sub = "SubcategoryName"
    metric = "Sales"
    try:
        df_sub_sales = (
            get_sub_td_metric(df, metric, col_sub, "YTD", ytd_filter, lytd_filter)
            .join(
                get_sub_td_metric(df, metric, col_sub, "QTD", ytd_filter, lytd_filter),
                on=col_sub,
            )
            .join(
                get_sub_td_metric(df, metric, col_sub, "MTD", ytd_filter, lytd_filter),
                on=col_sub,
            )
        )
    except Exception:
        df_sub_sales = pl.DataFrame({"Subcategory": ["No Data"]})

    st.caption(f"Total Sales of {cat_sel} - {subcat}  by Subcategory")
    st.dataframe(
        df_sub_sales,
        column_config={
            "SubcategoryName": st.column_config.TextColumn("Subcategory"),
            "YTD": st.column_config.NumberColumn(format="$%d"),
            "QTD": st.column_config.NumberColumn(format="$%d"),
            "MTD": st.column_config.NumberColumn(format="$%d"),
            "YTD Growth": st.column_config.ProgressColumn(),
            "QTD Growth": st.column_config.ProgressColumn(),
            "MTD Growth": st.column_config.ProgressColumn(),
        },
    )

    # ------------------------------
    # Total Sales by Brand or Product
    # ------------------------------
    col_detail = "ProductName" if cat == "BrandName" else "BrandName"
    metric = "Sales"
    try:
        df_detail_sales = (
            get_sub_td_metric(df, metric, col_detail, "YTD", ytd_filter, lytd_filter)
            .join(
                get_sub_td_metric(
                    df, metric, col_detail, "QTD", ytd_filter, lytd_filter
                ),
                on=col_detail,
            )
            .join(
                get_sub_td_metric(
                    df, metric, col_detail, "MTD", ytd_filter, lytd_filter
                ),
                on=col_detail,
            )
        )
    except Exception:
        df_detail_sales = pl.DataFrame({col_detail.strip("Name"): ["No Data"]})

    st.caption(f"Total Sales of {cat_sel} - {subcat} by {col_detail.strip('Name')}")
    st.dataframe(
        df_detail_sales,
        column_config={
            col_detail: st.column_config.TextColumn(col_detail.strip("Name")),
            "YTD": st.column_config.NumberColumn(format="$%d"),
            "QTD": st.column_config.NumberColumn(format="$%d"),
            "MTD": st.column_config.NumberColumn(format="$%d"),
            "YTD Growth": st.column_config.ProgressColumn(),
            "QTD Growth": st.column_config.ProgressColumn(),
            "MTD Growth": st.column_config.ProgressColumn(),
        },
    )


# ------------------------------
# Monthly Sales Heatmap
# ------------------------------
with st.expander("Monthly Sales Heatmap", expanded=True):
    cols_filter_ov = st.columns(3)
    with cols_filter_ov[0]:
        year_sel_ov = st.radio(
            "Year",
            options=[DATE.year, DATE.year - 1],
            index=0,
            horizontal=True,
        )

    with cols_filter_ov[1]:
        cat_sel_ov = st.radio("Breakdown by", CAT, horizontal=True)
        cat_ov = CAT_MAP.get(cat_sel_ov)

    with cols_filter_ov[2]:
        subcat_list_ov = sorted(df_raw[cat_ov].unique().to_list())
        subcat_ov = st.selectbox("Further Breakdown", [None] + subcat_list_ov)

    fig_heatmap = get_monthly_ov_heatmap(df_raw, year_sel_ov, cat_ov, subcat_ov)
    st.plotly_chart(fig_heatmap)


with st.expander("Total Sales Trend (Available to Admin)", expanded=False):
    df_ov = get_df_ov(df_raw)

    st.dataframe(
        df_ov,
        column_config={
            "CurrentYear": st.column_config.BarChartColumn(
                f"{DATE.year} Jan - {DATE.strftime('%b')}", width="large", y_min=0
            ),
            "LastYear": st.column_config.BarChartColumn(
                f"{DATE.year - 1} Jan - Dec",
                width="large",
                y_min=0,
            ),
        },
    )
