# SmartKKA

**Sistem Otomatisasi Kertas Kerja Audit Pemerintahan Berbasis Multimodal AI & RAG**

Aplikasi web berbasis AI untuk melakukan *cross-check* otomatis antara data realisasi anggaran dengan dokumen bukti pertanggungjawaban serta peraturan pemerintah.

## Manfaat Utama
*   **Full-Population Audit:** Memeriksa 100% baris transaksi secara otomatis.
*   **Akurat & Terverifikasi (Anti-Halusinasi):** Menggunakan RAG untuk menarik pasal aturan resmi.
*   **Traceability Tinggi:** Bukti terhubung langsung ke halaman PDF spesifik.
*   **Efisiensi Ekspor Laporan:** Mengotomatiskan narasi baku audit menjadi `.docx`.

## Alur Sistem
1. **Upload Data:** Unggah `.xlsx` dan bundel `.pdf`.
2. **Automated Cross-Check:** Pencocokan AI antar dokumen.
3. **Legal RAG Matching:** Pencarian pasal dari *Vector Database* lokal.
4. **Review & Export:** Verifikasi via *split-screen* dan unduh `.docx`.

## Cara Menjalankan secara Lokal
```bash
pip install -r requirements.txt
streamlit run app.py
