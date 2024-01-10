from odoo import fields, models, api

class User(models.Model):
    _inherit = "res.users"

    id_role = fields.Many2one('users.role', string='Role User', default=lambda self: self.env['users.role'].search([('name','=','None')]))

    @api.model
    def create(self, vals):
        # Jika user yang baru dibuat tidak memiliki role_id, berikan nilai default
        if not vals.get('id_role'):
            # Ganti 'default_role_id' dengan ID role default yang diinginkan
            default_role_id = self.env['user_oauth_manager.users.role'].search([('id', '=', 1)], limit=1)  # Ganti dengan ID role default yang diinginkan
            vals['id_role'] = default_role_id.id if default_role_id else False

        return super(User, self).create(vals)