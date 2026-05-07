# Panduan Penggunaan Demo Data (Data Dummy)

File demo data (`demo/demo_data.xml`) dibuat secara khusus untuk mempermudah Anda melakukan **pengujian antarmuka (UI Testing)** tanpa harus menginput data secara manual satu per satu. 

Berikut adalah panduan lengkap cara memuat dan menggunakan data dummy tersebut.

---

## 1. Apa Isi dari Demo Data?
Data dummy ini akan secara otomatis memasukkan *record* berikut ke dalam database Odoo Anda:
1. **2 User Asesor**: `Asesor Joko` dan `Asesor Rina` (Password login: `admin`).
2. **25 Partner Asesi**: Dinamai secara berurutan `Asesi 01` hingga `Asesi 25`.
3. **1 Jadwal Ujian**: Bernama `"Ujian Web Developer (Skenario 25 Asesi)"` yang sudah ditautkan secara langsung dengan ke-25 Asesi di atas.

---

## 2. Cara Memuat (Load) Demo Data ke Odoo
Secara default, file demo berada di blok `'demo': [...]` pada file `__manifest__.py`. Odoo **hanya akan memuat file ini** jika database Anda dibuat dengan mencentang opsi **"Load Demo Data"**.

### Skenario A: Menggunakan Database "Load Demo Data"
Jika Anda sedang men-develop di database test (yang dicentang load demo datanya saat pembuatan database), Anda cukup melakukan upgrade modul:
```bash
# Buka terminal di folder project3-odoo-template dan jalankan:
docker compose exec odoo-web odoo -u plugins_manajement_asesor -d odoo-db --stop-after-init
```

### Skenario B: Paksa Memuat Data Tanpa Database Demo
Jika Anda menggunakan database produksi atau tidak mencentang opsi demo data, Anda dapat **memaksa** Odoo memuat data ini dengan cara memindahkannya ke blok `'data'` pada `__manifest__.py`:
1. Buka file `__manifest__.py`.
2. Pindahkan baris `'demo/demo_data.xml'` dari dalam `demo: [...]` ke bagian bawah dalam `data: [...]`.
3. Simpan file, lalu upgrade modul Anda via Terminal Odoo atau via menu Apps di browser Odoo.

---

## 3. Cara Menguji Aturan "1 Asesor Maksimal 10 Asesi"
Setelah demo data berhasil masuk ke sistem, ikuti langkah berikut dari browser Anda:

1. Login sebagai **Admin LSP**.
2. Masuk ke modul/menu **Penugasan Asesor / Jadwal Ujian**.
3. Buka jadwal ujian bernama **"Ujian Web Developer (Skenario 25 Asesi)"**.
4. Di bagian asesi, Anda akan melihat ada 25 asesi yang sudah disematkan.
5. Buat **Penugasan Asesor** untuk jadwal tersebut.
6. **Uji Pemblokiran:** Cobalah untuk hanya memasukkan 1 Asesor (misalnya Asesor Joko).
7. **Verifikasi:** Saat Anda klik tombol **Distribusi & Validasi Otomatis** (atau saat menyimpan), sistem **wajib menolak dan mengeluarkan Alert Error** karena 1 asesor (batas 10 asesi) tidak sebanding dengan total 25 asesi.
8. **Uji Keberhasilan:** Tambahkan `Asesor Rina` (total 2 asesor, batas 20) — sistem masih akan menolak. Anda harus membuat satu asesor tambahan dari UI, menjadikannya 3 asesor (batas 30), lalu distribusikan. Sistem akan membagi 25 asesi tersebut secara merata ke 3 asesor tersebut tanpa ada yang melebihi 10 asesi per asesor.

---

## 4. Keuntungan Menggunakan Cara Ini
- Menghemat waktu penginputan (klik-klik UI yang repetitif).
- Jika database Anda *crash* atau ter-reset, data dummy akan kembali ada saat modul di-install ulang.
- Membantu developer lain dalam tim untuk memvalidasi algoritma `action_distribusi_otomatis` tanpa bingung mencari data yang cocok untuk test.

---

## 5. Cara Menghapus Demo Data
Jika Anda sudah selesai melakukan pengujian dan ingin membersihkan database dari data dummy ini, Anda bisa menghapusnya dengan sangat mudah melalui antarmuka web Odoo:

1. **Menghapus Jadwal Ujian:**
   - Buka menu **LSP > Jadwal Ujian** (atau **Penugasan Asesor > Jadwal Ujian**).
   - Centang jadwal "Ujian Web Developer (Skenario 25 Asesi)".
   - Klik tombol **Action (Tindakan) > Delete (Hapus)**.

2. **Menghapus Partner (Asesi):**
   - Buka aplikasi **Contacts**.
   - Cari kata kunci `Asesi` di kolom pencarian.
   - Klik kotak centang di kiri atas (di sebelah kolom nama) untuk **memilih semua** 25 asesi tersebut.
   - Klik **Action > Delete**.

3. **Menghapus User (Asesor):**
   - Masuk ke mode Developer (opsional tapi disarankan).
   - Buka **Settings > Users & Companies > Users**.
   - Cari `Asesor Joko` dan `Asesor Rina`.
   - Centang keduanya dan klik **Action > Delete**.

Odoo secara otomatis akan menghapus semua penugasan (lines) yang berkaitan saat jadwal ujian tersebut Anda hapus, jadi proses pembersihan sangat cepat dan aman.

---

## 6. Mencegah Data Dummy Muncul Lagi di Masa Depan (Production)
Jika database lokal Anda sebelumnya menolak memuat data demo (karena tidak dicentang saat pembuatan database), Anda mungkin telah memindahkan rujukan file `demo_data.xml` ini secara "paksa" ke dalam blok `data:` biasa di file `__manifest__.py`.

Jika suatu saat modul ini akan **dirilis (production)** atau diinstal di database klien yang baru, kita harus mengembalikan file ini ke posisi aslinya agar asesi dummy ini tidak ikut ter-install ke sistem asli mereka.

**Langkah pengembaliannya:**
1. Buka file `__manifest__.py`.
2. Pindahkan baris `'demo/demo_data.xml',` dari dalam blok `'data': [...]` ke dalam blok `'demo': [...]` (jika blok demo belum ada, silakan buat list baru).
3. Simpan file tersebut.

Dengan cara ini, Anda tetap bisa menguji data yang sudah terlanjur ada di database saat ini, tetapi sistem Odoo tidak akan menambahkannya lagi pada instalasi database berikutnya, kecuali user secara eksplisit mencentang kotak "Load demo data".
