from odoo import fields, models, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        new_user = super(ResUsers, self).create(vals)
        pegawai = self.env['docav.pegawai'].search([('email', '=', new_user.email)])
        for peg in pegawai:
            peg.write({'user_id': new_user.id})
        if pegawai:
            new_user.oauth_provider_id = False

        return new_user