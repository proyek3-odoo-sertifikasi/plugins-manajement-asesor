import math

from odoo import api, fields, models, _
from odoo.exceptions import UserError


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
    tanggal_mulai = fields.Datetime(
        string='Tanggal Mulai',
        required=True,
    )
    tanggal_selesai = fields.Datetime(
        string='Tanggal Selesai',
        required=True,
    )
    ruangan = fields.Char(
        string='Ruangan',
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
