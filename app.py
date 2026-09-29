import streamlit as st
import pandas as pd
import cv2
import numpy as np
from PIL import Image
import io

# Konfigurasi Halaman Wide & Tanpa Sidebar
st.set_page_config(
    page_title="Footwear Material Yield & Costing AI",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS agar tampilan ringkas
st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    div[data-testid="stVerticalBlock"] > div {gap: 0.3rem;}
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI OPENCV UNTUK EKSTRAKSI NET AREA ---
def process_pattern_image(uploaded_file, dpi=96):
    """
    Membaca gambar pola, melacak kontur terluar, dan menghitung luas area dalam cm².
    dpi: Dots Per Inch gambar (Default 96 DPI untuk gambar web standard, 300 DPI untuk scan/CAD)
    """
    try:
        # 1. Convert uploaded file ke OpenCV Format
        image_bytes = uploaded_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        img_np = np.array(image)
        
        # Konversi ke Grayscale
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # 2. Thresholding / Binarization (Memisahkan garis pola dari background)
        # Gunakan Otsu's Thresholding untuk menangkap kontur secara otomatis
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 3. Temukan Kontur (Outlines Pola)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return 0.0

        # Ambil kontur terbesar (diasumsikan sebagai komponen pola utama)
        largest_contour = max(contours, key=cv2.contourArea)
        area_in_pixels = cv2.contourArea(largest_contour)

        # 4. Konversi Piksel ke cm²
        # 1 inch = 2.54 cm -> 1 cm = dpi / 2.54 pixels
        pixels_per_cm = dpi / 2.54
        area_in_cm2 = area_in_pixels / (pixels_per_cm ** 2)

        return round(area_in_cm2, 2)
    except Exception as e:
        st.error(f"Gagal memproses gambar: {e}")
        return 0.0


# --- UI APLIKASI STREAMLIT ---
st.title("👟 Footwear Material Yield & Costing AI")
st.caption("Deteksi Net Area Otomatis Menggunakan OpenCV & Kalkulasi Biaya Material.")

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

# Header Kolom
h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([2, 1, 1, 1.2, 0.9, 2, 1.1, 1, 1.2])
h1.markdown("**Komponen Material**")
h2.markdown("**P (cm)**")
h3.markdown("**L (cm)**")
h4.markdown("**Net Area (cm²)**")
h5.markdown("**Waste (%)**")
h6.markdown("**Upload Pattern (OpenCV)**")
h7.markdown("**Harga / Sheet (Rp)**")
h8.markdown("**Pairs/Sheet**")
h9.markdown("**Cost / Pair (Rp)**")

st.markdown("---")

updated_list = []
total_cost_per_pair = 0.0

# Render Baris Material
for i, row in enumerate(st.session_state.material_list):
    c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([2, 1, 1, 1.2, 0.9, 2, 1.1, 1, 1.2])
    
    # Input Langsung dalam Baris
    name = c1.text_input(f"name_{i}", value=row["Komponen"], placeholder="Nama Komponen...", label_visibility="collapsed", key=f"name_{i}")
    length = c2.number_input(f"len_{i}", value=float(row["Panjang (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"len_{i}")
    width = c3.number_input(f"wid_{i}", value=float(row["Lebar (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"wid_{i}")
    
    # Upload Pattern Slot + OpenCV Processing
    uploaded_file = c6.file_uploader(f"file_{i}", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key=f"file_{i}")
    
    net_area_val = float(row["Net Area (cm²)"])
    
    if uploaded_file is not None:
        # Ekstraksi Net Area menggunakan OpenCV
        detected_area = process_pattern_image(uploaded_file, dpi=96)
        if detected_area > 0:
            net_area_val = detected_area
            c6.caption(f"✅ OpenCV Area: **{detected_area} cm²**")

    net_area = c4.number_input(f"net_{i}", value=net_area_val, min_value=0.0, label_visibility="collapsed", key=f"net_{i}")
    waste = c5.number_input(f"wst_{i}", value=float(row["Waste (%)"]), min_value=0.0, label_visibility="collapsed", key=f"wst_{i}")
    price = c7.number_input(f"price_{i}", value=float(row.get("Harga / Sheet (Rp)", 0.0)), min_value=0.0, step=1000.0, label_visibility="collapsed", key=f"price_{i}")

    # Kalkulasi Yield & Costing
    sheet_area = length * width
    gross_area = net_area * (1 + (waste / 100))
    
    pairs = int(sheet_area / gross_area) if gross_area > 0 else 0
    yield_pct = (net_area / gross_area * 100) if gross_area > 0 else 0.0
    cost_per_pair = (price / pairs) if pairs > 0 else 0.0
    total_cost_per_pair += cost_per_pair

    # Display Hasil
    c8.markdown(f"**{pairs}** pairs\n\n*({yield_pct:.1f}% yield)*")
    c9.markdown(f"**Rp {cost_per_pair:,.0f}**" if cost_per_pair > 0 else "-")
    
    updated_list.append({
        "Komponen": name,
        "Panjang (cm)": length,
        "Lebar (cm)": width,
        "Net Area (cm²)": net_area,
        "Waste (%)": waste,
        "Harga / Sheet (Rp)": price
    })

# Simpan Perubahan State
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

# Rekap Total Cost
st.markdown("---")
if total_cost_per_pair > 0:
    st.subheader(f"💵 Total Material Cost per Pair: Rp {total_cost_per_pair:,.0f}")
