import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Forex Risk Calculator", page_icon="📈", layout="centered")

# Custom CSS for UI
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
        risk_percent = st.slider("Risk Percentage (%)", 0.1, 10.0, 1.0)
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
                
                # Pip Value Logic
                if "JPY" in pair_clean:
                    pip_value_std = (0.01 / current_price) * 100000
                elif "XAU" in pair_clean:
                    pip_value_std = 10.0  
                else:
                    if pair_clean.startswith("USD"):
                        pip_value_std = (0.0001 / current_price) * 100000
                    else:
                        pip_value_std = 10.0

                risk_amount = balance * (risk_percent / 100)
                lot_size = risk_amount / (stop_loss_pips * pip_value_std)

                st.divider()
                st.success(f"### Recommended Lot Size: **{lot_size:.2f}**")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("Price", round(current_price, 4))
                res_col2.metric("Risk ($)", f"${risk_amount:.2f}")
                res_col3.metric("Pip Value", f"${pip_value_std:.2f}")

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
                st.error("Price data unavailable.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- History Section with Delete Button ---
if st.session_state.history:
    st.divider()
    st.subheader("📜 Calculation History")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
    
    col_dl, col_clr = st.columns(2)
    with col_dl:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download CSV", data=csv, file_name="trade_log.csv")
    with col_clr:
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun() # Refresh the app to show empty history
