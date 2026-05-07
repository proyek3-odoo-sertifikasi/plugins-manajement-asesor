import math

from odoo import api, fields, models, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError, ValidationError


class LspPenugasanAsesor(models.Model):
    _name = 'lsp.penugasan.asesor'
    _description = 'Penugasan Asesor LSP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tanggal_penugasan desc, id desc'

    name = fields.Char(
        string='Nomor Penugasan',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    jadwal_id = fields.Many2one(
        comodel_name='lsp.jadwal.ujian',
        string='Jadwal Ujian',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    skema_display = fields.Char(
        string='Skema Sertifikasi',
        compute='_compute_skema_display',
        readonly=True,
        store=True,
    )
    tanggal_penugasan = fields.Date(
        string='Tanggal Penugasan',
        default=fields.Date.today,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('dikunci', 'Dikunci'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
    )
    penugasan_line_ids = fields.One2many(
        comodel_name='lsp.penugasan.line',
        inverse_name='penugasan_id',
        string='Detail Penugasan',
    )
    total_asesor = fields.Integer(
        string='Total Asesor',
        compute='_compute_total_asesor',
        store=True,
    )
    total_asesi = fields.Integer(
        string='Total Asesi',
        compute='_compute_total_asesi',
        store=True,
    )
    jumlah_asesor_dibutuhkan = fields.Integer(
        string='Jumlah Asesor Dibutuhkan',
        compute='_compute_jumlah_asesor_dibutuhkan',
        store=True,
    )
    is_valid = fields.Boolean(
        string='Kuota Asesor Valid',
        compute='_compute_is_valid',
        store=True,
    )
    notes = fields.Text(
        string='Catatan',
    )

    _sql_constraints = [
        ('unique_jadwal_tanggal_penugasan', 'UNIQUE(jadwal_id, tanggal_penugasan)',
         'Sudah ada penugasan untuk jadwal dan tanggal yang sama. '
         'Satu jadwal hanya boleh memiliki satu record penugasan per hari.')
    ]

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
                      'dalam rentang jadwal ujian "%s" '
                      '(%s s/d %s).') % (
                        tgl.strftime('%d %B %Y'),
                        jadwal.name,
                        jadwal.tanggal_mulai.strftime('%d %B %Y'),
                        jadwal.tanggal_selesai.strftime('%d %B %Y'),
                    )
                )

    @api.constrains('jadwal_id', 'tanggal_penugasan')
    def _check_unique_jadwal_tanggal(self):
        for record in self:
            if not record.jadwal_id or not record.tanggal_penugasan:
                continue
            duplikat = self.search([
                ('jadwal_id', '=', record.jadwal_id.id),
                ('tanggal_penugasan', '=', record.tanggal_penugasan),
                ('id', '!=', record.id)
            ])
            if duplikat:
                raise ValidationError(
                    _('Sudah ada penugasan untuk jadwal "%s" pada tanggal %s. '
                      'Satu jadwal hanya boleh memiliki satu penugasan per hari.') % (
                        record.jadwal_id.name,
                        record.tanggal_penugasan.strftime('%d %B %Y')
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('lsp.penugasan.asesor') or _('New')
        return super(LspPenugasanAsesor, self).create(vals_list)

    @api.depends('penugasan_line_ids')
    def _compute_total_asesor(self):
        for record in self:
            record.total_asesor = len(record.penugasan_line_ids)

    @api.depends('jadwal_id', 'jadwal_id.jumlah_asesi')
    def _compute_total_asesi(self):
        for record in self:
            record.total_asesi = record.jadwal_id.jumlah_asesi if record.jadwal_id else 0

    @api.depends('jadwal_id', 'jadwal_id.skema_id')
    def _compute_skema_display(self):
        for record in self:
            skema = False
            if record.jadwal_id:
                # jadwal.skema_id may be Char or Many2one in future
                val = record.jadwal_id.skema_id
                if hasattr(val, 'name'):
                    skema = val.name
                else:
                    skema = val
            record.skema_display = skema or ''

    @api.depends('total_asesi')
    def _compute_jumlah_asesor_dibutuhkan(self):
        for record in self:
            if record.total_asesi > 0:
                record.jumlah_asesor_dibutuhkan = math.ceil(record.total_asesi / 10)
            else:
                record.jumlah_asesor_dibutuhkan = 0

    @api.depends('total_asesor', 'jumlah_asesor_dibutuhkan')
    def _compute_is_valid(self):
        for record in self:
            record.is_valid = record.total_asesor >= record.jumlah_asesor_dibutuhkan

    def action_distribusi_otomatis(self):
        """Distribusi asesi ke asesor secara otomatis dan merata (round-robin)."""
        self.ensure_one()

        asesi_list = self.jadwal_id.asesi_ids
        asesor_lines = self.penugasan_line_ids

        if not asesor_lines:
            raise UserError(_('Belum ada asesor yang ditambahkan. Silakan tambahkan asesor terlebih dahulu.'))

        asesor_dibutuhkan = math.ceil(len(asesi_list) / 10)
        if len(asesor_lines) < asesor_dibutuhkan:
            kekurangan = asesor_dibutuhkan - len(asesor_lines)
            raise UserError(
                _('Jumlah asesor belum mencukupi. '
                  'Saat ini: %d asesor, dibutuhkan minimal %d asesor untuk %d asesi. '
                  'Tambahkan %d asesor lagi.') % (
                    len(asesor_lines), asesor_dibutuhkan, len(asesi_list), kekurangan
                )
            )

        # Prepare mapping untuk asignasi per line (hindari multiple write/append)
        line_records = list(asesor_lines)
        assignments = {line.id: [] for line in line_records}

        # Algoritma distribusi round-robin
        asesi_sorted = asesi_list.sorted(key=lambda r: r.id)
        asesor_count = len(line_records)
        for idx, asesi in enumerate(asesi_sorted):
            target_line = line_records[idx % asesor_count]
            assignments[target_line.id].append(asesi.id)

        # Tulis assignments sekali per line menggunakan (6,0,ids) untuk replace
        for line in line_records:
            ids = assignments.get(line.id, [])
            line.asesi_ids = [(6, 0, ids)]

        self.message_post(
            body=_('Distribusi otomatis berhasil. %d asesi telah didistribusikan ke %d asesor secara merata.') % (
                len(asesi_list), len(asesor_lines)
            ),
            message_type='notification',
        )
        return True

    def action_kunci_penugasan(self):
        """Mengunci penugasan dan mengirim notifikasi ke semua asesor."""
        self.ensure_one()

        if not self.is_valid:
            raise UserError(
                _('Penugasan tidak dapat dikunci karena jumlah asesor belum mencukupi. '
                  'Dibutuhkan minimal %d asesor, saat ini hanya %d.') % (
                    self.jumlah_asesor_dibutuhkan, self.total_asesor
                )
            )

        # Validasi field baris penugasan (pitstop dan asesi)
        for line in self.penugasan_line_ids:
            if not line.ruangan:
                raise UserError(
                    _('Ruangan (Pitstop) untuk asesor %s belum diisi! '
                      'Pastikan semua asesor memiliki ruangan sebelum penugasan dikunci.') % line.asesor_id.name
                )
            if not line.asesi_ids:
                raise UserError(
                    _('Asesor %s belum ditugaskan untuk menguji asesi apapun. '
                      'Silakan lakukan Distribusi & Validasi Otomatis terlebih dahulu.') % line.asesor_id.name
                )

        self.state = 'dikunci'

        # Kirim notifikasi ke semua asesor via mail template
        template = self.env.ref(
            'plugins_manajement_asesor.lsp_penugasan_email_template',
            raise_if_not_found=False,
        )
        for line in self.penugasan_line_ids:
            if line.asesor_id and line.asesor_id.partner_id:
                if template:
                    template.send_mail(self.id, force_send=False, email_values={
                        'recipient_ids': [(4, line.asesor_id.partner_id.id)],
                    })
                # Internal notification via chatter
                line.asesor_id.partner_id.message_post(
                    body=_('Anda telah ditugaskan sebagai Asesor pada jadwal ujian: %s. '
                           'Silakan cek portal untuk melihat detail penugasan.') % self.jadwal_id.name,
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',
                )

        self.message_post(
            body=_('Penugasan dikunci oleh %s pada %s') % (
                self.env.user.name,
                fields.Datetime.now(),
            ),
            message_type='notification',
        )
        return True

    def action_buka_kunci(self):
        """Membuka kunci penugasan (hanya Admin LSP)."""
        self.ensure_one()
        # Pengecekan group dilakukan via XML (groups attribute pada button)
        self.state = 'draft'
        self.message_post(
            body=_('Penugasan dibuka kuncinya oleh %s pada %s') % (
                self.env.user.name,
                fields.Datetime.now(),
            ),
            message_type='notification',
        )
        return True
