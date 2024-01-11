from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from .selection import ApprovalMethods, DocumentState, ApproverState, ApprovalStep, DocumentVisibility

import logging
import os
import base64
import re, time

def cetak(var):
    logger = logging.getLogger(__name__)
    logger.info(var)
    


_editable_states = {
    False: [('readonly', False)],
    'draft': [('readonly', False)],
}


class DocApprovalDocumentPackage(models.Model):
    _name = 'xf.doc.approval.document.package'
    _inherit = ['mail.thread']
    _description = 'Document Package'

    active = fields.Boolean(default=True)
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        readonly=True,
        states=_editable_states,
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        translate=True,
    )
    state = fields.Selection(
        string='Status',
        selection=DocumentState.list,
        required=True,
        default=DocumentState.default,
        readonly=True,
        tracking=True,
    )
    approval_state = fields.Selection(
        string='Approval Status',
        selection=ApproverState.list,
        compute='_compute_approval_state',
    )
    approval_step = fields.Selection(
        string='Approval Step',
        selection=ApprovalStep.list,
        compute='_compute_approval_step',
    )
    method = fields.Selection(
        string='Approval Method',
        selection=ApprovalMethods.list,
        required=True,
        default=ApprovalMethods.default,
        readonly=True,
        states=_editable_states,
    )
    visibility = fields.Selection(
        string='Visibility',
        selection=DocumentVisibility.list,
        required=True,
        default=DocumentVisibility.default,
    )
    initiator_user_id = fields.Many2one(
        string='Initiator',
        comodel_name='res.users',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        states=_editable_states,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
        states=_editable_states,
    )
    approval_team_id = fields.Many2one(
        string='Approval Team',
        comodel_name='xf.doc.approval.team',
        readonly=True,
        states=_editable_states,
        domain="[('company_id', '=', company_id)]",
    )
    approver_ids = fields.One2many(
        string='Approvers',
        comodel_name='xf.doc.approval.document.approver',
        inverse_name='document_package_id',
        readonly=True,
        states=_editable_states,
    )
    document_ids = fields.One2many(
        string='Documents',
        comodel_name='xf.doc.approval.document',
        inverse_name='document_package_id',
        readonly=True,
        states=_editable_states,
    )

    is_initiator = fields.Boolean('Is Initiator', compute='_compute_access')
    is_approver = fields.Boolean('Is Approver', compute='_compute_access')
    reject_reason = fields.Text('Reject Reason')

    # Compute fields

    @api.depends('state', 'approval_team_id')
    def _compute_access(self):
        for record in self:
            # Check if the current user is initiator (true for admin)
            record.is_initiator = self.env.user == record.initiator_user_id or self.env.user._is_admin()

            # Check if the document needs approval from current user (true for admin)
            current_approvers = record.get_current_approvers()
            cetak("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            cetak(current_approvers)
            responsible = self.env.user in current_approvers.mapped('employee_id.user_id') or self.env.user._is_admin()
            record.is_approver = record.approval_state == 'pending' and responsible

    @api.depends('approver_ids.state')
    def _compute_approval_state(self):
        for record in self:
            approvers = record.approver_ids
            if len(approvers) == len(approvers.filtered(lambda a: a.state == 'approved')):
                record.approval_state = 'approved'
            elif approvers.filtered(lambda a: a.state == 'rejected'):
                record.approval_state = 'rejected'
            elif approvers.filtered(lambda a: a.state == 'pending'):
                record.approval_state = 'pending'
            else:
                record.approval_state = 'to approve'

    @api.depends('approver_ids.state', 'approver_ids.step')
    def _compute_approval_step(self):
        for record in self:
            approval_step = None
            steps = record.approver_ids.mapped('step')
            steps.sort()
            for step in steps:
                if record.approver_ids.filtered(lambda a: a.step == step and a.state != 'approved'):
                    approval_step = step
                    break
            record.approval_step = approval_step

    # Onchange handlers

    @api.onchange('approval_team_id')
    def onchange_approval_team(self):
        if self.approval_team_id:
            team_approvers = []
            for team_approver in self.approval_team_id.approver_ids:
                team_approvers += [{
                    'step': team_approver.step,
                    'user_id': team_approver.employee_id.user_id.id,
                    'role': team_approver.role,
                    'employee_id': team_approver.employee_id
                }]
            approvers = self.approver_ids.browse([])
            for a in team_approvers:
                approvers += approvers.new(a)
            self.approver_ids = approvers

    @api.onchange('approver_ids')
    def onchange_approvers(self):
        if self.approval_team_id:
            cetak("Terdapat approval_team_id")
            if self.approval_team_id.approver_ids.mapped('employee_id.user_id') != self.approver_ids.mapped('employee_id.user_id'):
                self.approval_team_id = None

    # Validation

    @api.constrains('company_id')
    def _validate_company(self):
        for record in self:
            record.approver_ids.validate_company(record.company_id)

    @api.constrains('state', 'approver_ids')
    def _check_approvers(self):
        for record in self:
            if record.state == 'approval' and not record.approver_ids:
                raise ValidationError(_('Please add at least one approver!'))

    @api.constrains('state', 'document_ids')
    def _check_documents(self):
        for record in self:
            if record.state == 'approval' and not record.document_ids:
                raise ValidationError(_('Please add at least one document!'))

    # Helpers
    def set_state(self, state, vals=None):
        if vals is None:
            vals = {}
        vals.update({'state': state})
        return self.write(vals)

    def get_next_approvers(self):
        self.ensure_one()
        next_approvers = self.approver_ids.filtered(lambda a: a.state == 'to approve').sorted('step')
        if not next_approvers:
            return next_approvers
        next_step = next_approvers[0].step
        return next_approvers.filtered(lambda a: a.step == next_step)

    def get_current_approvers(self):
        self.ensure_one()
        cetak("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        cetak(self.approver_ids.filtered(lambda a: a.state == 'pending' and a.step == self.approval_step))
        return self.approver_ids.filtered(lambda a: a.state == 'pending' and a.step == self.approval_step)

    def get_current_approver(self):
        self.ensure_one()
        current_approvers = self.get_current_approvers()
        if not current_approvers:
            raise UserError(_('There are not approvers for this document package!'))

        current_approver = current_approvers.filtered(lambda a: a.employee_id.user_id == self.env.user)
        if not current_approver and self.env.user._is_admin():
            current_approver = current_approvers[0]
        if not current_approver:
            raise AccessError(_('You are not allowed to approve this document package!'))
        return current_approver

    def send_notification(self, view_ref, partner_ids):
        for record in self:
            record.message_post_with_view(
                view_ref,
                subject=_('Document Approval: %s') % record.name,
                composition_mode='mass_mail',
                partner_ids=[(6, 0, partner_ids)],
                auto_delete=False,
                auto_delete_message=False,
                parent_id=False,
                subtype_id=self.env.ref('mail.mt_note').id)

    # User actions

    def action_send_for_approval(self):
        for record in self:
            if record.state == 'draft' and record.approver_ids:
                # Subscribe approvers
                record.message_subscribe(partner_ids=record.approver_ids.mapped('employee_id.user_id').mapped('partner_id').ids)
            if record.approval_state == 'pending':
                raise UserError(_('The document package have already been sent for approval!'))
            elif record.approval_state == 'approved':
                raise UserError(_('The document package have already been approved!'))
            elif record.approval_state == 'rejected':
                raise UserError(_('The document package was rejected! To send it for approval again, please update document(s) first.'))
            elif record.approval_state == 'to approve':
                next_approvers = record.get_next_approvers()
                if next_approvers:
                    if record.state == 'draft':
                        record.state = 'approval'
                    next_approvers.write({'state': 'pending'})
                    partner_ids = next_approvers.mapped('employee_id.user_id').mapped('partner_id').ids
                    record.send_notification('xf_doc_approval.request_to_approve', partner_ids)
                else:
                    raise UserError(_('There are not approvers for this document package!'))

    def action_approve_wizard(self):
        self.ensure_one()
        current_approver = self.get_current_approver()
        return current_approver.action_wizard('action_approve_wizard', _('Approve'))

    def action_reject_wizard(self):
        self.ensure_one()
        current_approver = self.get_current_approver()
        return current_approver.action_wizard('action_reject_wizard', _('Reject'))

    def action_draft(self):
        for record in self:
            record.approver_ids.write({'state': 'to approve', 'notes': None})
            record.write({'state': 'draft', 'reject_reason': None})
        return True

    def action_cancel(self):
        if not self.env.user._is_admin() and self.filtered(lambda record: record.state == 'approved'):
            raise UserError(_("Cannot cancel a document package that is approved."))
        return self.set_state('cancelled')

    def action_finish_approval(self):
        for record in self:
            if record.approval_state == 'approved':
                record.state = 'approved'
            else:
                raise UserError(_('Document Package must be fully approved!'))

    # Built-in methods

    def unlink(self):
        if any(self.filtered(lambda record: record.state not in ('draft', 'cancelled'))):
            raise UserError(_('You cannot delete a record which is not draft or cancelled!'))
        return super(DocApprovalDocumentPackage, self).unlink()

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'approval':
            return self.env.ref('xf_doc_approval.mt_document_package_approval')
        elif 'state' in init_values and self.state == 'approved':
            return self.env.ref('xf_doc_approval.mt_document_package_approved')
        elif 'state' in init_values and self.state == 'cancelled':
            return self.env.ref('xf_doc_approval.mt_document_package_cancelled')
        elif 'state' in init_values and self.state == 'rejected':
            return self.env.ref('xf_doc_approval.mt_document_package_rejected')

        return super(DocApprovalDocumentPackage, self)._track_subtype(init_values)


class DocApprovalDocument(models.Model):
    _name = 'xf.doc.approval.document'
    _description = 'Document'

    document_package_id = fields.Many2one(
        string='Document Package',
        comodel_name='xf.doc.approval.document.package',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    file = fields.Binary(
        string='File'
    )
    file_path = fields.Char(
        string="File Path",
        required=True,
    )
    file_uploaded = fields.Boolean(
        string="File Terupload",
        default=False,
        readonly=True
    )
    file_name = fields.Char(
        string='File Name'
    )

    @api.onchange('file_name')
    def _onchange_file_name(self):
        if self.file_name and not self.name:
            self.name = self.file_name
    
    @api.onchange('file', 'file_name')
    def _onchange_file_path(self):
        if self.file and self.file_name:
            file_name = self.generate_filename(self.file_name)
            # Tetapkan lokasi penyimpanan file
            self.file_path = f'/etc/file-storage/documents/{file_name}'
    
    @api.model
    def create(self, vals):
        new_record = super(DocApprovalDocument, self).create(vals)
        new_record.save_file_locally()  # Memanggil fungsi save_file_locally saat record baru dibuat
        return new_record
    
    def unlink(self):
        for record in self:
            if record.file_uploaded:
                if os.path.exists(record.file_path):
                    os.remove(record.file_path)
        
        return super(DocApprovalDocument, self).unlink()

    def save_file_locally(self):
        for record in self:
            if record.file:
                # Tulis data file ke dalam file lokal
                file_data = base64.b64decode(self.file)
                with open(record.file_path, 'wb') as file:
                    file.write(file_data)
                record.file_uploaded = True
                record.file = False
    
    def download_file(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        controller_url = f"{base_url}/download/file?id={self.id}"
        return {
            'type': 'ir.actions.act_url',
            'url': controller_url,
            'target': 'self',
        }

    def generate_filename(self, file):
        '''
            yang harus dilakukan pada saat generate file name
            1. pastikan file name hanya memiliki satu format ex .pdf tidak boleh ada perulangan .ec.re
            2. hanya boleh ada satu .
            3. gunakan filename yang ramah url / tidak diperbolehkan ada simbol khusus
        '''
        filename_list = os.path.basename(file).split(".")
        file_name = "-".join(filename_list[0:-1])
        file_format = filename_list[-1]

        #ubah spasi dan symbol menjadi -
        pattern = r"[\s\W]"
        file_name1 = re.sub(pattern, "-", file_name)
        return f"{time.time_ns()}-{file_name1}.{file_format}"  
