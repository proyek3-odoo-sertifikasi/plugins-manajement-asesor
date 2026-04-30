import math

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class LspWizardTambahAsesor(models.TransientModel):
    _name = 'lsp.wizard.tambah.asesor'
    _description = 'Wizard Tambah Asesor ke Penugasan'

    penugasan_id = fields.Many2one(
        comodel_name='lsp.penugasan.asesor',
        string='Penugasan',
        required=True,
        default=lambda self: self.env.context.get('active_id'),
        ondelete='cascade',
    )
    asesor_ids = fields.Many2many(
        comodel_name='res.users',
        string='Asesor',
        domain=lambda self: [('groups_id', 'in', [self.env.ref('plugins_manajement_asesor.group_asesor', raise_if_not_found=False).id or 0])],
    )
    preview_info = fields.Text(
        string='Informasi Preview',
        compute='_compute_preview_info',
    )

    @api.depends('penugasan_id', 'asesor_ids')
    def _compute_preview_info(self):
        for wizard in self:
            if wizard.penugasan_id:
                total_asesi = wizard.penugasan_id.total_asesi
                current_asesor = wizard.penugasan_id.total_asesor
                dibutuhkan = math.ceil(total_asesi / 10) if total_asesi > 0 else 0
                akan_ditambah = len(wizard.asesor_ids)
                wizard.preview_info = _(
                    'Saat ini: %d asesor, butuh minimal %d asesor untuk %d asesi.\n'
                    'Akan ditambahkan: %d asesor.\n'
                    'Total setelah ditambahkan: %d asesor.'
                ) % (current_asesor, dibutuhkan, total_asesi, akan_ditambah, current_asesor + akan_ditambah)
            else:
                wizard.preview_info = ''

    def action_tambah_asesor(self):
        """Menambahkan asesor yang dipilih ke penugasan."""
        self.ensure_one()

        if not self.asesor_ids:
            raise UserError(_('Silakan pilih minimal satu asesor untuk ditambahkan.'))

        existing_asesor_ids = self.penugasan_id.penugasan_line_ids.mapped('asesor_id').ids

        for asesor in self.asesor_ids:
            if asesor.id in existing_asesor_ids:
                raise UserError(
                    _('Asesor %s sudah ditambahkan di penugasan ini!') % asesor.name
                )
            self.env['lsp.penugasan.line'].create({
                'penugasan_id': self.penugasan_id.id,
                'asesor_id': asesor.id,
            })

        return {'type': 'ir.actions.act_window_close'}
