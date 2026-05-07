import math

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class LspJadwalUjian(models.Model):
    _name = 'lsp.jadwal.ujian'
    _description = 'Jadwal Ujian Sertifikasi LSP'
    # TODO: replace with _inherit = 'lsp.jadwal.ujian' when lsp_penjadwalan_ujian module is ready

    name = fields.Char(
        string='Nama/Kode Jadwal',
        required=True,
        copy=False,
    )
    # TODO: replace with Many2one ke lsp.skema.sertifikasi when module is ready
    skema_id = fields.Char(
        string='Skema Sertifikasi',
    )
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
        default=7.5,
        help='Jam mulai ujian setiap harinya. Contoh: 7.5 = 07:30',
    )
    waktu_selesai = fields.Float(
        string='Jam Selesai (Harian)',
        default=16.0,
        help='Jam selesai ujian setiap harinya. Contoh: 16.0 = 16:00',
    )
    waktu_mulai_display = fields.Char(
        string='Mulai',
        compute='_compute_waktu_display',
        store=True,
    )
    waktu_selesai_display = fields.Char(
        string='Selesai',
        compute='_compute_waktu_display',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('terjadwal', 'Terjadwal'),
            ('penugasan', 'Proses Penugasan'),
            ('berlangsung', 'Berlangsung'),
            ('selesai', 'Selesai'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )
    # TODO: replace with lsp.asesi model from lsp_pengajuan_asesi
    asesi_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='lsp_jadwal_ujian_asesi_rel',
        column1='jadwal_id',
        column2='partner_id',
        string='Daftar Asesi',
    )
    penugasan_ids = fields.One2many(
        comodel_name='lsp.penugasan.asesor',
        inverse_name='jadwal_id',
        string='Penugasan',
    )
    jumlah_asesi = fields.Integer(
        string='Jumlah Asesi',
        compute='_compute_jumlah_asesi',
        store=True,
    )
    jumlah_asesor_dibutuhkan = fields.Integer(
        string='Jumlah Asesor Dibutuhkan',
        compute='_compute_jumlah_asesor_dibutuhkan',
        store=True,
    )
    jumlah_asesor_tersedia = fields.Integer(
        string='Jumlah Asesor Tersedia',
        compute='_compute_jumlah_asesor_tersedia',
    )
    is_kuota_cukup = fields.Boolean(
        string='Kuota Asesor Cukup?',
        compute='_compute_is_kuota_cukup',
    )

    @api.depends('asesi_ids')
    def _compute_jumlah_asesi(self):
        for record in self:
            record.jumlah_asesi = len(record.asesi_ids)

    @api.depends('jumlah_asesi')
    def _compute_jumlah_asesor_dibutuhkan(self):
        for record in self:
            if record.jumlah_asesi > 0:
                record.jumlah_asesor_dibutuhkan = math.ceil(record.jumlah_asesi / 10)
            else:
                record.jumlah_asesor_dibutuhkan = 0

    @api.depends('penugasan_ids.penugasan_line_ids.asesor_id')
    def _compute_jumlah_asesor_tersedia(self):
        for record in self:
            asesor_set = set()
            for penugasan in record.penugasan_ids:
                for line in penugasan.penugasan_line_ids:
                    if line.asesor_id:
                        asesor_set.add(line.asesor_id.id)
            record.jumlah_asesor_tersedia = len(asesor_set)

    @api.depends('jumlah_asesor_tersedia', 'jumlah_asesor_dibutuhkan')
    def _compute_is_kuota_cukup(self):
        for record in self:
            record.is_kuota_cukup = record.jumlah_asesor_tersedia >= record.jumlah_asesor_dibutuhkan

    @api.depends('waktu_mulai', 'waktu_selesai')
    def _compute_waktu_display(self):
        for record in self:
            def float_to_time(f):
                jam = int(f)
                menit = int(round((f - jam) * 60))
                return '%02d.%02d' % (jam, menit)

            record.waktu_mulai_display = float_to_time(record.waktu_mulai) if record.waktu_mulai else '00.00'
            record.waktu_selesai_display = float_to_time(record.waktu_selesai) if record.waktu_selesai else '00.00'

    @api.constrains('tanggal_mulai', 'tanggal_selesai', 'waktu_mulai', 'waktu_selesai')
    def _check_waktu(self):
        for record in self:
            if record.waktu_selesai <= record.waktu_mulai:
                raise ValidationError(
                    _('Jam selesai harus lebih besar dari jam mulai ujian.')
                )
            if record.tanggal_selesai and record.tanggal_mulai \
                    and record.tanggal_selesai < record.tanggal_mulai:
                raise ValidationError(
                    _('Tanggal selesai tidak boleh lebih awal dari tanggal mulai.')
                )

    def action_mulai_penugasan(self):
        """Membuat record penugasan baru terkait jadwal ini dan mengubah state."""
        self.ensure_one()
        if self.state != 'terjadwal':
            raise UserError(_('Penugasan hanya dapat dimulai dari jadwal berstatus "Terjadwal".'))

        penugasan = self.env['lsp.penugasan.asesor'].create({
            'jadwal_id': self.id,
        })
        self.state = 'penugasan'

        return {
            'type': 'ir.actions.act_window',
            'name': _('Penugasan Asesor'),
            'res_model': 'lsp.penugasan.asesor',
            'res_id': penugasan.id,
            'view_mode': 'form',
            'target': 'current',
        }
