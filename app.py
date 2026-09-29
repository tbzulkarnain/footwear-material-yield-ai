import streamlit as st
import pandas as pd
import cv2
import numpy as np
import uuid

# Konfigurasi Halaman Wide & Tanpa Sidebar
st.set_page_config(
    page_title="Footwear Material Yield & Costing AI",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk menyembunyikan sidebar dan merapatkan tampilan
st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    div[data-testid="stVerticalBlock"] > div {gap: 0.3rem;}
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI OPENCV MULTI-CONTOUR DETECTION ---
def process_multi_pattern_image(uploaded_file, dpi=96, min_area_px=300):
    try:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
        
        if img is None:
            st.error("Format file tidak dapat dibaca oleh OpenCV.")
            return []

        if len(img.shape) == 3 and img.shape[2] == 4:
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        elif len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        pixels_per_cm = dpi / 2.54
        detected_components = []
        
        img_h, img_w = gray.shape[:2]
        max_area_px = (img_h * img_w) * 0.9

        valid_contours = []
        for cnt in contours:
            area_px = cv2.contourArea(cnt)
            if min_area_px <= area_px <= max_area_px:
                valid_contours.append((cnt, area_px))

        if not valid_contours:
            return []

        # Ambil area terbesar sebagai acuan rasio
        max_component_px = max(valid_contours, key=lambda x: x[1])[1]

        for idx, (cnt, area_px) in enumerate(valid_contours):
            area_cm2 = area_px / (pixels_per_cm ** 2)
            ratio = area_px / max_component_px
            
            # Dynamic waste berdasarkan rasio ukuran relatif komponen
            if ratio > 0.6:
                default_waste = 7.0
            elif ratio > 0.25:
                default_waste = 5.0
            else:
                default_waste = 3.0

            detected_components.append({
                "id": str(uuid.uuid4()),  # Unique ID untuk hindari bug delete
                "Komponen": f"Pola Component #{len(detected_components)+1}",
                "Panjang (cm)": 100.0,
                "Lebar (cm)": 140.0,
                "Net Area (cm²)": round(area_cm2, 2),
                "Waste (%)": default_waste,
                "Harga / Sheet ($)": 0.0
            })

        return detected_components
    except Exception as e:
        st.error(f"Error Pemrosesan OpenCV: {e}")
        return []

# --- FUNGSI OPENCV SINGLE-CONTOUR ---
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
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return 0.0

        img_h, img_w = gray.shape[:2]
        max_area_px = (img_h * img_w) * 0.9

        valid_contours = [c for c in contours if cv2.contourArea(c) <= max_area_px]
        if not valid_contours:
            return 0.0

        largest_contour = max(valid_contours, key=cv2.contourArea)
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
            "id": str(uuid.uuid4()),
            "Komponen": "Upper Leather / Synthetic", 
            "Panjang (cm)": 100.0, 
            "Lebar (cm)": 140.0, 
            "Net Area (cm²)": 220.0, 
            "Waste (%)": 5.0,
            "Harga / Sheet ($)": 10.00
        }
    ]

# --- AREA UPLOAD MASTER PATTERN ---
with st.expander("🧩 **Upload Gambar Master Pattern (Otomatis Deteksi & Pecah Banyak Komponen)**", expanded=True):
    master_file = st.file_uploader("Upload 1 lembar gambar berisi kumpulan pola komponen terpisah:", type=["png", "jpg", "jpeg"], key="master_pattern_uploader")
    
    if master_file is not None:
        if st.button("🚀 Process & Generate Komponen Otomatis"):
            new_components = process_multi_pattern_image(master_file)
            if new_components:
                st.session_state.material_list = new_components
                st.success(f"Berhasil mendeteksi {len(new_components)} komponen dari gambar master!")
                st.rerun()
            else:
                st.warning("Tidak ada kontur pola terpisah yang terdeteksi.")

st.markdown("---")

# Header Kolom Tabel
h1, h2, h3, h4, h5, h6, h7, h8, h9, h10 = st.columns([2, 0.9, 0.9, 1.1, 0.8, 1.8, 1.1, 0.9, 1.1, 0.6])
h1.markdown("**Komponen Material**")
h2.markdown("**P (cm)**")
h3.markdown("**L (cm)**")
h4.markdown("**Net Area (cm²)**")
h5.markdown("**Waste (%)**")
h6.markdown("**Upload Single Pattern**")
h7.markdown("**Harga / Sheet ($)**")
h8.markdown("**Pairs/Sheet**")
h9.markdown("**Cost / Pair ($)**")
h10.markdown("**Aksi**")

st.markdown("---")

total_cost_per_pair = 0.0
id_to_delete = None

# Render Baris Material Menggunakan Unique UUID
for row in st.session_state.material_list:
    row_id = row["id"]
    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns([2, 0.9, 0.9, 1.1, 0.8, 1.8, 1.1, 0.9, 1.1, 0.6])
    
    row["Komponen"] = c1.text_input(f"name_{row_id}", value=row["Komponen"], placeholder="Nama Komponen...", label_visibility="collapsed")
    row["Panjang (cm)"] = c2.number_input(f"len_{row_id}", value=float(row["Panjang (cm)"]), min_value=0.0, label_visibility="collapsed")
    row["Lebar (cm)"] = c3.number_input(f"wid_{row_id}", value=float(row["Lebar (cm)"]), min_value=0.0, label_visibility="collapsed")
    
    # Upload Single File per Baris
    uploaded_file = c6.file_uploader(f"file_{row_id}", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        detected_area = process_single_pattern_image(uploaded_file)
        if detected_area > 0:
            row["Net Area (cm²)"] = detected_area
            c6.caption(f"✅ Area: **{detected_area} cm²**")

    row["Net Area (cm²)"] = c4.number_input(f"net_{row_id}", value=float(row["Net Area (cm²)"]), min_value=0.0, label_visibility="collapsed")
    row["Waste (%)"] = c5.number_input(f"wst_{row_id}", value=float(row["Waste (%)"]), min_value=0.0, label_visibility="collapsed")
    row["Harga / Sheet ($)"] = c7.number_input(f"price_{row_id}", value=float(row.get("Harga / Sheet ($)", 0.0)), min_value=0.0, step=0.1, format="%.2f", label_visibility="collapsed")

    # Kalkulasi Yield & Costing (USD)
    sheet_area = row["Panjang (cm)"] * row["Lebar (cm)"]
    gross_area = row["Net Area (cm²)"] * (1 + (row["Waste (%)"] / 100))
    
    pairs = int(sheet_area / gross_area) if gross_area > 0 else 0
    yield_pct = (row["Net Area (cm²)"] / gross_area * 100) if gross_area > 0 else 0.0
    cost_per_pair = (row["Harga / Sheet ($)"] / pairs) if pairs > 0 else 0.0
    total_cost_per_pair += cost_per_pair

    # Display Hasil
    c8.markdown(f"**{pairs}** pairs\n\n*({yield_pct:.1f}% yield)*")
    c9.markdown(f"**${cost_per_pair:.3f}**" if cost_per_pair > 0 else "-")
    
    # Tombol Hapus Baris
    if c10.button("🗑️", key=f"del_{row_id}", help="Hapus komponen ini"):
        id_to_delete = row_id

# Eksekusi Hapus Baris Berdasarkan Unique ID
if id_to_delete is not None:
    st.session_state.material_list = [item for item in st.session_state.material_list if item["id"] != id_to_delete]
    st.rerun()

# Tombol Tambah Baris Manual
st.markdown("")
if st.button("➕ Tambah Baris Manual"):
    st.session_state.material_list.append({
        "id": str(uuid.uuid4()),
        "Komponen": "",
        "Panjang (cm)": 0.0,
        "Lebar (cm)": 0.0,
        "Net Area (cm²)": 0.0,
        "Waste (%)": 0.0,
        "Harga / Sheet ($)": 0.0
    })
    st.rerun()

# Rekap Total Cost
st.markdown("---")
if total_cost_per_pair > 0:
    st.subheader(f"💵 Total Material Cost per Pair: ${total_cost_per_pair:.3f}")
