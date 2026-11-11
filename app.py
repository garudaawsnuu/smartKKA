import streamlit as st
import pandas as pd
import io
import base64
from audit_logic import process_excel_data, extract_pdf_text, run_rag_and_multimodal_llm, export_to_docx

st.set_page_config(layout="wide", page_title="SmartKKA")

st.title("SmartKKA: Sistem Otomatisasi Kertas Kerja Audit")
st.markdown("Berbasis Multimodal AI & RAG untuk *Full-Population Audit* dan pencocokan regulasi otomatis.")

# --- FUNGSI GENERATE DATA UJI COBA ---
def get_sample_excel():
    """Membuat file Excel dummy di memori untuk keperluan uji coba."""
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

# --- SIDEBAR: UNDUH DATA UJI COBA ---
with st.sidebar:
    st.header("💡 Data Uji Coba")
    st.markdown("Gunakan *file* Excel ini untuk menguji coba fitur *Full-Population Audit* jika Anda belum memiliki data.")
    
    st.download_button(
        label="📥 Unduh Sample_Anggaran.xlsx",
        data=get_sample_excel(),
        file_name="Sample_Realisasi_Anggaran.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="secondary"
    )
    st.info("Catatan: Untuk bukti PDF, Anda dapat mengunggah file PDF sembarang (misal: draf dokumen atau artikel) sebagai simulasi *Traceability* dokumen pendukung.")

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
        with st.spinner("Memproses 100% baris transaksi dan menjalankan Multimodal LLM..."):
            
            df, summary_excel = process_excel_data(excel_file)
            pdf_texts = extract_pdf_text(pdf_files)
            
            draft_kka_result = run_rag_and_multimodal_llm(summary_excel, pdf_texts)
            
            st.success("Analisis Selesai! Tidak ada baris yang terlewat.")
            st.session_state['draft'] = draft_kka_result
            st.session_state['pdf_bytes'] = pdf_files[0].getvalue() # Mengambil PDF pertama untuk preview visual
    else:
        st.warning("Harap unggah file laporan anggaran (Excel/CSV) dan minimal satu dokumen bukti PDF pendukung.")

# --- 4. REVIEW & EXPORT (SPLIT-SCREEN) ---
if 'draft' in st.session_state:
    st.header("4. Review & Export")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📝 Draf Kertas Kerja Audit (KKA)")
        edited_draft = st.text_area("Edit Narasi Baku Audit (Kondisi, Kriteria, Sebab, Akibat):", st.session_state['draft'], height=400)
        
        # Tombol Unduh Laporan KKA ke format Word
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
        # Menampilkan PDF bukti secara real-time di kolom kanan
        base64_pdf = base64.b64encode(st.session_state['pdf_bytes']).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="480" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
