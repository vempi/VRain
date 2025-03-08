### **Panduan Pengguna (User Manual) untuk Program VRainStorm v.1**

---

#### **1. Pendahuluan**
Program **VRainStorm** adalah aplikasi untuk menganalisis durasi dan distribusi curah hujan berdasarkan data curah hujan jam-jaman. 
Program ini dapat digunakan untuk memproses data curah hujan jam-jaman, mengelompokkan kejadian hujan, dan menghasilkan visualisasi distribusi curah hujan menggunakan metode Huff.

---

#### **2. Instalasi**
Jalankan program dengan menjalankan file `VRainStorm.exe`.

---

#### **3. Antarmuka Pengguna**
Program ini memiliki antarmuka grafis (GUI) yang terdiri dari beberapa bagian:

1. **Menu Bar**:
   - **File**: Untuk membuka file CSV, menyimpan hasil, dan keluar dari program.
   - **Plot**: Untuk menampilkan visualisasi distribusi curah hujan.
   - **Help**: Menampilkan informasi tentang lisensi dan cara menggunakan program.

2. **Input Data**:
   - **Data Type**: Pilih tipe data curah hujan (default: `Default`).
   - **Load CSV File**: Tombol untuk memuat file CSV yang berisi data curah hujan.
   - **File ID**: Masukkan nama stasiun atau identifikasi file.

3. **Parameter Threshold Curah Hujan**:
   - **Threshold Type**: Pilih jenis threshold hujan total dalam satu event (nilai absolut dalam mm atau persentil dalam fraksi).
     Event didefinisikan sebagai hujan jam-jaman secara beruntun.
     Input dalam persentil akan menghasilkan batas berdasarkan distribusi hujan total jam-jaman
     (misal pada suatu kasus dengan batas  99th persentil data akan ekuivalen dengan batas 47.5 mm) 
   - **Threshold Value**: Masukkan nilai threshold hujan total dalam satu event (misalnya, 50 mm atau 0.75 untuk persentil).
     Nilai ini menentukan batas hujan akumulatif dalam periode tertentu, yang bisa didefinisikan sebagai batas hujan deras (misal > 50 mm).
     Semakin besar nilai ini akan mengurangi jumlah sampel event hujan yang dihitung.
   - **Minimum Hourly Rainfall**: Masukkan nilai minimum curah hujan per jam yang akan diikutsertakan (misal > 1mm).
     Secara umum, semakin besar nilai ini akan menyebabkan durasi hujan jam-jaman rerata akan berkurang (semakin pendek).

4. **Output Directory**:
   - **Output Directory**: Pilih direktori tempat hasil analisis akan disimpan.

5. **Processing**:
   - **Duration Type**: Pilih jenis durasi untuk plot (persentase, durasi dominan, atau durasi tetap).
     *Persentase*: Memberikan pola hujan jam-jaman dengan rentang 0-100% (dengan step tiap 10%). Pilihan ini lebih fleksibel dan dapat diterapkan untuk berbagai durasi total.
     *Durasi dominan*: Menetapkan durasi yang didapat nilai rerata durasi hujan (dalam jam) seluruh sampel event hujan yang dihitung.
     Pilihan ini memberikan model hujan jam-jaman dengan periode yang moderate, sesuai dengan data empiris (rerata).
     *Durasi tetap*: Menentukan durasi total hujan jam-jaman rancangan sesuai dengan kebutuhan.
   - **Process Data**: Tombol untuk memulai proses analisis data.
   - **Reset**: Tombol untuk mereset semua input dan output.
   - **Check Saved Files**: Tombol untuk membuka direktori output.

6. **Progress Log**:
   - Menampilkan status proses analisis data.

7. **Plot Dashboard**:
   - Menampilkan visualisasi hasil analisis curah hujan.

---

#### **4. Cara Menggunakan Program**

1. **Membuka File CSV**:
   - Klik tombol **Load CSV File** untuk memilih file CSV yang berisi data curah hujan.
   - Pastikan file CSV memiliki kolom `Time` dan `Rain` (curah hujan).

2. **Mengatur Parameter**:
   - Pilih **Threshold Type** (nilai absolut atau persentil).
   - Masukkan nilai **Threshold Value** sesuai dengan jenis threshold yang dipilih.
   - Masukkan nilai **Minimum Hourly Rainfall** (curah hujan minimum per jam yang akan diikutsertakan).

3. **Memilih Direktori Output**:
   - Klik tombol **Browse** untuk memilih direktori tempat hasil analisis akan disimpan.

4. **Memulai Proses Analisis**:
   - Klik tombol **Process Data** untuk memulai analisis data.
   - Proses akan ditampilkan di **Progress Bar**.

5. **Melihat Hasil**:
   - Setelah proses selesai, hasil analisis akan disimpan di direktori output yang telah dipilih.
   - Klik tombol **Check Saved Files** untuk membuka direktori output.
   - Hasil analisis meliputi:
     - File CSV yang berisi data curah hujan yang telah diproses.
     - Visualisasi distribusi curah hujan dalam bentuk grafik.

6. **Melihat Plot**:
   - Setelah proses selesai, Anda dapat melihat plot distribusi curah hujan dengan memilih menu **Plot** > **Huff quarter**.

7. **Reset**:
   - Jika ingin memulai analisis baru, klik tombol **Reset** untuk mereset semua input dan output.

---

#### **5. Contoh Format File CSV**
Program ini menerima file CSV dengan format default sebagai berikut, yakni dengan hanya dua kolom berisi waktu dan nilai curah hujan jam-jaman:

- **Default**:
  ```
  Time;Rain(mm)
  1/1/2001 0:00;0.5
  1/1/2001 1:00;1.2
  1/1/2001 2:00;0.8
  ...
  ```

---

#### **6. Penjelasan Output**
1. **File CSV**:
   - `VRain_[Date]-[Station]_selected.csv`: Berisi data curah hujan yang telah dipilih berdasarkan threshold.
   - `VRain_[Date]-[Station]_pivot.csv`: Berisi data curah hujan yang telah di-pivot.
   - `VRain_[Date]-[Station]_duration.csv`: Berisi durasi kejadian hujan.
   - `VRain_[Date]-[Station]_cumulated-[Duration].csv`: Berisi data curah hujan yang telah diakumulasi.

2. **Plot**:
   - `VRain_[Date]-[Station]_duration.png`: Grafik durasi kejadian hujan.
   - `VRain_[Date]-[Station]_histogram-duration.png`: Histogram durasi kejadian hujan.
   - `VRain_[Date]-[Station]_mean-duration-[Duration]-hour.png`: Grafik distribusi curah hujan.

---

#### **7. Troubleshooting**
- **Error saat memuat file CSV**: Pastikan file CSV memiliki format yang benar dan kolom `Time` serta `Rain` tersedia.
- **Error saat memproses data**: Pastikan nilai threshold dan parameter lainnya telah diisi dengan benar.
- **Plot tidak muncul**: Pastikan proses analisis telah selesai dan data yang diproses valid.

---

#### **8. Lisensi**
Program ini dilisensikan di bawah **Perjanjian Lisensi Perangkat Lunak**. Anda diperbolehkan menggunakan program ini untuk keperluan edukasi atau komersial, namun tidak diperbolehkan mendistribusikan, memodifikasi, atau menjual program ini tanpa izin.

Untuk informasi lebih lanjut, hubungi:  
**Vempi Satriya Adi Hendrawan**  
Email: [vempi@ugm.ac.id](mailto:vempi@ugm.ac.id)  
Website: [vempi.staff.ugm.ac.id](https://vempi.staff.ugm.ac.id)

---

#### **9. Penutup**
Program **VRainStorm** diharapkan dapat membantu Anda dalam menganalisis durasi dan distribusi curah hujan dengan mudah dan efisien. Jika Anda memiliki pertanyaan atau masukan, jangan ragu untuk menghubungi pengembang.

**Terima kasih telah menggunakan VRainStorm!**
