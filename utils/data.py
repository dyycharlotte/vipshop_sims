import calendar
import datetime as dt

import plotly.express as px
import polars as pl
import streamlit as st

from utils.config import DATA_FILE


@st.cache_data
def load_data():
    df_raw = (
        pl.read_csv(DATA_FILE)
        .with_columns(
            pl.col("OrderDate").str.to_date(format="%m/%d/%y"),
        )
        .with_columns(
            Sales=(pl.col("UnitPrice") - pl.col("Discount")) * pl.col("Quantity"),
            StockValue=(pl.col("UnitPrice") - pl.col("Discount")) * pl.col("Stock"),
        )
        .with_columns(Profit=(pl.col("Sales") - pl.col("Cost") * pl.col("Quantity")))
        .with_columns(
            BuyerName=pl.concat_str(
                pl.col("BuyerFirstName"), pl.col("BuyerLastName"), separator=" "
            )
        )
    )
    return df_raw


def get_td_filters(year, month, quarter, day):
    ytd_filter = pl.col("OrderDate").dt.year() == year
    qtd_filter = (pl.col("OrderDate").dt.year() == year) & (
        pl.col("OrderDate").dt.quarter() == quarter
    )
    mtd_filter = (pl.col("OrderDate").dt.year() == year) & (
        pl.col("OrderDate").dt.month() == month
    )
    lytd_filter = pl.col("OrderDate").is_between(
        dt.date(year - 1, 1, 1), dt.date(year - 1, month, day)
    )
    lqtd_filter = pl.col("OrderDate").is_between(
        dt.date(year - 1, (quarter - 1) * 3 + 1, 1),
        dt.date(year - 1, quarter * 3, day),
    )
    lmtd_filter = pl.col("OrderDate").is_between(
        dt.date(year - 1, month, 1), dt.date(year - 1, month, day)
    )
    return ytd_filter, qtd_filter, mtd_filter, lytd_filter, lqtd_filter, lmtd_filter


def get_td_metric(df, metric, filters):
    ytd_filter, qtd_filter, mtd_filter, lytd_filter, lqtd_filter, lmtd_filter = filters
    df_td_metric = (
        pl.DataFrame(
            {
                "Range": ["YTD", "QTD", "MTD"],
                "CurrentPeriod": [
                    df.filter(ytd_filter).select(pl.sum(metric)).get_columns()[0][0],
                    df.filter(qtd_filter).select(pl.sum(metric)).get_columns()[0][0],
                    df.filter(mtd_filter).select(pl.sum(metric)).get_columns()[0][0],
                ],
                "LastPeriod": [
                    df.filter(lytd_filter).select(pl.sum(metric)).get_columns()[0][0],
                    df.filter(lqtd_filter).select(pl.sum(metric)).get_columns()[0][0],
                    df.filter(lmtd_filter).select(pl.sum(metric)).get_columns()[0][0],
                ],
            }
        )
        .with_columns(Growth=(pl.col("CurrentPeriod") / pl.col("LastPeriod") - 1))
        .with_columns(
            pl.when(pl.col("Growth").is_infinite())
            .then(float("nan"))
            .otherwise(pl.col("Growth"))
            .alias("Growth")
        )
    )
    return df_td_metric


def get_sub_td_metric(df, metric, col_sub, col_td, td_filter, ltd_filter):
    col_ltd = col_td + " Growth"

    df_sub_td_metric = (
        df.filter(td_filter | ltd_filter)
        .with_columns(
            pl.when(td_filter)
            .then(pl.lit(col_td))
            .otherwise(pl.lit(col_ltd))
            .alias("Range")
        )
        .group_by(col_sub, "Range")
        .agg(pl.sum(metric).alias(metric))
        .pivot("Range", index=col_sub, values=metric)
        .sort(col_sub)
        .filter(pl.col(col_td).is_not_null())
        .with_columns(
            # Add col_ltd with NaN if missing using coalesce
            pl.coalesce(pl.col(f"^{col_ltd}$"), pl.lit(float("nan"))).alias(col_ltd)
        )
        .with_columns(
            # Compute the growth
            (pl.col(col_td) / pl.col(col_ltd) - 1).alias(col_ltd)
        )
        .with_columns(
            # Handle infinite values and replace with NaN
            pl.when(pl.col(col_ltd).is_infinite())
            .then(pl.lit(float("nan")))
            .otherwise(pl.col(col_ltd))
            .alias(col_ltd)
        )
        .select(col_sub, col_td, col_ltd)
    )

    return df_sub_td_metric


def get_monthly_ov_heatmap(df, year, group, subgroup):
    month_abbr_list = calendar.month_abbr[1:]
    if subgroup is None:
        group_final = group
        colormap = "Agsunset_r"
    else:
        group_final = "SubcategoryName" if group == "BrandName" else "BrandName"
        colormap = "Bluyl"

    df_monthly = (
        df.filter(pl.col("OrderDate").dt.year() == year)
        .filter(pl.col(group) == subgroup if subgroup else True)
        .with_columns(pl.col("OrderDate").dt.strftime("%b").alias("Month"))
        .group_by(group_final, "Month")
        .agg(pl.sum("Sales"))
        .pivot("Month", index=group_final, values="Sales")
        .sort(group_final)
        .with_columns(
            pl.coalesce(pl.col(f"^{mab}$"), pl.lit(float("nan"))).alias(mab)
            for mab in month_abbr_list
        )
        .select(pl.col(group_final, *month_abbr_list))
    )

    fig_heatmap = px.imshow(
        df_monthly.select(pl.col(month_abbr_list)),
        y=df_monthly[group_final].to_numpy(),
        x=month_abbr_list,
        color_continuous_scale=colormap,
        labels={"x": "Month", "y": group_final, "color": "Sales"},
    )

    return fig_heatmap


def get_df_ov(df):
    df_ov = (
        df.group_by(
            [
                pl.col("OrderDate").dt.year().alias("Year"),
                pl.col("OrderDate").dt.month().alias("Month"),
            ]
        )
        .agg(
            pl.sum("Sales").alias("Sales"),
            pl.sum("Profit").alias("Profit"),
        )
        .sort(["Year", "Month"])
        .with_columns(Cost=pl.col("Sales") - pl.col("Profit"))
        .select(pl.exclude(["Year", "Month"]))
        .transpose(include_header=True)
        .select(
            pl.col("column").alias("Item"),
            CurrentYear=pl.concat_list(pl.col([f"column_{i}" for i in range(13, 21)])),
            LastYear=pl.concat_list(pl.col([f"column_{i}" for i in range(13)])),
        )
    )

    return df_ov


def get_df_turnover(df, group, turnover, n_month):
    sales_col = f"Sales({n_month}M)"
    avg_sales_col = f"AvgSales({n_month}M)"
    quantity_col = f"Quantity({n_month}M)"
    avg_quantity_col = f"AvgQuantity({n_month}M)"
    df_turnover = (
        df.with_columns(pl.col("OrderDate").dt.month().alias("Month"))
        .group_by("Month", group)
        .agg(
            pl.sum("Sales").alias("Sales"),
            pl.sum("Quantity").alias("Quantity"),
            pl.last("StockValue").alias("StockValue"),
            pl.last("Stock").alias("Stock"),
        )
        .sort("Month")
        .group_by(group)
        .agg(
            pl.concat_list("Sales").alias(sales_col),
            pl.mean("Sales").alias(avg_sales_col),
            pl.last("StockValue").alias("StockValue"),
            pl.concat_list("Quantity").alias(quantity_col),
            pl.mean("Quantity").alias(avg_quantity_col),
            pl.last("Stock").alias("Stock"),
        )
        .with_columns(
            (pl.col("StockValue") / pl.col(avg_sales_col) * 30)
            .round()
            .alias("DollarTurnover"),
            (pl.col("Stock") / pl.col(avg_quantity_col) * 30).round().alias("Turnover"),
        )
        .with_columns(
            pl.when(pl.col(turnover) >= 90)
            .then(pl.lit("🥶"))
            .when(pl.col(turnover).is_between(60, 90, closed="left"))
            .then(pl.lit("😊"))
            .when(pl.col(turnover).is_between(30, 60, closed="left"))
            .then(pl.lit("😥"))
            .otherwise(pl.lit("🥵"))
            .alias("TurnoverStatus")
        )
        .sort(group)
    )
    return df_turnover
