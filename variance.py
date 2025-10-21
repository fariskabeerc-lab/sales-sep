import streamlit as st
import pandas as pd
import os

# ===============================
# CONFIGURATION
# ===============================
st.set_page_config(page_title="Sales & Profit Dashboard", layout="wide")

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
# LOAD ALL DATA
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

# Remove items without category
df = df[df["Category"].notna()]

# Ensure numeric
for col in ["Total Sales", "Total Profit"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Compute margin %
df["Margin %"] = (df["Total Profit"] / df["Total Sales"] * 100).fillna(0).round(2)

# ===============================
# SIDEBAR FILTERS
# ===============================
st.sidebar.header("🔍 Filters")

# Category Filter
categories = ["All"] + sorted(df["Category"].unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", categories)

# Exclude Categories Filter (multi-select)
exclude_categories = st.sidebar.multiselect("Exclude Categories", options=df["Category"].unique())

# Outlet Filter
outlets = ["All"] + sorted(df["Outlet"].unique().tolist())
selected_outlet = st.sidebar.selectbox("Select Outlet", outlets)

# Margin Filter (non-overlapping)
margin_filters = ["All", "< 0", "0 - 5", "5 - 10", "10 - 20", "20 - 30", "30 +"]
selected_margin = st.sidebar.selectbox("Select Margin Range (%)", margin_filters)

# ===============================
# APPLY FILTERS
# ===============================
filtered_df = df.copy()

# Include Category
if selected_category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == selected_category]

# Exclude Categories
if exclude_categories:
    filtered_df = filtered_df[~filtered_df["Category"].isin(exclude_categories)]

# Outlet
if selected_outlet != "All":
    filtered_df = filtered_df[filtered_df["Outlet"] == selected_outlet]

# Margin (non-overlapping)
if selected_margin != "All":
    if selected_margin == "< 0":
        filtered_df = filtered_df[filtered_df["Margin %"] < 0]
    elif selected_margin == "0 - 5":
        filtered_df = filtered_df[(filtered_df["Margin %"] >= 0) & (filtered_df["Margin %"] < 5)]
    elif selected_margin == "5 - 10":
        filtered_df = filtered_df[(filtered_df["Margin %"] >= 5) & (filtered_df["Margin %"] < 10)]
    elif selected_margin == "10 - 20":
        filtered_df = filtered_df[(filtered_df["Margin %"] >= 10) & (filtered_df["Margin %"] < 20)]
    elif selected_margin == "20 - 30":
        filtered_df = filtered_df[(filtered_df["Margin %"] >= 20) & (filtered_df["Margin %"] < 30)]
    elif selected_margin == "30 +":
        filtered_df = filtered_df[filtered_df["Margin %"] >= 30]

# ===============================
# SEARCH BAR
# ===============================
st.title("📊 Sales & Profit Insights (Sep)")
# Search by Item Name
search_name = st.text_input("🔎 Search Item Name", placeholder="Type an item name...")

# Search by Item Code
search_code = st.text_input("🔎 Search Item Code", placeholder="Type an item code...")

# Apply search filters
if search_name:
    filtered_df = filtered_df[filtered_df["Items"].str.contains(search_name, case=False, na=False)]
if search_code:
    filtered_df = filtered_df[filtered_df["Item Code"].astype(str).str.contains(search_code, case=False, na=False)]

# ===============================
# KEY INSIGHTS
# ===============================
if not filtered_df.empty:
    total_sales = filtered_df["Total Sales"].sum()
    total_profit = filtered_df["Total Profit"].sum()
    avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

    st.subheader("📈 Key Insights")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Sales", f"{total_sales:,.2f}")
    c2.metric("📊 Total Profit", f"{total_profit:,.2f}")
    c3.metric("⚙️ Avg. Margin %", f"{avg_margin:.2f}%")
else:
    st.warning("No data found for the selected filters or search term.")

# ===============================
# ITEM-WISE DETAILS
# ===============================
st.subheader("📋 Item-wise Sales, Profit & Margin")

if not filtered_df.empty:
    st.dataframe(
        filtered_df[["Outlet", "Category","Item Code", "Items", "Total Sales", "Total Profit", "Margin %"]]
        .sort_values(by="Margin %", ascending=True)
        .reset_index(drop=True),
        use_container_width=True,
        height=450
    )

# ===============================
# OUTLET-WISE TOTALS
# ===============================
st.subheader("🏪 Outlet-wise Total Sales, Profit & Avg Margin")

if not filtered_df.empty:
    outlet_summary = (
        filtered_df.groupby("Outlet")
        .agg({"Total Sales": "sum", "Total Profit": "sum"})
        .reset_index()
    )
    # Correct avg margin using total profit/total sales
    outlet_summary["Avg Margin %"] = (outlet_summary["Total Profit"] / outlet_summary["Total Sales"] * 100).round(2)
    outlet_summary = outlet_summary.sort_values("Total Sales", ascending=False)

    st.dataframe(outlet_summary, use_container_width=True, height=350)
else:
    st.info("No outlet data to display.")
