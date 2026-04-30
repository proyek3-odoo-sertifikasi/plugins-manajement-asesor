from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDistribusiOtomatis(TransactionCase):
    """Unit test distribusi round-robin asesi ke asesor."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Buat group asesor
        cls.group_asesor = cls.env.ref('plugins_manajement_asesor.group_asesor')

        # Buat user asesor
        cls.asesor_users = cls.env['res.users']
        for i in range(1, 6):
            user = cls.env['res.users'].create({
                'name': 'Asesor Distrib %d' % i,
                'login': 'asesor_distrib_%d' % i,
                'email': 'asesor_distrib_%d@test.com' % i,
                'groups_id': [(4, cls.group_asesor.id)],
            })
            cls.asesor_users |= user

        # Buat partner asesi
        cls.asesi_partners = cls.env['res.partner']
        for i in range(1, 31):
            partner = cls.env['res.partner'].create({
                'name': 'Asesi Distrib %d' % i,
                'email': 'asesi_distrib_%d@test.com' % i,
            })
            cls.asesi_partners |= partner

    def _create_jadwal(self, asesi_count):
        """Helper: buat jadwal dengan sejumlah asesi."""
        asesi = self.asesi_partners[:asesi_count]
        jadwal = self.env['lsp.jadwal.ujian'].create({
            'name': 'Jadwal Distrib %s' % datetime.now().strftime('%H%M%S%f'),
            'skema_id': 'Skema Distrib Test',
            'tanggal_mulai': datetime.now(),
            'tanggal_selesai': datetime.now() + timedelta(hours=3),
            'ruangan': 'Ruang Distrib',
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
    # TestCase 1: test_distribusi_merata_genap
    # =============================================
    def test_distribusi_merata_genap(self):
        """20 asesi, 2 asesor → setiap asesor mendapat tepat 10 asesi."""
        jadwal = self._create_jadwal(asesi_count=20)
        penugasan = self._create_penugasan(jadwal, self.asesor_users[:2])

        penugasan.action_distribusi_otomatis()

        counts = set(penugasan.penugasan_line_ids.mapped('jumlah_asesi'))
        self.assertEqual(counts, {10},
                         "Setiap asesor harus mendapat tepat 10 asesi.")

    # =============================================
    # TestCase 2: test_distribusi_merata_ganjil
    # =============================================
    def test_distribusi_merata_ganjil(self):
        """15 asesi, 2 asesor → total 15, tidak ada > 10."""
        jadwal = self._create_jadwal(asesi_count=15)
        penugasan = self._create_penugasan(jadwal, self.asesor_users[:2])

        penugasan.action_distribusi_otomatis()

        total = sum(penugasan.penugasan_line_ids.mapped('jumlah_asesi'))
        max_count = max(penugasan.penugasan_line_ids.mapped('jumlah_asesi'))

        self.assertEqual(total, 15,
                         "Total asesi harus 15.")
        self.assertLessEqual(max_count, 10,
                             "Tidak boleh ada asesor yang menangani lebih dari 10 asesi.")

    # =============================================
    # TestCase 3: test_distribusi_satu_asesor_sedikit_asesi
    # =============================================
    def test_distribusi_satu_asesor_sedikit_asesi(self):
        """8 asesi, 1 asesor → semua 8 asesi masuk ke 1 asesor."""
        jadwal = self._create_jadwal(asesi_count=8)
        penugasan = self._create_penugasan(jadwal, self.asesor_users[:1])

        penugasan.action_distribusi_otomatis()

        self.assertEqual(penugasan.penugasan_line_ids[0].jumlah_asesi, 8,
                         "Asesor tunggal harus menangani semua 8 asesi.")

    # =============================================
    # TestCase 4: test_distribusi_ulang_tidak_duplikat
    # =============================================
    def test_distribusi_ulang_tidak_duplikat(self):
        """Distribusi 2 kali berturut → total tetap sama, tidak ada duplikat asesi."""
        jadwal = self._create_jadwal(asesi_count=20)
        penugasan = self._create_penugasan(jadwal, self.asesor_users[:2])

        # Distribusi pertama
        penugasan.action_distribusi_otomatis()
        total_first = sum(penugasan.penugasan_line_ids.mapped('jumlah_asesi'))

        # Distribusi kedua
        penugasan.action_distribusi_otomatis()
        total_second = sum(penugasan.penugasan_line_ids.mapped('jumlah_asesi'))

        self.assertEqual(total_first, total_second,
                         "Total asesi harus sama setelah distribusi ulang.")

        # Cek tidak ada duplikat asesi antar line
        all_asesi_ids = []
        for line in penugasan.penugasan_line_ids:
            all_asesi_ids.extend(line.asesi_ids.ids)
        self.assertEqual(len(all_asesi_ids), len(set(all_asesi_ids)),
                         "Tidak boleh ada duplikat asesi antar line.")

    # =============================================
    # TestCase 5: test_semua_asesi_tertugaskan
    # =============================================
    def test_semua_asesi_tertugaskan(self):
        """Setelah distribusi, set asesi di semua line == set asesi di jadwal."""
        jadwal = self._create_jadwal(asesi_count=18)
        penugasan = self._create_penugasan(jadwal, self.asesor_users[:2])

        penugasan.action_distribusi_otomatis()

        asesi_di_jadwal = set(jadwal.asesi_ids.ids)
        asesi_di_line = set()
        for line in penugasan.penugasan_line_ids:
            asesi_di_line.update(line.asesi_ids.ids)

        self.assertEqual(asesi_di_jadwal, asesi_di_line,
                         "Semua asesi di jadwal harus tertugaskan, tidak ada yang terlewat.")
