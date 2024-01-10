from odoo import fields, models, api

class UserRole(models.Model):
    _name = "users.role"
    _description = "Data Role User"

    name = fields.Char(string='Role Name', required=True)

    @api.model
    def _auto_init_data(self):
        roles = [
            {'name': 'None'}
        ]

        for role_data in roles:
            self.create(role_data)
    