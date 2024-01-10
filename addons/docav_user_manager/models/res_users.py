from odoo import fields, models, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        new_user = super(ResUsers, self).create(vals)
        pegawai = self.env['docav.pegawai'].search([('email', '=', new_user.email)], limit=1)
        if pegawai:
            pegawai.write({'user_id': new_user.id})
            new_user.write({'groups_id': [(6, 0, [1,16,17,7,13,6])]})

        return new_user