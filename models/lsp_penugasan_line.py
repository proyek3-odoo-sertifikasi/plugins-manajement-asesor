from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LspPenugasanLine(models.Model):
    _name = 'lsp.penugasan.line'
    _description = 'Detail Baris Penugasan Asesor'

    penugasan_id = fields.Many2one(
        comodel_name='lsp.penugasan.asesor',
        string='Penugasan',
        required=True,
        ondelete='cascade',
    )
    asesor_id = fields.Many2one(
        comodel_name='res.users',
        string='Asesor',
        required=True,
        ondelete='restrict',
    )
    
    asesor_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner Asesor',
        related='asesor_id.partner_id',
        readonly=True,
        store=False,
    )
    # TODO: replace with lsp.asesi model from lsp_pengajuan_asesi
    asesi_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='lsp_penugasan_line_asesi_rel',
        column1='line_id',
        column2='partner_id',
        string='Daftar Asesi',
    )
    jumlah_asesi = fields.Integer(
        string='Jumlah Asesi',
        compute='_compute_jumlah_asesi',
        store=True,
    )
    is_overload = fields.Boolean(
        string='Overload?',
        compute='_compute_is_overload',
        store=True,
    )
    state = fields.Selection(
        string='Status',
        related='penugasan_id.state',
        readonly=True,
        store=False,
    )

    _sql_constraints = [
        ('unique_asesor_per_penugasan', 'UNIQUE(penugasan_id, asesor_id)',
         'Asesor yang sama tidak boleh ditambahkan dua kali dalam satu penugasan.')
    ]

    @api.depends('asesi_ids')
    def _compute_jumlah_asesi(self):
        for line in self:
            line.jumlah_asesi = len(line.asesi_ids)

    @api.depends('jumlah_asesi')
    def _compute_is_overload(self):
        for line in self:
            line.is_overload = line.jumlah_asesi > 10

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
