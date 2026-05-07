# LSP - Manajemen Penugasan Asesor

![Odoo Version](https://img.shields.io/badge/Odoo-19.0-blue.svg)
![License](https://img.shields.io/badge/license-LGPL--3-green.svg)
![Status](https://img.shields.io/badge/status-Stable-success.svg)

Modul **plugins_manajement_asesor** adalah esktensi custom Odoo 19 untuk Sistem ERP Lembaga Sertifikasi Profesi (LSP). Modul ini difokuskan pada pengelolaan, pendistribusian, dan validasi penugasan Asesor (penguji) ke Asesi (peserta sertifikasi) secara otomatis berdasarkan rasio kapasitas pengujian. 

---

## 📑 Daftar Isi
- [Fitur Utama](#-fitur-utama)
- [Prasyarat](#-prasyarat)
- [Instalasi](#-instalasi)
- [Alur Kerja (Workflow)](#-alur-kerja-workflow)
- [Penggunaan](#-penggunaan)
- [Batasan \& Known Issues](#-batasan--known-issues)
- [Kontribusi](#-kontribusi)
- [Kredit](#-kredit)
- [Lisensi](#-lisensi)

## 📚 Dokumentasi Lengkap
- [Panduan Instalasi & Pengujian](INSTALLATION.md)
- [Panduan Penggunaan Demo Data](DEMO_DATA.md)
- [Konteks & Aturan Bisnis](CONTEXT.md)
- [Catatan Perubahan](CHANGELOG.md)

## ✨ Fitur Utama

- **Distribusi Otomatis (Round-Robin)**: Mendistribusikan Asesi kepada Asesor secara otomatis, adil, dan merata untuk sebuah jadwal pengujian.
- **Validasi Rasio Kuota**: Sistem akan memvalidasi secara ketat dan mengatur beban Asesor, di mana **1 Asesor maksimal menangani 10 Asesi** (`BR-01`).
- **Pencegahan Overload**: Sistem akan menahan proses validasi dan penguncian jika jumlah Asesor kurang dari rasio yang dibutuhkan (`BR-02`).
- **Sistem Penguncian (Locking)**: Data penugasan yang telah divalidasi akan dikunci (Read-Only) sebagai *audit trail* (`BR-04`). Hanya Admin LSP yang bisa membuka kuncinya.
- **Notifikasi Otomatis**: Mendukung pengiriman form penugasan terenkripsi ke email/dashboard portal internal Asesor.
- **Integrasi Portal**: Menyediakan *QWeb Template* Portal yang memungkinkan Asesor melihat beban uji secara mandiri dari portal luar Odoo.

## 🛠️ Prasyarat

- **Odoo 19.0** (Community atau Enterprise)
- Modul Dasar Odoo Terkait:
  - `base`
  - `mail` (untuk fitur pengiriman notifikasi/log)
  - `portal` (untuk akses Asesor eksternal)
- Ketergantungan Ekosistem LSP (Opsial/Sesuai Konteks):
  - Sistem Penjadwalan Ujian 

## 📥 Instalasi

1. Pastikan Anda masuk ke direktori *addons* folder Odoo/Docker Anda.
2. Clone atau Copy folder modul `plugins_manajement_asesor` ke dalam direktori tersebut.
3. Restart *Odoo Server* Anda (misalnya dengan Docker):
   ```bash
   docker-compose restart odoo-web
   ```
4. Masuk ke environtment Odoo, aktifkan **Developer Mode**.
5. Buka Menu **Apps** > Klik **Update Apps List**.
6. Cari `LSP - Penugasan Asesor` lalu klik **Activate** / **Install**.

*(Untuk detail setup instalasi environment bisa dilihat pada referensi [INSTALLATION.md](INSTALLATION.md))*

## 🔄 Alur Kerja (Workflow)

```text
[ Admin LSP ] Pilih Skema & Jadwal Ujian
      ↓
[ Admin LSP ] Tambahkan Asesor ke dalam Jadwal
      ↓
[  Sistem   ] Validasi Kecukupan Asesor (Rasio Maks 1:10)
      ↓
[  Sistem   ] >> JIKA KURANG: Muncul Peringatan, Minta Tambah Asesor
[  Sistem   ] >> JIKA CUKUP: Distribusi Asesi secara otomatis & merata
      ↓
[ Admin LSP ] Kunci Penugasan (Lock Record)
      ↓
[  Asesor   ] Menerima Pemberitahuan & Melaksanakan Penilaian
```

## 💻 Penggunaan

1. Login sebagai **Admin LSP**.
2. Masuk ke menu modul **LSP**.
3. Buat penugasan baru. Pilih **Jadwal Ujian** yang masih aktif.
4. Klik **Tambah Asesor**, dan pilih asesor melalui *wizard* (popup form) yang disediakan hingga *Jumlah Asesor* memenuhi syarat minimal di tabel halaman.
5. Klik **Distribusi & Validasi Otomatis** untuk membagi asesi secara rotasi (round-robin) ke tiap asesor yang dipilih.
6. Simpan dokumen, kemudian pilih aksi **Kunci Penugasan** untuk mem-validasi final rekaman agar tidak dapat diubah kembali.
  
## 🐞 Batasan & Known Issues
- Sesuai standarisasi perombakan XML pada Odoo 19, validasi filter data Asesor berdasarkan Hak Akses (Group ID) dipindah full ke area domain Lambda Python. Tidak menggunakan inline XML validation.
- Saat mode Draft, `Asesi` yang baru masuk akan di-refresh paksa susunannnya oleh sistem per _Distribusi Ulang_.

## 🤝 Kontribusi

*Pull request* dipersilahkan. Untuk perubahan model/relasi Odoo besar, harap mendiskusikannya terlebih dahulu sebelum eksekusi. Pastikan untuk selalu lulus unit test yang disiapkan:

```bash
# Perintah mengeksekusi test runner bawaan
docker-compose run --rm odoo-web odoo -i plugins_manajement_asesor --test-enable --stop-after-init
```

## 👨‍💻 Kredit

Dikembangkan oleh **Muhammad Adhyaksa Fadillah (NIM: 231524051)** dan **Mohammad Amadeus Andhika Fadhil (NIM: 231524050)** dari kelas **D4-3B POLBAN**. Bagian dari standarisasi sistem ERP Lembaga Sertifikasi Profesi.

## 📄 Lisensi

Didistribusikan di bawah lisensi **LGPL-3.0**. Lihat file Odoo manifests untuk lisensi selengkapnya.
