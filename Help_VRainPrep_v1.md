**VRainPrep v.1 - Panduan Penggunaan Singkat**

**Deskripsi:**
VRainPrep adalah perangkat lunak untuk memproses data curah hujan dengan berbagai skala Waktu (menitan, jam-jaman, dst) 
dari berbagai sumber, seperti PERSIANN, GSMAP, GPM, dan Stasiun hujan miliki Laboratorium Hidraulika UGM (UGM-Hidro). 
Program ini memungkinkan pengguna untuk menggabungkan data dari single file CSV atau beberapa file CSV (di dalam suatu folder), 
serta melakukan agregasi data berdasarkan periode waktu tertentu.

---

**Fitur Utama:**
1. **Input Data:**
   - Memilih folder berisi file CSV atau memilih satu file CSV.
   - Sumber data yang didukung: PERSIANN, GSMAP, GPM, UGM-Hidro, atau file table dengan format yang mirip dengan data-data tersebut.

2. **Pengolahan Data:**
   - Data akan diurutkan berdasarkan waktu dan dapat diaggregasi berdasarkan periode:
     - 30-menit, 1-jam, 3-jam, 6-jam, 12-jam, 24-jam, Bulanan, Triwulanan, Tahunan, dan Musiman.
   - Jenis perhitungan yang tersedia: Jumlah, Rata-rata, Maksimum, Minimum, dan Jumlah kejadian hujan > 1mm.

3. **Ekspor Data:**
   - Data yang telah diproses akan disimpan dalam format CSV di folder yang dipilih.

---

**Cara Penggunaan:**
1. Buka program VRainPrep.
2. Pilih folder atau file CSV sebagai input.
3. Pilih sumber data yang sesuai.
4. Pilih periode agregasi.
5. Pilih jenis perhitungan (Sum, Average, Maximum, Minimum, Count).
6. Tentukan folder output untuk menyimpan hasil.
7. Klik "Process" untuk menjalankan pemrosesan.
8. Jika berhasil, file hasil akan tersimpan di folder output.

---

**Pesan Kesalahan yang Mungkin Muncul:**
- "Please select data source type correctly!" → Pastikan memilih sumber data yang benar. Pastikan misal data yang anda download adalah GPM, pilih sumber data GPM.
- "No CSV files found in the selected directory." → Folder tidak mengandung file CSV. Folder dan atau subfolder harus berisi file-file CSV.
- "Error in reading CSV files or missing folders!" → Kesalahan saat membaca file, periksa format dan pastikan lokasi file benar.
- "File can not be saved! Please close the file." → File output sedang dibuka di program lain, tutup Excel sebelum menjalankan ulang.

---

**Kontak:**
Website: [vempi.staff.ugm.ac.id](https://vempi.staff.ugm.ac.id)
Email: vempi@ugm.ac.id

