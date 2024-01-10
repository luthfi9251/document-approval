from odoo import fields, models, api

class HREmployee(models.Model):
    _name="docav.pegawai"
    _description="Model untuk pegawai yang ada"
    _inherit="hr.employee"
    _rec_name = "full_name"


    id_siakad = fields.Char(string = "ID Siakad")
    npwp = fields.Char(string = "NPWP") 
    no_kk = fields.Char(string = "No. KK") 
    nik = fields.Char(string = "NIK") 
    gelar_depan = fields.Char(string = "Gelar Depan", default="") 
    gelar_belakang = fields.Char(string = "Gelar Belakang", default="") 
    kecamatan = fields.Char(string = "Kecamatan")
    full_name = fields.Char(string = "Nama Lengkap", compute="_compute_fullname")
    no_dplk = fields.Char(string = "No. DPLK")
    rekening_bpd = fields.Char(string = "Rekening BPD")
    rekening_bni = fields.Char(string = "Rekening BNI")
    bpjs = fields.Char(string = "BPJS")
    no_sk_awal = fields.Char(string = "No SK Awal")
    tanggal_sk_awal = fields.Date(string = "Tanggal SK Awal")
    tanggal_lahir = fields.Date(string = "Tanggal Lahir")
    tempat_lahir = fields.Date(string = "Tempat Lahir")
    golongan_darah = fields.Selection([('a', 'A'), ('b', 'B'), ('ab', 'AB'), ('o','O'), ('x', 'Undefined')], string="Golongan Darah")
    gender = fields.Selection([('1','Laki-laki'), ('2', 'Perempuan')], string="Gender")
    marital_status = fields.Selection([('1', 'Belum Menikah'),('2','Menikah'), ('3', 'Duda/Janda')], string="Marital Status")
    npp = fields.Char(string="NPP")
    structural = fields.Selection([('1', 'Kepala'), ('2', 'Wakil'), ('3','Ketua'),('4', 'Sekretaris'), ('5','Anggota')], string="Structural")
    scope_kerja = fields.Many2one('docav.department', string='Departemen')
    status_kepegawaian = fields.Selection((('11', 'Dosen Tetap'), ('12','Pegawai Tetap'),('20', 'DosenKontrak'), ('21', 'PegawaiKontrak'),('88', 'Dosen Luar'),('89', 'Magang'), ('99', 'Lainnya')), string="Status Kepegawaian")
    status_terakhir = fields.Selection([('1', 'aktif'), ('2', 'non aktif'),('3','keluar'), ('4', 'meninggal'),('5','Pensiun'),('6', 'Pemberhentian Hormat'),('7', 'Pemberhentian tidak Hormat'),('8','Pemberhentian Sementara'),('9','Cuti diluar Tanggungan'),('10', 'Mengundurkan diri'),('0','undefined')], string="Status Terakhir")
    user_id = fields.Many2one('res.users', string="ID User")
    punya_user = fields.Boolean(string="Punya User", compute="_compute_is_punya_user")
    email= fields.Char(string="Email")
    phone=fields.Char(string="Phone")
    mobile=fields.Char(string="Mobile")
    aktif = fields.Boolean(string="Aktif")

    category_ids = fields.Char(string = "kategori")

    @api.depends("name", 'gelar_depan', 'gelar_belakang')
    def _compute_fullname(self):
        for record in self:
            if record["name"] and record["gelar_depan"] and record["gelar_belakang"]:
                record.full_name = record.gelar_depan + " " + record.name + " " +record.gelar_belakang
            else:
                record.full_name = ""
    
    @api.depends('punya_user')
    def _compute_is_punya_user(self):
        for record in self:
            if record.user_id:  # Mengecek apakah fields Many2one kosong atau tidak
                record.punya_user = True
            else:
                record.punya_user = False
