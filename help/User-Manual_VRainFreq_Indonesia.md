# Panduan Pengguna VRainFreq

Selamat datang di panduan pengguna **VRainFreq v.1** (Program Analisis Frekuensi versi 1). 
Dokumen ini memberikan panduan lengkap tentang cara menggunakan perangkat lunak VRainFreq untuk analisis frekuensi data hidrologi atau meteorologi. 
Alat ini dirancang untuk membantu pengguna menganalisis dan memvisualisasikan data menggunakan berbagai metode statistik dan distribusi probabilitas.

---

## Daftar Isi
1. [Pengenalan](#pengenalan)
2. [Instalasi](#instalasi)
3. [Memulai](#memulai)
4. [Ikhtisar Antarmuka Pengguna](#ikhtisar-antarmuka-pengguna)
5. [Memuat Data](#memuat-data)
6. [Melakukan Analisis Frekuensi](#melakukan-analisis-frekuensi)
7. [Analisis Batch](#analisis-batch)
8. [Memvisualisasikan Hasil](#memvisualisasikan-hasil)
9. [Mengekspor Hasil](#mengekspor-hasil)
10. [Lisensi](#lisensi)
11. [Pemecahan Masalah](#pemecahan-masalah)

---

## Pengenalan

VRainFreq adalah aplikasi berbasis Python yang dirancang untuk analisis frekuensi data hidrologi atau meteorologi. 
Aplikasi ini mendukung berbagai distribusi probabilitas (GEV, Normal, Log-Normal, Gumbel, Log-Pearson III). 
Program ini juga menyediakan output grafis dan tabel untuk memudahkan interpretasi hasil.

---

## Instalasi

### Prasyarat
(Tidak ada prasyarat)

### Langkah Instalasi
Jalankan aplikasi dengan membuka `VRainFreq_v1.exe`

---

## Memulai

Setelah aplikasi berjalan, Anda akan melihat jendela utama dengan judul 
**"VRain | Frequency Analysis Tool (VRainFreq v.1)"**. 

Antarmuka dibagi menjadi dua bagian utama:
- **Panel Kiri**: Kontrol input dan tabel statistik dasar dan probabilitas yang dipakai.
- **Panel Kanan**: Output grafis (plot).

---

## Ikhtisar Antarmuka Pengguna

### Menu Bar
- **File**:
  - **Open**: Memuat satu file atau beberapa file untuk analisis batch.
  - **Exit**: Menutup aplikasi.
- **Help**:
  - **License**: Menampilkan lisensi perangkat lunak.

### Panel Kiri
- **Enable Batch Analysis**: Centang opsi ini untuk menganalisis beberapa file dalam satu folder.
- **Browse**: Pilih file atau folder yang berisi data.
- **Column Selection**: Pilih kolom yang akan dianalisis (untuk mode file tunggal).
- **Method Selection**: Pilih metode statistik untuk ranking frekuensi empiris (hanya untuk plotting).
- **Significance Level (α)**: Tetapkan tingkat signifikansi untuk penggambaran Confidence Interval (hanyak untuk distribusi GEV).
- **Return Periods**: Masukkan periode ulang untuk analisis (nilai dipisahkan koma).
- **Output Directory**: Tetapkan direktori untuk menyimpan hasil (opsional). Jika tidak diisi, maka output files akan disimpan pada directory yang sama dengan input file(s)
- **Run Frequency Analysis**: Melakukan analisis frekuensi pada data yang dipilih.
- **Batch Run**: Melakukan analisis pada semua kolom dalam dataset yang dimuat. 

### Panel Kanan
- **Frequency Plot**: Menampilkan plot probability empiris dan/atau analisis frekuensi dari berbagai jenis distribusi (GEV, log-pearson III, log-normal, normal, gumbel).
- **Histogram with PDF**: Menampilkan histogram dengan Probability Density Function (PDF) dari berbagai jenis distribusi.

---

## Memuat Data

### Mode File Tunggal
1. Jangan centang **Enable Batch Analysis**.
2. Klik **Browse** dan pilih file CSV atau Excel.
3. Pilih kolom yang akan dianalisis dari menu dropdown.

### Mode Batch
1. Centang **Enable Batch Analysis**.
2. Klik **Browse** dan pilih folder yang berisi file CSV atau Excel.
3. Alat akan menggabungkan semua file menjadi satu dataset untuk dianalisis.
4. Lalu pilih kembali file yang sudah digabung tersebut dengan mode File Tunggal (ikuti cara diatas).

---

## Melakukan Analisis Frekuensi

1. **Pilih Metode**: Pilih dari dropdown metode ranking plot probability statistik data empiris (yang paling umum digunakan untuk Extreme Value (GEV, Gumbel) adalah Gringorten).
2. **Tetapkan Return Periods**: Masukkan periode ulang (misalnya, `1.1,5,10,20,50,100,200`).
3. **Tetapkan Tingkat Signifikansi**: Pilih tingkat signifikansi untuk penggambaran batas Confidence Interval GEV (misalnya, 0.05).
4. **Jalankan Analisis**:
   - Untuk analisis kolom tunggal, klik **Run Frequency Analysis**.
   - Untuk analisis batch, klik **Batch Run**.

---

## Analisis Batch

Dalam mode batch, alat akan:
1. Menggabungkan semua file dalam folder yang dipilih.
2. Melakukan analisis frekuensi pada setiap kolom.
3. Menyimpan hasil untuk setiap kolom data di direktori output.

---

## Memvisualisasikan Hasil

### Frequency Plot
- Dengan klik tombol Run, program akan menampilkan secara otomatis data observasi dan distribusi yang sesuai.
- Menyertakan interval kepercayaan untuk distribusi GEV.
- Anotasi menyediakan parameter GEV (shape, location, scale) dan informasi penskalaan.

### Histogram with PDF
- Menampilkan histogram data.
- Menampilkan fungsi kepadatan probabilitas dari berbagai jenis distribusi untuk perbandingan.

---

## Mengekspor Hasil

Alat secara otomatis menyimpan file berikut di direktori output:
1. **VRain_ks_{nama_stasiun}.csv**: Hasil uji Kolmogorov-Smirnov.
2. **VRain_chi-square_{nama_stasiun}.csv**: Hasil uji Chi-square.
3. **VRain_return-levels_{nama_stasiun}.csv**: Tingkat return untuk periode ulang yang dipilih.
4. **VRain_stat_{nama_stasiun}.csv**: Ringkasan statistik.

---

## Lisensi

Perangkat lunak ini disediakan di bawah perjanjian lisensi berikut:
- **Hak Cipta**: © 2025 Vempi Satriya Adi Hendrawan.
- **Izin**: Gratis untuk penggunaan edukasi dan komersial.
- **Pembatasan**: Redistribusi, modifikasi, atau penjualan perangkat lunak dilarang tanpa izin.
- **Penafian**: Perangkat lunak disediakan "sebagaimana adanya" tanpa jaminan. Pengembang tidak bertanggung jawab atas kerusakan apa pun.

Untuk pertanyaan, hubungi:  
**vempi@ugm.ac.id** | **vempi.staff.ugm.ac.id**

---

## Troubleshooting

### Masalah Umum
1. **File Tidak Dimuat**:
   - Pastikan path file benar.
   - Periksa apakah format file didukung (CSV atau Excel).

2. **Error Memori**:
   - Adanya ketidak laziman distribusi data sehingga return values (mm) hasil fitting distribusi didapatkan nilai yang sangat besar.
   - Cek kelaziman nilai data

3. **Input Tidak Valid**:
   - Pastikan periode ulang dimasukkan sebagai nilai yang dipisahkan koma (misalnya, `1,5,10`).

4. **Error Plotting**:
   - Periksa apakah data mengandung nilai yang hilang atau tidak valid.

### Dukungan
Untuk bantuan lebih lanjut, hubungi pengembang di **vempi@ugm.ac.id**.

---

Terima kasih telah menggunakan VRainFreq! Semoga alat ini membantu Anda dalam melakukan analisis frekuensi.
