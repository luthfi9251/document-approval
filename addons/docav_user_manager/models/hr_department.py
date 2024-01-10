from odoo import fields, models, api

class HREmployee(models.Model):
    _name="docav.department"
    _description="Model untuk departemen"
    _inherit="hr.department"

    tipe_unit = fields.Selection([('0', 'Universitas'), ('1','Fakultas'),('2','Jurusan'), ('3','Prodi'),('4','Laboratorium'),('5','UPT'),('6','Penyelenggara MKU'),('7', 'Ormawa')], string = "Tipe Unit")
    sekretaris = fields.Many2one('docav.pegawai', string = "Sekretaris")
    singkatan = fields.Char(string="Singkatan")
    nama_inggris = fields.Char(string="nama_inggris")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    fax = fields.Char(string="Fax.")
    sambutan_ketua = fields.Html(string="Sambutan Ketua")
    sambutan_inggris = fields.Html(string="Sambutan Inggris")
    visi = fields.Char(string="Visi")
    visi_inggirs = fields.Char(string="Visi Inggris")
    misi = fields.Html(string="Misi")
    misi_inggris = fields.Html(string="Misi Inggris")
    kode_fakultas = fields.Char(string="Kode Fakultas")




