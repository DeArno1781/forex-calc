import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# ตั้งค่าหน้าเว็บให้ดูทันสมัย
st.set_page_config(page_title="Forex Risk Calculator", page_icon="📈", layout="centered")

# ตกแต่ง CSS เล็กน้อยให้เหมาะกับมือถือ/iPad
st.markdown("""
    <style>
    .main { opacity: 0.95; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_index=True)

st.title("📈 Forex & Gold Calculator")
st.caption("คำนวณ Lot Size แม่นยำด้วยราคา Real-time จาก Yahoo Finance")

# --- ส่วนจัดการ Session State สำหรับเก็บประวัติ ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- ส่วนรับข้อมูลจากผู้ใช้ ---
with st.container():
    st.subheader("⚙️ ตั้งค่าการเทรด")
    col_a, col_b = st.columns(2)
    with col_a:
        balance = st.number_input("เงินทุนในพอร์ต ($)", min_value=1.0, value=1000.0, step=100.0)
        risk_percent = st.slider("ความเสี่ยงที่ยอมรับได้ (%)", 0.1, 10.0, 1.0, help="จำนวน % ของพอร์ตที่จะเสียถ้าโดน SL")
    with col_b:
        pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", "XAUUSD=X"]
        selected_pair = st.selectbox("เลือกคู่เงิน / ทองคำ", pairs)
        stop_loss_pips = st.number_input("ระยะ Stop Loss (Pips)", min_value=1.0, value=30.0, step=5.0)

# --- ส่วนการคำนวณ ---
if st.button("🚀 คำนวณ Lot Size"):
    with st.spinner('กำลังดึงราคาตลาดปัจจุบัน...'):
        try:
            ticker = yf.Ticker(selected_pair)
            data = ticker.history(period="1d")
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                pair_clean = selected_pair.replace("=X", "")
                
                # Logic คำนวณ Pip Value
                if "JPY" in pair_clean:
                    pip_value_std = (0.01 / current_price) * 100000
                elif "XAU" in pair_clean:
                    pip_value_std = 10.0  # สำหรับทอง 1 Lot ขยับ 0.1 (1 pip) = $10
                else:
                    # ถ้า USD อยู่หน้า เช่น USDCAD
                    if pair_clean.startswith("USD"):
                        pip_value_std = (0.0001 / current_price) * 100000
                    else: # ถ้า USD อยู่หลัง เช่น EURUSD
                        pip_value_std = 10.0

                # คำนวณผลลัพธ์สุดท้าย
                risk_amount = balance * (risk_percent / 100)
                lot_size = risk_amount / (stop_loss_pips * pip_value_std)

                # แสดงผลลัพธ์
                st.success(f"### แนะนำให้เปิด: **{lot_size:.2f} Lot**")
                
                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("ราคาปัจจุบัน", round(current_price, 3))
                res_col2.metric("เงินที่เสี่ยง (Risk)", f"${risk_amount:.2f}")
                res_col3.metric("Pip Value", f"${pip_value_std:.2f}")

                # บันทึกลงประวัติ
                new_entry = {
                    "เวลา": datetime.now().strftime("%H:%M:%S"),
                    "คู่เงิน": pair_clean,
                    "ราคา": round(current_price, 4),
                    "Risk($)": round(risk_amount, 2),
                    "SL(Pips)": stop_loss_pips,
                    "Lot": round(lot_size, 2)
                }
                st.session_state.history.insert(0, new_entry) # เอาอันล่าสุดไว้บน

            else:
                st.error("ไม่สามารถดึงข้อมูลได้ กรุณาเช็คการเชื่อมต่ออินเทอร์เน็ต")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

# --- ส่วนแสดงประวัติการคำนวณ ---
if st.session_state.history:
    st.divider()
    st.subheader("📜 ประวัติการคำนวณ (Session นี้)")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download History (CSV)", data=csv, file_name="trade_log.csv")
