from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class LspSlotWaktu(models.Model):
    """Model slot waktu ujian per asesor dalam satu penugasan.

    Setiap record mewakili satu sesi/slot waktu (misal 07.30–09.00)
    yang ditangani oleh satu asesor di satu ruangan (pitstop) tertentu.
    """
    _name = 'lsp.slot.waktu'
    _description = 'Slot Waktu Ujian per Asesor'
    _order = 'jam_mulai asc, id asc'

    penugasan_line_id = fields.Many2one(
        comodel_name='lsp.penugasan.line',
        string='Baris Penugasan',
        required=True,
        ondelete='cascade',
    )
    penugasan_id = fields.Many2one(
        comodel_name='lsp.penugasan.asesor',
        string='Penugasan',
        related='penugasan_line_id.penugasan_id',
        store=True,
        readonly=True,
    )
    jam_mulai = fields.Float(
        string='Jam Mulai',
        required=True,
        help='Contoh: 7.5 = 07:30, 9.0 = 09:00',
    )
    jam_selesai = fields.Float(
        string='Jam Selesai',
        required=True,
        help='Contoh: 9.0 = 09:00, 10.5 = 10:30',
    )
    jam_mulai_display = fields.Char(
        string='Waktu Mulai',
        compute='_compute_jam_display',
        store=True,
    )
    jam_selesai_display = fields.Char(
        string='Waktu Selesai',
        compute='_compute_jam_display',
        store=True,
    )
    waktu_display = fields.Char(
        string='Waktu',
        compute='_compute_jam_display',
        store=True,
        help='Format tampilan: 07.30-09.00',
    )
    # TODO: replace with lsp.asesi model from lsp_pengajuan_asesi
    asesi_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='lsp_slot_waktu_asesi_rel',
        column1='slot_id',
        column2='partner_id',
        string='Asesi di Slot Ini',
    )
    jumlah_asesi_slot = fields.Integer(
        string='Jumlah Asesi',
        compute='_compute_jumlah_asesi_slot',
        store=True,
    )
    state = fields.Selection(
        string='Status',
        related='penugasan_line_id.state',
        readonly=True,
        store=False,
    )

    @api.depends('jam_mulai', 'jam_selesai')
    def _compute_jam_display(self):
        for slot in self:
            def float_to_time(f):
                jam = int(f)
                menit = int(round((f - jam) * 60))
                return '%02d.%02d' % (jam, menit)

            mulai = float_to_time(slot.jam_mulai) if slot.jam_mulai else '00.00'
            selesai = float_to_time(slot.jam_selesai) if slot.jam_selesai else '00.00'
            slot.jam_mulai_display = mulai
            slot.jam_selesai_display = selesai
            slot.waktu_display = '%s-%s' % (mulai, selesai)

    @api.depends('asesi_ids')
    def _compute_jumlah_asesi_slot(self):
        for slot in self:
            slot.jumlah_asesi_slot = len(slot.asesi_ids)

    @api.constrains('jam_mulai', 'jam_selesai')
    def _check_jam(self):
        for slot in self:
            if slot.jam_selesai <= slot.jam_mulai:
                raise ValidationError(
                    _('Jam selesai harus lebih besar dari jam mulai.')
                )
            if slot.jam_mulai < 0 or slot.jam_selesai > 24:
                raise ValidationError(
                    _('Jam tidak valid. Harus antara 00.00 dan 24.00.')
                )
