import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF untuk generate dan render PDF dengan aman
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
            
            st.success("Analisis Selesai! Tidak ada baris yang terlewat.")
            st.session_state['draft'] = draft_kka_result
            st.session_state['pdf_bytes'] = pdf_files[0].getvalue() # Simpan bytes PDF
    else:
        st.warning("Harap unggah file laporan anggaran (Excel) dan minimal satu dokumen bukti (PDF).")

# --- 4. REVIEW & EXPORT (SPLIT-SCREEN) ---
if 'draft' in st.session_state:
    st.header("4. Review & Export")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📝 Draf Kertas Kerja Audit (KKA)")
        edited_draft = st.text_area("Edit Narasi Baku Audit:", st.session_state['draft'], height=400)
        
        docx_file = export_to_docx(edited_draft)
        st.download_button(
            label="📄 Ekspor ke Laporan Word (.docx)",
            data=docx_file,
            file_name="Draf_KKA_SmartKKA.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
        
    with col_right:
        st.subheader("🔍 PDF Viewer (Bukti Traceability)")
        
        # PERBAIKAN: Menggunakan PyMuPDF (fitz) untuk merender PDF menjadi gambar
        try:
            # Buka dokumen PDF dari byte stream
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            
            # Loop melalui setiap halaman dan tampilkan sebagai gambar
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150) # Set DPI agar resolusi jelas
                
                # Menampilkan render gambar ke Streamlit
                st.image(pix.tobytes(), caption=f"Halaman {page_num + 1}", use_column_width=True)
                st.divider() # Garis pemisah antar halaman
                
        except Exception as e:
            st.error(f"Gagal memuat visualisasi PDF: {e}")
