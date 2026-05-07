# Dokumentasi Perubahan Modul `plugins_manajement_asesor`

> **Versi:** Revisi Sesi Mei 2026  
> **Dibuat oleh:** Tim D4-3B POLBAN  
> **Referensi Excel:** Jadwal Ujian LSP (Senin 17 Feb & Selasa 18 Feb 2023)

---

## Latar Belakang Perubahan

Implementasi awal modul memiliki beberapa ketidaksesuaian dengan proses bisnis nyata LSP:

| Masalah Awal | Solusi yang Diterapkan |
|---|---|
| Tanggal jadwal berupa `Datetime` rentang | Diubah ke `Date` rentang (tanpa jam) |
| Tidak ada slot waktu per asesor | Ditambah model `lsp.slot.waktu` |
| Ruangan (pitstop) tidak ada | Ditambah ke `lsp.penugasan.line` |
| 1 jadwal hanya boleh 1 penugasan | Diubah: 1 jadwal boleh N penugasan (beda hari) |
| Tidak ada validasi tanggal spesifik | Ditambah `@api.constrains` |

---

## 1. Model: `lsp_jadwal_ujian.py`

### 1.1 Perubahan Field Tanggal

**Sebelum:**
```python
tanggal_mulai = fields.Datetime(string='Tanggal Mulai', required=True)
tanggal_selesai = fields.Datetime(string='Tanggal Selesai', required=True)
ruangan = fields.Char(string='Ruangan')
```

**Sesudah:**
```python
tanggal_mulai = fields.Date(
    string='Tanggal Mulai',
    required=True,
    help='Tanggal mulai periode ujian.',
)
tanggal_selesai = fields.Date(
    string='Tanggal Selesai',
    required=True,
    help='Tanggal selesai periode ujian.',
)
waktu_mulai = fields.Float(
    string='Jam Mulai (Harian)',
    default=7.5,          # 07:30
    help='Jam mulai ujian setiap harinya.',
)
waktu_selesai = fields.Float(
    string='Jam Selesai (Harian)',
    default=16.0,         # 16:00
    help='Jam selesai ujian setiap harinya.',
)
waktu_mulai_display = fields.Char(compute='_compute_waktu_display', store=True)
waktu_selesai_display = fields.Char(compute='_compute_waktu_display', store=True)
```

> **Alasan:**  
> - Tipe `Datetime` diganti `Date` karena jadwal ujian cukup dicatat tanggalnya saja, jam harian dipisah.  
> - `ruangan` dihapus dari jadwal karena ruangan bersifat per-asesor (setiap asesor di ruangan/pitstop berbeda).

### 1.2 Method Baru: `_compute_waktu_display`

```python
@api.depends('waktu_mulai', 'waktu_selesai')
def _compute_waktu_display(self):
    for record in self:
        def float_to_time(f):
            jam = int(f)
            menit = int(round((f - jam) * 60))
            return '%02d.%02d' % (jam, menit)

        record.waktu_mulai_display = float_to_time(record.waktu_mulai)
        record.waktu_selesai_display = float_to_time(record.waktu_selesai)
```

Mengubah nilai float (misal `7.5`) menjadi format tampilan `07.30`.

### 1.3 Constraint Baru: `_check_waktu`

```python
@api.constrains('tanggal_mulai', 'tanggal_selesai', 'waktu_mulai', 'waktu_selesai')
def _check_waktu(self):
    for record in self:
        if record.waktu_selesai <= record.waktu_mulai:
            raise ValidationError(_('Jam selesai harus lebih besar dari jam mulai ujian.'))
        if record.tanggal_selesai and record.tanggal_mulai \
                and record.tanggal_selesai < record.tanggal_mulai:
            raise ValidationError(_('Tanggal selesai tidak boleh lebih awal dari tanggal mulai.'))
```

### 1.4 Penomoran Kode Jadwal Otomatis

**Sebelum:**
Field `name` diisi manual oleh user.

**Sesudah:**
Field `name` dibuat _Read-Only_ di *view* dan di-*generate* otomatis oleh *sequence* Odoo dengan format `JDW/%(year)s/%(month)s/XXX` (contoh: `JDW/2026/05/001`) saat record disave (melalui *override* fungsi `create`).

### 1.5 Perbaikan Alur Status Jadwal (Workflow)

**Masalah:** 
Sebelumnya tidak ada tombol untuk mengubah status jadwal dari `draft` ke `terjadwal`. Selain itu, tombol `Mulai Penugasan Asesor` menghilang setelah penugasan pertama dibuat karena status berubah menjadi `penugasan`.

**Solusi:**
1. Menambahkan tombol **Konfirmasi Jadwal** (`action_set_terjadwal`) untuk memajukan status dari `draft` menjadi `terjadwal`.
2. Mengubah visibilitas tombol **Mulai Penugasan Asesor** (`action_mulai_penugasan`) agar tetap muncul baik saat status `terjadwal` maupun `penugasan` (`invisible="state not in ('terjadwal', 'penugasan')"`). Hal ini selaras dengan aturan bisnis di mana 1 jadwal boleh memiliki lebih dari 1 penugasan (untuk hari yang berbeda).

---

## 2. Model Baru: `lsp_slot_waktu.py`

File baru: `models/lsp_slot_waktu.py`

### Tujuan
Merepresentasikan satu **sesi/slot waktu** ujian per asesor di satu penugasan. Sesuai kolom **Waktu** pada Excel (07.30–09.00, 09.00–10.30, dst.).

### Fields

| Field | Tipe | Keterangan |
|---|---|---|
| `penugasan_line_id` | Many2one | FK ke `lsp.penugasan.line` (cascade delete) |
| `penugasan_id` | Many2one | Related dari line (untuk filter/groupby) |
| `jam_mulai` | Float | Jam mulai slot, misal `7.5` = 07:30 |
| `jam_selesai` | Float | Jam selesai slot, misal `9.0` = 09:00 |
| `jam_mulai_display` | Char | Computed: `"07.30"` |
| `jam_selesai_display` | Char | Computed: `"09.00"` |
| `waktu_display` | Char | Computed: `"07.30-09.00"` |
| `asesi_ids` | Many2many | Asesi yang diuji pada slot ini |
| `jumlah_asesi_slot` | Integer | Computed: `len(asesi_ids)` |

### Constraint
- `jam_selesai > jam_mulai` (validasi urutan jam)
- `jam_mulai >= 0` dan `jam_selesai <= 24`

### Akses di `models/__init__.py`
```python
from . import lsp_slot_waktu   # ← ditambahkan
```

---

## 3. Model: `lsp_penugasan_line.py`

### Field Baru

**`ruangan`** — nomor/nama ruangan (pitstop) per asesor:
```python
ruangan = fields.Char(
    string='Ruangan (Pitstop)',
    help='Nomor atau nama ruangan tempat asesor ini bertugas.',
)
```

**`slot_waktu_ids`** — relasi ke slot waktu:
```python
slot_waktu_ids = fields.One2many(
    comodel_name='lsp.slot.waktu',
    inverse_name='penugasan_line_id',
    string='Jadwal Waktu Ujian',
)
```

---

## 4. Model: `lsp_penugasan_asesor.py`

### 4.1 Perubahan SQL Constraint

**Sebelum:**
```python
_sql_constraints = [
    ('unique_jadwal_penugasan', 'UNIQUE(jadwal_id)',
     'Satu jadwal hanya boleh memiliki satu record penugasan.')
]
```

**Sesudah:**
```python
_sql_constraints = [
    ('unique_jadwal_tanggal_penugasan', 'UNIQUE(jadwal_id, tanggal_penugasan)',
     'Satu jadwal hanya boleh memiliki satu record penugasan per hari.')
]
```

> **Alasan:** Satu Jadwal Ujian bisa berlangsung beberapa hari. Tiap hari memiliki record `lsp.penugasan.asesor` tersendiri. Contoh sesuai Excel:
> - Penugasan Senin 17 Feb → `jadwal_id=1, tanggal_penugasan=2023-02-17`
> - Penugasan Selasa 18 Feb → `jadwal_id=1, tanggal_penugasan=2023-02-18`

### 4.2 Constraint Baru: Validasi Tanggal Dalam Rentang

```python
@api.constrains('tanggal_penugasan', 'jadwal_id')
def _check_tanggal_dalam_rentang(self):
    for record in self:
        if not record.tanggal_penugasan or not record.jadwal_id:
            continue
        jadwal = record.jadwal_id
        if not jadwal.tanggal_mulai or not jadwal.tanggal_selesai:
            continue
        tgl = record.tanggal_penugasan
        if tgl < jadwal.tanggal_mulai or tgl > jadwal.tanggal_selesai:
            raise ValidationError(
                _('Tanggal Ujian (Hari Spesifik) "%s" harus berada '
                  'dalam rentang jadwal ujian "%s" (%s s/d %s).') % (
                    tgl.strftime('%d %B %Y'),
                    jadwal.name,
                    jadwal.tanggal_mulai.strftime('%d %B %Y'),
                    jadwal.tanggal_selesai.strftime('%d %B %Y'),
                )
            )
```

Validasi ini aktif setiap kali field `tanggal_penugasan` atau `jadwal_id` berubah dan data disimpan.

---

## 5. Views

### 5.1 `lsp_jadwal_ujian_views.xml`

**Form View — Perubahan:**
- Ganti field `tanggal_mulai`/`tanggal_selesai` Datetime → Date picker
- Tambah widget `float_time` untuk jam ujian harian dalam satu baris:
  ```xml
  <label for="waktu_mulai" string="Jam Ujian (Harian)"/>
  <div class="o_field_widget">
      <field name="waktu_mulai" widget="float_time" class="oe_inline" style="width:80px"/>
      <span class="mx-1">–</span>
      <field name="waktu_selesai" widget="float_time" class="oe_inline" style="width:80px"/>
  </div>
  ```

**List View — Perubahan:**
- Tampilkan `tanggal_mulai`, `tanggal_selesai`, `waktu_mulai_display`, `waktu_selesai_display`

**Search View — Fix:**
- Hapus `expand="0"` dari `<group>` (tidak valid di Odoo 19)
- Ganti `<group>` dengan `<separator/>` + filter biasa

### 5.2 `lsp_penugasan_asesor_views.xml`

**Perubahan label:**
```xml
<field name="tanggal_penugasan"
       string="Tanggal Ujian (Hari Spesifik)"
       readonly="state == 'dikunci'"/>
```

**Tambah kolom `ruangan` di inline list asesor:**
```xml
<field name="ruangan"
       string="Ruangan (Pitstop)"
       readonly="parent.state == 'dikunci'"
       placeholder="Contoh: 1, 2, Ruang A..."/>
```

### 5.3 `lsp_penugasan_line_views.xml`

**List View:** Tambah kolom `Ruangan (Pitstop)` setelah kolom Asesor.

**Form View:** Tambah section baru **Jadwal Waktu Ujian (per Slot)**:
```xml
<field name="slot_waktu_ids" readonly="state == 'dikunci'">
    <list editable="bottom" string="Slot Waktu">
        <field name="jam_mulai" widget="float_time" string="Jam Mulai"/>
        <field name="jam_selesai" widget="float_time" string="Jam Selesai"/>
        <field name="waktu_display" string="Waktu" readonly="1"/>
        <field name="asesi_ids" widget="many2many_tags" string="Asesi di Slot Ini"/>
        <field name="jumlah_asesi_slot" string="Jml. Asesi" readonly="1"/>
    </list>
</field>
```

---

## 6. Security: `ir.model.access.csv`

Tambah 2 baris akses untuk model baru `lsp.slot.waktu`:

```csv
access_lsp_slot_waktu_admin,lsp.slot.waktu admin,model_lsp_slot_waktu,plugins_manajement_asesor.group_admin_lsp,1,1,1,1
access_lsp_slot_waktu_asesor,lsp.slot.waktu asesor,model_lsp_slot_waktu,plugins_manajement_asesor.group_asesor,1,0,0,0
```

---

## 7. Pemetaan Arsitektur Final (Sesuai Excel)

```
lsp.jadwal.ujian  ─── "Ujian Sertifikasi Feb 2023"
  tanggal_mulai  : 17 Feb 2023
  tanggal_selesai: 18 Feb 2023
  waktu_mulai    : 07.30  (jam harian)
  waktu_selesai  : 16.00
  asesi_ids      : [semua peserta ujian]
       │
       ├─ lsp.penugasan.asesor ── "Senin, 17 Februari 2023"
       │    tanggal_penugasan : 17 Feb 2023
       │    │
       │    ├─ lsp.penugasan.line ── Asesor: Alif Ahmad Fadlil Z.
       │    │    ruangan      : 1  (Pitstop 1)
       │    │    asesi_ids    : [Adit, Afrizal, Al Firza, Alfa, Almas]
       │    │    slot_waktu_ids:
       │    │         07.30-09.00 → [Adit]
       │    │         09.00-10.30 → [Afrizal]
       │    │         10.30-12.00 → [Al Firza]
       │    │         13.00-14.30 → [Alfa]
       │    │         14.30-16.00 → [Almas]
       │    │
       │    ├─ lsp.penugasan.line ── Asesor: Anggi Permana T.
       │    │    ruangan      : 2  (Pitstop 2)
       │    │    ...
       │    └─ ...
       │
       └─ lsp.penugasan.asesor ── "Selasa, 18 Februari 2023"
            tanggal_penugasan : 18 Feb 2023
            ...
```

---

## 8. Aturan Bisnis yang Diterapkan

| Kode | Aturan | Implementasi |
|---|---|---|
| BR-DATE-01 | Jadwal ujian memiliki **rentang tanggal** (bukan 1 hari) | `tanggal_mulai` + `tanggal_selesai` (Date) |
| BR-DATE-02 | Setiap hari dalam rentang memiliki **1 record penugasan** | `UNIQUE(jadwal_id, tanggal_penugasan)` |
| BR-DATE-03 | Tanggal penugasan **harus dalam rentang** jadwal | `@api.constrains` di `lsp_penugasan_asesor` |
| BR-ROOM-01 | Setiap asesor bertugas di **1 ruangan (pitstop)** | Field `ruangan` di `lsp_penugasan_line` |
| BR-SLOT-01 | Tiap sesi ujian memiliki **slot waktu** (jam mulai–selesai) | Model `lsp.slot.waktu` |
| BR-SLOT-02 | Jam selesai slot > jam mulai slot | `@api.constrains` di `lsp_slot_waktu` |
| BR-TIME-01 | Jam selesai harian > jam mulai harian | `@api.constrains` di `lsp_jadwal_ujian` |

---

## 9. Cara Update Modul

Setelah perubahan ini, lakukan update modul di Odoo:

```
Settings → Technical → Modules → plugins_manajement_asesor → Upgrade
```

Atau via command (dari dalam container):
```bash
docker exec odoo-web odoo -d lsp -u plugins_manajement_asesor --stop-after-init
```

> ⚠️ **Wajib dilakukan** setiap ada perubahan pada **model Python** (fields, constraints) karena Odoo perlu memperbarui skema database.  
> Restart container biasa sudah cukup untuk perubahan **XML view** saja.
