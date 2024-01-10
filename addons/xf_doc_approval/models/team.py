# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .selection import ApproverState, ApprovalMethods, ApprovalStep

def get_selection_label(self, object, field_name, field_value):
  return _(dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])

import logging

def cetak(var):
    logger = logging.getLogger(__name__)
    logger.info(var)

class DocApprovalTeam(models.Model):
    _name = 'xf.doc.approval.team'
    _description = 'Doc Approval Team'

    active = fields.Boolean('Active', default=True)

    name = fields.Char(
        string='Name',
        required=True,
    )
    user_id = fields.Many2one(
        string='Team Leader',
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user,
        index=True
    )
    employee_name = fields.Char(
        string='Nama Team Leader',
        compute='_compute_team_leader'
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company.id,
        index=True,
    )
    approver_ids = fields.One2many(
        string='Approvers',
        comodel_name='xf.doc.approval.team.approver',
        inverse_name='team_id',
    )

    # Validation

    @api.constrains('company_id')
    def _check_team_company(self):
        for team in self:
            team.approver_ids.validate_company(team.company_id)
    
    @api.depends('user_id')
    def _compute_team_leader(self):
        for record in self:
            if record.user_id:
                pegawai_obj = self.env['docav.pegawai'].search([('user_id', '=', record.user_id.id)], limit=1)
                record.employee_name = pegawai_obj.full_name if pegawai_obj else "Unknown"


class DocApprovalApproverAbstract(models.Model):
    _name = 'xf.doc.approval.approver.abstract'
    _description = 'Abstract Approver'
    _order = 'step'
    _rec_name = 'user_id'
    step = fields.Selection(
        string='Step',
        selection=ApprovalStep.list,
        required=True,
        default=ApprovalStep.default,
    )
    user_id = fields.Many2one(
        string='Nama User',
        comodel_name='res.users'
    )
    employee_id = fields.Many2one(
        string="Nama Pegawai",
        comodel_name='docav.pegawai',
        required=True
    )
    role = fields.Char(
        string='Role/Position',
        required=True,
        default="Approver"
    )


    # Onchange handlers

    @api.onchange('employee_id')
    def _update_user_id(self):
        users = []
        for approver in self:
            if approver.employee_id:
                structure = approver.employee_id.structural
                jabatan = get_selection_label(self, 'docav.pegawai', 'structural', structure)
                department = approver.employee_id.scope_kerja.name
                approver.role = f"{jabatan} - {department}"

    # Validation

    @api.constrains('employee_id')
    def _check_users(self):
        for approver in self:
            if not approver.employee_id.user_id.has_group('xf_doc_approval.group_xf_doc_approval_user'):
                raise ValidationError(_('%s does not have access to the Doc Approval module.') % (approver.employee_id.user_id.name,)
                                      + '\n' +
                                      _('Please ask system administrator to add him/her to the Doc Approval module group first.'))

    def validate_company(self, company):
        if not company:
            return
        
        for approver in self:
        
            if company not in approver.employee_id.user_id.company_ids:
                raise ValidationError(
                    _('%s does not have access to the company %s') % (approver.employee_id.user_id.name, company.name))


class DocApprovalTeamApprover(models.Model):
    _name = 'xf.doc.approval.team.approver'
    _inherit = ['xf.doc.approval.approver.abstract']
    _description = 'Approval Team Member'

    team_id = fields.Many2one(
        string='Team',
        comodel_name='xf.doc.approval.team',
        required=True,
        ondelete='cascade'
    )

    # Validation

    @api.constrains('employee_id', 'team_id')
    def _check_users(self):
        for approver in self:
            approver.validate_company(approver.team_id.company_id)
        return super(DocApprovalTeamApprover, self)._check_users()


class DocApprovalDocumentApprover(models.Model):
    _name = 'xf.doc.approval.document.approver'
    _inherit = ['xf.doc.approval.approver.abstract']
    _description = 'Doc Approver'

    team_approver_id = fields.Many2one(
        string='Doc Team Approver',
        comodel_name='xf.doc.approval.team.approver',
        ondelete='set null'
    )
    document_package_id = fields.Many2one(
        string='Document Package',
        comodel_name='xf.doc.approval.document.package',
        required=True,
        ondelete='cascade',
    )
    method = fields.Selection(
        string='Method',
        selection=ApprovalMethods.list,
        related='document_package_id.method',
        readonly=True,
    )
    state = fields.Selection(
        string='Status',
        selection=ApproverState.list,
        readonly=True,
        required=True,
        default=ApproverState.default
    )
    notes = fields.Text(
        string='Notes',
        readonly=True,
    )

    # Validation

    @api.constrains('employee_id', 'document_package_id')
    def _check_users(self):
        for approver in self:
            approver.validate_company(approver.document_package_id.company_id)
        return super(DocApprovalDocumentApprover, self)._check_users()

    # User actions

    def action_wizard(self, view_ref, window_title):
        self.ensure_one()
        view = self.env.ref('xf_doc_approval.' + view_ref)
        return {
            'name': window_title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new'
        }

    def action_approve(self):
        for approver in self:
            document_package = approver.document_package_id
            approver.state = 'approved'
            if document_package.approval_state == 'to approve':
                document_package.sudo().action_send_for_approval()
            elif document_package.approval_state == 'approved':
                document_package.sudo().action_finish_approval()

    def action_reject(self):
        for approver in self:
            approver.state = 'rejected'
            approver.document_package_id.sudo().set_state('rejected', {'reject_reason': approver.notes})
