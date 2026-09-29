import streamlit as st
import pandas as pd

# Konfigurasi Halaman Wide & Tanpa Sidebar
st.set_page_config(
    page_title="Footwear Material Yield & Costing AI",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS agar tampilan ringkas & rapat
st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    div[data-testid="stVerticalBlock"] > div {gap: 0.3rem;}
    </style>
""", unsafe_allow_html=True)

st.title("👟 Footwear Material Yield & Costing AI")
st.caption("Input cepat komponen material, kalkulasi yield, dan estimasi biaya per pasang sepatu.")

# Initialize Data awal
if "material_list" not in st.session_state:
    st.session_state.material_list = [
        {
            "Komponen": "Upper Leather / Synthetic", 
            "Panjang (cm)": 100.0, 
            "Lebar (cm)": 140.0, 
            "Net Area (cm²)": 220.0, 
            "Waste (%)": 5.0,
            "Harga / Sheet (Rp)": 150000.0
        }
    ]

# Header Kolom (Ditambahkan Kolom Harga & Cost/Pair)
h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([2, 1, 1, 1.2, 0.9, 1.8, 1, 1, 1.2])
h1.markdown("**Komponen Material**")
h2.markdown("**P (cm)**")
h3.markdown("**L (cm)**")
h4.markdown("**Net Area (cm²)**")
h5.markdown("**Waste (%)**")
h6.markdown("**Upload Pattern**")
h7.markdown("**Harga / Sheet (Rp)**")
h8.markdown("**Pairs/Sheet**")
h9.markdown("**Cost / Pair (Rp)**")

st.markdown("---")

updated_list = []
total_cost_per_pair = 0.0

# Render Baris Material
for i, row in enumerate(st.session_state.material_list):
    c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([2, 1, 1, 1.2, 0.9, 1.8, 1, 1, 1.2])
    
    # Input Langsung dalam Baris
    name = c1.text_input(f"name_{i}", value=row["Komponen"], placeholder="Nama Komponen...", label_visibility="collapsed", key=f"name_{i}")
    length = c2.number_input(f"len_{i}", value=float(row["Panjang (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"len_{i}")
    width = c3.number_input(f"wid_{i}", value=float(row["Lebar (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"wid_{i}")
    
    # Upload Pattern Slot
    uploaded_file = c6.file_uploader(f"file_{i}", type=["png", "jpg", "jpeg", "dxf"], label_visibility="collapsed", key=f"file_{i}")
    
    net_area_val = float(row["Net Area (cm²)"])
    if uploaded_file is not None:
        simulated_ai_area = 210.50
        net_area_val = simulated_ai_area
        c6.caption("✅ Net Area: 210.5 cm²")

    net_area = c4.number_input(f"net_{i}", value=net_area_val, min_value=0.0, label_visibility="collapsed", key=f"net_{i}")
    waste = c5.number_input(f"wst_{i}", value=float(row["Waste (%)"]), min_value=0.0, label_visibility="collapsed", key=f"wst_{i}")
    
    # Input Harga Material per Lembar / Roll
    price = c7.number_input(f"price_{i}", value=float(row.get("Harga / Sheet (Rp)", 0.0)), min_value=0.0, step=1000.0, label_visibility="collapsed", key=f"price_{i}")

    # --- KALKULASI YIELD & COSTING ---
    sheet_area = length * width
    gross_area = net_area * (1 + (waste / 100))
    
    pairs = int(sheet_area / gross_area) if gross_area > 0 else 0
    yield_pct = (net_area / gross_area * 100) if gross_area > 0 else 0.0
    
    # Hitung Biaya Material per Pasang (Cost per Pair)
    # Cara 1: Menggunakan Harga Lembaran dibagi Hasil Pasang (Pairs per Sheet)
    cost_per_pair = (price / pairs) if pairs > 0 else 0.0
    total_cost_per_pair += cost_per_pair

    # Display Hasil Langsung di Baris
    c8.markdown(f"**{pairs}** pairs\n\n*({yield_pct:.1f}% yield)*")
    c9.markdown(f"**Rp {cost_per_pair:,.0f}**" if cost_per_pair > 0 else "-")
    
    # Simpan state terbaru
    updated_list.append({
        "Komponen": name,
        "Panjang (cm)": length,
        "Lebar (cm)": width,
        "Net Area (cm²)": net_area,
        "Waste (%)": waste,
        "Harga / Sheet (Rp)": price
    })

# Simpan Perubahan
st.session_state.material_list = updated_list

# Tombol Tambah Baris
st.markdown("")
if st.button("➕ Tambah Baris Material Baru"):
    st.session_state.material_list.append({
        "Komponen": "",
        "Panjang (cm)": 0.0,
        "Lebar (cm)": 0.0,
        "Net Area (cm²)": 0.0,
        "Waste (%)": 0.0,
        "Harga / Sheet (Rp)": 0.0
    })
    st.rerun()

# --- REKAP BIAYA TOTAL SEPATU ---
st.markdown("---")
if total_cost_per_pair > 0:
    st.subheader(f"💵 Total Material Cost per Pair: Rp {total_cost_per_pair:,.0f}")
