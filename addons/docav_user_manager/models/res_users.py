from odoo import fields, models, api
import logging

def cetak(var):
    logger = logging.getLogger(__name__)
    logger.info(var)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        new_user = super(ResUsers, self).create(vals)
        pegawai = self.env['docav.pegawai'].search([('email', '=', new_user.email)], limit=1)
        group_internal = self.env.ref('base.group_user')
        group_initiator_docav = self.env.ref('xf_doc_approval.group_xf_doc_approval_initiator')
        group_no_one = self.env.ref('base.group_no_one')
        group_mail_template_editor = self.env.ref('mail.group_mail_template_editor')
        group_partner_manager = self.env.ref('base.group_partner_manager')
        group_export = self.env.ref('base.group_allow_export')
        group_private_adress = self.env.ref('base.group_private_addresses')
        

        if pegawai:
            default_user_id = pegawai.user_id.id
            pegawai.write({'user_id': new_user.id})
            new_user.write({'groups_id': [(6, 0, [group_internal.id, group_initiator_docav.id, group_no_one.id, group_mail_template_editor.id, group_partner_manager.id, group_export.id, group_private_adress.id])]})
            delete_default_user_id = self.env['res.users'].search([('id', '=', default_user_id)], limit=1)
            if delete_default_user_id:
                delete_default_user_id.unlink()


        return new_user
    
    def docav_user_default_hook(self):
        # Create the new user record
        user = super(ResUsers, self).create({
            'name': 'docav default',
            'login': 'docav_default',
            'password': 'cobatebak',
            'email': 'docav_default@example.com'
        })
        # Assign necessary groups
        user.write({'groups_id': [(4, self.env.ref('base.group_user').id)]})