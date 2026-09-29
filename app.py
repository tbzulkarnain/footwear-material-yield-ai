import streamlit as st
import pandas as pd

# Konfigurasi Halaman (Lebar Penuh)
st.set_page_config(
    page_title="Footwear Material Yield AI",
    page_icon="👟",
    layout="wide"
)

# Custom CSS untuk styling card/modul material
st.markdown("""
    <style>
    .material-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Main Header
st.title("👟 Footwear Material Yield AI")
st.caption("Hitung dan optimasi material yield sepatu secara langsung per komponen.")

# Session State untuk menyimpan list material
if "materials" not in st.session_state:
    st.session_state.materials = [
        {"id": 1, "name": "Upper Leather / Synthetic", "length": 100.0, "width": 140.0, "net_area": 0.0, "allowance": 5.0}
    ]

# Function Tambah Baris Material
def add_material():
    new_id = len(st.session_state.materials) + 1
    st.session_state.materials.append({
        "id": new_id,
        "name": f"Material Component #{new_id}",
        "length": 100.0,
        "width": 140.0,
        "net_area": 0.0,
        "allowance": 5.0
    })

# Function Hapus Baris Material
def remove_material(index):
    if len(st.session_state.materials) > 1:
        st.session_state.materials.pop(index)

# Loop Render Setiap Material
results = []

for i, mat in enumerate(st.session_state.materials):
    st.markdown(f"### 📦 Komponen Material #{i+1}")
    
    with st.container():
        col1, col2, col3 = st.columns([1.2, 1.5, 1])
        
        # --- KOLOM 1: PARAMETER MATERIAL ---
        with col1:
            st.subheader("1. Parameter Sheet")
            mat["name"] = st.text_input("Nama Material / Komponen", value=mat["name"], key=f"name_{i}")
            mat["length"] = st.number_input("Panjang Roll/Sheet (cm)", value=mat["length"], min_value=0.0, key=f"len_{i}")
            mat["width"] = st.number_input("Lebar Roll/Sheet (cm)", value=mat["width"], min_value=0.0, key=f"wid_{i}")
            mat["allowance"] = st.number_input("Waste Allowance (%)", value=mat["allowance"], min_value=0.0, key=f"allow_{i}")

        # --- KOLOM 2: NET AREA & UPLOAD ---
        with col2:
            st.subheader("2. Net Area Pattern")
            
            # Pilihan kalkulasi / upload
            calc_method = st.radio(
                "Sumber Data Net Area:",
                ["Input Manual", "Upload Gambar Pattern (AI / Vision)"],
                key=f"method_{i}"
            )
            
            if calc_method == "Input Manual":
                mat["net_area"] = st.number_input(
                    "Net Area Pattern per Pasang (cm²)", 
                    value=mat["net_area"], 
                    min_value=0.0, 
                    key=f"net_{i}"
                )
            else:
                uploaded_file = st.file_uploader(
                    "Upload Pattern CAD / Foto Pattern", 
                    type=["png", "jpg", "jpeg", "dxf"], 
                    key=f"file_{i}"
                )
                if uploaded_file is not None:
                    # SIMULASI DUMMY AI DETEKSI AREA (Nanti bisa dihubungkan ke OpenCV/AI Model)
                    simulated_detected_area = 245.50  # Contoh nilai hasil olah gambar
                    st.success(f"Pattern Terdeteksi! Net Area: {simulated_detected_area} cm²")
                    mat["net_area"] = simulated_detected_area
                else:
                    st.info("Upload file gambar pattern untuk ekstraksi area otomatis.")

        # --- KOLOM 3: HASIL YIELD & PERHITUNGAN ---
        with col3:
            st.subheader("3. Hasil Material Yield")
            
            sheet_area = mat["length"] * mat["width"]
            
            if mat["net_area"] > 0 and sheet_area > 0:
                gross_area_needed = mat["net_area"] * (1 + (mat["allowance"] / 100))
                yield_percentage = (mat["net_area"] / gross_area_needed) * 100 if gross_area_needed > 0 else 0
                pairs_per_sheet = int(sheet_area / gross_area_needed) if gross_area_needed > 0 else 0
                
                st.metric("Total Sheet Area", f"{sheet_area:,.1f} cm²")
                st.metric("Pairs / Sheet", f"{pairs_per_sheet} Pairs")
                st.metric("Material Yield", f"{yield_percentage:.2f}%")
                
                results.append({
                    "Komponen": mat["name"],
                    "Sheet Area (cm²)": sheet_area,
                    "Net Area (cm²)": mat["net_area"],
                    "Allowance (%)": mat["allowance"],
                    "Pairs/Sheet": pairs_per_sheet,
                    "Yield (%)": round(yield_percentage, 2)
                })
            else:
                st.warning("Lengkapi data Sheet & Net Area untuk melihat hasil yield.")
                
        # Tombol Hapus Baris jika material > 1
        if len(st.session_state.materials) > 1:
            st.button("🗑️ Hapus Material Ini", key=f"del_{i}", on_click=remove_material, args=(i,))

    st.markdown("---")

# --- TOMBOL KONTROL UTAMA ---
col_add, col_blank = st.columns([1, 3])
with col_add:
    st.button("➕ Tambah Material / Komponen", on_click=add_material, use_container_width=True)

# --- REKAPITULASI SUMMARY TABLE ---
if results:
    st.subheader("📊 Ringkasan Material Yield")
    df_results = pd.DataFrame(results)
    st.dataframe(df_results, use_container_width=True)
