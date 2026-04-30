from datetime import datetime, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPenugasanAsesor(TransactionCase):
    """Unit test validasi rasio, duplikat, dan penguncian penugasan."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Buat group asesor
        cls.group_asesor = cls.env.ref('plugins_manajement_asesor.group_asesor')
        cls.group_admin = cls.env.ref('plugins_manajement_asesor.group_admin_lsp')

        # Buat user asesor
        cls.asesor_user_1 = cls.env['res.users'].create({
            'name': 'Asesor Test 1',
            'login': 'asesor_test_1',
            'email': 'asesor1@test.com',
            'groups_id': [(4, cls.group_asesor.id)],
        })
        cls.asesor_user_2 = cls.env['res.users'].create({
            'name': 'Asesor Test 2',
            'login': 'asesor_test_2',
            'email': 'asesor2@test.com',
            'groups_id': [(4, cls.group_asesor.id)],
        })
        cls.asesor_user_3 = cls.env['res.users'].create({
            'name': 'Asesor Test 3',
            'login': 'asesor_test_3',
            'email': 'asesor3@test.com',
            'groups_id': [(4, cls.group_asesor.id)],
        })

        # Buat partner asesi
        cls.asesi_partners = cls.env['res.partner']
        for i in range(1, 21):
            partner = cls.env['res.partner'].create({
                'name': 'Asesi Test %d' % i,
                'email': 'asesi%d@test.com' % i,
            })
            cls.asesi_partners |= partner

    def _create_jadwal(self, asesi_count=10):
        """Helper: buat jadwal dengan sejumlah asesi."""
        asesi = self.asesi_partners[:asesi_count]
        jadwal = self.env['lsp.jadwal.ujian'].create({
            'name': 'Jadwal Test %s' % datetime.now().strftime('%H%M%S'),
            'skema_id': 'Skema Test',
            'tanggal_mulai': datetime.now(),
            'tanggal_selesai': datetime.now() + timedelta(hours=3),
            'ruangan': 'Ruang 101',
            'state': 'terjadwal',
            'asesi_ids': [(6, 0, asesi.ids)],
        })
        return jadwal

    def _create_penugasan(self, jadwal, asesor_users):
        """Helper: buat penugasan dengan asesor yang ditentukan."""
        penugasan = self.env['lsp.penugasan.asesor'].create({
            'jadwal_id': jadwal.id,
        })
        for user in asesor_users:
            self.env['lsp.penugasan.line'].create({
                'penugasan_id': penugasan.id,
                'asesor_id': user.id,
            })
        return penugasan

    # =============================================
    # TestCase 1: test_rasio_valid_batas_maksimal
    # =============================================
    def test_rasio_valid_batas_maksimal(self):
        """10 asesi, 1 asesor → distribusi harus berhasil, asesor mendapat tepat 10."""
        jadwal = self._create_jadwal(asesi_count=10)
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1])

        penugasan.action_distribusi_otomatis()

        line = penugasan.penugasan_line_ids[0]
        self.assertEqual(line.jumlah_asesi, 10,
                         "Asesor harus menangani tepat 10 asesi.")

    # =============================================
    # TestCase 2: test_rasio_overload_raise_error
    # =============================================
    def test_rasio_overload_raise_error(self):
        """Paksa assign 11 asesi ke 1 line → harus raise ValidationError."""
        jadwal = self._create_jadwal(asesi_count=11)
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1])
        line = penugasan.penugasan_line_ids[0]

        with self.assertRaises(ValidationError) as ctx:
            line.write({
                'asesi_ids': [(6, 0, self.asesi_partners[:11].ids)],
            })
        self.assertIn('10 asesi', str(ctx.exception),
                      "Pesan error harus menyebutkan batas 10 asesi.")

    # =============================================
    # TestCase 3: test_kurang_asesor_blokir_distribusi
    # =============================================
    def test_kurang_asesor_blokir_distribusi(self):
        """20 asesi, 1 asesor → distribusi harus raise UserError."""
        jadwal = self._create_jadwal(asesi_count=20)
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1])

        with self.assertRaises(UserError) as ctx:
            penugasan.action_distribusi_otomatis()
        self.assertIn('asesor', str(ctx.exception).lower(),
                      "Pesan error harus menyebutkan jumlah asesor yang kurang.")

    # =============================================
    # TestCase 4: test_cukup_asesor_distribusi_berhasil
    # =============================================
    def test_cukup_asesor_distribusi_berhasil(self):
        """20 asesi, 2 asesor → distribusi harus berhasil, tidak ada line > 10."""
        jadwal = self._create_jadwal(asesi_count=20)
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1, self.asesor_user_2])

        penugasan.action_distribusi_otomatis()

        total_assigned = sum(penugasan.penugasan_line_ids.mapped('jumlah_asesi'))
        max_per_line = max(penugasan.penugasan_line_ids.mapped('jumlah_asesi'))

        self.assertEqual(total_assigned, 20,
                         "Total asesi di semua line harus 20.")
        self.assertLessEqual(max_per_line, 10,
                             "Tidak boleh ada asesor yang menangani lebih dari 10 asesi.")

    # =============================================
    # TestCase 5: test_asesor_duplikat_raise_error
    # =============================================
    def test_asesor_duplikat_raise_error(self):
        """Tambah asesor yang sama 2x → harus raise error (SQL atau Python constraint)."""
        jadwal = self._create_jadwal(asesi_count=10)
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1])

        with self.assertRaises(Exception):
            self.env['lsp.penugasan.line'].create({
                'penugasan_id': penugasan.id,
                'asesor_id': self.asesor_user_1.id,
            })

    # =============================================
    # TestCase 6: test_kunci_saat_tidak_valid_raise_error
    # =============================================
    def test_kunci_saat_tidak_valid_raise_error(self):
        """Penugasan dengan is_valid == False → kunci harus raise UserError."""
        jadwal = self._create_jadwal(asesi_count=20)
        # Hanya 1 asesor untuk 20 asesi → is_valid False
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1])

        self.assertFalse(penugasan.is_valid,
                         "Penugasan seharusnya belum valid (kurang asesor).")

        with self.assertRaises(UserError):
            penugasan.action_kunci_penugasan()

    # =============================================
    # TestCase 7: test_kunci_berhasil_dan_state_berubah
    # =============================================
    def test_kunci_berhasil_dan_state_berubah(self):
        """Penugasan valid → kunci harus berhasil dan state berubah ke 'dikunci'."""
        jadwal = self._create_jadwal(asesi_count=10)
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1])

        # Distribusi dulu
        penugasan.action_distribusi_otomatis()

        self.assertTrue(penugasan.is_valid,
                        "Penugasan harus valid sebelum dikunci.")

        penugasan.action_kunci_penugasan()
        self.assertEqual(penugasan.state, 'dikunci',
                         "State harus berubah ke 'dikunci'.")

    # =============================================
    # TestCase 8: test_field_readonly_setelah_dikunci
    # =============================================
    def test_field_readonly_setelah_dikunci(self):
        """Penugasan yang sudah dikunci → state harus 'dikunci'."""
        jadwal = self._create_jadwal(asesi_count=10)
        penugasan = self._create_penugasan(jadwal, [self.asesor_user_1])

        penugasan.action_distribusi_otomatis()
        penugasan.action_kunci_penugasan()

        self.assertEqual(penugasan.state, 'dikunci',
                         "State harus 'dikunci' setelah penguncian.")

        # Verifikasi buka kunci hanya oleh admin
        penugasan.action_buka_kunci()
        self.assertEqual(penugasan.state, 'draft',
                         "State harus kembali ke 'draft' setelah buka kunci.")
