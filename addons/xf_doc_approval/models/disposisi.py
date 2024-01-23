from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from .selection import StatusSurat, KodeAgenda

from datetime import datetime

_editable_states = {
    False: [('readonly', False)],
    'draft': [('readonly', False)],
}

import logging
import os
import base64
import re, time

def cetak(var):
    logger = logging.getLogger(__name__)
    logger.info(var)

class LembarDisposisi(models.Model):
    # _name = 'xf.doc.approval.document.disposisi'
    _description = 'Model Lembar Disposisi'
    _inherit = 'xf.doc.approval.document.package'

    asal_dokumen = fields.Many2one('docav.pegawai', string="Dari", required=True, default=lambda self: self._default_asal_dokumen(), readonly=True)
    nomor = fields.Char(string="Nomor", states=_editable_states)
    tanggal_surat = fields.Date(string='Tanggal Surat', default=fields.Date.today, states=_editable_states)
    status_dokumen = fields.Selection(
        string='Status Dokumen',
        selection=StatusSurat.list,
        required=True,
        default=StatusSurat.default,
        states=_editable_states
    )
    tanggal_agenda = fields.Date(string='Tanggal Agenda')
    nomor_agenda = fields.Char(string="Nomor Agenda", readonly=True)
    kode_agenda = fields.Selection(
        string='Kode Agenda',
        selection=KodeAgenda.list,
        required=True,
        default=KodeAgenda.default
    )
    kode_nomor_agenda = fields.Char(string="No. Agenda", compute='_compute_kode_nomor_agenda')
    created_at = fields.Datetime(string='Tanggal Pembuatan', default=fields.Datetime.now, readonly=True)

    @api.depends('nomor_agenda', 'kode_agenda')
    def _compute_kode_nomor_agenda(self):
        if self.kode_agenda and self.nomor_agenda:
            self.kode_nomor_agenda = f"{self.kode_agenda}-{self.nomor_agenda}"
        else:
            self.kode_nomor_agenda = ""
    
    def _default_asal_dokumen(self):
        user_id = self.env.user
        employee_id = self.env["docav.pegawai"].search([("user_id","=",user_id.id)], limit=1)

        if employee_id:
            return employee_id.id
        else:
            return False
    
    def _generate_nomor_agenda(self):
        # Get the current year


        current_year = datetime.now().year

        # Search for the last document of the current year
        last_document = self.env['xf.doc.approval.document.package'].search([('created_at', '>=', f'{current_year}-01-01 00:00:00'), ('created_at', '<=', f'{current_year}-12-31 23:59:59')], order='created_at desc', limit=2)
        # If there is a last document, increment its code; otherwise, start from 1
        if len(last_document) > 1:
            last_code = last_document[1]["nomor_agenda"]
            last_code_number = int(last_code)
            new_code_number = last_code_number + 1
            new_code = f'{new_code_number:04d}'
        else:
            new_code = f'0000'

        return new_code
    
    def generate_nomor_agenda(self):
        if self["nomor_agenda"]:
            return
        else:
            self["nomor_agenda"] = self._generate_nomor_agenda()
    
    def generate_pdf(self):
        # Use the `report` module to generate PDF
        report_name = "xf_doc_approval.report_disposisi"  # Set the report template ID
        return self.env.ref(report_name).report_action(self)