# Panduan Pengguna: Thiessen Polygon Generator

## Ikhtisar
Thiessen Polygon Generator adalah program yang dirancang untuk membuat poligon Thiessen (juga dikenal sebagai diagram Voronoi) dari input titik input (misal stasiun hujan) dan shapefile batas (misal DAS). 
Program ini memungkinkan pengguna untuk memvisualisasikan poligon, mendapatkan bobot (proporsi) masing-masing poligon, menyesuaikan sistem referensi koordinat (CRS), dan menyimpan output dalam format (SHP, CSV). 
Panduan pengguna ini memberikan petunjuk langkah demi langkah tentang cara menggunakan program.

---

## Persyaratan Sistem
- **Sistem Operasi**: Windows
- **Executable Standalone**: Jika menggunakan versi `.exe`, tidak diperlukan instalasi tambahan.

---

## Instalasi
**Executable Standalone**:
- Unduh file `.exe`.
- Klik dua kali file tersebut untuk menjalankan program.

---

## Ikhtisar Antarmuka Pengguna
Antarmuka program terdiri dari komponen berikut:

1. **Menu Bar**:
   - **File**: Buka direktori output `Open Output` atau keluar dari program `Exit`.
   - **Plot Style**: Ubah gaya visualisasi plot.
   - **About**: Lihat perjanjian lisensi perangkat lunak.

2. **Input Frame**:
   - **Shapefile Area**: Muat shapefile batas.
   - **CSV/SHP Koordinat**: Muat file CSV atau shapefile yang berisi koordinat titik (stasiun hujan).
   - **Pilih CRS**: Pilih CRS untuk titik input (jika menggunakan CSV).

3. **Output Frame**:
   - **Pilih CRS Output**: Pilih CRS untuk file output.
   - **Generate Thiessen Polygons**: Buat poligon berdasarkan data input.
   - **Save Outputs**: Simpan poligon yang dihasilkan dan data stasiun hujan.
   - **Reset**: Hapus semua data yang dimuat dan reset antarmuka.

4. **Visualization Frame**:
   - Menampilkan shapefile batas, titik input, dan poligon Thiessen yang dihasilkan.

---

## Petunjuk Langkah demi Langkah

### 1. Memuat Shapefile Batas
- Klik tombol **Browse** di sebelah kolom "Shapefile Area".
- Pilih file `.shp` yang mendefinisikan area batas.
- Batas akan ditampilkan di frame visualisasi.

### 2. Memuat Data Titik
- Klik tombol **Browse** di sebelah kolom "CSV/SHP Koordinat".
- Pilih file `.csv` atau `.shp` yang berisi koordinat titik.
  - Untuk file CSV, pastikan file tersebut memiliki kolom bernama `x` dan `y` (atau `X` dan `Y`) untuk koordinat.
- Jika menggunakan file CSV, pilih CRS yang sesuai dari menu dropdown.

### 3. Membuat Poligon Thiessen
- Setelah memuat shapefile batas dan data titik, klik tombol **Generate Thiessen Polygons**.
- Aplikasi akan membuat poligon dan menampilkannya di frame visualisasi.

### 4. Mengubah Gaya Plot
- Gunakan menu **Plot Style** untuk mengubah gaya visualisasi plot (misalnya, classic, seaborn, grayscale).

### 5. Menyimpan Output
- Klik tombol **Save Outputs** untuk menyimpan poligon yang dihasilkan dan data stasiun hujan.
- Pilih direktori untuk menyimpan file. File berikut akan dibuat:
  - `VRain_Thiessen_Polygons.shp`: Shapefile yang berisi poligon Thiessen.
  - `VRain_Rainfall_Stations_With_Weights.csv`: File CSV yang berisi data stasiun hujan dengan bobot poligon.

### 6. Mereset Data
- Klik tombol **Reset** untuk menghapus semua data yang dimuat dan mengatur ulang antarmuka.

---

## Fitur Tambahan

### Melihat Contoh Format CSV
- Klik tombol **Lihat format CSV** untuk melihat contoh format CSV yang diperlukan.

### Membuka Direktori Output
- Setelah menyimpan output, gunakan menu **File > Open Output** untuk membuka direktori tempat file disimpan.

### Mengubah CRS Output
- Gunakan dropdown **Output CRS** untuk memilih CRS yang diinginkan untuk file output.

---

## Pemecahan Masalah

### 1. Kesalahan File CSV
- Pastikan file CSV memiliki kolom bernama `x` dan `y` (atau `X` dan `Y`) untuk koordinat.
- Jika file tidak dapat dimuat, periksa data yang hilang atau format yang salah.

### 2. Kesalahan Shapefile
- Pastikan shapefile valid dan berisi geometri poligon.
- Jika file tidak dapat dimuat, periksa file lain misal`.shx` atau `.dbf` yang hilang di direktori yang sama.

### 3. Masalah Visualisasi
- Jika plot tidak ditampilkan dengan benar, coba ubah gaya plot atau reset data.

---

## Lisensi
Perangkat lunak ini disediakan di bawah perjanjian lisensi berikut:

```
Rainfall Data Preparation (VRainPrep) v.1
Perjanjian Lisensi Perangkat Lunak
Hak Cipta (c) 2025 Vempi Satriya Adi Hendrawan

Izin diberikan untuk menggunakan perangkat lunak ini untuk tujuan pendidikan atau komersial.
Pembatasan:
- Anda tidak boleh mendistribusikan, memodifikasi, atau menjual perangkat lunak ini tanpa izin.
Penafian:
Perangkat lunak ini disediakan "sebagaimana adanya" tanpa jaminan. Pengembang tidak bertanggung jawab atas kerusakan apa pun.
```

Untuk pertanyaan, hubungi:  
**vempi@ugm.ac.id** | **vempi.staff.ugm.ac.id**

---

## Dukungan
Untuk dukungan tambahan atau permintaan fitur, silakan hubungi pengembang di alamat email yang tercantum di atas.

---

Terima kasih telah menggunakan Thiessen Polygon Generator!
