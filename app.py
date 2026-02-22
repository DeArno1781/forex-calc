import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Forex Risk Calculator", page_icon="📈", layout="centered")

# Custom CSS for a better UI on Mobile/iPad
st.markdown("""
    <style>
    .main { opacity: 0.95; }
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        height: 3em; 
        background-color: #007bff; 
        color: white; 
        font-weight: bold;
    }
    stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Forex & Gold Calculator")
st.caption("Calculate precise Lot Sizes using real-time market data.")

# Session State for History Tracking
if 'history' not in st.session_state:
    st.session_state.history = []

# --- User Input Section ---
with st.container():
    st.subheader("⚙️ Trading Settings")
    col_a, col_b = st.columns(2)
    with col_a:
        balance = st.number_input("Account Balance ($)", min_value=1.0, value=1000.0, step=100.0)
        risk_percent = st.slider("Risk Percentage (%)", 0.1, 10.0, 1.0, help="Percentage of account to risk per trade.")
    with col_b:
        pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", "XAUUSD=X"]
        selected_pair = st.selectbox("Select Asset", pairs)
        stop_loss_pips = st.number_input("Stop Loss Distance (Pips)", min_value=1.0, value=30.0, step=5.0)

# --- Calculation Logic ---
if st.button("🚀 Calculate Lot Size"):
    with st.spinner('Fetching latest market price...'):
        try:
            ticker = yf.Ticker(selected_pair)
            data = ticker.history(period="1d")
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                pair_clean = selected_pair.replace("=X", "")
                
                # Pip Value Calculation Logic
                if "JPY" in pair_clean:
                    # For JPY pairs, 1 pip is 0.01
                    pip_value_std = (0.01 / current_price) * 100000
                elif "XAU" in pair_clean:
                    # For Gold, 1 pip (0.10 price move) = $10 per Standard Lot
                    pip_value_std = 10.0  
                else:
                    # For non-JPY pairs, 1 pip is 0.0001
                    if pair_clean.startswith("USD"):
                        # Indirect quotes (USD/CAD, USD/CHF)
                        pip_value_std = (0.0001 / current_price) * 100000
                    else:
                        # Direct quotes (EUR/USD, GBP/USD)
                        pip_value_std = 10.0

                # Final Calculations
                risk_amount = balance * (risk_percent / 100)
                # Formula: Risk Amount / (SL Pips * Pip Value per 1 Lot)
                lot_size = risk_amount / (stop_loss_pips * pip_value_std)

                # Display Results
                st.divider()
                st.success(f"### Recommended Lot Size: **{lot_size:.2f}**")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("Current Price", round(current_price, 4))
                res_col2.metric("Risk Amount", f"${risk_amount:.2f}")
                res_col3.metric("Pip Value (1 Lot)", f"${pip_value_std:.2f}")

                # Save to History
                new_entry = {
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Asset": pair_clean,
                    "Price": round(current_price, 4),
                    "Risk($)": round(risk_amount, 2),
                    "SL(Pips)": stop_loss_pips,
                    "Lot Size": round(lot_size, 2)
                }
                st.session_state.history.insert(0, new_entry) 

            else:
                st.error("Could not fetch price data. Please check your internet connection.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- History Section ---
if st.session_state.history:
    st.divider()
    st.subheader("📜 Calculation History")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download History (CSV)", data=csv, file_name="trade_log.csv")
