from odoo import fields, models, api
import logging


def cetak(var):
    logger = logging.getLogger(__name__)
    logger.info(var)
    

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
    tempat_lahir = fields.Char(string = "Tempat Lahir")
    golongan_darah = fields.Selection([('a', 'A'), ('b', 'B'), ('ab', 'AB'), ('o','O'), ('x', 'Undefined')], string="Golongan Darah")
    gender = fields.Selection([('1','Laki-laki'), ('2', 'Perempuan')], string="Gender")
    marital_status = fields.Selection([('1', 'Belum Menikah'),('2','Menikah'), ('3', 'Duda/Janda')], string="Marital Status")
    npp = fields.Char(string="NPP")
    structural = fields.Selection([('1', 'Kepala'), ('2', 'Wakil'), ('3','Ketua'),('4', 'Sekretaris'), ('5','Anggota')], string="Structural")
    scope_kerja = fields.Many2one('docav.department', string='Departemen')
    status_kepegawaian = fields.Selection((('11', 'Dosen Tetap'), ('12','Pegawai Tetap'),('20', 'DosenKontrak'), ('21', 'PegawaiKontrak'),('88', 'Dosen Luar'),('89', 'Magang'), ('99', 'Lainnya')), string="Status Kepegawaian")
    status_terakhir = fields.Selection([('1', 'aktif'), ('2', 'non aktif'),('3','keluar'), ('4', 'meninggal'),('5','Pensiun'),('6', 'Pemberhentian Hormat'),('7', 'Pemberhentian tidak Hormat'),('8','Pemberhentian Sementara'),('9','Cuti diluar Tanggungan'),('10', 'Mengundurkan diri'),('0','undefined')], string="Status Terakhir", default="0")
    user_id = fields.Many2one('res.users', string="ID User")
    punya_user = fields.Boolean(string="Punya User", compute="_compute_is_punya_user")
    email= fields.Char(string="Email")
    phone=fields.Char(string="Phone")
    mobile=fields.Char(string="Mobile")
    aktif = fields.Boolean(string="Aktif")
    category_ids = fields.Char(string = "kategori")
    resource_id = fields.Many2one('resource.resource', required=False, default=False)

    @api.depends("name", 'gelar_depan', 'gelar_belakang')
    def _compute_fullname(self):
        for record in self:
            gelar_depan = record["gelar_depan"] if record["gelar_depan"] else ""
            gelar_belakang = record["gelar_belakang"] if record["gelar_belakang"] else ""
            if record["name"]:
                record.full_name = gelar_depan + " " + record.name + " " +gelar_belakang
            else:
                record.full_name = ""
    
    @api.depends('punya_user')
    def _compute_is_punya_user(self):
        for record in self:
            nama_user_default = f"docav_{record.name}"
            default_user =  self.env['res.users'].search([('name', '=', nama_user_default)])
            if record.user_id and record.user_id != default_user:  # Mengecek apakah fields Many2one kosong atau tidak
                record.punya_user = True
            else:
                record.punya_user = False
    
    @api.depends('status_terakhir')
    def _compute_aktif(self):
        for record in self:
            if int(record.status_terakhir) in [ 1,2,9 ]:
                record.aktif = True
            else:
                record.aktif = False
    
    # @api.onchange('name')
    # def _onchange_name(self):
    #     if self.name and not self.resource_id:
    #         new_resource = self.env['resource.resource'].create({'name': self.name})
    #         self.resource_id = new_resource
    #         if not self.user_id:
    #             default_user =  self.env['res.users'].search([('login', '=', 'default_docav')], limit=1)
    #             self.user_id = default_user
    
    # @api.onchange('resource_id')
    # def _onchange_resouce_id(self):
    #     pass

    # def _default_user_id(self):
    #     default_user =  self.env['res.users'].search([('login', '=', 'default_docav')], limit=1)
    #     return default_user.id
    
    @api.model
    def create(self, vals):
        new_resource = self.env['resource.resource'].create({'name': vals["name"]})
        group_initiator_docav = self.env.ref('xf_doc_approval.group_xf_doc_approval_user')
        group_internal = self.env.ref('base.group_user')
        user_id_data = {
            "name": f'docav_{vals["name"]}',
            "login": f'docav_{vals["email"]}',
            "password" : "cobatebakpassnya",
            "groups_id": [(4, group_internal.id),(4,group_initiator_docav.id)]
        }
        default_user =  self.env['res.users'].create(user_id_data)
        vals["resource_id"] = new_resource.id
        vals["user_id"] = default_user.id
        pegawai = super(HREmployee, self).create(vals)
        
        return pegawai

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        
        if name:
            records = self.search([('name', operator, name)])
            return records.name_get()
        
        
        return self.search([('full_name', operator, name)]+args, limit=limit).name_get()


    
