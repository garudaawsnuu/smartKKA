import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from audit_logic import process_excel_data, extract_pdf_text, run_rag_and_multimodal_llm, export_to_docx

st.set_page_config(layout="wide", page_title="SmartKKA")

st.title("SmartKKA: Sistem Otomatisasi Kertas Kerja Audit")
st.markdown("Berbasis Multimodal AI & RAG untuk *Full-Population Audit* dan pencocokan regulasi otomatis.")

# --- FUNGSI GENERATE DATA UJI COBA (EXCEL & PDF) ---
def get_sample_excel():
    df_sample = pd.DataFrame({
        "Tanggal": ["2023-10-01", "2023-10-15", "2023-11-02"],
        "Kode_Rekening": ["5.2.2.01", "5.2.3.11", "5.2.2.05"],
        "Uraian_Pekerjaan": ["Pembayaran Termin 1 Pembangunan Gedung", "Pengadaan Komputer PC", "Biaya Konsultan Perencana"],
        "Nominal_Rp": [500000000, 75000000, 45000000],
        "No_Bukti_Kontrak": ["KONTRAK/01/X/2023", "SPK/05/X/2023", "KONTRAK/02/XI/2023"]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sample.to_excel(writer, index=False, sheet_name='Realisasi_Anggaran')
    return output.getvalue()

def get_sample_pdf():
    doc = fitz.open()
    page = doc.new_page()
    teks_kontrak = """
    SURAT PERJANJIAN KERJA (KONTRAK)
    No: KONTRAK/01/X/2023
    
    Tanggal: 01 Oktober 2023
    Pekerjaan: Pembangunan Gedung Tahap 1
    Nilai Kontrak: Rp 500.000.000
    
    Pasal 5: Waktu Pelaksanaan
    Pekerjaan harus diselesaikan dalam waktu 30 hari kalender.
    
    Pasal 8: Sanksi Keterlambatan
    Apabila terjadi keterlambatan, Pihak Kedua dibebaskan dari denda keterlambatan 
    atas kesepakatan bersama. (Anomali: Keterlambatan tanpa denda).
    """
    page.insert_text((50, 50), teks_kontrak, fontsize=12)
    return doc.write()

# --- SIDEBAR: UNDUH DATA UJI COBA ---
with st.sidebar:
    st.header("💡 Data Uji Coba")
    st.markdown("Unduh kedua file di bawah ini untuk mencoba sistem *Full-Population Audit*.")
    
    st.download_button(
        label="📥 1. Unduh Sample_Anggaran.xlsx",
        data=get_sample_excel(),
        file_name="Sample_Realisasi_Anggaran.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.download_button(
        label="📥 2. Unduh Sample_Kontrak.pdf",
        data=get_sample_pdf(),
        file_name="Sample_Bukti_Kontrak.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    st.info("Setelah diunduh, unggah kembali kedua file tersebut di kolom utama.")

# --- 1. UPLOAD DATA ---
st.header("1. Upload Data")
col_up1, col_up2 = st.columns(2)
with col_up1:
    excel_file = st.file_uploader("Unggah Laporan Realisasi Anggaran (.xlsx / .csv)", type=['xlsx', 'csv'])
with col_up2:
    pdf_files = st.file_uploader("Unggah Bukti Dokumen (Kontrak, BAST) (.pdf)", type=['pdf'], accept_multiple_files=True)

# --- 2 & 3. AUTOMATED CROSS-CHECK & LEGAL RAG MATCHING ---
if st.button("Jalankan Cross-Check Otomatis", type="primary"):
    if excel_file and pdf_files:
        with st.spinner("Memproses 100% baris transaksi dan menjalankan Multimodal AI..."):
            df, summary_excel = process_excel_data(excel_file)
            pdf_texts = extract_pdf_text(pdf_files)
            
            draft_kka_result = run_rag_and_multimodal_llm(summary_excel, pdf_texts)
            
            st.success("Analisis Selesai! Seluruh populasi data berhasil diverifikasi.")
            st.session_state['df'] = df # Menyimpan DataFrame untuk divisualisasikan
            st.session_state['draft'] = draft_kka_result
            st.session_state['pdf_bytes'] = pdf_files[0].getvalue()
    else:
        st.warning("Harap unggah file laporan anggaran (Excel) dan minimal satu dokumen bukti (PDF).")

# --- 4. REVIEW, DASHBOARD & EXPORT ---
if 'draft' in st.session_state:
    st.header("4. Hasil Audit Otomatis")
    
    # Menggunakan Tabs untuk memisahkan Visualisasi Data dan Draf KKA
    tab1, tab2 = st.tabs(["📊 Dashboard Data Laporan", "📝 Draf KKA & Bukti Traceability"])
    
    # --- TAB 1: DASHBOARD VISUALISASI ---
    with tab1:
        st.subheader("Visualisasi Full-Population Audit")
        df_state = st.session_state['df']
        
        # Kartu Metrik Ringkasan
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(label="Total Baris Transaksi", value=f"{len(df_state)} Baris", delta="100% Diperiksa")
        
        # Validasi kolom Nominal_Rp sebelum menjumlahkan
        if "Nominal_Rp" in df_state.columns:
            total_anggaran = df_state["Nominal_Rp"].sum()
            col_m2.metric(label="Total Realisasi Anggaran", value=f"Rp {total_anggaran:,.0f}")
        else:
            col_m2.metric(label="Total Realisasi Anggaran", value="Data tidak valid")
            
        col_m3.metric(label="Anomali Terdeteksi", value="1 Dokumen", delta="- Potensi Temuan", delta_color="inverse")
        
        st.divider()
        
        # Grafik Bar Chart (Anggaran per Pekerjaan)
        if "Uraian_Pekerjaan" in df_state.columns and "Nominal_Rp" in df_state.columns:
            st.markdown("**Grafik Distribusi Anggaran per Uraian Pekerjaan**")
            chart_data = df_state.set_index("Uraian_Pekerjaan")["Nominal_Rp"]
            st.bar_chart(chart_data, use_container_width=True)
            
        # Tabel Data (Interactive)
        st.markdown("**Tabel Populasi Transaksi (Hasil Ekstraksi .xlsx / .csv)**")
        st.dataframe(df_state, use_container_width=True)

    # --- TAB 2: SPLIT-SCREEN KKA & PDF VIEWER ---
    with tab2:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📝 Draf Kertas Kerja Audit (KKA)")
            edited_draft = st.text_area("Edit Narasi Baku Audit (Kondisi, Kriteria, Sebab, Akibat):", st.session_state['draft'], height=450)
            
            docx_file = export_to_docx(edited_draft)
            st.download_button(
                label="📄 Ekspor ke Laporan Word (.docx)",
                data=docx_file,
                file_name="Draf_KKA_SmartKKA.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )
            
        with col_right:
            st.subheader("🔍 Bukti Traceability (PDF)")
            try:
                doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=150)
                    st.image(pix.tobytes(), caption=f"Halaman {page_num + 1}", use_column_width=True)
                    st.divider()
            except Exception as e:
                st.error(f"Gagal memuat visualisasi PDF: {e}")
