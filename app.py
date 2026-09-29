import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from PIL import Image
from google import genai

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="tbzulkarnain | Footwear Material Yield AI",
    page_icon="✂️",
    layout="wide"
)

# Custom CSS for Industrial Engineering styling
st.markdown("""
<style>
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .footer-text {
        text-align: center;
        color: #64748B;
        font-size: 13px;
        padding: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# API Key Initialization (Gemini)
API_KEY = st.sidebar.text_input("🔑 Gemini API Key", type="password", help="Masukkan Google Gemini API Key Anda untuk mengaktifkan AI Pattern & Interlock Analyzer.")

# ==========================================
# 2. TITLE & HEADER
# ==========================================
st.title("✂️ Footwear Material Yield & Cutting Interlock AI")
st.caption("Developed by **tbzulkarnain** | Industrial Engineering & Material Optimization Tool")
st.markdown("---")

# Sidebar - Material & Production Input
st.sidebar.header("📋 Production Parameters")
material_type = st.sidebar.selectbox("Material Type", ["Synthetic Leather Roll", "Textile / Mesh Roll", "Genuine Leather Hide"])
roll_width = st.sidebar.number_input("Roll Width (Inches)", value=54.0, step=1.0)
price_per_unit = st.sidebar.number_input("Material Price ($ / Meter)", value=4.50, step=0.10)
order_qty = st.sidebar.number_input("Order Quantity (Pairs)", value=10000, step=1000)

# ==========================================
# 3. TABS LAYOUT
# ==========================================
tab1, tab2 = st.tabs(["📊 Yield & Cost Calculator", "🔍 AI Pattern & Interlock Analyzer"])

# ------------------------------------------
# TAB 1: YIELD & COST CALCULATOR
# ------------------------------------------
with tab1:
    st.subheader("Calculator & What-If Scenario Analysis")
    
    col_in1, col_in2 = st.columns(2)
    
    with col_in1:
        st.markdown("#### Baseline Scenario")
        net_area_base = st.number_input("Net Pattern Area per Pair (m²)", value=0.145, format="%.4f", key="net_base")
        efficiency_base = st.slider("Current Nesting Efficiency (%)", 50.0, 95.0, 72.0, key="eff_base")
        scrap_allowance = st.number_input("Cutting Scrap Allowance (%)", value=3.0, step=0.5, key="scrap_base")
        
    with col_in2:
        st.markdown("#### Optimized Scenario (Target)")
        net_area_opt = st.number_input("Net Pattern Area per Pair (m²)", value=net_area_base, format="%.4f", key="net_opt")
        efficiency_opt = st.slider("Target Nesting Efficiency (%)", 50.0, 95.0, 78.0, key="eff_opt")

    # Formulas
    gross_cons_base = net_area_base / (efficiency_base / 100.0)
    cost_pair_base = gross_cons_base * price_per_unit
    total_mat_base = gross_cons_base * order_qty * (1 + (scrap_allowance / 100.0))
    total_cost_base = total_mat_base * price_per_unit
    
    gross_cons_opt = net_area_opt / (efficiency_opt / 100.0)
    cost_pair_opt = gross_cons_opt * price_per_unit
    total_mat_opt = gross_cons_opt * order_qty * (1 + (scrap_allowance / 100.0))
    total_cost_opt = total_mat_opt * price_per_unit
    
    cost_saving = total_cost_base - total_cost_opt
    material_saved = total_mat_base - total_mat_opt

    st.markdown("---")
    st.subheader("💡 Financial & Material Impact")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross Cons. (Base)", f"{gross_cons_base:.4f} m²/pair")
    m2.metric("Gross Cons. (Opt)", f"{gross_cons_opt:.4f} m²/pair", delta=f"{(gross_cons_opt - gross_cons_base):.4f}")
    m3.metric("Material Cost / Pair", f"${cost_pair_opt:.2f}", delta=f"-${(cost_pair_base - cost_pair_opt):.2f}")
    m4.metric("Total Project Savings", f"${cost_saving:,.2f}", delta_color="normal")

    # Donut Chart - Material Usage Breakdown
    st.markdown("---")
    st.markdown("#### Material Waste Breakdown (Baseline)")
    used_area = net_area_base
    wasted_area = gross_cons_base - net_area_base
    
    fig = go.Figure(data=[go.Pie(
        labels=['Net Pattern Area (Utilized)', 'Scrap / Interlock Gap (Waste)'],
        values=[used_area, wasted_area],
        hole=.5,
        marker_colors=['#0284C7', '#EF4444']
    )])
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# TAB 2: AI PATTERN & INTERLOCK ANALYZER
# ------------------------------------------
with tab2:
    st.subheader("AI-Powered Pattern & Nesting Interlock Optimization")
    st.caption("Upload foto/gambar susunan pola cutting (interlock layout) untuk dianalisis oleh Gemini AI.")
    
    uploaded_file = st.file_uploader("Upload Cutting Pattern Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Pattern Layout", use_container_width=True)
        
        analyze_btn = st.button("🚀 Analyze Pattern & Interlock Efficiency")
        
        if analyze_btn:
            if not API_KEY:
                st.error("⚠️ Masukkan Gemini API Key di sidebar terlebih dahulu!")
            else:
                with st.spinner("AI sedang menganalisis kontur pola & celah interlock..."):
                    try:
                        client = genai.Client(api_key=API_KEY)
                        
                        prompt = """
                        Kamu adalah pakar Pattern CAD, Cutting Yield, dan Industrial Engineering di manufaktur sepatu.
                        Analisis gambar pola potongan upper sepatu (nesting layout) ini.
                        Berikan output HANYA berupa JSON valid dengan format persis seperti ini:
                        {
                            "pattern_count": 12,
                            "estimated_nesting_efficiency": 76.5,
                            "interlock_rating": "Good",
                            "waste_area_analysis": "Celah antar komponen vamp dan quarter masih terlalu lebar.",
                            "recommendation": "Putar posisi eyestay 180 derajat untuk mengisi selang-seling area lekukan."
                        }
                        Jangan tambahkan teks markdown pendahuluan atau penutup lain di luar JSON.
                        """
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[image, prompt]
                        )
                        
                        clean_json = response.text.replace("```json", "").replace("```", "").strip()
                        result = json.loads(clean_json)
                        
                        st.success("Analisis AI Selesai!")
                        
                        res_col1, res_col2 = st.columns(2)
                        with res_col1:
                            st.metric("Detected Pattern Count", f"{result.get('pattern_count', 'N/A')} pcs")
                            st.metric("Est. Nesting Efficiency", f"{result.get('estimated_nesting_efficiency', 'N/A')}%")
                            st.info(f"**Interlock Rating:** {result.get('interlock_rating', 'N/A')}")
                            
                        with res_col2:
                            st.markdown("#### 📌 Waste Analysis")
                            st.write(result.get("waste_area_analysis", "-"))
                            st.markdown("#### 💡 AI Recommendation for Improvement")
                            st.write(result.get("recommendation", "-"))
                            
                    except Exception as e:
                        st.error(f"Gagal memproses gambar dengan AI: {str(e)}")

# ==========================================
# 4. FOOTER WITH SUBTLE VISITOR COUNTER
# ==========================================
st.markdown("---")
visitor_counter_html = """
<div style="text-align: center; color: #6B7280; font-size: 13px; padding-top: 10px; padding-bottom: 10px;">
    Footwear Material Yield AI | Industrial Engineering Portfolio | 
    <span style="display: inline-block; vertical-align: middle; margin-left: 5px;">
        <img src="https://hitwebcounter.com/counter/counter.php?page=18249015&style=0007&nbdigits=4&type=page&initCount=1" title="Counter Widget" Alt="Visit Counter" border="0" />
    </span>
</div>
"""
st.components.v1.html(visitor_counter_html, height=50)
