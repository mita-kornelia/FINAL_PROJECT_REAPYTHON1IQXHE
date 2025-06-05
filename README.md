<<<<<<< HEAD
# Voice-Based Fast Food Ordering System

## Deskripsi
Aplikasi ini adalah sistem pemesanan makanan cepat saji berbasis suara yang dibangun menggunakan Streamlit. Pengguna dapat memesan makanan dengan berbicara, mengedit pesanan, dan melakukan pembayaran dengan berbagai metode.

## Fitur Utama
1. **Pemesanan Suara**: Menggunakan model Whisper dari Hugging Face untuk mengenali suara dan mengubahnya menjadi teks.
2. **Pengelolaan Pesanan**: Tambah, kurangi, atau hapus item pesanan secara dinamis.
3. **Pembayaran**: Mendukung metode pembayaran tunai, e-wallet, dan kartu debit.
4. **Cetak Struk**: Struk pembelian dapat dicetak dan disimpan sebagai file teks.

## Teknologi yang Digunakan
- **Streamlit**: Framework untuk membangun aplikasi web interaktif.
- **Hugging Face Whisper**: Model untuk pengenalan suara.
- **SpeechRecognition**: Library untuk merekam audio.
- **Librosa**: Digunakan untuk memproses file audio.

## Cara Menjalankan
1. Pastikan Python dan semua dependensi telah terinstal.
2. Jalankan perintah berikut di terminal:
   ```bash
   streamlit run voice.py
   ```
3. Akses aplikasi melalui browser di `http://localhost:8501`.

## Struktur File
- `voice.py`: File utama aplikasi.
- `requirements.text`: Daftar dependensi yang diperlukan.
- `struk_pembelian_*.txt`: File struk pembelian yang disimpan.

## Instalasi
1. Buat environment virtual:
   ```bash
   python -m venv myenv
   ```
2. Aktifkan environment:
   - Windows:
     ```bash
     .\myenv\Scripts\Activate.ps1
     ```
   - Mac/Linux:
     ```bash
     source myenv/bin/activate
     ```
3. Instal dependensi:
   ```bash
   pip install -r requirements.text
   ```

## Catatan
- Pastikan mikrofon berfungsi dengan baik untuk pemesanan suara.
- File audio sementara akan dihapus setelah diproses.

## Lisensi
Proyek ini dilisensikan di bawah [MIT License](LICENSE).
=======
# FINAL_PROJECT_REAPYTHON1IQXHE
>>>>>>> b534afd1e9ce584aa6b27c58a3711d59931a9cc6
