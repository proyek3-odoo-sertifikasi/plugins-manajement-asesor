# AGENT PROMPT: PENGEMBANGAN MODUL CUSTOM PENUGASAN ASESOR
## Sistem ERP LSP Berbasis Odoo 19

---

## 🎯 KONTEKS PROYEK

Kamu adalah senior Odoo developer yang bertugas membangun **Modul Custom Penugasan Asesor** untuk sistem Lembaga Sertifikasi Profesi (LSP) berbasis **Odoo 19 (versi terbaru)**. Sistem ini digunakan oleh SMK yang bertindak sebagai penyelenggara sertifikasi kompetensi berstandar BNSP (Badan Nasional Sertifikasi Profesi).

Modul ini adalah bagian dari ekosistem 6 modul custom LSP. Modul ini bergantung pada data jadwal ujian dan data asesi terdaftar yang sudah ada di sistem.

---

## 📋 DESKRIPSI MODUL

**Nama Modul:** `plugins_manajement_asesor`
**Tujuan:** Mengelola pemetaan tanggung jawab penilaian antara Asesor (penguji) dengan Asesi (peserta ujian) secara otomatis, dengan validasi rasio kuota **maksimal 1 Asesor untuk 10 Asesi** dalam satu jadwal ujian.

---

## 🔁 ALUR PROSES BISNIS (BPMN) YANG HARUS DIIMPLEMENTASIKAN

Implementasi harus mengikuti alur berikut secara ketat:

### Aktor yang Terlibat:
1. **Admin LSP** — inisiator penugasan
2. **Sistem (Odoo)** — validator otomatis & distributor
3. **Asesor** — penerima penugasan

### Tahapan Alur:

```
[START]
  │
  ▼
[Admin LSP] Pilih Skema Sertifikasi & Jadwal Ujian
  │
  ▼
[Admin LSP] Pilih & Tambahkan Asesor ke Jadwal
  │
  ▼
[Sistem] Validasi Kecukupan Asesor dengan Jumlah Asesi yang Ada
  │
  ▼
[Gateway] Jumlah Asesor Cukup? (rasio maks 1:10)
  ├── TIDAK → Kembali ke [Admin LSP] Tambahkan Asesor Lagi
  └── YA
       │
       ▼
      [Sistem] Distribusi Asesi ke Asesor secara Otomatis & Merata
       │
       ▼
      [Sistem] Simpan & Kunci Penugasan (Lock / Read-Only)
       │
       ▼
      [Sistem] Kirim Notifikasi Penugasan ke setiap Asesor
       │
       ▼
      [Asesor] Terima Notifikasi Jadwal & Asesi
       │
       ▼
      [Asesor] Cek Penugasan di Portal/Dashboard
       │
       ▼
      [Asesor] Lakukan Penilaian
       │
       ▼
     [END]
```

### Aturan Bisnis Mutlak (WAJIB Diimplementasikan):
- `BR-01`: Satu Asesor **MAKSIMAL** menangani **10 Asesi** dalam satu jadwal ujian.
- `BR-02`: Sistem **HARUS memblokir** penambahan penugasan jika rasio kapasitas terlampaui (gunakan `system constraint` di model).
- `BR-03`: Distribusi Asesi ke Asesor dilakukan **otomatis dan merata** (round-robin atau pembagian seimbang).
- `BR-04`: Setelah penugasan dikunci (`locked`), **tidak ada perubahan** yang dapat dilakukan oleh user manapun kecuali Admin dengan aksi eksplisit buka kunci.
- `BR-05`: Notifikasi penugasan **wajib terkirim** ke email/internal message setiap Asesor yang ditugaskan.
- `BR-06`: Satu Asesor yang sama tidak boleh ditugaskan duplikat pada jadwal yang sama.

---

## 🗂️ STRUKTUR FOLDER & FILE (STANDAR ODOO 19)

Buat struktur direktori persis seperti berikut. **Jangan ada file yang hilang.**

> ⚠️ **Odoo 19 tidak lagi menggunakan folder `static/src/js` dengan widget lama. Gunakan OWL (Owl Component Framework) untuk semua komponen JS custom. Pastikan semua aset JS/CSS didaftarkan via `assets` di `__manifest__.py`, bukan via `web.assets_backend` di XML.**

```
plugins_manajement_asesor/
├── __init__.py
├── __manifest__.py
├── konteks.md                            # Dokumentasi konteks modul (referensi internal tim)
├── README_INSTALASI.md                   # Panduan instalasi & konfigurasi
├── README.md                             # Dokumentasi umum modul
├── .gitkeep
│
├── models/
│   ├── __init__.py
│   ├── lsp_jadwal_ujian.py               # Model jadwal ujian (inherit/extend jika sudah ada, atau buat baru)
│   ├── lsp_penugasan_asesor.py           # Model utama penugasan (header)
│   └── lsp_penugasan_line.py             # Model detail baris penugasan (Asesor ↔ Asesi)
│
├── wizards/
│   ├── __init__.py
│   └── wizard_tambah_asesor.py           # Wizard untuk Admin menambah Asesor ke jadwal
│
├── views/
│   ├── lsp_penugasan_asesor_views.xml    # Form, list, search view penugasan
│   ├── lsp_penugasan_line_views.xml      # View baris detail asesor-asesi
│   ├── lsp_jadwal_ujian_views.xml        # View jadwal (tambahkan tombol penugasan)
│   ├── wizard_tambah_asesor_views.xml    # View wizard
│   ├── portal_templates.xml              # QWeb template untuk portal Asesor
│   └── menu_views.xml                    # Definisi menu navigasi
│
├── security/
│   ├── ir.model.access.csv               # Hak akses model
│   └── lsp_penugasan_security.xml        # Record rules & group definition
│
├── data/
│   └── lsp_penugasan_data.xml            # Mail template, sequence & data master awal
│
├── controllers/
│   ├── __init__.py
│   └── portal_penugasan.py               # Controller portal Asesor (cek penugasan via web)
│
├── static/
│   └── description/
│       └── icon.png                      # Icon modul (gunakan placeholder 1x1 px jika perlu)
│
└── tests/
    ├── __init__.py
    ├── test_penugasan_asesor.py           # Unit test validasi rasio 1:10
    └── test_distribusi_otomatis.py        # Unit test distribusi round-robin
```

---

## 📄 SPESIFIKASI DETAIL SETIAP FILE

### 1. `__manifest__.py`

```python
{
    'name': 'LSP - Penugasan Asesor',
    'version': '19.0.1.0.0',
    'category': 'LSP/Sertifikasi',
    'summary': 'Modul penugasan asesor ke asesi dengan validasi rasio kuota otomatis untuk LSP',
    'description': """
        Modul ini mengelola:
        - Pemetaan Asesor ke Asesi secara otomatis dan merata
        - Validasi rasio kuota (maks 1 Asesor : 10 Asesi)
        - Penguncian data penugasan (audit trail)
        - Notifikasi otomatis ke Asesor
        - Portal Asesor untuk melihat penugasan
    """,
    'author': 'Tim Manajemen Asesor - D4-3B POLBAN',
    'depends': [
        'base',
        'mail',
        'portal',
        # Tambahkan 'lsp_pengajuan_asesi' jika modul tersebut sudah siap
        # Tambahkan 'lsp_penjadwalan_ujian' jika modul jadwal sudah siap
    ],
    'data': [
        'security/lsp_penugasan_security.xml',
        'security/ir.model.access.csv',
        'data/lsp_penugasan_data.xml',
        'views/menu_views.xml',
        'views/lsp_jadwal_ujian_views.xml',
        'views/lsp_penugasan_asesor_views.xml',
        'views/lsp_penugasan_line_views.xml',
        'views/wizard_tambah_asesor_views.xml',
        'views/portal_templates.xml',
    ],
    # Odoo 19: tidak ada lagi 'qweb' key terpisah, semua template masuk ke 'data'
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    # Odoo 19: tambahkan cloc_exclude jika ada file yang tidak perlu dihitung
}
```

---

### 2. `models/__init__.py`

```python
from . import lsp_jadwal_ujian
from . import lsp_penugasan_asesor
from . import lsp_penugasan_line
```

---

### 3. `models/lsp_jadwal_ujian.py`

Buat model jadwal ujian sebagai referensi konteks penugasan. **Jika modul penjadwalan sudah ada, gunakan `_inherit` bukan `_name` baru.**

Field-field wajib yang harus ada di model ini:
- `name`: Char, auto-generate sequence format `JDW/YYYY/MM/XXX`, `copy=False`, readonly di view
- `skema_id`: Many2one ke `lsp.skema.sertifikasi` (atau Char sementara jika modul belum ada)
- `tanggal_mulai`: Datetime (required)
- `tanggal_selesai`: Datetime (required)
- `ruangan`: Char
- `state`: Selection `[('draft','Draft'),('terjadwal','Terjadwal'),('penugasan','Proses Penugasan'),('berlangsung','Berlangsung'),('selesai','Selesai')]`
- `asesi_ids`: Many2many ke `res.partner` (dengan domain yang memfilter hanya asesi yang sudah disetujui)
- `penugasan_ids`: One2many ke `lsp.penugasan.asesor`
- `jumlah_asesi`: Integer (computed, count dari `asesi_ids`)
- `jumlah_asesor_dibutuhkan`: Integer (computed: `math.ceil(jumlah_asesi / 10)`)
- `jumlah_asesor_tersedia`: Integer (computed: count asesor unik dari `penugasan_ids.penugasan_line_ids`)
- `is_kuota_cukup`: Boolean (computed: `jumlah_asesor_tersedia >= jumlah_asesor_dibutuhkan`)

Tambahkan tombol `action_set_terjadwal` untuk mengubah status dari `'draft'` menjadi `'terjadwal'`.
Tambahkan button `action_mulai_penugasan` yang aktif saat `state in ('terjadwal', 'penugasan')`, yang membuat record `lsp.penugasan.asesor` baru terkait jadwal ini dan mengubah state ke `'penugasan'`.

---

### 4. `models/lsp_penugasan_asesor.py`

Model header penugasan (satu record per jadwal):

```
Model name : lsp.penugasan.asesor
_inherit   : ['mail.thread', 'mail.activity.mixin']  # WAJIB untuk notifikasi & chatter
```

> ⚠️ **Odoo 19**: Import menggunakan `from odoo import api, fields, models, _` — tidak ada perubahan di sini, tetapi pastikan menggunakan `fields.Html` jika perlu rich text, bukan `fields.Text` dengan widget html lama.

**Fields wajib:**
- `name`: Char, auto-generate sequence format `PENUGASAN/YYYY/MM/XXX`, `copy=False`
- `jadwal_id`: Many2one `lsp.jadwal.ujian`, required, `ondelete='restrict'`, `tracking=True`
- `skema_display`: Char, related dari `jadwal_id.skema_id.name`, readonly
- `tanggal_penugasan`: Date, default=`fields.Date.today`
- `state`: Selection `[('draft','Draft'),('dikunci','Dikunci')]`, default=`'draft'`, `tracking=True`, `copy=False`
- `penugasan_line_ids`: One2many ke `lsp.penugasan.line`, field `penugasan_id`
- `total_asesor`: Integer, computed dari count `penugasan_line_ids`
- `total_asesi`: Integer, related/computed dari `jadwal_id.jumlah_asesi`
- `jumlah_asesor_dibutuhkan`: Integer, computed `math.ceil(total_asesi / 10)`
- `is_valid`: Boolean, computed: `total_asesor >= jumlah_asesor_dibutuhkan`
- `notes`: Text

**Methods wajib:**

`action_distribusi_otomatis(self)`:
- `self.ensure_one()`
- Ambil semua asesi dari `jadwal_id.asesi_ids`
- Ambil semua asesor dari `penugasan_line_ids` yang sudah ditambahkan
- Validasi: jika `len(asesor_list) < math.ceil(len(asesi_list) / 10)` → raise `UserError` dengan pesan yang menjelaskan berapa asesor yang masih dibutuhkan
- **Algoritma distribusi round-robin**: bagi asesi merata ke setiap asesor, tidak boleh ada yang melebihi 10
- Hapus dulu semua `asesi_ids` dari setiap line, kemudian isi ulang hasil distribusi
- Tampilkan pesan sukses via `self.message_post()`

`action_kunci_penugasan(self)`:
- `self.ensure_one()`
- Validasi `is_valid == True` dulu, jika tidak raise `UserError`
- Set `state = 'dikunci'`
- Kirim notifikasi ke semua asesor: loop `penugasan_line_ids`, kirim `mail_template` ke `line.asesor_id.partner_id`
- `self.message_post()` dengan body: "Penugasan dikunci oleh {user} pada {datetime}"

`action_buka_kunci(self)`:
- Hanya bisa dipanggil oleh group `plugins_manajement_asesor.group_admin_lsp`
- Set `state = 'draft'`
- `self.message_post()` log pembukaan kunci

**SQL Constraint:**
```python
_sql_constraints = [
    ('unique_jadwal_penugasan', 'UNIQUE(jadwal_id)',
     'Sudah ada penugasan untuk jadwal ini. Satu jadwal hanya boleh memiliki satu record penugasan.')
]
```

---

### 5. `models/lsp_penugasan_line.py`

Model detail baris (satu asesor + daftar asesinya):

```
Model name : lsp.penugasan.line
_description: 'Detail Baris Penugasan Asesor'
```

**Fields wajib:**
- `penugasan_id`: Many2one `lsp.penugasan.asesor`, required, `ondelete='cascade'`
- `asesor_id`: Many2one `res.users`, required, domain filter hanya user dengan group asesor
- `asesor_partner_id`: Many2one `res.partner`, related dari `asesor_id.partner_id`, readonly
- `asesi_ids`: Many2many `res.partner` (atau model asesi custom), dengan domain filter asesi pada jadwal yang sama
- `jumlah_asesi`: Integer, computed: `len(self.asesi_ids)`, `store=True`
- `is_overload`: Boolean, computed: `self.jumlah_asesi > 10`
- `state`: Selection, related dari `penugasan_id.state`, readonly (untuk kontrol readonly di view)

**Constraints wajib:**

```python
@api.constrains('asesi_ids')
def _check_max_asesi(self):
    for line in self:
        if len(line.asesi_ids) > 10:
            raise ValidationError(
                _('Asesor %s tidak boleh menangani lebih dari 10 asesi. '
                  'Saat ini: %d asesi.') % (line.asesor_id.name, len(line.asesi_ids))
            )

@api.constrains('asesor_id', 'penugasan_id')
def _check_asesor_unik(self):
    for line in self:
        duplikat = self.search([
            ('penugasan_id', '=', line.penugasan_id.id),
            ('asesor_id', '=', line.asesor_id.id),
            ('id', '!=', line.id)
        ])
        if duplikat:
            raise ValidationError(
                _('Asesor %s sudah ditambahkan di penugasan ini!') % line.asesor_id.name
            )
```

**SQL Constraint:**
```python
_sql_constraints = [
    ('unique_asesor_per_penugasan', 'UNIQUE(penugasan_id, asesor_id)',
     'Asesor yang sama tidak boleh ditambahkan dua kali dalam satu penugasan.')
]
```

---

### 6. `wizards/wizard_tambah_asesor.py`

```
Model name : lsp.wizard.tambah.asesor
_description: 'Wizard Tambah Asesor ke Penugasan'
```

**Fields:**
- `penugasan_id`: Many2one `lsp.penugasan.asesor`, required, default dari context `active_id`
- `asesor_ids`: Many2many `res.users`, domain filter hanya group asesor
- `preview_info`: Text, computed: tampilkan info "Saat ini: X asesor, butuh minimal Y asesor untuk Z asesi"

**Method `action_tambah_asesor`:**
- Loop `asesor_ids`
- Cek duplikat: jika asesor sudah ada di `penugasan_id.penugasan_line_ids` → raise `UserError`
- Buat `lsp.penugasan.line` baru untuk setiap asesor yang belum ada
- Return `{'type': 'ir.actions.act_window_close'}`

---

### 7. `views/lsp_penugasan_asesor_views.xml`

Buat view lengkap di dalam tag `<odoo>`:

**Form View `lsp.penugasan.asesor`:**
- `<header>` dengan `<field name="state" widget="statusbar" statusbar_visible="draft,dikunci"/>`
- Tombol `Distribusi & Validasi Otomatis`: gunakan `invisible="state == 'dikunci'"` (**Odoo 19: `attrs` sudah DEPRECATED, gunakan ekspresi Python inline langsung di atribut `invisible`, `readonly`, `required`**), `type="object"`, method `action_distribusi_otomatis`
- Tombol `Kunci Penugasan`: `invisible="state == 'dikunci' or not is_valid"`, type `object`, method `action_kunci_penugasan`, class `btn-primary`
- Tombol `Buka Kunci (Admin)`: `invisible="state != 'dikunci'"`, `groups="plugins_manajement_asesor.group_admin_lsp"`, method `action_buka_kunci`
- `<sheet>` dengan informasi header (name, jadwal_id, skema_display, tanggal_penugasan)
- **Alert banner** jika `is_valid == False` dan `state == 'draft'`: gunakan `<div class="alert alert-warning" invisible="is_valid or state == 'dikunci'">` — tampilkan pesan "⚠️ Jumlah asesor belum mencukupi. Tambahkan X asesor lagi."
- `<notebook>` dengan dua tab:
  - Tab **"Daftar Asesor & Asesi"**: tampilkan `penugasan_line_ids` sebagai one2many tree + tombol `Tambah Asesor` yang membuka wizard
  - Tab **"Informasi Jadwal"**: tampilkan `jumlah_asesi`, `jumlah_asesor_dibutuhkan`, `total_asesor`, `is_valid` dalam readonly
- `<chatter/>` shorthand di bawah sheet (**Odoo 19: gunakan `<chatter/>` tag tunggal, bukan `<div class="oe_chatter">` + sub-widget manual**)
- Semua field harus `readonly="state == 'dikunci'"` menggunakan ekspresi inline (bukan `attrs`)

**Tree View `lsp.penugasan.asesor`:**
- Kolom: `name`, `jadwal_id`, `total_asesor`, `jumlah_asesor_dibutuhkan`, `total_asesi`, `state`
- `decoration-danger="not is_valid and state == 'draft'"`
- `decoration-success="state == 'dikunci'"`

**Search View:**
- Filter: `Draft` (`state = 'draft'`), `Dikunci` (`state = 'dikunci'`)
- Group by: `jadwal_id`, `state`, `tanggal_penugasan`

> ⚠️ **Odoo 19 — Perubahan Kritis di XML View:**
> - **HAPUS semua `attrs="{...}"`** — sudah fully deprecated dan akan error di Odoo 19
> - Gunakan atribut langsung: `invisible="..."`, `readonly="..."`, `required="..."` dengan ekspresi Python
> - Contoh lama (SALAH di Odoo 19): `attrs="{'readonly': [('state', '=', 'dikunci')]}"`
> - Contoh baru (BENAR di Odoo 19): `readonly="state == 'dikunci'"`
> - **`<group col="...">` masih valid**, tapi gunakan `<field>` dengan `column_invisible` untuk kolom list
> - **Gunakan `<list>` bukan `<tree>`** — di Odoo 17+ tag `<tree>` sudah diganti `<list>`, dan di Odoo 19 ini wajib

---

### 8. `views/lsp_penugasan_line_views.xml`

**List View (embedded di form penugasan — bukan standalone):**
- Gunakan tag `<list>` bukan `<tree>` (**Odoo 19: `<tree>` deprecated, wajib pakai `<list>`**)
- Kolom: `asesor_id`, `jumlah_asesi`, `is_overload`
- Field `asesi_ids` dengan `widget="many2many_tags"`
- `decoration-danger="is_overload == True"`
- `editable="bottom"` hanya saat `penugasan_id.state == 'draft'`
- Gunakan `readonly="state == 'dikunci'"` pada setiap field (ekspresi inline, bukan `attrs`)

---

### 9. `views/wizard_tambah_asesor_views.xml`

```xml
<!-- Form view untuk lsp.wizard.tambah.asesor -->
<!-- Target: new (popup dialog) -->
<!-- Odoo 19: gunakan <dialog> wrapper atau target="new" di action -->
<!-- Tampilkan: penugasan_id (readonly), preview_info (readonly, widget text), asesor_ids (many2many_tags) -->
<!-- Footer: tombol 'Tambah Asesor' (type=object, action_tambah_asesor) + tombol 'Batal' (special=cancel) -->
<!-- INGAT: gunakan invisible="..." bukan attrs di semua elemen -->
```

---

### 10. `views/portal_templates.xml`

Buat dua QWeb template:

**Template 1: `portal_my_penugasan_list`**
- Extend `portal.portal_my_home` atau buat halaman `/my/penugasan`
- Tampilkan tabel list penugasan: Kode Penugasan | Jadwal | Tanggal | Status
- Link setiap row ke `/my/penugasan/<id>`

**Template 2: `portal_my_penugasan_detail`**
- Tampilkan detail: nama jadwal, skema, tanggal, ruangan
- Tampilkan tabel daftar asesi yang ditugaskan ke asesor yang login
- Tombol "Kembali ke Daftar Penugasan"

---

### 11. `views/menu_views.xml`

```xml
<!-- Struktur menu: -->
<!-- LSP (top menu, category=LSP) -->
<!--   └── Penugasan Asesor (menu group) -->
<!--         ├── Semua Penugasan → action tree+form lsp.penugasan.asesor -->
<!--         └── Jadwal Ujian → action tree+form lsp.jadwal.ujian -->
```

---

### 12. `security/lsp_penugasan_security.xml`

Definisikan:

**Groups:**
- `group_admin_lsp` (nama: "Admin LSP"): dapat buat, edit, kunci, buka kunci penugasan
- `group_asesor` (nama: "Asesor LSP"): hanya dapat READ penugasan yang ditugaskan kepadanya

**Record Rules:**

Rule 1 — Asesor hanya lihat line miliknya:
```xml
<!-- Model: lsp.penugasan.line -->
<!-- Domain: [('asesor_id.id', '=', user.id)] -->
<!-- Groups: group_asesor -->
<!-- perm_read=1, perm_write=0, perm_create=0, perm_unlink=0 -->
```

Rule 2 — Asesor hanya lihat penugasan yang mengandung dirinya:
```xml
<!-- Model: lsp.penugasan.asesor -->
<!-- Domain: [('penugasan_line_ids.asesor_id', '=', user.id)] -->
<!-- Groups: group_asesor -->
<!-- perm_read=1, perm_write=0, perm_create=0, perm_unlink=0 -->
```

---

### 13. `security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_lsp_penugasan_asesor_admin,lsp.penugasan.asesor admin,model_lsp_penugasan_asesor,plugins_manajement_asesor.group_admin_lsp,1,1,1,1
access_lsp_penugasan_asesor_asesor,lsp.penugasan.asesor asesor,model_lsp_penugasan_asesor,plugins_manajement_asesor.group_asesor,1,0,0,0
access_lsp_penugasan_line_admin,lsp.penugasan.line admin,model_lsp_penugasan_line,plugins_manajement_asesor.group_admin_lsp,1,1,1,1
access_lsp_penugasan_line_asesor,lsp.penugasan.line asesor,model_lsp_penugasan_line,plugins_manajement_asesor.group_asesor,1,0,0,0
access_lsp_jadwal_ujian_admin,lsp.jadwal.ujian admin,model_lsp_jadwal_ujian,plugins_manajement_asesor.group_admin_lsp,1,1,1,1
access_lsp_jadwal_ujian_asesor,lsp.jadwal.ujian asesor,model_lsp_jadwal_ujian,plugins_manajement_asesor.group_asesor,1,0,0,0
access_lsp_wizard_tambah_asesor,lsp.wizard.tambah.asesor,model_lsp_wizard_tambah_asesor,plugins_manajement_asesor.group_admin_lsp,1,1,1,1
```

---

### 14. `data/lsp_penugasan_data.xml`

Buat:

**Sequence** untuk auto-numbering penugasan:
```xml
<!-- id: seq_lsp_penugasan -->
<!-- name: Penugasan Asesor LSP -->
<!-- code: lsp.penugasan.asesor -->
<!-- prefix: PENUGASAN/%(year)s/%(month)s/ -->
<!-- padding: 4 -->
```

**Sequence** untuk auto-numbering jadwal ujian:
```xml
<!-- id: seq_lsp_jadwal_ujian -->
<!-- name: Jadwal Ujian LSP -->
<!-- code: lsp.jadwal.ujian -->
<!-- prefix: JDW/%(year)s/%(month)s/ -->
<!-- padding: 3 -->
```

**Mail Template** untuk notifikasi ke Asesor:
```xml
<!-- id: lsp_penugasan_email_template -->
<!-- name: Notifikasi Penugasan Asesor LSP -->
<!-- model_id: lsp.penugasan.asesor -->
<!-- subject: [LSP] Penugasan Asesor: ${object.jadwal_id.name} -->
<!-- body_html: QWeb template berisi informasi lengkap penugasan + daftar asesi + link portal -->
<!-- auto_delete: False -->
```

---

### 15. `controllers/portal_penugasan.py`

```python
# Inherit dari: odoo.addons.portal.controllers.portal.CustomerPortal
#
# Override _prepare_home_portal_values():
#   - Hitung count penugasan milik user yang login
#   - Tambahkan ke values dengan key 'penugasan_count'
#
# Route GET /my/penugasan:
#   - Query lsp.penugasan.asesor yang memiliki line dengan asesor_id == request.env.user
#   - Render template portal_my_penugasan_list
#
# Route GET /my/penugasan/<int:penugasan_id>:
#   - Validasi akses: line.asesor_id == request.env.user
#   - Jika tidak ada akses: return 403 atau redirect
#   - Ambil detail penugasan dan list asesi untuk asesor ini
#   - Render template portal_my_penugasan_detail
```

---

### 16. `tests/test_penugasan_asesor.py`

```python
# Gunakan: from odoo.tests.common import TransactionCase
# Decorator: @tagged('post_install', '-at_install')

# TestCase 1: test_rasio_valid_batas_maksimal
#   Buat jadwal dengan 10 asesi, 1 asesor
#   Jalankan distribusi → HARUS berhasil tanpa error
#   Verifikasi: penugasan_line_ids[0].jumlah_asesi == 10

# TestCase 2: test_rasio_overload_raise_error
#   Buat jadwal dengan 11 asesi, 1 asesor
#   Paksa assign 11 asesi ke 1 line → HARUS raise ValidationError
#   Verifikasi pesan error mengandung "10 asesi"

# TestCase 3: test_kurang_asesor_blokir_distribusi
#   Buat jadwal 20 asesi, 1 asesor
#   Panggil action_distribusi_otomatis() → HARUS raise UserError
#   Verifikasi pesan error menyebutkan jumlah asesor yang kurang

# TestCase 4: test_cukup_asesor_distribusi_berhasil
#   Buat jadwal 20 asesi, 2 asesor
#   Panggil action_distribusi_otomatis() → HARUS berhasil
#   Verifikasi: total asesi di semua line == 20, tidak ada line > 10

# TestCase 5: test_asesor_duplikat_raise_error
#   Tambah asesor yang sama 2x ke penugasan yang sama
#   HARUS raise ValidationError (constraint SQL atau Python)

# TestCase 6: test_kunci_saat_tidak_valid_raise_error
#   Buat penugasan dengan is_valid == False
#   Panggil action_kunci_penugasan() → HARUS raise UserError

# TestCase 7: test_kunci_berhasil_dan_state_berubah
#   Buat penugasan valid (cukup asesor, sudah distribusi)
#   Panggil action_kunci_penugasan()
#   Verifikasi: self.state == 'dikunci'

# TestCase 8: test_field_readonly_setelah_dikunci
#   Penugasan sudah dikunci
#   Coba write field notes → HARUS raise AccessError atau tidak ada perubahan
#   (tergantung implementasi: bisa via group check atau @api.constrains state)
```

---

### 17. `tests/test_distribusi_otomatis.py`

```python
# TestCase 1: test_distribusi_merata_genap
#   20 asesi, 2 asesor
#   Setelah distribusi: setiap asesor mendapat tepat 10 asesi
#   Verifikasi: set(line.jumlah_asesi for line in penugasan_line_ids) == {10}

# TestCase 2: test_distribusi_merata_ganjil
#   15 asesi, 2 asesor
#   Setelah distribusi: tidak ada asesor > 10, total = 15
#   Verifikasi: sum(line.jumlah_asesi) == 15 dan max(line.jumlah_asesi) <= 10

# TestCase 3: test_distribusi_satu_asesor_sedikit_asesi
#   8 asesi, 1 asesor
#   Semua 8 asesi masuk ke 1 asesor
#   Verifikasi: penugasan_line_ids[0].jumlah_asesi == 8

# TestCase 4: test_distribusi_ulang_tidak_duplikat
#   Jalankan distribusi 2 kali berturut-turut
#   Verifikasi: total asesi di semua line tetap sama, tidak ada duplikat asesi antar-line

# TestCase 5: test_semua_asesi_tertugaskan
#   Buat penugasan apapun yang valid
#   Setelah distribusi: set asesi di semua line == set asesi di jadwal
#   Tidak boleh ada asesi yang "ketinggalan" tidak ditugaskan
```

---

## ⚠️ ATURAN PENGKODEAN WAJIB (ODOO 19)

### Python:
1. Gunakan `@api.constrains` di level model — constraint tidak boleh hanya ada di wizard atau UI.
2. Gunakan `@api.depends` dengan dependency yang tepat untuk semua field computed.
3. Semua string pesan user-facing harus menggunakan `_('...')` dari `odoo.tools.translate` — di Odoo 19 import via `from odoo import _`.
4. Jangan gunakan `sudo()` tanpa komentar alasan keamanan yang jelas.
5. Method `action_*` yang dipanggil button HARUS return dict action atau `True`, bukan `None`.
6. Selalu definisikan `ondelete=` secara eksplisit di setiap field Many2one.
7. Gunakan `self.ensure_one()` di method yang hanya boleh dijalankan untuk satu record.
8. Jangan gunakan `@api.one` atau `@api.multi` (deprecated sejak Odoo 14, error di Odoo 19).
9. Gunakan `_sql_constraints` untuk constraint uniqueness di level database.
10. Field `state` wajib punya `copy=False` dan `tracking=True`.
11. **Odoo 19 — NEW**: Gunakan `model._fields['field_name'].selection` untuk akses dynamic selection, bukan hardcode.
12. **Odoo 19 — NEW**: Untuk computed stored field yang perlu recompute manual, gunakan `self.env.add_to_compute(self._fields['field_name'], records)`.
13. **Odoo 19 — NEW**: Jika menggunakan `Environment`, gunakan `self.env` bukan `self.pool` (sudah tidak ada di Odoo 19).
14. **Odoo 19 — NEW**: Gunakan `@api.model_create_multi` untuk override `create()` — bukan `@api.model` saja.

### XML Views:
1. Root element setiap file XML adalah `<odoo>`.
2. Setiap `<record>` wajib punya `id` unik dengan prefix `lsp_penugasan_`.
3. Setiap action window wajib mendefinisikan `view_mode`, `res_model`, dan `name`.
4. **Odoo 19 — WAJIB**: Ganti semua `attrs="{...}"` dengan ekspresi inline:
   - `invisible="ekspresi_python"` 
   - `readonly="ekspresi_python"`
   - `required="ekspresi_python"`
   - Contoh: `readonly="state == 'dikunci'"` — BUKAN `attrs="{'readonly': [('state','=','dikunci')]}"`
5. **Odoo 19 — WAJIB**: Gunakan `<list>` bukan `<tree>` untuk semua list/tree view.
6. **Odoo 19 — WAJIB**: Gunakan `<chatter/>` tag tunggal, bukan `<div class="oe_chatter">`.
7. Form view wajib menggunakan `<sheet>`.
8. Tombol yang memanggil Python method gunakan `type="object"`.
9. Jangan lupa `string=` di setiap elemen `<button>`.
10. **Odoo 19 — NEW**: Untuk domain di field, gunakan format `domain="[('field', '=', value)]"` — syntax tidak berubah, tapi pastikan tidak menggunakan `[]` string (harus list Python).
11. **Odoo 19 — NEW**: `states=` attribute di `<field>` tag sudah DEPRECATED, ganti dengan `invisible=` / `readonly=`.

### CSV Security:
1. Header kolom wajib persis: `id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink`
2. Tidak boleh ada spasi di sekitar koma.
3. Format `model_id:id` adalah `model_` diikuti nama model dengan titik diganti underscore.
   Contoh: `lsp.penugasan.asesor` → `model_lsp_penugasan_asesor`

---

## 🔗 INTEGRASI DENGAN MODUL LAIN

Karena modul lain mungkin belum selesai, gunakan pendekatan berikut:

```python
# Strategi integrasi bertahap:
# 
# FASE 1 (modul ini berdiri sendiri):
#   - Buat model lsp.jadwal.ujian minimal di dalam modul ini
#   - Gunakan res.partner dengan tag 'asesi' untuk data asesi sementara
#   - Tandai dengan komentar: # TODO: replace with lsp.asesi model from lsp_pengajuan_asesi
#
# FASE 2 (setelah modul lain siap):
#   - Ubah _name menjadi _inherit di model yang overlap
#   - Update depends di __manifest__.py
#   - Hapus model minimal yang sudah digantikan
```

---

## 📬 SPESIFIKASI NOTIFIKASI

Notifikasi yang dikirim ke Asesor (via mail.template) harus mengandung:
- Nama dan kode jadwal ujian
- Tanggal & waktu ujian
- Ruangan ujian
- Nama skema sertifikasi
- Daftar nama lengkap asesi yang ditugaskan (format: numbered list)
- Link langsung ke portal: `/my/penugasan/<penugasan_line_id>`
- Nama Admin yang mengunci penugasan + timestamp penguncian

---

## ✅ CHECKLIST WAJIB SEBELUM MENYATAKAN SELESAI

Pastikan semua item berikut terpenuhi sebelum menyerahkan hasil:

**Struktur File:**
- [ ] Semua file dalam struktur folder sudah dibuat dan tidak ada yang kosong
- [ ] Semua `__init__.py` sudah mengimpor modul yang benar
- [ ] `__manifest__.py` sudah mendaftarkan semua file di key `'data'`

**Fungsionalitas Inti:**
- [ ] Constraint rasio 1:10 tervalidasi di level model Python (bukan hanya UI/wizard)
- [ ] SQL constraint unique asesor per penugasan sudah ada
- [ ] Distribusi otomatis tidak menghasilkan asesi lebih dari 10 per asesor
- [ ] Semua asesi di jadwal tertugaskan setelah distribusi (tidak ada yang terlewat)
- [ ] State `dikunci` membuat semua field menjadi readonly — gunakan `readonly="state == 'dikunci'"` di XML (Odoo 19: bukan `attrs`)

**Notifikasi & Audit:**
- [ ] Notifikasi terkirim ke chatter/email setiap Asesor saat penugasan dikunci
- [ ] Setiap perubahan state tercatat di chatter (tracking=True berfungsi)

**Keamanan & Akses:**
- [ ] `ir.model.access.csv` mencakup semua model baru
- [ ] Asesor hanya bisa melihat penugasan dan line miliknya (record rules berfungsi)
- [ ] Admin bisa buka kunci, Asesor tidak bisa

**Portal:**
- [ ] Portal `/my/penugasan` hanya menampilkan data milik asesor yang login
- [ ] Halaman detail menampilkan daftar asesi yang benar

**Testing:**
- [ ] Semua unit test berjalan tanpa error
- [ ] Modul dapat diinstall: `./odoo-bin -i plugins_manajement_asesor` tanpa error
- [ ] Modul dapat diupdate: `./odoo-bin -u plugins_manajement_asesor` tanpa error

**Kualitas Kode:**
- [ ] Tidak ada `print()` statement di kode produksi
- [ ] Semua string user-facing menggunakan `_('...')`
- [ ] Tidak ada hardcoded database ID
- [ ] Tidak ada `@api.one` atau `@api.multi` (error di Odoo 19)
- [ ] Tidak ada `attrs="{...}"` di XML (deprecated di Odoo 19, gunakan ekspresi inline)
- [ ] Tidak ada `<tree>` tag di XML view (wajib pakai `<list>` di Odoo 19)
- [ ] Tidak ada `states=` attribute di `<field>` tag (deprecated, pakai `invisible=`/`readonly=`)
- [ ] Tidak ada `<div class="oe_chatter">` manual (pakai `<chatter/>` di Odoo 19)

---

## 🚫 LARANGAN KERAS

1. **JANGAN** menggunakan API Odoo versi lama (`osv`, `orm`, `@api.one`, `@api.multi`).
2. **JANGAN** skip pembuatan file `tests/` — pengujian adalah bagian dari deliverable wajib.
3. **JANGAN** hardcode ID database (contoh: `group_id = 5`), selalu gunakan XML ID.
4. **JANGAN** letakkan business logic di dalam file XML view — semua logika ada di Python model.
5. **JANGAN** gunakan `eval` di domain XML — gunakan format list domain standar Odoo.
6. **JANGAN** biarkan field Many2one tanpa atribut `ondelete`.
7. **JANGAN** buat file Python tanpa mengimpornya di `__init__.py` yang sesuai.
8. **JANGAN** gunakan `sudo()` pada validasi security-sensitive tanpa penjelasan.
9. **JANGAN** lupa menambahkan `copy=False` pada field sequence/name dan state.
10. **JANGAN** gunakan `attrs="{...}"` di XML — **ini akan menyebabkan error di Odoo 19**.
11. **JANGAN** gunakan `<tree>` tag untuk list view — **wajib ganti dengan `<list>` di Odoo 19**.
12. **JANGAN** gunakan `states=` attribute di `<field>` — sudah deprecated, gunakan `invisible=` atau `readonly=`.
13. **JANGAN** gunakan `<div class="oe_chatter">` secara manual — gunakan `<chatter/>` di Odoo 19.
14. **JANGAN** gunakan `self.pool` — sudah tidak ada di Odoo 19, gunakan `self.env`.
15. **JANGAN** override `create()` dengan `@api.model` saja — gunakan `@api.model_create_multi` di Odoo 19.

---

## 📦 OUTPUT YANG DIHARAPKAN

Setelah selesai, hasilkan:

1. **Seluruh isi folder `plugins_manajement_asesor/`** dengan semua file yang fungsional dan dapat langsung di-copy ke direktori addons Odoo 19.
2. **File `README_INSTALASI.md`** di dalam folder modul, berisi:
   - Langkah instalasi ke Odoo 19
   - Cara menjalankan unit test: `./odoo-bin -i plugins_manajement_asesor --test-enable --stop-after-init`
   - Daftar group user yang perlu dikonfigurasi
   - Catatan dependensi dengan modul lain
   - Catatan migrasi jika upgrade dari Odoo 17/18 ke 19
3. **Tidak ada placeholder kosong** — setiap method, class, dan file harus berisi implementasi yang nyata dan dapat dijalankan.

---

## 🆕 RINGKASAN PERUBAHAN PENTING ODOO 19 vs ODOO 17

| Aspek | Odoo 17 (Lama) | Odoo 19 (Wajib Digunakan) |
|---|---|---|
| List view tag | `<tree>` | `<list>` |
| Dynamic visibility | `attrs="{'invisible': [...]}"` | `invisible="ekspresi_python"` |
| Dynamic readonly | `attrs="{'readonly': [...]}"` | `readonly="ekspresi_python"` |
| Field states attr | `states="draft: readonly"` | `readonly="state != 'draft'"` |
| Chatter | `<div class="oe_chatter">...` | `<chatter/>` |
| Create override | `@api.model` | `@api.model_create_multi` |
| Pool access | `self.pool['model']` | `self.env['model']` |
| Manifest version | `'17.0.1.0.0'` | `'19.0.1.0.0'` |
| QWeb assets | `web.assets_backend` di XML | `assets` key di `__manifest__.py` |

---

*Dokumen prompt ini disusun berdasarkan:*
*- Dokumen Analisis Proses Bisnis LSP, Kelas D4-3B POLBAN 2025*
*- Diagram BPMN Alur Penugasan Asesor (IV.5)*
*- Standar pengembangan modul Odoo 19 (versi terbaru)*