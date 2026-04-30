# 📦 README INSTALASI — Modul LSP Penugasan Asesor

## Informasi Modul

| Item | Detail |
|------|--------|
| **Nama Teknis** | `lsp_penugasan_asesor` |
| **Versi** | 19.0.1.0.0 |
| **Kategori** | LSP/Sertifikasi |
| **Lisensi** | LGPL-3 |
| **Author** | Tim Manajemen Asesor — D4-3B POLBAN |

---

## 🔧 Langkah Instalasi ke Odoo 19

### Prasyarat

- Odoo 19 Community atau Enterprise sudah terinstall dan berjalan.
- PostgreSQL aktif dan terhubung ke Odoo.
- Modul bawaan `mail` dan `portal` sudah terinstall (biasanya sudah default).

### Langkah-langkah

1. **Copy folder modul** ke direktori `addons` Odoo Anda:

   ```bash
   cp -r plugins_manajement_asesor /path/to/odoo19/addons/
   ```

   Atau jika menggunakan Docker, pastikan folder ini di-mount ke container di path addons.

2. **Tambahkan path addons** ke konfigurasi Odoo (jika belum):

   Edit file `odoo.conf`:
   ```ini
   [options]
   addons_path = /path/to/odoo19/addons,/path/to/custom-addons
   ```

3. **Restart Odoo server**:

   ```bash
   # Non-Docker
   ./odoo-bin -c odoo.conf

   # Docker Compose
   docker-compose restart odoo
   ```

4. **Update daftar modul** di Odoo:

   - Login ke Odoo sebagai Administrator
   - Aktifkan **Developer Mode**: `Settings → General Settings → Developer Tools → Activate Developer Mode`
   - Buka menu `Apps`
   - Klik tombol **Update Apps List** (ikon refresh / menu hamburger)
   - Konfirmasi update

5. **Install modul**:

   - Di menu `Apps`, cari **"LSP - Penugasan Asesor"**
   - Klik tombol **Install**

6. **Verifikasi instalasi**:

   - Pastikan menu **LSP → Penugasan Asesor** muncul di navigation bar
   - Pastikan sub-menu **Semua Penugasan** dan **Jadwal Ujian** tersedia

### Install via Command Line

```bash
# Install modul langsung
./odoo-bin -d <nama_database> -i lsp_penugasan_asesor --stop-after-init

# Update modul setelah ada perubahan kode
./odoo-bin -d <nama_database> -u lsp_penugasan_asesor --stop-after-init
```

---

## 🧪 Cara Menjalankan Unit Test

### Via Command Line

```bash
# Jalankan semua test modul ini
./odoo-bin -d <nama_database> -i lsp_penugasan_asesor --test-enable --test-tags lsp_penugasan_asesor --stop-after-init

# Jalankan test spesifik
./odoo-bin -d <nama_database> -i lsp_penugasan_asesor --test-enable --test-tags post_install --stop-after-init
```

### Daftar Test yang Tersedia

| File | Test Cases | Deskripsi |
|------|-----------|-----------|
| `tests/test_penugasan_asesor.py` | 8 test cases | Validasi rasio 1:10, duplikasi asesor, penguncian/pembukaan kunci |
| `tests/test_distribusi_otomatis.py` | 5 test cases | Distribusi round-robin: merata genap/ganjil, redistribusi, kelengkapan |

### Detail Test Cases

**test_penugasan_asesor.py:**
1. `test_rasio_valid_batas_maksimal` — 10 asesi + 1 asesor → berhasil
2. `test_rasio_overload_raise_error` — 11 asesi ke 1 asesor → ValidationError
3. `test_kurang_asesor_blokir_distribusi` — 20 asesi + 1 asesor → UserError
4. `test_cukup_asesor_distribusi_berhasil` — 20 asesi + 2 asesor → berhasil
5. `test_asesor_duplikat_raise_error` — Asesor sama 2x → error
6. `test_kunci_saat_tidak_valid_raise_error` — Kunci saat kuota kurang → UserError
7. `test_kunci_berhasil_dan_state_berubah` — Kunci valid → state 'dikunci'
8. `test_field_readonly_setelah_dikunci` — Verifikasi state setelah kunci & buka kunci

**test_distribusi_otomatis.py:**
1. `test_distribusi_merata_genap` — 20 asesi ÷ 2 asesor = 10 masing-masing
2. `test_distribusi_merata_ganjil` — 15 asesi ÷ 2 asesor, max ≤ 10
3. `test_distribusi_satu_asesor_sedikit_asesi` — 8 asesi → 1 asesor
4. `test_distribusi_ulang_tidak_duplikat` — Distribusi 2x, total tetap sama
5. `test_semua_asesi_tertugaskan` — Tidak ada asesi yang terlewat

---

## 👥 Daftar Group User yang Perlu Dikonfigurasi

Setelah instalasi, konfigurasikan group berikut untuk setiap user yang terlibat:

### 1. Admin LSP (`group_admin_lsp`)

| Hak Akses | Keterangan |
|-----------|------------|
| **Read** | ✅ Semua data penugasan, jadwal, line |
| **Write** | ✅ Membuat & mengedit penugasan |
| **Create** | ✅ Membuat penugasan baru, menambah asesor |
| **Delete** | ✅ Menghapus penugasan |
| **Khusus** | ✅ Mengunci & membuka kunci penugasan |

**Cara assign:**
1. Buka `Settings → Users & Companies → Users`
2. Pilih user yang akan dijadikan Admin LSP
3. Pada bagian **LSP**, set ke **Admin LSP**

### 2. Asesor LSP (`group_asesor`)

| Hak Akses | Keterangan |
|-----------|------------|
| **Read** | ✅ Hanya penugasan & line miliknya sendiri |
| **Write** | ❌ |
| **Create** | ❌ |
| **Delete** | ❌ |
| **Portal** | ✅ Melihat penugasan via `/my/penugasan` |

**Cara assign:**
1. Buka `Settings → Users & Companies → Users`
2. Pilih user yang akan dijadikan Asesor
3. Pada bagian **LSP**, set ke **Asesor LSP**

> ⚠️ **Penting:** Group Admin LSP secara otomatis mewarisi (implied) group Asesor LSP. Jadi Admin tidak perlu di-assign ke kedua group.

---

## 🔗 Catatan Dependensi dengan Modul Lain

### Dependensi Wajib (sudah terinstall di Odoo default)

| Modul | Kegunaan |
|-------|----------|
| `base` | Model dasar Odoo (`res.users`, `res.partner`) |
| `mail` | Chatter, tracking, notifikasi email, mail template |
| `portal` | Portal website untuk Asesor (`/my/penugasan`) |

### Dependensi Opsional (Integrasi FASE 2)

Modul ini dirancang untuk bisa berdiri sendiri (FASE 1). Ketika modul LSP lain sudah siap, lakukan integrasi sebagai berikut:

| Modul Tujuan | Perubahan yang Diperlukan |
|--------------|--------------------------|
| `lsp_pengajuan_asesi` | Ganti `res.partner` di `asesi_ids` dengan model `lsp.asesi`. Hapus tag `# TODO: replace with lsp.asesi` di kode. |
| `lsp_penjadwalan_ujian` | Ubah `lsp.jadwal.ujian` dari `_name` menjadi `_inherit` (extend model dari modul jadwal). Hapus definisi model minimal di `models/lsp_jadwal_ujian.py`. |
| `lsp_skema_sertifikasi` | Ubah field `skema_id` dari `Char` menjadi `Many2one` ke `lsp.skema.sertifikasi`. |

### Cara Integrasi FASE 2

1. Tambahkan nama modul ke `depends` di `__manifest__.py`:
   ```python
   'depends': [
       'base',
       'mail',
       'portal',
       'lsp_pengajuan_asesi',       # Uncomment setelah modul siap
       'lsp_penjadwalan_ujian',     # Uncomment setelah modul siap
   ],
   ```

2. Update model sesuai catatan `# TODO` di file Python.

3. Jalankan update modul:
   ```bash
   ./odoo-bin -d <nama_database> -u lsp_penugasan_asesor --stop-after-init
   ```

---

## 📂 Struktur File Modul

```
plugins_manajement_asesor/
├── __init__.py
├── __manifest__.py
├── README.md
├── README_INSTALASI.md
├── konteks.md
│
├── models/
│   ├── __init__.py
│   ├── lsp_jadwal_ujian.py
│   ├── lsp_penugasan_asesor.py
│   └── lsp_penugasan_line.py
│
├── wizards/
│   ├── __init__.py
│   └── wizard_tambah_asesor.py
│
├── views/
│   ├── menu_views.xml
│   ├── lsp_jadwal_ujian_views.xml
│   ├── lsp_penugasan_asesor_views.xml
│   ├── lsp_penugasan_line_views.xml
│   ├── wizard_tambah_asesor_views.xml
│   └── portal_templates.xml
│
├── security/
│   ├── lsp_penugasan_security.xml
│   └── ir.model.access.csv
│
├── data/
│   └── lsp_penugasan_data.xml
│
├── controllers/
│   ├── __init__.py
│   └── portal_penugasan.py
│
├── static/
│   └── description/
│       └── icon.png
│
└── tests/
    ├── __init__.py
    ├── test_penugasan_asesor.py
    └── test_distribusi_otomatis.py
```

---

## ⚡ Quick Start

```bash
# 1. Copy modul ke addons
cp -r plugins_manajement_asesor /path/to/odoo/addons/

# 2. Install
./odoo-bin -d mydb -i lsp_penugasan_asesor --stop-after-init

# 3. Jalankan test
./odoo-bin -d mydb --test-enable --test-tags post_install -i lsp_penugasan_asesor --stop-after-init

# 4. Jalankan server
./odoo-bin -d mydb
```

---

*Dokumen ini adalah bagian dari Modul LSP Penugasan Asesor — D4-3B POLBAN 2026*
