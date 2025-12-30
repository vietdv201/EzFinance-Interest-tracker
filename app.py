import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(
    page_title="EZ.Finance Interest Tracker",
    page_icon="🏦",
    layout="wide",
)

# Custom CSS for Dark Corporate Theme
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    .brand-title {
        font-size: 3rem !important;
        font-weight: 800;
        color: #FF5722; 
        margin-bottom: 0;
        line-height: 1;
    }
    .brand-subtitle {
        font-size: 1rem;
        color: #aaaaaa;
        margin-top: 5px;
    }
    .nav-links {
        text-align: right;
        padding-top: 1.5rem;
    }
    .nav-links a {
        color: #FF5722;
        text-decoration: none;
        font-weight: 600;
        margin-left: 20px;
        font-size: 1.1rem;
        border: 1px solid #FF5722;
        padding: 8px 16px;
        border-radius: 5px;
        transition: all 0.3s;
    }
    .nav-links a:hover {
        background-color: #FF5722;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. HEADER SECTION ---
col_head_1, col_head_2 = st.columns([2, 3])

with col_head_1:
    st.markdown('<div class="brand-title">EZ.Finance</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Vietnam Bank Interest Tracker</div>', unsafe_allow_html=True)

with col_head_2:
    st.markdown("""
    <div class="nav-links">
        <a href="#">News</a>
        <a href="#">Contact</a>
        <a href="#">Social Media</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 3. DATA LOADING (GOOGLE SHEETS) ---

@st.cache_data(ttl=600)
def load_data():
    """
    Loads bank data from Google Sheets.
    Falls back to mock data if connection fails.
    """
    try:
        # Create a connection object
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Read the worksheet "BankRates" (as requested)
        # Use first 7 columns: Bank, Group, Type, 1M, 3M, 6M, 12M
        df = conn.read(worksheet="BankRates", usecols=list(range(7)), ttl=600)
        
        # Validate required columns exist
        required_columns = ["Bank", "Group", "Type", "1M", "3M", "6M", "12M"]
        if not all(col in df.columns for col in required_columns):
            st.error("Google Sheet column mismatch. Falling back to mock data.")
            raise ValueError("Column mismatch")
            
        return df

    except Exception as e:
        # st.warning(f"Using Mock Data. (Error connecting to Google Sheets: {e})")
        # st.info("Tip: Setup .streamlit/secrets.toml with your Google Sheet URL.")
        
        # Fallback Mock Data (Matches structure: Bank, Group, Type, 1M, 3M, 6M, 12M)
        data = [
            {"Bank": "Vietcombank", "Group": "Big 4", "Type": "Online", "1M": 2.9, "3M": 3.2, "6M": 4.1, "12M": 5.0},
            {"Bank": "BIDV", "Group": "Big 4", "Type": "Online", "1M": 3.0, "3M": 3.3, "6M": 4.2, "12M": 5.1},
            {"Bank": "Agribank", "Group": "Big 4", "Type": "Counter", "1M": 2.8, "3M": 3.0, "6M": 4.0, "12M": 5.0},
            {"Bank": "Techcombank", "Group": "Private Bank", "Type": "Online", "1M": 3.5, "3M": 3.8, "6M": 4.8, "12M": 5.5},
            {"Bank": "VPBank", "Group": "Private Bank", "Type": "Online", "1M": 3.6, "3M": 4.0, "6M": 5.2, "12M": 5.6},
            {"Bank": "MB Bank", "Group": "Private Bank", "Type": "Online", "1M": 3.4, "3M": 3.8, "6M": 4.7, "12M": 5.4},
        ]
        return pd.DataFrame(data)

@st.cache_data
def load_fintech_data():
    """
    Mock Data for Fintech/Bonds (Static for now)
    """
    data = [
        {"Product/App": "Vikky", "Type": "Fintech Saving", "Interest Rate (%/year)": 5.5, "Min Term": "Flexible"},
        {"Product/App": "Tikop", "Type": "Fintech Saving", "Interest Rate (%/year)": 6.8, "Min Term": "Flexible"},
        {"Product/App": "Finhay", "Type": "Fintech Saving", "Interest Rate (%/year)": 7.0, "Min Term": "3 Months"},
        {"Product/App": "Vingroup Bond", "Type": "Corp Bond", "Interest Rate (%/year)": 10.0, "Min Term": "24 Months"},
    ]
    return pd.DataFrame(data)

# --- 4. MAIN CONTENT (TABS) ---
tab1, tab2 = st.tabs(["Lãi suất Tiền gửi (Savings)", "Trái phiếu & Fintech (Bonds/Apps)"])

df_banks = load_data()
df_fintech = load_fintech_data()

with tab1:
    st.subheader("🏦 Bảng Lãi Suất Ngân Hàng")
    
    # Check if we are using fallback or real data
    # (Optional logic, just displaying data directly)
    
    rate_cols = ["1M", "3M", "6M", "12M"]
    
    # Ensure numeric types
    for col in rate_cols:
        if col in df_banks.columns:
            df_banks[col] = pd.to_numeric(df_banks[col], errors='coerce')

    # Apply styling: Highlight max in rate columns
    styled_df = df_banks.style.highlight_max(subset=rate_cols, color='#FF5722', axis=0) \
                              .format("{:.2f}%", subset=rate_cols)
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("📈 Trái Phiếu & Fintech")
    st.dataframe(
        df_fintech.style.format("{:.2f}%", subset=["Interest Rate (%/year)"]),
        use_container_width=True, 
        hide_index=True
    )

# --- 5. VISUALIZATION (MARKET AVERAGE) ---
st.markdown("---")
st.subheader("📊 Thống kê Lãi suất Trung bình (Market Average)")

if not df_banks.empty:
    # Group by 'Group' and calculate mean
    avg_df = df_banks.groupby("Group")[rate_cols].mean().reset_index()

    # Melt for Plotly
    melted_df = avg_df.melt(id_vars="Group", var_name="Term", value_name="Average Rate")

    # Filter for Chart (Map 1M, 3M... to nicer labels if needed, or keep as is)
    # Keeping is simpler for now as they are "1M", "3M"...
    
    fig = px.bar(
        melted_df,
        x="Term",
        y="Average Rate",
        color="Group",
        barmode="group",
        text_auto='.2f',
        color_discrete_map={
            "Big 4": "#2E86C1",      
            "Private Bank": "#FF5722" 
        },
        title="Comparison: Big 4 vs Private Banks Average Rates"
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        yaxis=dict(showgrid=True, gridcolor="#333"),
        xaxis=dict(showgrid=False)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("No bank data available to plot.")

# Footer
st.markdown("""
<div style='text-align: center; color: #666; padding-top: 50px;'>
    © 2025 Ez.Finance. Data updated daily.
</div>
""", unsafe_allow_html=True)
