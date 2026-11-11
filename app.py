import streamlit as st
import base64
from audit_logic import process_excel_data, extract_pdf_text, run_rag_and_multimodal_llm, export_to_docx

st.set_page_config(layout="wide", page_title="SmartKKA")

st.title("SmartKKA: Sistem Otomatisasi Kertas Kerja Audit")
st.markdown("Berbasis Multimodal AI & RAG untuk *Full-Population Audit* dan pencocokan regulasi otomatis.")

# 1. Upload Data
st.header("1. Upload Data")
col_up1, col_up2 = st.columns(2)
with col_up1:
    excel_file = st.file_uploader("Unggah Laporan Realisasi Anggaran (.xlsx / .csv)", type=['xlsx', 'csv'])
with col_up2:
    pdf_files = st.file_uploader("Unggah Bukti Dokumen (Kontrak, BAST) (.pdf)", type=['pdf'], accept_multiple_files=True)

if st.button("Jalankan Cross-Check Otomatis", type="primary"):
    if excel_file and pdf_files:
        with st.spinner("Memproses RAG dan Multimodal LLM..."):
            # 2. Automated Cross-Check & 3. Legal RAG Matching
            df, summary_excel = process_excel_data(excel_file)
            pdf_texts = extract_pdf_text(pdf_files)
            
            draft_kka_result = run_rag_and_multimodal_llm(summary_excel, pdf_texts)
            
            st.success("Analisis Selesai!")
            st.session_state['draft'] = draft_kka_result
            st.session_state['pdf_bytes'] = pdf_files[0].getvalue() # Mengambil PDF pertama untuk preview
    else:
        st.warning("Harap unggah file laporan anggaran dan minimal satu dokumen PDF pendukung.")

# 4. Review & Export (Split-Screen)
if 'draft' in st.session_state:
    st.header("4. Review & Export")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Draf Kertas Kerja Audit (KKA)")
        edited_draft = st.text_area("Edit Narasi (Kondisi, Kriteria, Sebab, Akibat)", st.session_state['draft'], height=400)
        
        # Tombol Unduh Docx
        docx_file = export_to_docx(edited_draft)
        st.download_button(
            label="Unduh Laporan (.docx)",
            data=docx_file,
            file_name="Draf_KKA_SmartKKA.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    with col_right:
        st.subheader("PDF Viewer (Bukti Traceability)")
        # Menampilkan PDF menggunakan Base64 iframe
        base64_pdf = base64.b64encode(st.session_state['pdf_bytes']).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="450" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
