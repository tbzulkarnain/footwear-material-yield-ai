import streamlit as st
import pandas as pd

# Konfigurasi Halaman Wide & Tanpa Sidebar
st.set_page_config(
    page_title="Footwear Material Yield AI",
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

st.title("👟 Footwear Material Yield AI")
st.caption("Input cepat komponen material dalam bentuk baris ringkas.")

# Initialize Data: Hanya Baris 1 yang terisi default, selebihnya kosong
if "material_list" not in st.session_state:
    st.session_state.material_list = [
        # Baris 1 (Default Terisi) - Lebar: 140 cm (~55 inci) atau 110 cm (~44 inci)
        {"Komponen": "Upper Leather / Synthetic", "Panjang (cm)": 100.0, "Lebar (cm)": 140.0, "Net Area (cm²)": 220.0, "Waste (%)": 5.0}
    ]

# Header Kolom
h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2.2, 1.2, 1.2, 1.5, 1, 2.2, 1.2, 1.2])
h1.markdown("**Komponen Material**")
h2.markdown("**P (cm)**")
h3.markdown("**L (cm)**")
h4.markdown("**Net Area (cm²)**")
h5.markdown("**Waste (%)**")
h6.markdown("**Upload Pattern (Opsional)**")
h7.markdown("**Pairs/Sheet**")
h8.markdown("**Yield (%)**")

st.markdown("---")

updated_list = []

# Render Baris Material
for i, row in enumerate(st.session_state.material_list):
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2.2, 1.2, 1.2, 1.5, 1, 2.2, 1.2, 1.2])
    
    # Input Langsung dalam Baris
    name = c1.text_input(f"name_{i}", value=row["Komponen"], placeholder="Nama Komponen...", label_visibility="collapsed", key=f"name_{i}")
    length = c2.number_input(f"len_{i}", value=float(row["Panjang (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"len_{i}")
    width = c3.number_input(f"wid_{i}", value=float(row["Lebar (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"wid_{i}")
    
    # Upload Pattern Slot Ringkas
    uploaded_file = c6.file_uploader(f"file_{i}", type=["png", "jpg", "jpeg", "dxf"], label_visibility="collapsed", key=f"file_{i}")
    
    net_area_val = float(row["Net Area (cm²)"])
    if uploaded_file is not None:
        # Simulasi AI extraction dari file
        simulated_ai_area = 210.50
        net_area_val = simulated_ai_area
        c6.caption("✅ AI Net Area: 210.5 cm²")

    net_area = c4.number_input(f"net_{i}", value=net_area_val, min_value=0.0, label_visibility="collapsed", key=f"net_{i}")
    waste = c5.number_input(f"wst_{i}", value=float(row["Waste (%)"]), min_value=0.0, label_visibility="collapsed", key=f"wst_{i}")

    # Kalkulasi Otomatis per Baris
    sheet_area = length * width
    gross_area = net_area * (1 + (waste / 100))
    
    pairs = int(sheet_area / gross_area) if gross_area > 0 else 0
    yield_pct = (net_area / gross_area * 100) if gross_area > 0 else 0.0

    # Display Hasil Langsung di Baris
    c7.markdown(f"**{pairs}** pairs" if pairs > 0 else "-")
    c8.markdown(f"**{yield_pct:.1f}%**" if yield_pct > 0 else "-")
    
    # Simpan state terbaru
    updated_list.append({
        "Komponen": name,
        "Panjang (cm)": length,
        "Lebar (cm)": width,
        "Net Area (cm²)": net_area,
        "Waste (%)": waste
    })

# Simpan Perubahan
st.session_state.material_list = updated_list

# Tombol Tambah Baris (Baris baru ditambahkan dalam keadaan KOSONG / 0)
st.markdown("")
if st.button("➕ Tambah Baris Material Baru"):
    st.session_state.material_list.append({
        "Komponen": "",
        "Panjang (cm)": 0.0,
        "Lebar (cm)": 0.0,
        "Net Area (cm²)": 0.0,
        "Waste (%)": 0.0
    })
    st.rerun()
