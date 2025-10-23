import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# PAGE SETUP
# ==============================
st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")
st.title("📊 Al Madina: Monthly Sales & Profit Dashboard")

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    df = pd.read_excel("sales_data.xlsx")  # your file here
    return df

df = load_data()

# ==============================
# SIDEBAR FILTERS
# ==============================
st.sidebar.header("🔍 Filters")

# Category filter (single select)
categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", categories)

# Filter the data
if selected_category != "All":
    filtered_df = df[df["Category"] == selected_category]
else:
    filtered_df = df.copy()

# ==============================
# KEY INSIGHTS SECTION
# ==============================
st.markdown("### 📈 Key Insights")

total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
avg_gp_percent = (total_profit / total_sales) * 100 if total_sales != 0 else 0
top_outlet = filtered_df.groupby("Outlet")["Sales"].sum().idxmax()
top_category = (
    selected_category if selected_category != "All"
    else df.groupby("Category")["Sales"].sum().idxmax()
)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Sales", f"AED {total_sales:,.0f}")
col2.metric("Total Profit", f"AED {total_profit:,.0f}")
col3.metric("Avg GP%", f"{avg_gp_percent:.2f}%")
col4.metric("Top Outlet", top_outlet)
col5.metric("Top Category", top_category)

st.markdown("---")

# ==============================
# VISUALIZATIONS
# ==============================
# Sales vs Profit Bar Chart
sales_profit_chart = px.bar(
    filtered_df,
    x="Outlet",
    y=["Sales", "Profit"],
    barmode="group",
    title="Outlet-wise Sales & Profit",
    labels={"value": "Amount (AED)", "variable": "Metric"},
)
st.plotly_chart(sales_profit_chart, use_container_width=True)

# GP% Scatter
filtered_df["GP%"] = (filtered_df["Profit"] / filtered_df["Sales"]) * 100
gp_chart = px.scatter(
    filtered_df,
    x="Outlet",
    y="GP%",
    size="Sales",
    color="Outlet",
    title="Gross Profit % by Outlet",
    hover_data=["Category", "Sales", "Profit"],
)
st.plotly_chart(gp_chart, use_container_width=True)
