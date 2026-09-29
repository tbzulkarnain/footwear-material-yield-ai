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

# Custom CSS untuk menyembunyikan sidebar dan memperrapat tampilan
st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    div[data-testid="stVerticalBlock"] > div {gap: 0.3rem;}
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI OPENCV MULTI-CONTOUR DETECTION ---
def process_multi_pattern_image(uploaded_file, dpi=96, min_area_px=500):
    """
    Membaca 1 gambar berisi BANYAK POLA, melacak semua kontur tertutup,
    dan mengembalikan list dari luas area (cm²) untuk tiap komponen yang terdeteksi.
    """
    try:
        # Read file into OpenCV
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
        
        if img is None:
            st.error("Format file tidak dapat dibaca oleh OpenCV.")
            return []

        # Convert to Grayscale
        if len(img.shape) == 3 and img.shape[2] == 4: # RGBA
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        elif len(img.shape) == 3: # RGB/BGR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Preprocessing: Blur & Thresholding
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Otsu's thresholding + Canny edge fallback
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological Closing untuk menyambungkan garis terputus
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Temukan Kontur
        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        pixels_per_cm = dpi / 2.54
        detected_components = []

        # Loop semua kontur dan hitung luas masing-masing
        for idx, cnt in enumerate(contours):
            area_px = cv2.contourArea(cnt)
            
            # Filter noise / bercak kecil
            if area_px >= min_area_px:
                area_cm2 = area_px / (pixels_per_cm ** 2)
                detected_components.append({
                    "Komponen": f"Pola Component #{len(detected_components)+1}",
                    "Panjang (cm)": 100.0,
                    "Lebar (cm)": 140.0,
                    "Net Area (cm²)": round(area_cm2, 2),
                    "Waste (%)": 5.0,
                    "Harga / Sheet (Rp)": 0.0
                })

        return detected_components
    except Exception as e:
        st.error(f"Error Pemrosesan OpenCV: {e}")
        return []

# --- FUNGSI OPENCV SINGLE-CONTOUR (UNTUK BARIS INDIVIDUAL) ---
def process_single_pattern_image(uploaded_file, dpi=96):
    try:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
        
        if img is None:
            return 0.0

        if len(img.shape) == 3 and img.shape[2] == 4:
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        elif len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return 0.0

        largest_contour = max(contours, key=cv2.contourArea)
        area_px = cv2.contourArea(largest_contour)
        pixels_per_cm = dpi / 2.54
        return round(area_px / (pixels_per_cm ** 2), 2)
    except Exception:
        return 0.0


# --- UI APLIKASI STREAMLIT ---
st.title("👟 Footwear Material Yield & Costing AI")
st.caption("Auto-Breakdown Multi-Component Pattern Menggunakan OpenCV & AI Vision")

# Initialize State Data
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

# --- AREA UPLOAD MASTER PATTERN (MULTI DETEKSI) ---
with st.expander("🧩 **Upload Gambar Master Pattern (Otomatis Deteksi & Pecah Banyak Komponen)**", expanded=True):
    master_file = st.file_uploader("Upload 1 lembar gambar berisi kumpulan semua pola komponen sepatu:", type=["png", "jpg", "jpeg"], key="master_pattern_uploader")
    
    if master_file is not None:
        if st.button("🚀 Process & Generate Komponen Otomatis"):
            new_components = process_multi_pattern_image(master_file)
            if new_components:
                st.session_state.material_list = new_components
                st.success(f"Berhasil mendeteksi {len(new_components)} komponen dari gambar master!")
                st.rerun()
            else:
                st.warning("Tidak ada kontur pola yang terdeteksi. Coba upload gambar dengan garis pola yang lebih jelas/kontras.")

st.markdown("---")

# Header Kolom Tabel
h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([2, 1, 1, 1.2, 0.9, 2, 1.1, 1, 1.2])
h1.markdown("**Komponen Material**")
h2.markdown("**P (cm)**")
h3.markdown("**L (cm)**")
h4.markdown("**Net Area (cm²)**")
h5.markdown("**Waste (%)**")
h6.markdown("**Upload Single Pattern**")
h7.markdown("**Harga / Sheet (Rp)**")
h8.markdown("**Pairs/Sheet**")
h9.markdown("**Cost / Pair (Rp)**")

st.markdown("---")

updated_list = []
total_cost_per_pair = 0.0

# Render Baris Material
for i, row in enumerate(st.session_state.material_list):
    c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([2, 1, 1, 1.2, 0.9, 2, 1.1, 1, 1.2])
    
    name = c1.text_input(f"name_{i}", value=row["Komponen"], placeholder="Nama Komponen...", label_visibility="collapsed", key=f"name_{i}")
    length = c2.number_input(f"len_{i}", value=float(row["Panjang (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"len_{i}")
    width = c3.number_input(f"wid_{i}", value=float(row["Lebar (cm)"]), min_value=0.0, label_visibility="collapsed", key=f"wid_{i}")
    
    # Upload Per Baris
    uploaded_file = c6.file_uploader(f"file_{i}", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key=f"file_{i}")
    
    net_area_val = float(row["Net Area (cm²)"])
    if uploaded_file is not None:
        detected_area = process_single_pattern_image(uploaded_file)
        if detected_area > 0:
            net_area_val = detected_area
            c6.caption(f"✅ Area: **{detected_area} cm²**")

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

st.session_state.material_list = updated_list

# Tombol Tambah Baris Manual
st.markdown("")
if st.button("➕ Tambah Baris Manual"):
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
