from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class PortalPenugasan(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """Override untuk menambahkan count penugasan ke portal home."""
        values = super()._prepare_home_portal_values(counters)
        if 'penugasan_count' in counters:
            user = request.env.user
            penugasan_count = request.env['lsp.penugasan.asesor'].sudo().search_count([
                ('penugasan_line_ids.asesor_id', '=', user.id),
            ])
            values['penugasan_count'] = penugasan_count
        return values

    @http.route(['/my/penugasan', '/my/penugasan/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_penugasan_list(self, page=1, **kw):
        """Halaman daftar penugasan milik asesor yang login."""
        user = request.env.user
        PenugasanAsesor = request.env['lsp.penugasan.asesor'].sudo()

        domain = [('penugasan_line_ids.asesor_id', '=', user.id)]
        penugasan_count = PenugasanAsesor.search_count(domain)

        pager = portal_pager(
            url='/my/penugasan',
            total=penugasan_count,
            page=page,
            step=10,
        )

        penugasan_list = PenugasanAsesor.search(
            domain,
            limit=10,
            offset=pager['offset'],
            order='tanggal_penugasan desc',
        )

        values = {
            'penugasan_list': penugasan_list,
            'pager': pager,
            'page_name': 'penugasan',
            'default_url': '/my/penugasan',
        }
        return request.render('plugins_manajement_asesor.portal_my_penugasan_list', values)

    @http.route(['/my/penugasan/<int:penugasan_id>'],
                type='http', auth='user', website=True)
    def portal_my_penugasan_detail(self, penugasan_id, **kw):
        """Halaman detail penugasan untuk asesor yang login."""
        user = request.env.user
        penugasan = request.env['lsp.penugasan.asesor'].sudo().browse(penugasan_id)

        if not penugasan.exists():
            return request.redirect('/my/penugasan')

        # Validasi akses: asesor harus ada di penugasan ini
        my_lines = penugasan.penugasan_line_ids.filtered(
            lambda l: l.asesor_id.id == user.id
        )
        if not my_lines:
            return request.redirect('/my/penugasan')

        # Ambil asesi yang ditugaskan ke asesor ini
        my_asesi = my_lines.mapped('asesi_ids')

        values = {
            'penugasan': penugasan,
            'my_lines': my_lines,
            'my_asesi': my_asesi,
            'page_name': 'penugasan_detail',
        }
        return request.render('plugins_manajement_asesor.portal_my_penugasan_detail', values)
