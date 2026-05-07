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
        'views/wizard_tambah_asesor_views.xml',
        'views/menu_views.xml',
        'views/lsp_jadwal_ujian_views.xml',
        'views/lsp_penugasan_asesor_views.xml',
        'views/lsp_penugasan_line_views.xml',
        'views/portal_templates.xml',
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # OWL/JS/CSS assets can be added here if needed by the module
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
