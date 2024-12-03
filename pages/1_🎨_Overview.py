import plotly.express as px
import polars as pl
import streamlit as st

from utils.data import load_data
from utils.config import DATE, DATE_MIN

st.set_page_config(layout="wide", page_title="Overview", page_icon="🎨")
st.title("Overview")

df_raw = load_data()

# -----------------------------------
# raw data
# -----------------------------------
with st.expander("View Raw Data", expanded=False):
    st.dataframe(df_raw)


# -----------------------------------
# filter
# -----------------------------------
with st.expander("Filter", expanded=True):
    metric = st.radio("Metric", ["Sales", "Profit", "Cost"], index=0, horizontal=True)

    date_range = [DATE_MIN, DATE]
    date_range_selected = st.slider(
        "Date Range",
        min_value=date_range[0],
        max_value=date_range[1],
        value=date_range,
    )

df_date_range = df_raw.filter(
    pl.col("OrderDate").is_between(date_range_selected[0], date_range_selected[1])
)

# -----------------------------------
# sunburst chart
# -----------------------------------
with st.expander(
    f"{metric} Proportion between {date_range_selected[0]} and {date_range_selected[1]}",
    expanded=True,
):
    color_map_cat = px.colors.qualitative.Prism
    color_map_team = px.colors.qualitative.T10
    color_map_brand = px.colors.qualitative.Alphabet

    col_sunburst = st.columns(3)
    with col_sunburst[0]:
        fig_sunburst_cat_sales = px.sunburst(
            df_date_range.group_by("CategoryName", "SubcategoryName")
            .agg(pl.sum(metric))
            .sort("CategoryName", "SubcategoryName"),
            path=["CategoryName", "SubcategoryName"],
            values=metric,
            title="Category",
            color_discrete_sequence=color_map_cat,
        )
        st.plotly_chart(fig_sunburst_cat_sales)

    with col_sunburst[1]:
        fig_sunburst_team_sales = px.sunburst(
            df_date_range.group_by("TeamID", "BuyerName")
            .agg(pl.sum(metric))
            .sort("TeamID", "BuyerName"),
            path=["TeamID", "BuyerName"],
            values=metric,
            title="Team",
            color_discrete_sequence=color_map_team,
        )
        st.plotly_chart(fig_sunburst_team_sales)

    with col_sunburst[2]:
        fig_sunburst_brand_sales = px.sunburst(
            df_date_range.group_by("BrandName").agg(pl.sum(metric)).sort("BrandName"),
            path=["BrandName"],
            values=metric,
            title="Brand",
            color_discrete_sequence=color_map_brand,
        )
        st.plotly_chart(fig_sunburst_brand_sales)

# -----------------------------------
# time series chart
# -----------------------------------
fig_ts_cat = px.area(
    df_raw.with_columns(
        pl.col("OrderDate").dt.year().alias("Year"),
        pl.col("OrderDate").dt.month().alias("Month"),
    )
    .group_by("Year", "Month", "CategoryName", maintain_order=True)
    .agg(pl.sum(metric))
    .with_columns(
        pl.date(pl.col("Year"), pl.col("Month"), 1).dt.month_end().alias("OrderDate")
    )
    .sort("OrderDate", "CategoryName"),
    x="OrderDate",
    y=metric,
    color="CategoryName",
    color_discrete_sequence=color_map_cat,
    title="Category",
)
fig_ts_cat.update_traces(mode="markers+lines", hovertemplate="$%{y: ,.2r}")
fig_ts_cat.update_layout(hovermode="x unified")

fig_ts_team = px.area(
    df_raw.with_columns(
        pl.col("OrderDate").dt.year().alias("Year"),
        pl.col("OrderDate").dt.month().alias("Month"),
    )
    .group_by("Year", "Month", "TeamID", maintain_order=True)
    .agg(pl.sum(metric))
    .with_columns(
        pl.date(pl.col("Year"), pl.col("Month"), 1).dt.month_end().alias("OrderDate")
    )
    .sort("OrderDate", "TeamID"),
    x="OrderDate",
    y=metric,
    color="TeamID",
    color_discrete_sequence=color_map_team,
    title="Team",
)
fig_ts_team.update_traces(mode="markers+lines", hovertemplate="$%{y: ,.2r}")
fig_ts_team.update_layout(hovermode="x unified")


fig_ts_brand = px.area(
    df_raw.with_columns(
        pl.col("OrderDate").dt.year().alias("Year"),
        pl.col("OrderDate").dt.month().alias("Month"),
    )
    .group_by("Year", "Month", "BrandName", maintain_order=True)
    .agg(pl.sum(metric))
    .with_columns(
        pl.date(pl.col("Year"), pl.col("Month"), 1).dt.month_end().alias("OrderDate")
    )
    .sort("OrderDate", "BrandName"),
    x="OrderDate",
    y=metric,
    color="BrandName",
    color_discrete_sequence=color_map_brand,
    title="Brand",
)
fig_ts_brand.update_traces(mode="markers+lines", hovertemplate="$%{y: ,.2r}")
fig_ts_brand.update_layout(hovermode="x unified")

with st.expander(
    f"{metric} Trend between {date_range[0]} and {date_range[1]}", expanded=True
):
    st.plotly_chart(fig_ts_cat)
    st.plotly_chart(fig_ts_team)
    st.plotly_chart(fig_ts_brand)
