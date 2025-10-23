import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ===============================
# CONFIGURATION
# ===============================
st.set_page_config(page_title="Item Sales Across Outlets", layout="wide")

OUTLET_FILES = {
    "Hilal": "Hilal.Xlsx",
    "Safa Super": "safa super.Xlsx",
    "Azhar HP": "Azhar HP.Xlsx",
    "Azhar GT": "Azhar GT.Xlsx",
    "Blue Pearl": "Blue Pearl.Xlsx",
    "Fida": "Fida HP.Xlsx",
    "Hadeqat": "Hadeqat.Xlsx",
    "Jais": "jais.Xlsx",
    "Sabah": "sabah.Xlsx",
    "Sahat": "sahat.Xlsx",
    "Shams salem": "Salem.Xlsx",
    "Shams Liwan": "liwan.Xlsx",
    "Superstore": "superstore.Xlsx",
    "Tay Tay": "Tay Tay.Xlsx",
    "Safa oudmehta": "oudmehta.Xlsx",
    "Port saeed": "port saeed.Xlsx"
}

# ===============================
# PASSWORD PROTECTION
# ===============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Sales & Profit Dashboard")
    password = st.text_input("Enter Password to Continue", type="password")
    if st.button("Login"):
        if password == "123123":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password. Try again.")
    st.stop()

# ===============================
# LOAD ALL OUTLET DATA
# ===============================
@st.cache_data
def load_all_outlet_data():
    all_data = []
    for outlet, file in OUTLET_FILES.items():
        if os.path.exists(file):
            df = pd.read_excel(file)
            df["Outlet"] = outlet
            all_data.append(df)
        else:
            st.warning(f"⚠️ File not found: {file}")
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

df = load_all_outlet_data()

# Data cleanup
df = df[df["Category"].notna()]
for col in ["Total Sales", "Total Profit"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
df["Margin %"] = (df["Total Profit"] / df["Total Sales"] * 100).fillna(0).round(2)

# ===============================
# SIDEBAR FILTERS
# ===============================
st.sidebar.header("🔍 Filters")

category_list = ["All"] + sorted(df["Category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", category_list)

outlet_list = ["All"] + sorted(df["Outlet"].dropna().unique().tolist())
selected_outlet = st.sidebar.selectbox("Select Outlet", outlet_list)

st.sidebar.divider()
search_name = st.sidebar.text_input("🔎 Search by Item Name", placeholder="Type item name...")
search_code = st.sidebar.text_input("📟 Search by Item Code", placeholder="Type item code...")

# ===============================
# FILTER LOGIC
# ===============================
# Main filtered dataset (category + outlet filters, for top products)
filtered_main = df.copy()
if selected_category != "All":
    filtered_main = filtered_main[filtered_main["Category"] == selected_category]
if selected_outlet != "All":
    filtered_main = filtered_main[filtered_main["Outlet"] == selected_outlet]

# Filtered dataset including search (for tables & outlet summary)
filtered_df = filtered_main.copy()
search_term = None
if search_name:
    filtered_df = filtered_df[filtered_df["Items"].str.contains(search_name, case=False, na=False)]
    search_term = search_name
elif search_code:
    filtered_df = filtered_df[filtered_df["Item Code"].astype(str).str.contains(search_code, case=False, na=False)]
    search_term = search_code

# ===============================
# PAGE TITLE
# ===============================
st.title("📦 Item Sales Across Outlets")

# ===============================
# KEY INSIGHTS
# ===============================
if not filtered_main.empty:
    total_sales = filtered_main["Total Sales"].sum()
    total_profit = filtered_main["Total Profit"].sum()
    gp_percent = (total_profit / total_sales * 100) if total_sales > 0 else 0

    st.markdown("### 📈 Key Insights")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Sales", f"{total_sales:,.2f}")
    c2.metric("📊 Total Profit (GP)", f"{total_profit:,.2f}")
    c3.metric("⚙️ GP%", f"{gp_percent:.2f}%")
    st.markdown("---")

# ===============================
# DISPLAY SEARCH RESULTS
# ===============================
if search_term and not filtered_df.empty:
    st.markdown(f"## 🧾 Results for: **{search_term}**")

    # ----------- FIRST TABLE: Item-wise Details -----------
    st.markdown("### 📋 Item Details per Outlet")
    item_details = filtered_df[["Items", "Item Code", "Category", "Outlet", "Total Sales", "Total Profit", "Margin %"]] \
        .sort_values(by="Total Sales", ascending=False) \
        .reset_index(drop=True)
    st.dataframe(item_details, use_container_width=True, height=400)

    # ----------- SECOND TABLE: Outlet Summary -----------
    st.markdown("### 🏪 Outlet-wise Total (for Searched Item)")
    outlet_summary = (
        filtered_df.groupby("Outlet")
        .agg({"Total Sales": "sum", "Total Profit": "sum"})
        .reset_index()
    )
    outlet_summary["Margin %"] = (outlet_summary["Total Profit"] / outlet_summary["Total Sales"] * 100).round(2)
    outlet_summary = outlet_summary.sort_values("Total Sales", ascending=False)
    st.dataframe(outlet_summary[["Outlet", "Total Sales", "Total Profit", "Margin %"]], use_container_width=True, height=350)

    # ----------- OUTLET-WISE BAR CHART -----------
    if selected_outlet == "All":
        fig_outlet = px.bar(
            outlet_summary,
            x="Outlet",
            y="Total Sales",
            color="Margin %",
            text="Total Sales",
            title=f"Outlet-wise Sales & GP for '{search_term}'"
        )
        fig_outlet.update_traces(texttemplate="%{text:.2s}", textposition="outside")
        fig_outlet.update_layout(xaxis_title="", yaxis_title="Sales (AED)", height=500)
        st.plotly_chart(fig_outlet, use_container_width=True)

# ===============================
# TOP 30 PRODUCTS BAR CHART
# ===============================
st.markdown("### 🏆 Top Selling Products")
top_products = (
    filtered_main.groupby("Items")
    .agg({"Total Sales": "sum", "Total Profit": "sum"})
    .sort_values("Total Sales", ascending=False)
    .head(30)
    .reset_index()
)

# Compute GP% for hover
top_products["GP%"] = (top_products["Total Profit"] / top_products["Total Sales"] * 100).round(2)

if not top_products.empty:
    fig_top = px.bar(
        top_products,
        x="Total Sales",
        y="Items",
        orientation="h",
        text="Total Sales",
        hover_data={"Total Sales": ":,.2f", "GP%": True},
        title=f"Top Selling Products ({selected_outlet})" if selected_outlet != "All" else "Top Selling Products (All Outlets)"
    )
    fig_top.update_traces(texttemplate="%{text:.2s}", textposition="outside", marker_color="teal")
    fig_top.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Sales", height=700)
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("No product data available for the selected filters.")
