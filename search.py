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

# Cleanup
df = df[df["Category"].notna()]
for col in ["Total Sales", "Total Profit"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
df["Margin %"] = (df["Total Profit"] / df["Total Sales"] * 100).fillna(0).round(2)

# ===============================
# SIDEBAR FILTERS
# ===============================
st.sidebar.header("🔍 Filters")

# Category filter (single select)
categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", categories)

# Apply category filter
if selected_category != "All":
    df = df[df["Category"] == selected_category]

# ===============================
# PAGE TITLE
# ===============================
st.title("📦 Item Sales Across Outlets")

# ===============================
# SEARCH SECTION
# ===============================
st.markdown("### 🔎 Search Items")

search_name = st.text_input("Search by Item Name", placeholder="Type item name...")
search_code = st.text_input("Search by Item Code", placeholder="Type item code...")

filtered_df = df.copy()
search_term = None

if search_name:
    filtered_df = filtered_df[filtered_df["Items"].str.contains(search_name, case=False, na=False)]
    search_term = search_name
elif search_code:
    filtered_df = filtered_df[filtered_df["Item Code"].astype(str).str.contains(search_code, case=False, na=False)]
    search_term = search_code

# ===============================
# KEY INSIGHTS (Top Section)
# ===============================
if not filtered_df.empty:
    total_sales = filtered_df["Total Sales"].sum()
    total_profit = filtered_df["Total Profit"].sum()
    avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    top_outlet = filtered_df.groupby("Outlet")["Total Sales"].sum().idxmax()
    top_category = (
        selected_category if selected_category != "All"
        else df.groupby("Category")["Total Sales"].sum().idxmax()
    )

    st.markdown("### 📈 Key Insights")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Total Sales", f"{total_sales:,.2f}")
    c2.metric("📊 Total Profit (GP)", f"{total_profit:,.2f}")
    c3.metric("⚙️ Avg Margin %", f"{avg_margin:.2f}%")
    c4.metric("🏪 Top Outlet", top_outlet)
    c5.metric("🏷️ Top Category", top_category)

    st.markdown("---")

# ===============================
# DISPLAY RESULTS
# ===============================
if search_term and not filtered_df.empty:
    st.markdown(f"## 🧾 Results for: **{search_term}**")

    # -------- FIRST TABLE: Item Details per Outlet --------
    st.markdown("### 📋 Item Details per Outlet")
    item_details = filtered_df[["Items", "Item Code", "Outlet", "Total Sales", "Total Profit", "Margin %"]] \
        .sort_values(by="Total Sales", ascending=False) \
        .reset_index(drop=True)
    st.dataframe(item_details, use_container_width=True, height=400)

    # -------- SECOND TABLE: Outlet Summary --------
    st.markdown("### 🏪 Outlet-wise Total (for Searched Item)")
    outlet_summary = (
        filtered_df.groupby("Outlet")[["Total Sales", "Total Profit"]]
        .sum()
        .reset_index()
    )
    outlet_summary["Margin %"] = (outlet_summary["Total Profit"] / outlet_summary["Total Sales"] * 100).round(2)
    outlet_summary = outlet_summary.sort_values("Total Sales", ascending=False)

    total_sales = outlet_summary["Total Sales"].sum()
    total_profit = outlet_summary["Total Profit"].sum()
    avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Sales", f"{total_sales:,.2f}")
    c2.metric("📊 Total Profit (GP)", f"{total_profit:,.2f}")
    c3.metric("⚙️ Avg Margin %", f"{avg_margin:.2f}%")

    st.dataframe(outlet_summary, use_container_width=True, height=350)

    # -------- CHART --------
    fig = px.bar(
        outlet_summary,
        x="Outlet",
        y="Total Sales",
        color="Margin %",
        text="Total Sales",
        title=f"Outlet-wise Sales & GP for '{search_term}'",
        color_continuous_scale="Blues"
    )
    fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
    fig.update_layout(xaxis_title="", yaxis_title="Sales (AED)", height=500)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Search for an item name or code to view its sales and GP across outlets.")
