from datetime import datetime, timedelta

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
# import datetime
import base64
import logging
import xlrd
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date
import json
import re

_logger = logging.getLogger(__name__)


class ProductRequest(models.Model):
    _name = "product.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Request"
    _order = 'id desc'

    name = fields.Char(string="Request No", readonly=True, required=True, copy=False, default='New')
    requested_date = fields.Date(string="Requested Date", default=lambda self: fields.Date.today(), readonly=True)

    replacement_method = fields.Selection([
        ('replacement', 'Replacement'),
        ('new_req', 'New requirement at existing location'),
        ('add_upgrade', 'Capacity Addition or upgrade'),
        ('new_location', 'New Location')
    ], string='Purchase Type', readonly=True,
    )

    # replacement_reason = fields.Text(string="Why Replacement required", help="Describe the reason for replacement", required=True)
    # need_of_oldAsset = fields.Text(string="What are we going to do with old asset", required=True)
    # oldAsset_capDate = fields.Date(string="Old asset Capitalisation date", required=True)
    # BookValue = fields.Float(string="Book Value", required=True)
    # app_resale_value = fields.Float(string="Approx resale value", required=True)
    # rep_photo_upload = fields.Binary("Attachment of existing item photos")
    # select_budgeted = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Budgeted', tracking=True, required=True)

    # justification = fields.Text(string="Business Justification", required=True)
    # annualBusiness_newAddition = fields.Float(string="Additional annual busines with new addition", required=True)
    # break_even_period = fields.Integer(string="Break Even Period", required=True)

    # curr_cap_utilization = fields.Float(string="What is the current capacity utilisation")
    # exp_monthly_revenue = fields.Float(string="Addional monthly revenue expected with additional capacity")
    # location_detail = fields.Char(string="Location Details")

    replacement_reason = fields.Text(string="Why Replacement required", help="Describe the reason for replacement", tracking=True)
    need_of_oldAsset = fields.Text(string="What are we going to do with old asset", tracking=True)
    oldAsset_capDate = fields.Date(string="Old asset Capitalisation date", tracking=True)
    BookValue = fields.Float(string="Book Value", tracking=True)
    app_resale_value = fields.Float(string="Approx resale value", tracking=True)
    rep_photo_upload = fields.Binary("Attachment of existing item photos", tracking=True)
    select_budgeted = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Budgeted', tracking=True)
    justification = fields.Text(string="Business Justification", tracking=True)
    annualBusiness_newAddition = fields.Float(string="Additional annual busines with new addition", tracking=True)
    break_even_period = fields.Integer(string="Break Even Period", tracking=True)
    curr_cap_utilization = fields.Float(string="What is the current capacity utilisation", tracking=True)
    exp_monthly_revenue = fields.Float(string="Addional monthly revenue expected with additional capacity", tracking=True)
    location_detail = fields.Char(string="Location Details", tracking=True)


    def _get_required_fields(self):
        required_fields = []
        if self.replacement_method == 'replacement':
            required_fields = [
                ('replacement_reason', 'Why Replacement required'),
                ('need_of_oldAsset', 'What are we going to do with old asset'),
                ('oldAsset_capDate', 'Old asset Capitalisation date'),
                ('BookValue', 'Book Value'),
                ('app_resale_value', 'Approx resale value'),
            ]
        elif self.replacement_method == 'new_req':
            required_fields = [
                ('justification', 'Business Justification'),
                ('annualBusiness_newAddition', 'Additional annual business with new addition'),
                ('break_even_period', 'Break Even Period'),
                ('select_budgeted', 'Budgeted'),
            ]
        elif self.replacement_method == 'add_upgrade':
            required_fields = [
                ('curr_cap_utilization', 'What is the current capacity utilisation'),
                ('exp_monthly_revenue', 'Additional monthly revenue expected with additional capacity'),
                ('break_even_period', 'Break Even Period'),
                ('select_budgeted', 'Budgeted'),
                ('location_detail', 'Location Details'),
            ]
        elif self.replacement_method == 'new_location':
            required_fields = []
        return required_fields

    @api.constrains('replacement_method', 'replacement_reason', 'need_of_oldAsset', 'oldAsset_capDate',
                    'BookValue', 'app_resale_value', 'rep_photo_upload', 'select_budgeted', 'justification',
                    'annualBusiness_newAddition', 'break_even_period', 'curr_cap_utilization',
                    'exp_monthly_revenue', 'location_detail', 'date_field')
    def _check_required_fields(self):
        cutoff_date = datetime.strptime('2025-07-02', '%Y-%m-%d').date()
        for record in self:
            print("record date",record.requested_date)
            if record.expense_type == 'cap' and record.requested_date and record.requested_date>= cutoff_date:
                if not record.replacement_method:
                    raise ValidationError(
                        "Purchase Type is mandatory when expense type is 'Capex' when the date is on or after July 2, 2025."
                    )
                required_fields = record._get_required_fields()
                print("the required field are",required_fields)
                if required_fields:
                    empty_fields = []
                    for field_name, field_label in required_fields:
                        value = getattr(record, field_name)
                        if value is False or value is None or value == '':
                            empty_fields.append(field_label)
                    if empty_fields:
                        raise ValidationError(
                            f"The following fields are mandatory for {record.replacement_method} when the date is after July 2, 2025: {', '.join(empty_fields)}"
                        )

    @api.model
    def create(self, vals):
        record = super(ProductRequest, self).create(vals)
        record._check_required_fields()
        return record

    def write(self, vals):
        res = super(ProductRequest, self).write(vals)
        self._check_required_fields()
        return res

    @api.onchange('expense_type')
    def _onchange_expense_type(self):
        """Set default values based on expense_type and replacement_method."""
        if self.expense_type == 'op':  # OpEx case
            self.replacement_method = False  # Not applicable, but required=False handled by attrs
            self.replacement_reason = 'N/A'
            self.need_of_oldAsset = 'N/A'
            self.oldAsset_capDate = fields.Date.today()
            self.BookValue = 0.0
            self.app_resale_value = 0.0
            # self.rep_photo_upload = False
            self.select_budgeted = 'no'  # Default for OpEx, assuming no budget allocation
            self.justification = 'Operational need'
            self.annualBusiness_newAddition = 0.0
            self.break_even_period = 0
            self.curr_cap_utilization = 0.0
            self.exp_monthly_revenue = 0.0
            self.location_detail = 'N/A'

    @api.onchange('replacement_method')
    def _onchange_replacement_method(self):
        """Set default values for fields tied to non-selected replacement_method options."""
        if self.replacement_method == 'replacement':
            print("-----its replacement ", self.justification)
            print("-----its replacement ",self.location_detail)
            self.replacement_reason = ''
            self.need_of_oldAsset = ''
            self.oldAsset_capDate = ''
            self.BookValue = ''
            self.app_resale_value = ''
            self.rep_photo_upload = self.rep_photo_upload
            self.select_budgeted = self.select_budgeted
            # Reset fields for other options
            self.justification = 'NA'
            self.annualBusiness_newAddition = 0.0
            self.break_even_period = 0
            self.curr_cap_utilization = 0.0
            self.exp_monthly_revenue = 0.0
            self.location_detail = 'NA'
        elif self.replacement_method == 'new_req':
            print("-----new req ",self.replacement_reason)
            self.justification = ''
            self.annualBusiness_newAddition = ''
            self.break_even_period = ''
            # Reset fields for other options
            self.replacement_reason = 'NA'
            self.need_of_oldAsset = 'NA'
            self.oldAsset_capDate = fields.Date.today()
            self.BookValue = 0.0
            self.app_resale_value = 0.0
            self.rep_photo_upload = False
            self.curr_cap_utilization = 0.0
            self.exp_monthly_revenue = 0.0
            self.location_detail = 'NA'
        elif self.replacement_method == 'add_upgrade':
            self.curr_cap_utilization = ''
            self.exp_monthly_revenue = ''
            self.location_detail = ''
            # Reset fields for other options
            self.replacement_reason = 'NA'
            self.need_of_oldAsset = 'NA'
            self.oldAsset_capDate = fields.Date.today()
            self.BookValue = 0.0
            self.app_resale_value = 0.0
            self.rep_photo_upload = False
            self.justification = 'NA'
            self.annualBusiness_newAddition = 0.0
        elif self.replacement_method == 'new_location':
            # Reset fields for all other options
            self.replacement_reason = 'NA'
            self.need_of_oldAsset = 'NA'
            self.oldAsset_capDate = fields.Date.today()
            self.BookValue = 0.0
            self.app_resale_value = 0.0
            self.rep_photo_upload = False
            self.justification = 'NA'
            self.annualBusiness_newAddition = 0.0
            self.break_even_period = 0
            self.curr_cap_utilization = 0.0
            self.exp_monthly_revenue = 0.0
        else:
            # Reset all fields if no method is selected
            self.replacement_reason = 'NA'
            self.need_of_oldAsset = 'NA'
            self.oldAsset_capDate = fields.Date.today()
            self.BookValue = 0.0
            self.app_resale_value = 0.0
            self.rep_photo_upload = False
            self.justification = 'NA'
            self.annualBusiness_newAddition = 0.0
            self.break_even_period = 0
            self.curr_cap_utilization = 0.0
            self.exp_monthly_revenue = 0.0
            self.location_detail = 'NA'

    product_request_line_ids = fields.One2many('product.request.line',
                                               'product_request_id',
                                               string='Product Request Line',
                                               tracking=True)

    pr_approve_line = fields.One2many('pr.approve.line',
                                      'product_request_id',
                                      string='Pr Approve Line',
                                      tracking=True)
    cr_need_approve_line = fields.One2many('cr.need.approve.line',
                                      'product_request_id',
                                      string='CR Need Approve Line',
                                      tracking=True)

    pr_rfi_ids = fields.One2many('pr.rfi.line',
                                 'pr_id',
                                 string='Product Request Line',
                                 tracking=True)

    status = fields.Selection(
        selection=[('draft', 'DRAFT'),('initiate','INITIATED'),('revert','REVERTED BACK'),('on_check','ON CHECK'),('requested', 'REQUESTED'), ('wait', 'CONTRACT REQUESTED')
            , ('lease', 'LEASED'), ('accepted', 'APPROVED'), ('declined', 'REJECTED'),('rfi','REQUEST FOR INFORMATION')],
        string='Requirement Status',
        default='draft',
        required=True
    )

    requested_by = fields.Many2one('res.users', 'Requested By', default=lambda self: self.env.user, readonly=True)

    approve_users = fields.Many2many(
        'res.users',
        'product_request_approve_users_rel',
        'request_id',
        'user_id',
        string='Approve Users',
        # default=lambda
        #     self: self.env.ref("product_purchase.group_initial_approval").users.ids
    )
    approve_users_cr = fields.Many2many(
        'res.users',
        'cr_need_approve_users_rel',
        'request_id',
        'user_id',
        string='Approve Users',
        # default=lambda
        #     self: self.env.ref("product_purchase.group_initial_approval").users.ids
    )

    approved_users = fields.Many2many(
        'res.users',
        'product_request_approved_users_rel',
        'request_id',
        'user_id',
        string='Approved Users',
    )
    approved_users_cr = fields.Many2many(
        'res.users',
        'cr_need_approved_users_rel',
        'request_id',
        'user_id',
        string='Approved Users',
    )

    remarks_ids = fields.One2many('remark.save',
                                    'pr_id',
                                    string='Remarks',
                                    tracking=True)


    approve_check = fields.Boolean(compute="_approve_check", string="Approve Check", default=False)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)

    next_approve_user_id = fields.Many2many('res.users', string="Next Approve User ID")

    next_approve_user_id_cr = fields.Many2many('res.users', 'cr_next_approved_users_rel',string="Next Approve User ID CR")

    user_approve_check = fields.Boolean(string="User Approve check", compute="_compute_total", default=False)

    user_approve_check_cr = fields.Boolean(string="User Approve check", compute="_compute_total_cr", default=False)

    bill_to = fields.Many2one('res.branch', "Bill To", required=True,default=lambda self: self.env.user.branch_id,domain=lambda self: [('company_id', 'in', self.env.user.company_ids.ids)])

    ship_to = fields.Many2one('res.branch', "Ship To", required=True)

    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True, required=True)

    exp_category = fields.Many2one('expense.category','Expense Category', required=True)

    exp_category_domain = fields.Char(
        compute="_compute_exp_category_domain",
        readonly=True,
        store=False,
    )


    total_price = fields.Float(string="Total Price", compute="compute_total")
    deligated_user = fields.Many2one(
        'res.users', string='User Deligated', tracking=True, compute="_compute_user_id")

    department_id = fields.Many2one('hr.department', string="Department", required=True)
    appr = fields.Boolean(compute="_compute_edit", string="Approve Check", readonly=False, store=True)
    group_id = fields.Many2one('groups', string='Group')

    contract_selection = fields.Selection([
        ('with_contract', 'With Contract'),
        ('one_time', 'One Time'),
    ], 'Purchase Type',default='with_contract')

    budget_details = fields.Many2one('product.request.budget', string='Budget',compute='_compute_budget')
    budget_amount_avail = fields.Float(string="Budget Remaining")
    product_group = fields.Many2many('products.group', 'groups_prrel', 'contrcts_id', 'group_id',
                                     string="Product Group")
    file_upload = fields.Binary("Attachment")
    revert_reason = fields.One2many('revert.back',
                                'pr_id',
                                string='Revert ReasonLine',
                                tracking=True)
    purchase_plan = fields.Selection([
        ('monthly', 'Monthly'),
        ('one_time', 'One Time'),
    ], string="Purchase Plan", required=True)
    check_requested_by = fields.Boolean(string="User Requested check", compute="_compute_requested_by", default=False)
    type_input = fields.Char(string="Attachment Name")
    main_remark = fields.Text(string="Remark" , required=True)
    active = fields.Boolean(string='Active', default=True,compute='action_archive_records' , tracking=True,store=True)
    is_to_user = fields.Boolean(compute='_compute_is_to_user', string='Is To User')
    product_bundle = fields.Html(string='Product Bundle')
    can_edit_lines = fields.Boolean(compute="_compute_can_edit_lines")




    @api.depends('status', 'next_approve_user_id')
    def _compute_can_edit_lines(self):
        user = self.env.user
        for rec in self:
            if rec.status in ('draft', 'revert'):
                rec.can_edit_lines = True  
            else:
                in_group = user.has_group('lease_management.group_record_pr')
                is_next_approver = user in rec.next_approve_user_id 
                rec.can_edit_lines = bool(rec.status == 'requested' and in_group and is_next_approver)






    def cancel_contract(self):
        tender_lines = self.env['tenders'].search([
            ('product_requested_id', '=', self.id)
        ])
        print("the tender lines are", tender_lines)
        if tender_lines:
            self.write({
                'approved_users': [(5, 0, 0)],
                'approve_users': [(5, 0, 0)],
                'next_approve_user_id': [(5, 0, 0)],
            })
            self.pr_approve_line = [(5, 0, 0)]
            self.status = 'initiate'

            model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
            print("Model", model)
            pending_actions = self.env['pending.actions'].sudo().search([
                ('model', '=', model.id),
                ('record', '=', self.id),
                ('status', '=', 'open')
            ])
            print("Pending action", pending_actions)

            if pending_actions:
                for pend in pending_actions:
                    pend.status = 'closed'
            if self.budget_details:
                self.sudo().budget_details.amount_used -= self.total_price
            self.message_post(body=f" {self.env.user.name} The Contract is Cancelled.")

            purchase_orders = self.env['purchase.order'].search(
                [('pr_id', '=', self.id), ('state', '!=', 'cancel')])
            if purchase_orders:
                for po in purchase_orders:
                    stock_pickings = self.env['stock.picking'].search(
                        [('origin', '=', po.name), ('state', '!=', 'cancel')])
                    if stock_pickings:
                        print("The pickings are:", stock_pickings)


                        for picking in stock_pickings:
                            # picking.state = 'cancel'
                            print("the state is",picking.state)
                            picking.write({'is_locked': False})

                            for move in picking.move_ids_without_package:
                                print("The move is:", move.name)
                                print("The quantity done before reset:", move.quantity_done)

                                # Unreserve the move before setting quantity to zero
                                if move.state == 'assigned':
                                    move._do_unreserve()  # Unreserve first

                                move.write({'quantity_done': 0})  # Reset quantity


                            picking.state = 'cancel'
                            print("the state 2",picking.state)

                            self.message_post(
                                body=f"{self.env.user.name} has cancelled the stock transfer {picking.name}."
                            )

                            # Close pending actions
                            model = self.env['ir.model'].sudo().search([('model', '=', 'stock.picking')], limit=1)
                            pending_action = self.env['pending.actions'].sudo().search(
                                [('model', '=', model.id), ('record', '=', po.id), ('status', '=', 'open')], limit=1
                            )
                            if pending_action:
                                pending_action.status = 'closed'

                            # Commit changes to database
                            self.env.cr.commit()

                            print("The quantity done after reset:", move.quantity_done)

                    # po.button_cancel()
                    po.state = 'cancel'
                    self.message_post(body=f"{self.env.user.name} has cancelled the Purchase Order {po.name}.")

                    model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                    pending_action = self.env['pending.actions'].sudo().search(
                        [('model', '=', model.id), ('record', '=', po.id), ('status', '=', 'open')], limit=1)

                    if pending_action:
                        pending_action.status = 'closed'


                    invoices = self.env['account.move'].search(
                        [('invoice_origin', '=', po.name), ('state', '!=', 'cancel')])
                    if invoices:
                        for invoice in invoices:
                            invoice.button_cancel()
                            self.message_post(body=f"{self.env.user.name} has cancelled the Invoice {invoice.name}.")
                            model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)
                            pending_action = self.env['pending.actions'].sudo().search(
                                [('model', '=', model.id), ('record', '=', invoice.id), ('status', '=', 'open')])

                            if pending_action:
                                for pend in pending_action:
                                    pend.status = 'closed'

            for tender_line in tender_lines:

                tender_line.state = 'rfq' if tender_line.contracting_method == 'multi' else 'draft'
                tender_line.write({
                    'approved_users': [(5, 0, 0)],
                    'approve_users': [(5, 0, 0)],
                    'next_approve_user_id': [(5, 0, 0)],
                })

                tender_line.tender_approve_line = [(5, 0, 0)]

                tender_line.write({'tender_response_tender_check': False})

                tender_contract = self.env['product.tender.line'].search([
                    ('request_no', '=', tender_line.id)
                ])
                tender_contract.status = 'terminate'
                model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', tender_line.id), ('status', '=', 'open')])

                print("pending", pending_action)

                if pending_action:
                    for rec in pending_action:
                        print(rec.name)
                        rec.sudo().status = 'closed'

                activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')],
                                                                             limit=1)

                activity = self.env['mail.activity'].sudo().search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                    ('res_name', '=', tender_line.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                print("activity", activity)
                if activity:
                    for act in activity:
                        act.action_feedback(feedback="Activity Declined")

                # if self.tender_id.budget_details:
                #     self.tender_id.budget_details.amount_used -= self.tender_id.total_price
                tender_line.sudo().message_post(body=f" {self.env.user.name} Contract Cancellation Notification.")
                users_line = self.env['res.users.line'].sudo().search([
                    ('department_id.name', '=', 'SCM'),
                    ('designation', '=', 'Purchase Head')
                ], limit=1)

                if users_line:

                    model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                    pending_vals = {
                        'model': model.id,
                        'name': tender_line.name + " " + "Contract Cancellation Notification",
                        'record': tender_line.id,
                        'branch': tender_line.branch_ids.ids[0] if tender_line.branch_ids else None,
                        'date': date.today(),
                        'approve_users': [(6, 0, [users_line.res_user_id.id])]
                    }

                    pendings = self.env['pending.actions'].sudo().create(pending_vals)

                    subject = "Contract Cancellation Notification : %s" % tender_line.name
                    print("subject", subject)

                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Contracts')], limit=1) or False
                    print("Menu ", menu_id)
                    url_params = {
                        'id': tender_line.id,
                        'action': self.env.ref('product_purchase.action_tender_status').id,
                        'model': 'tenders',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    print("URL", url)

                    # email_to_list = [user.email if user.email else user.login for user in buyer_users]

                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)

                    body = (
                        f"Dear User, "
                        f"A Contract has Cancelled with the name <strong>{tender_line.name} .<br>"
                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                    )
                    if users_line:
                        mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': users_line.res_user_id.id,
                            'auto_delete': False,
                            'author_id': author.id
                        }
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)

            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            print("return", pending)
            if pending:
                print("if ", pending)
                return pending.open_record()
            else:
                print("else")
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action

        else:
            raise ValidationError(
            "No contract associated with this PR."
         )


    @api.onchange('active')
    def action_archive_records(self):
        for rec in self:
            print("ACTIVEEEEEEEEEEEEEEEEEEEE",self.env.user.has_group('lease_management.group_master_admin'),rec.active)
            if not self.env.user.has_group('lease_management.group_master_admin'):
                rec.active = True
                raise ValidationError(_('You do not have permission to deactivate this record.'))

                # If user has the master admin group, allow setting active to False
            if not self.env.user.has_group('lease_management.group_master_admin'):
                rec.active = False
                raise ValidationError(_('You do not have permission to activate this record.'))
            print("Action triggered by changing 'active' field")

    def attachments_to_contract(self):
        print("Inside Attachment copy")
        domain = [('res_model', '=', 'product.request'), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment'].read_group(domain, ['res_id'], ['res_id'])
        print("attachment data",attachment_data)
        contract = self.env['tenders'].sudo().search([('product_requested_id', '=', self.id)], limit=1)
        for data in attachment_data:
            print("datas",data)
            tender_id = data['res_id']
            attachment_count = data['res_id_count']

            # Fetch attachments for the current tender_id
            attachments = self.env['ir.attachment'].search([('res_model', '=', 'product.request'), ('res_id', '=', tender_id)])

            # Example: Create attachments for another_model
            for attachment in attachments:
                reco = self.env['ir.attachment'].create({
                    'name': attachment.name,
                    'datas': attachment.datas,  # Assuming 'datas' holds attachment content
                    'res_model': 'tenders',  # Target model
                    'res_id': contract.id  # ID of the record in other_model
                    # Add other necessary fields from 'ir.attachment' model
                })
                print("attac",reco)

    @api.depends('pr_rfi_ids')
    def _compute_is_to_user(self):
        current_user_id = self.env.user.id
        for record in self:
            record.is_to_user = any(not rfi.replayed and rfi.to_user.id == current_user_id for rfi in record.pr_rfi_ids)
            print("the user is", record.is_to_user)

    def add_activity(self):
        activity_type = self.env['mail.activity.type'].sudo().search(
            [('name', '=', 'Pending Request')], limit=1)
        activity_type_id = activity_type.id if activity_type else False
        res_model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'product.request')]).id

        activity_values = {
            'user_id': 2951,
            'res_id': self.id,
            'note': "Pending Action",
            'activity_type_id': activity_type_id,
            'res_model_id': res_model_id,
        }
        with self.env.cr.savepoint():
            self = self.with_context(mail_activity_quick_update=True)
            created_activity = self.env['mail.activity'].sudo().create(activity_values)
    def action_withdraw(self):
        if self.status == 'requested':
            flag = 0
            for line in self.pr_approve_line:
                if line.status != 'draft':
                    flag = 1
                    break
            if flag == 0:
                self.status = 'draft'
                self.pr_approve_line.unlink()
                self.write({'approve_users': [(5, 0, 0)]})
                self.write({'approved_users': [(5, 0, 0)]})
                self.write({'next_approve_user_id': [(5, 0, 0)]})
                self.cr_need_approve_line.unlink()
                self.write({'approve_users_cr': [(5, 0, 0)]})
                self.write({'approved_users_cr': [(5, 0, 0)]})
                self.write({'next_approve_user_id_cr': [(5, 0, 0)]})
                
                print("approvers,approved,next",self.approve_users,self.approved_users,self.next_approve_user_id)

                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                    ('res_name', '=', self.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback="Purchase Request Withdraw")
                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
                if pending_action:
                    for pending in pending_action:
                        pending.status = 'closed'

                if self.budget_details:
                    self.budget_details.amount_used -= self.total_price
                for line_ids in self.product_request_line_ids:
                    vendor_limit = self.env['vendor.limit'].sudo().search(
                        [('vendor_id', '=', line_ids.vendors.ids[0]),('start_date', '<=', line_ids.expected_date),
                    ('end_date', '>=', line_ids.expected_date), ('status', '=', 'active')], limit=1)
                    if vendor_limit:
                        vendor_limit.amount_used -= self.total_price
            else:
                raise ValidationError(_("Approvers states are not on draft"))
        if self.status == 'on_check':
            flag = 0
            for line in self.cr_need_approve_line:
                if line.status != 'draft':
                    flag = 1
                    break
            if flag == 0:
                self.status = 'draft'
                self.cr_need_approve_line.unlink()
                self.write({'approve_users_cr': [(5, 0, 0)]})
                self.write({'approved_users_cr': [(5, 0, 0)]})
                self.write({'next_approve_user_id_cr': [(5, 0, 0)]})
                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                    ('res_name', '=', self.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback="Purchase Request Withdraw")
                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
                if pending_action:
                    for pending in pending_action:
                        pending.status = 'closed'

            else:
                raise ValidationError(_("Need of PR Approvers states are not on draft"))

    
    @api.depends('requested_by')
    def _compute_requested_by(self):
        print("Inside requesed by check")
        current_user = self.env.user
        for record in self:
            print(record.requested_by)
            print(current_user)
            if current_user == record.requested_by:
                record.check_requested_by = True
            else:
                record.check_requested_by = False
    def action_add_approver_cr_need_admin(self):
        user_ids = [user.id for user in self.next_approve_user_id_cr]
        if not user_ids:
            return
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')
        action['context'] = {
            'default_pr_id_cr_need': self.id,
            'default_admin_add': True
        }

        return action
    def action_add_approver_admin(self):
        user_ids = [user.id for user in self.next_approve_user_id]
        if not user_ids:
            return
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')
        action['context'] = {
            'default_pr_id': self.id,
            'default_admin_add': True
        }

        return action
    def action_add_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')
        action['context'] = {'default_pr_id': self.id,

                             }
        print(action)
        return action
        
    def action_add_approver_cr_need(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')
        action['context'] = {'default_pr_id_cr_need': self.id,

                             }
        print(action)
        return action

    def send_replay(self):
        print("i am in replay")
        unreplied_rfi_record = self.pr_rfi_ids.filtered(lambda r: not r.replayed and r.to_user.id == self.env.user.id)
        print("the rfi record", unreplied_rfi_record)
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_replay_action')
        action['context'] = {'default_message_id': unreplied_rfi_record.id,
                             'default_message': unreplied_rfi_record.message}
        return action

    def action_revert(self):
        return {
            'name': 'Roll back to initiator',
            'view_mode': 'form',
            'view_id': self.env.ref('product_purchase.view_revert_back_form').id,
            'view_type': 'form',
            'res_model': 'revert.back.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_revert_from': self.env.user.id,
                'default_pr_id': self.id,
                'default_initiator': self.requested_by.id,
            },
        }
    def action_revert_cr(self):
        return {
            'name': 'Roll back to initiator',
            'view_mode': 'form',
            'view_id': self.env.ref('product_purchase.view_revert_back_form').id,
            'view_type': 'form',
            'res_model': 'revert.back.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_revert_from': self.env.user.id,
                'default_cr_id': self.id,
                'default_initiator': self.requested_by.id,
            },
        }
    def action_remark_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_approve_action')
        action['context'] = {'default_pr_id': self.id,
                             'default_cr_need': True,
                             'default_approve_type':'approve',
                             }
        print(action)
        return action
    def action_remark_reject(self):
        self.ensure_one()
        if self.exp_category and self.exp_category.reject_not_possible:
            raise ValidationError(
                "Rejection is not possible for this PR as the linked expense category does not allow rejection."
            )
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_approve_action')
        action['context'] = {'default_pr_id': self.id,
                             'default_cr_need': True,
                             'default_approve_type':'reject',
                             }
        print(action)
        return action
    def action_remark_pr_approve(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_approve_action')
        action['context'] = {'default_pr_id': self.id,
                             'default_cr_need': False,
                             'default_approve_type':'approve',
                             }
        print(action)
        return action
    def action_remark_pr_reject(self):
        self.ensure_one()
        if self.exp_category and self.exp_category.reject_not_possible:
            raise ValidationError(
                "Rejection is not possible for this PR as the linked expense category does not allow rejection."
            )
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_approve_action')
        action['context'] = {'default_pr_id': self.id,
                             'default_cr_need': False,
                             'default_approve_type':'reject',
                             }
        print(action)
        return action

    @api.onchange('product_group')
    def _onchange_product_group_ids(self):
        for rec in self:
            if rec.product_group:
                lines = [(5, 0, 0)]
                for line in rec.product_group.products_line:
                    val = {
                        'product': line.product_id.id,
                        'uom': line.uom.id,
                        'quantity': line.quantity,
                        'unit_price': line.unit_price,

                    }
                    lines.append((0, 0, val))
                rec.product_request_line_ids = lines
                rec.product_request_line_ids.onchange_in_product()
                rec.product_request_line_ids.onchange_vendors_quantity()
            else:
                rec.product_request_line_ids = [(5, 0, 0)]

    

    @api.depends('ship_to','expense_type','exp_category','department_id')
    def _compute_budget(self):
        # print("ffff")
        for data in self:
            if data.ship_to and data.expense_type and data.exp_category and data.department_id:
                pr_budget = self.env['product.request.budget'].sudo().search([('company_id', '=', self.company_id.id),
                            ('branch_id', '=', self.bill_to.id),('department_id', '=',self.department_id.id),
                            ('expense_type', '=', self.expense_type),('exp_category', '=',self.exp_category.id),
                            ('from_date', '<=', date.today()),('to_date', '>=', date.today())], limit=1)
                if pr_budget:
                    data.budget_details = pr_budget.id
                    data.budget_amount_avail = pr_budget.amount_available
                else:
                    data.budget_details = None
                    data.budget_amount_avail = 0
            else:
                data.budget_details = None
                data.budget_amount_avail = 0




    @api.depends('expense_type')
    def _compute_exp_category_domain(self):
        for rec in self:
            category_domain = []
            if rec.expense_type:
                categories = self.env['expense.category'].sudo().search([
                    ('exp_type', '=', rec.expense_type)
                ])
                if categories:
                    expense_types = categories.mapped('exp_type')
                    if expense_types:
                        category_domain = [('exp_type', '=', expense_types)]

            rec.exp_category_domain = json.dumps(category_domain)

    def action_view_contracts(self):
        print("gggggggg")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract Requests',
            'view_mode': 'tree,form',
            'res_model': 'tenders',
            'domain': [('product_requested_id', '=', self.id),
                      ],
            'target': 'current'
        }


    def action_view_po(self):
        print("cccccccc")
        return {
            'type': 'ir.actions.act_window',
            'name': 'PO',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('pr_id','=', self.id),
                       ],
            'target': 'current'
        }

    def action_open_lease(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lease Agreement',
            'view_mode': 'tree,form',
            'res_model': 'product.lease',
            'domain': [('product_request_id', '=', self.id),
                       ('state', '!=', 'reject')],
            'target': 'current'
        }

    def action_modify(self):
        if self.appr == True:
            self.appr = False
            print("yesss")
        # else:
        #     self.appr = False
        #     print("noooo")
        self.message_post(body="Button Modify Accessed")

    def write(self, vals):
        res = super(ProductRequest, self).write(vals)
        print(res)
        print(self)
        # if self.appr == False:  # Checking if appr is False
        #     self.appr = True
        return res

    @api.depends('approved_users')
    def _compute_edit(self):
        current_user = self.env.user
        for record in self:
            print(record.approved_users)
            print(current_user)
            if current_user in record.approved_users:
                record.appr = True
            else:
                record.appr = False

    def action_log_message(self):
        default_user_ids = self.approve_users.ids
        print(default_user_ids, "Usersssss")
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_message_action')
        action['context'] = {'default_request_id': self.id,
                             }
        print(action)
        return action

    @api.onchange('bill_to')
    def _onchange_bill_to(self):
        if self.bill_to:
            self.ship_to = self.bill_to

    @api.onchange('ship_to')
    def _onchange_ship_to(self):
        print("hhhhhhh")
        if self.ship_to:
            self.company_id = self.ship_to.company_id.id

    def _compute_user_id(self):
        for rec in self:
            rec.deligated_user = self.env.user.id

    @api.onchange('total_price')
    def onchange_in_total_price(self):
        # self.total_price = self.total_price
        print("Inside total_price price", self.total_price)

    @api.depends('product_request_line_ids')
    def compute_total(self):
        total_amount = 0
        for total in self:
            for lines in total.product_request_line_ids:
                total_amount += lines.quantity * lines.unit_price
        # print("total_amount ", total_amount)
        self.total_price = total_amount

    @api.depends("user_approve_check")
    def _compute_total(self):
        print('Inside user_approve_check')
        for rec in self:
            if self.env.user in rec.next_approve_user_id:
                rec.user_approve_check = True
            else:
                rec.user_approve_check = False

    @api.depends("user_approve_check_cr")
    def _compute_total_cr(self):
        print('Inside user_approve_check_cr')
        for rec in self:
            if self.env.user in rec.next_approve_user_id_cr:
                rec.user_approve_check_cr = True
            else:
                rec.user_approve_check_cr = False
                
    def _approve_check(self):
        self.approve_check = False
        if self.approved_users and (self.env.user.id in [user_ids.id for user_ids in self.approved_users]):
            self.approve_check = True
        else:
            self.approve_check = False

    def action_request(self):
        line_items = self.product_request_line_ids
        if all(line_item.contract_status == 'in_contract' for line_item in line_items):  # ALL IN CONTRACT
            # raise UserError("All products have existing rate contracts.")
            if not all(line_item.vendors for line_item in line_items):
                raise UserError("Please select the vendor for all Products")

            
            if (self.department_id.name == 'Branch - IT' or self.department_id.name == 'HO - IT') and self.status == 'draft':
                print("ITTTTT")
                workflow_data2 = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                        #   ('branch_id', '=', self.ship_to.id),
                                                                        (
                                                                        'department_id', '=', self.department_id.id),
                                                                        ('from_amount', '<=', self.total_price),
                                                                        ('to_amount', '>=', self.total_price),
                                                                        ('expense_type', '=', self.expense_type),
                                                                        ('exp_category', '=', self.exp_category.id),
                                                                        ('type', '=', 'pr')], limit=1)

                workflow_data = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                        #   ('branch_id', '=', self.ship_to.id),
                                                                        ('department_id', '=', self.department_id.id),
                                                                        ('from_amount', '<=', self.total_price),
                                                                        ('to_amount', '>=', self.total_price),
                                                                        ('expense_type', '=', self.expense_type),
                                                                        ('exp_category', '=', self.exp_category.id),
                                                                        ('type', '=', 'need_cr')], limit=1)
                print("cr_company_data : ", workflow_data)
                if workflow_data and workflow_data2:

                    approve_user_ids2 = []
                    workflow_line_data2 = self.env['pr.approve.users'].sudo().search(
                        [('pr_company_id', '=', workflow_data2.id)])  # searching in workflow line

                    ### First Check And then only Approval flow Commit Pr
                    pr_budget = self.env['product.request.budget'].sudo().search(
                        [('company_id', '=', self.company_id.id),
                            ('branch_id', '=', self.bill_to.id),
                            ('department_id', '=', self.department_id.id),
                            ('expense_type', '=', self.expense_type),
                            ('exp_category', '=', self.exp_category.id),
                            ('from_date', '<=', date.today()),
                            ('to_date', '>=', date.today()),
                            ], limit=1)
                    if self.department_id.name == 'HO - IT' and not("CAPEX N/A" in self.exp_category.name):
                        if pr_budget:
                            if self.total_price > pr_budget.amount_available:
                                self.status = 'draft'
                                msg = "Budget Amount Exceeded"
                                self.message_post(
                                    body="Budget amount exceeded. Please contact the admin for a budget expansion.")
                                return {
                                    'type': 'ir.actions.client',
                                    'tag': 'display_notification',
                                    'params': {
                                        'message': msg,
                                        'type': 'danger',
                                        'sticky': False,
                                        'next': {
                                            'type': 'ir.actions.act_window_close',
                                        }
                                    }
                                }
                                raise ValidationError(_("Budget is insufficient for the total amount."))

                        else:
                            raise ValidationError(_("No budget found"))
                            self.status = 'draft'
                    # else:
                    #     raise ValidationError("test")
                    for approverss in workflow_line_data2:
                        if approverss.branch_id.code == "COR":
                            ser_branch = approverss.branch_id.id
                            ser_branch_record = approverss.branch_id
                        else:
                            ser_branch = self.bill_to.id
                            ser_branch_record = self.bill_to
                        users_lines = self.env['res.users.line'].sudo().search(
                            [('company_id', '=', approverss.company_id.id), ('branch_id', '=', ser_branch),
                                ('department_id', '=', approverss.department_id.id),
                                ('designation', '=', approverss.designation.id)])  # searching user in users line
                        print(users_lines, "PR USERSSSSSSSSSSSSS")
                        if users_lines and users_lines.res_user_id:
                            pass
                        else:
                            raise ValidationError(
                                _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR PR APPROVAL") % (
                                    approverss.designation.name, approverss.department_id.name,
                                    ser_branch_record.name, approverss.company_id.name))

                    approve_user_ids = []
                    workflow_line_data = self.env['pr.approve.users'].sudo().search(
                        [('pr_company_id', '=', workflow_data.id)])  # searching in workflow line
                    print('pr_company_line_data : ', workflow_line_data)

                    ### First Check And then only Approval flow Commit cr need
                    order_requested = 0
                    requested_in_workflow = False
                    limit = 0
                    for approverss in workflow_line_data:
                        limit +=1
                    for approvers in workflow_line_data:
                        if approvers.branch_id.code == "COR":
                            ser_branch = approvers.branch_id.id
                            ser_branch_record = approvers.branch_id
                        else:
                            ser_branch = self.bill_to.id
                            ser_branch_record = self.bill_to
                        users_line = self.env['res.users.line'].sudo().search(
                            [('company_id', '=', approvers.company_id.id), ('branch_id', '=', ser_branch),
                                ('department_id', '=', approvers.department_id.id),
                                ('designation', '=', approvers.designation.id)])  # searching user in users line
                        print(users_line, "PR USERSSSSSSSSSSSSS")
                        if users_line and users_line.res_user_id:
                            if users_line.res_user_id.id == self.requested_by.id and limit >1:
                                order_requested = approvers.approve_order
                                requested_in_workflow = True
                        else:
                            raise ValidationError(
                                _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR CR NEED APPROVAL") % (
                                    approvers.designation.name, approvers.department_id.name,
                                    ser_branch_record.name, approvers.company_id.name))

                        ## ## For Approval execution(else partial flow will be executed)

                    for approvers in workflow_line_data:
                        if approvers.branch_id.code == "COR":
                            ser_branch = approvers.branch_id.id
                            ser_branch_record = approvers.branch_id
                            
                        else:
                            ser_branch = self.bill_to.id
                            ser_branch_record = self.bill_to
                        users_line = self.env['res.users.line'].sudo().search(
                            [('company_id', '=', approvers.company_id.id), ('branch_id', '=', ser_branch),
                                ('department_id', '=', approvers.department_id.id),
                                ('designation', '=', approvers.designation.id)])  # searching user in users line
                        print(users_line, "PR USERSSSSSSSSSSSSS")
                        if users_line and users_line.res_user_id:
                            if users_line.res_user_id.id == self.requested_by.id and limit >1:
                                print("order,req", order_requested, requested_in_workflow)
                            elif approvers.approve_order > order_requested and requested_in_workflow == True:
                                order = approvers.approve_order - 1
                                self.write({'approve_users_cr': [(4, users_line.res_user_id.id)]})
                                vals = {
                                    'user_id': users_line.res_user_id.id,
                                    'company_id': approvers.company_id.id,
                                    'branch_id': ser_branch,
                                    'department_id': approvers.department_id.id,
                                    'designation': approvers.designation.id,
                                    'approve_order': order,
                                    'product_request_id': self.id
                                }
                                approve_user_ids.append({'user_id': users_line.res_user_id.id,
                                                            'approve_order': order})
                                pr_approve_line = self.env['cr.need.approve.line'].create(vals)
                            else:

                                self.write({'approve_users_cr': [(4, users_line.res_user_id.id)]})
                                vals = {
                                    'user_id': users_line.res_user_id.id,
                                    'company_id': approvers.company_id.id,
                                    'branch_id': ser_branch,
                                    'department_id': approvers.department_id.id,
                                    'designation': approvers.designation.id,
                                    'approve_order': approvers.approve_order,
                                    'product_request_id': self.id
                                }
                                approve_user_ids.append({'user_id': users_line.res_user_id.id,
                                                            'approve_order': approvers.approve_order})
                                pr_approve_line = self.env['cr.need.approve.line'].create(vals)
                            self.env.cr.commit()
                            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                            pending_action = self.env['pending.actions'].sudo().search(
                                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')],
                                limit=1)
                            if pending_action:
                                print(pending_action.name)
                                pending_action.status = 'closed'

                            activity_type = self.env['mail.activity.type'].search(
                                [('name', '=', 'Pending Request')],
                                limit=1)
                            print("type is", self.env.user.id)
                            activity = self.env['mail.activity'].search([
                                ('res_model_id', '=',
                                    self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                                ('activity_type_id', '=', activity_type.id),
                            ], limit=1)
                            if activity:
                                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                                print(activity.id)

                                activity.action_feedback(feedback="Activity completed")
                        else:
                            raise ValidationError(
                                _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                    approvers.designation.name, approvers.department_id.name,
                                    ser_branch_record.name, approvers.company_id.name))

                        print("approve_user_ids : ", approve_user_ids)
                    if approve_user_ids:
                        mylist = sorted(approve_user_ids, key=lambda k: int(k['approve_order']))

                        order = mylist[0]['approve_order']
                        for users in mylist:
                            if users['approve_order'] == order:
                                self.write({'next_approve_user_id_cr': [(4, users['user_id'])]})
                    if not approve_user_ids:
                        raise UserError("No Approver's found for the current workflow")

                    self.status = 'on_check'
                    model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                    if approve_user_ids:
                        user_ids_to_pass = self.next_approve_user_id_cr.ids
                        for user in self.next_approve_user_id_cr:
                            model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                        limit=1)
                            pending_vals = {
                                'model': model.id,
                                'name': self.name + " " + "Need for Request Waiting For Approval",
                                'record': self.id,
                                'branch': self.bill_to.id,
                                'department_id': self.department_id.id,
                                'exp_category': self.exp_category.id,
                                'Created_doc_date': self.requested_date,
                                'date': date.today(),
                            }
                            print("user", user, "next", self.next_approve_user_id_cr)
                            if user:
                                print("workkkkkkkkkkk")
                                user_ids_to_pass = user.ids
                                pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                pendings = self.env['pending.actions'].create(pending_vals)
                                print("Pendinggg", pendings)
                                approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                pendings.write({'email': approve_users_emails})
                                activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Request')],
                                    limit=1)
                                activity_type_id = activity_type.id if activity_type else False
                                res_model_id = self.env['ir.model'].sudo().search(
                                    [('model', '=', 'product.request')]).id
                                for user_id in user_ids_to_pass:
                                    activity_values = {
                                        'user_id': user_id,
                                        'res_id': self.id,
                                        'note': "Pending Action",
                                        'summary': "Action",
                                        'activity_type_id': activity_type_id,
                                        'res_model_id': res_model_id,
                                    }
                                    with self.env.cr.savepoint():
                                        self = self.with_context(mail_activity_quick_update=True)
                                        created_activity = self.env['mail.activity'].create(activity_values)
                    print("next user", self.next_approve_user_id_cr)
                    subject = "Purchase Request Waiting For APPROVAL: %s" % self.name

                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Purchase Request')], limit=1) or False

                    url_params = {
                        'id': self.id,
                        'action': self.env.ref('product_purchase.action_product_requests').id,
                        'model': 'product.request',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    print(url)

                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)

                    body = (
                        f"Dear User, "
                        f"A new Purchase Request with the name <strong>{self.name} is waiting for Approval.<br>"
                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                    )
                    if self.next_approve_user_id_cr:
                        for user in self.next_approve_user_id_cr:
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                elif not workflow_data2:
                    raise ValidationError(
                        "Sorry,The criteria provided did not match any existing PR workflows,Please contact Administrator.")
                else:
                    raise ValidationError(
                        "Sorry,The criteria provided did not match any existing Need for Request workflows,Please contact Administrator.")

            else:
                workflow_data = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                        #   ('branch_id', '=', self.ship_to.id),
                                                                        ('department_id', '=', self.department_id.id),
                                                                        ('from_amount', '<=', self.total_price),
                                                                        ('to_amount', '>=', self.total_price),
                                                                        ('expense_type', '=', self.expense_type),
                                                                        ('exp_category', '=', self.exp_category.id),
                                                                        ('type', '=', 'pr')], limit=1)
                print("pr_company_data : ", workflow_data)
                if workflow_data:
                    approve_user_ids = []
                    workflow_line_data = self.env['pr.approve.users'].sudo().search(
                        [('pr_company_id', '=', workflow_data.id)])  # searching in workflow line
                    print('pr_company_line_data : ', workflow_line_data)

                    ### First Check And then only Approval flow Commit
                    order_requested = 0
                    requested_in_workflow = False
                    limit = 0
                    for approverss in workflow_line_data:
                        limit +=1
                    for approvers in workflow_line_data:
                        if approvers.branch_id.code == "COR":
                            ser_branch = approvers.branch_id.id
                            ser_branch_record = approvers.branch_id
                        else:
                            ser_branch = self.bill_to.id
                            ser_branch_record = self.bill_to
                        users_line = self.env['res.users.line'].sudo().search(
                            [('company_id', '=', approvers.company_id.id), ('branch_id', '=', ser_branch),
                            ('department_id', '=', approvers.department_id.id),
                            ('designation', '=', approvers.designation.id)])  # searching user in users line
                        print(users_line, "PR USERS")
                        if users_line and users_line.res_user_id:
                            if users_line.res_user_id.id == self.requested_by.id and limit>1:
                                order_requested = approvers.approve_order
                                requested_in_workflow = True
                        else:
                            raise ValidationError(
                                _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                    approvers.designation.name, approvers.department_id.name,
                                    ser_branch_record.name, approvers.company_id.name))
                    pr_budget = self.env['product.request.budget'].sudo().search(
                            [('company_id', '=', self.company_id.id),
                            ('branch_id', '=', self.bill_to.id),
                            ('department_id', '=', self.department_id.id),
                            ('expense_type', '=', self.expense_type),
                            ('exp_category', '=', self.exp_category.id),
                            ('from_date', '<=', date.today()),
                            ('to_date', '>=', date.today()),
                            ], limit=1)
                    if self.department_id.name == 'HO - IT' and not("CAPEX N/A" in self.exp_category.name):
                        if pr_budget:
                            if self.total_price > pr_budget.amount_available:
                                self.status = 'draft'
                                msg = "Budget Amount Exceeded"
                                self.message_post(
                                    body="Budget amount exceeded. Please contact the admin for a budget expansion.")
                                return {
                                    'type': 'ir.actions.client',
                                    'tag': 'display_notification',
                                    'params': {
                                        'message': msg,
                                        'type': 'danger',
                                        'sticky': False,
                                        'next': {
                                            'type': 'ir.actions.act_window_close',
                                        }
                                    }
                                }
                                raise ValidationError(_("Budget is insufficient for the total amount."))

                        else:
                            raise ValidationError(_("No budget found"))
                            self.status  = 'draft'
                        ## For Approval execution(else partial flow will be executed)
                    # else:
                    #     raise ValidationError("test")
                    for line_ids in self.product_request_line_ids:
                        print("line id", line_ids.vendors.name)
                        vendor_limit = self.env['vendor.limit'].sudo().search(
                            [('vendor_id', '=', line_ids.vendors.ids[0]), ('start_date', '<=', line_ids.expected_date),('end_date', '>=', line_ids.expected_date),('status', '=', 'active')], limit=1)
                        print("Limt", vendor_limit)
                        if vendor_limit:
                            print("values", vendor_limit.balance_amount, line_ids.quantity * line_ids.unit_price)
                            if vendor_limit.balance_amount < line_ids.quantity * line_ids.unit_price:
                                raise UserError(_("Buying limit from %s has reached." % line_ids.vendors.name))
                            else:
                                vendor_limit.amount_used += self.total_price


                    for approvers in workflow_line_data:
                        if approvers.branch_id.code == "COR":
                            ser_branch = approvers.branch_id.id
                        else:
                            ser_branch = self.bill_to.id
                        users_line = self.env['res.users.line'].sudo().search(
                            [('company_id', '=', approvers.company_id.id), ('branch_id', '=', ser_branch),
                                ('department_id', '=', approvers.department_id.id),
                                ('designation', '=', approvers.designation.id)])  # searching user in users line
                        print(users_line, "PR USERSSSSSSSSSSSSS")
                        if users_line :
                            if users_line.res_user_id.id == self.requested_by.id and limit>1:
                                print("order,req", order_requested)
                            elif approvers.approve_order > order_requested and requested_in_workflow == True:
                                order = approvers.approve_order - 1
                                self.write({'approve_users': [(4, users_line.res_user_id.id)]})
                                vals = {
                                    'user_id': users_line.res_user_id.id,
                                    'company_id': approvers.company_id.id,
                                    'branch_id': ser_branch,
                                    'department_id': approvers.department_id.id,
                                    'designation': approvers.designation.id,
                                    'approve_order': order,
                                    'product_request_id': self.id
                                }
                                approve_user_ids.append({'user_id': users_line.res_user_id.id,
                                                            'approve_order': order})
                                pr_approve_line = self.env['pr.approve.line'].create(vals)
                            else:
                                self.write({'approve_users': [(4, users_line.res_user_id.id)]})
                                vals = {
                                    'user_id': users_line.res_user_id.id,
                                    'company_id': approvers.company_id.id,
                                    'branch_id': ser_branch,
                                    'department_id': approvers.department_id.id,
                                    'designation': approvers.designation.id,
                                    'approve_order': approvers.approve_order,
                                    'product_request_id': self.id
                                }
                                approve_user_ids.append({'user_id': users_line.res_user_id.id,
                                                        'approve_order': approvers.approve_order})
                                pr_approve_line = self.env['pr.approve.line'].create(vals)
                            self.env.cr.commit()
                            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                            pending_action = self.env['pending.actions'].sudo().search(
                                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)
                            if pending_action:
                                print(pending_action.name)
                                pending_action.status = 'closed'

                            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')],
                                                                                    limit=1)
                            print("type is", self.env.user.id)
                            activity = self.env['mail.activity'].search([
                                ('res_model_id', '=',
                                    self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                                ('activity_type_id', '=', activity_type.id),
                            ], limit=1)
                            if activity:
                                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                                print(activity.id)

                                activity.action_feedback(feedback="Activity completed")

                        print("approve_user_ids : ", approve_user_ids)
                    if approve_user_ids:
                        mylist = sorted(approve_user_ids, key=lambda k: int(k['approve_order']))

                        order = mylist[0]['approve_order']
                        for users in mylist:
                            if users['approve_order'] == order:
                                self.write({'next_approve_user_id': [(4, users['user_id'])]})
                    if not approve_user_ids:
                        raise UserError("No Approver's found for the current workflow")
                            # user_admin = self.env['res.users'].sudo().search([('name', '=', 'Administrator')], limit=1)
                            # if user_admin:
                            #     self.write({'approve_users': [(4, user_admin.id)]})
                            #     self.write({'next_approve_user_id': [(4, user_admin.id)]})
                            #     self.message_post(
                            #         body="No Users Found based on Workflow, Purchase Request approval send for Admin.")
                            #     vals = {
                            #         'user_id': user_admin.id,
                            #         'company_id': '',
                            #         'branch_id': '',
                            #         'department_id': '',
                            #         'designation': '',
                            #         'approve_order': '1',
                            #         'product_request_id': self.id
                            #     }
                            # approve_user_ids.append({'user_id': user_admin.id,
                            #                          'approve_order': '1'})
                            # pr_approve_line = self.env['pr.approve.line'].create(vals)
                            # self.env.cr.commit()
                            # model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                            # pending_action = self.env['pending.actions'].sudo().search(
                            #     [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)
                            #
                            # if pending_action:
                            #     print(pending_action.name)
                            #     pending_action.status = 'closed'
                    self.status = 'requested'
                    model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                    if approve_user_ids:
                        user_ids_to_pass = self.next_approve_user_id.ids
                        for user in self.next_approve_user_id:
                            model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                            limit=1)
                            pending_vals = {
                                'model': model.id,
                                'name': self.name + " " + "Waiting For Approval",
                                'record': self.id,
                                'branch': self.bill_to.id,
                                'department_id': self.department_id.id,
                                'exp_category': self.exp_category.id,
                                'Created_doc_date': self.requested_date,
                                'date': date.today(),
                            }
                            if user:
                                user_ids_to_pass = user.ids
                                pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                pendings = self.env['pending.actions'].create(pending_vals)
                                approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                pendings.write({'email': approve_users_emails})
                                activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')],
                                                                                        limit=1)
                                activity_type_id = activity_type.id if activity_type else False
                                res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id
                                for user_id in user_ids_to_pass:
                                    activity_values = {
                                        'user_id': user_id,
                                        'res_id': self.id,
                                        'note': "Pending Action",
                                        'summary': "Action",
                                        'activity_type_id': activity_type_id,
                                        'res_model_id': res_model_id,
                                    }
                                    with self.env.cr.savepoint():
                                        self = self.with_context(mail_activity_quick_update=True)
                                        created_activity = self.env['mail.activity'].create(activity_values)

                    subject = "Purchase Request Waiting For APPROVAL: %s" % self.name

                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Purchase Request')], limit=1) or False

                    url_params = {
                        'id': self.id,
                        'action': self.env.ref('product_purchase.action_product_requests').id,
                        'model': 'product.request',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    print(url)

                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)

                    body = (
                        f"Dear User, "
                        f"A new Purchase Request with the name <strong>{self.name} is waiting for Approval.<br>"
                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                    )
                    if self.next_approve_user_id:
                        for user in self.next_approve_user_id:
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    if self.department_id.name == 'HO - IT':
                        pr_budget = self.env['product.request.budget'].sudo().search(
                            [('company_id', '=', self.company_id.id),
                                ('branch_id', '=', self.bill_to.id),
                                ('department_id', '=', self.department_id.id),
                                ('expense_type', '=', self.expense_type),
                                ('exp_category', '=', self.exp_category.id),
                                ('from_date', '<=', date.today()),
                                ('to_date', '>=', date.today()),
                                ], limit=1)
                        if pr_budget:
                            print(pr_budget.amount_allowed)
                            print("budget")
                            if self.total_price <= pr_budget.amount_available:
                                pr_budget.amount_used += self.total_price
                                msg = "Amount available in Budget"
                                return {
                                    'type': 'ir.actions.client',
                                    'tag': 'display_notification',
                                    'params': {
                                        'message': msg,
                                        'type': 'success',
                                        'sticky': False,
                                        'next': {
                                            'type': 'ir.actions.act_window_close',
                                        }
                                    }
                                }
                                print("Budget is available for the total amount.")
                            else:
                                msg = "Budget Amount Exceeded"
                                self.message_post(
                                    body="Budget amount exceeded. Please contact the admin for a budget expansion.")
                                return {
                                    'type': 'ir.actions.client',
                                    'tag': 'display_notification',
                                    'params': {
                                        'message': msg,
                                        'type': 'danger',
                                        'sticky': False,
                                        'next': {
                                            'type': 'ir.actions.act_window_close',
                                        }
                                    }
                                }
                                print("Budget is insufficient for the total amount.")
                        else:
                            print("No budget found")
                    # else:
                    #     raise ValidationError("test")
                else:
                    raise ValidationError(
                        "Sorry,The criteria provided did not match any existing workflows,Please contact Administrator.")
        if all(line_item.contract_status == 'new' for line_item in line_items):
            # Check if any line has vendors
            workflow_data2 = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                  #   ('branch_id', '=', self.ship_to.id),
                                                                  ('department_id', '=', self.department_id.id),
                                                                  ('from_amount', '<=', self.total_price),
                                                                  ('to_amount', '>=', self.total_price),
                                                                  ('expense_type', '=', self.expense_type),
                                                                  ('exp_category', '=', self.exp_category.id),
                                                                  ('type', '=', 'pr')], limit=1)

            workflow_data = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                #   ('branch_id', '=', self.ship_to.id),
                                                                  ('department_id', '=', self.department_id.id),
                                                                  ('from_amount', '<=', self.total_price),
                                                                  ('to_amount', '>=', self.total_price),
                                                                  ('expense_type', '=', self.expense_type),
                                                                  ('exp_category', '=', self.exp_category.id),
                                                                  ('type', '=', 'need_cr')], limit=1)
            print("cr_company_data : ", workflow_data)
            if workflow_data and workflow_data2:

                approve_user_ids2 = []
                workflow_line_data2 = self.env['pr.approve.users'].sudo().search(
                    [('pr_company_id', '=', workflow_data2.id)])  # searching in workflow line


                ### First Check And then only Approval flow Commit Pr

                for approverss in workflow_line_data2:
                    if approverss.branch_id.code == "COR":
                        ser_branch = approverss.branch_id.id
                        ser_branch_record = approverss.branch_id
                    else:
                        ser_branch = self.bill_to.id
                        ser_branch_record = self.bill_to
                    users_lines = self.env['res.users.line'].sudo().search(
                        [('company_id', '=', approverss.company_id.id), ('branch_id', '=', ser_branch),
                         ('department_id', '=', approverss.department_id.id),
                         ('designation', '=', approverss.designation.id)])  # searching user in users line
                    print(users_lines, "PR USERSSSSSSSSSSSSS")
                    if users_lines and users_lines.res_user_id:
                        pass
                    else:
                        raise ValidationError(
                            _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR PR APPROVAL") % (
                                approverss.designation.name, approverss.department_id.name,
                                ser_branch_record.name, approverss.company_id.name))

                approve_user_ids = []
                workflow_line_data = self.env['pr.approve.users'].sudo().search(
                    [('pr_company_id', '=', workflow_data.id)])  # searching in workflow line
                print('pr_company_line_data : ', workflow_line_data)

                ### First Check And then only Approval flow Commit cr need
                order_requested = 0
                requested_in_workflow = False
                limit = 0
                for approverss in workflow_line_data:
                    limit +=1
                for approvers in workflow_line_data:
                    if approvers.branch_id.code == "COR":
                        ser_branch = approvers.branch_id.id
                        ser_branch_record = approvers.branch_id
                    else:
                        ser_branch = self.bill_to.id
                        ser_branch_record = self.bill_to
                    users_line = self.env['res.users.line'].sudo().search(
                        [('company_id', '=', approvers.company_id.id), ('branch_id', '=', ser_branch),
                         ('department_id', '=', approvers.department_id.id),
                         ('designation', '=', approvers.designation.id)])  # searching user in users line
                    print(users_line, "PR USERSSSSSSSSSSSSS")
                    if users_line and users_line.res_user_id:
                        if users_line.res_user_id.id == self.requested_by.id and limit >1:
                            order_requested = approvers.approve_order
                            requested_in_workflow = True
                    else:
                        raise ValidationError(
                            _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR CR NEED APPROVAL") % (
                                approvers.designation.name, approvers.department_id.name,
                                ser_branch_record.name, approvers.company_id.name))

                    ## ## For Approval execution(else partial flow will be executed)
                pr_budget = self.env['product.request.budget'].sudo().search(
                            [('company_id', '=', self.company_id.id),
                            ('branch_id', '=', self.bill_to.id),
                            ('department_id', '=', self.department_id.id),
                            ('expense_type', '=', self.expense_type),
                            ('exp_category', '=', self.exp_category.id),
                            ('from_date', '<=', date.today()),
                            ('to_date', '>=', date.today()),
                            ], limit=1)
                if self.department_id.name == 'HO - IT' and not("CAPEX N/A" in self.exp_category.name):
                    if pr_budget:
                        pass

                    else:
                        raise ValidationError(_("No budget found"))
                        self.status  = 'draft'

                for approvers in workflow_line_data:
                    if approvers.branch_id.code == "COR":
                        ser_branch = approvers.branch_id.id
                        ser_branch_record = approvers.branch_id
                    else:
                        ser_branch = self.bill_to.id
                        ser_branch_record = self.bill_to
                    users_line = self.env['res.users.line'].sudo().search(
                        [('company_id', '=', approvers.company_id.id), ('branch_id', '=', ser_branch),
                         ('department_id', '=', approvers.department_id.id),
                         ('designation', '=', approvers.designation.id)])  # searching user in users line
                    print(users_line, "PR USERSSSSSSSSSSSSS")
                    if users_line and users_line.res_user_id:
                        if users_line.res_user_id.id == self.requested_by.id and limit>1:
                            print("order,req", order_requested,requested_in_workflow)
                        elif approvers.approve_order > order_requested and requested_in_workflow ==True :
                            order = approvers.approve_order-1
                            self.write({'approve_users_cr': [(4, users_line.res_user_id.id)]})
                            vals = {
                                'user_id': users_line.res_user_id.id,
                                'company_id': approvers.company_id.id,
                                'branch_id': ser_branch,
                                'department_id': approvers.department_id.id,
                                'designation': approvers.designation.id,
                                'approve_order': order,
                                'product_request_id': self.id
                            }
                            approve_user_ids.append({'user_id': users_line.res_user_id.id,
                                                    'approve_order': order})
                            pr_approve_line = self.env['cr.need.approve.line'].create(vals)
                        else:
                            
                            self.write({'approve_users_cr': [(4, users_line.res_user_id.id)]})
                            vals = {
                                'user_id': users_line.res_user_id.id,
                                'company_id': approvers.company_id.id,
                                'branch_id': ser_branch,
                                'department_id': approvers.department_id.id,
                                'designation': approvers.designation.id,
                                'approve_order': approvers.approve_order,
                                'product_request_id': self.id
                            }
                            approve_user_ids.append({'user_id': users_line.res_user_id.id,
                                                     'approve_order': approvers.approve_order})
                            pr_approve_line = self.env['cr.need.approve.line'].create(vals)
                        self.env.cr.commit()
                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                        pending_action = self.env['pending.actions'].sudo().search(
                            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)
                        if pending_action:
                            print(pending_action.name)
                            pending_action.status = 'closed'

                        activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')],
                                                                              limit=1)
                        print("type is", self.env.user.id)
                        activity = self.env['mail.activity'].search([
                            ('res_model_id', '=',
                             self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                            ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                            ('activity_type_id', '=', activity_type.id),
                        ], limit=1)
                        if activity:
                            print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                            print(activity.id)

                            activity.action_feedback(feedback="Activity completed")
                    else:
                        raise ValidationError(
                            _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                approvers.designation.name, approvers.department_id.name,
                                ser_branch_record.name, approvers.company_id.name))
                if approve_user_ids:
                    mylist = sorted(approve_user_ids, key=lambda k: int(k['approve_order']))

                    order = mylist[0]['approve_order']
                    for users in mylist:
                        if users['approve_order'] == order:
                            self.write({'next_approve_user_id_cr': [(4, users['user_id'])]})
                if not approve_user_ids:
                    raise UserError("No Approver's found for the current workflow")
                    print("approve_user_ids : ", approve_user_ids)
                if approve_user_ids:
                    mylist = sorted(approve_user_ids, key=lambda k: int(k['approve_order']))

                    order = mylist[0]['approve_order']
                    for users in mylist:
                        if users['approve_order'] == order:
                            self.write({'next_approve_user_id_cr': [(4, users['user_id'])]})
                if not approve_user_ids:
                    raise UserError("No Approver's found for the current workflow")

                self.status = 'on_check'
                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                if approve_user_ids:
                    user_ids_to_pass = self.next_approve_user_id_cr.ids
                    for user in self.next_approve_user_id_cr:
                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                   limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': self.name + " " + "Need for Request Waiting For Approval",
                            'record': self.id,
                            'branch': self.bill_to.id,
                            'department_id': self.department_id.id,
                            'exp_category': self.exp_category.id,
                            'Created_doc_date': self.requested_date,
                            'date': date.today(),
                        }
                        print("user",user,"next",self.next_approve_user_id_cr)
                        if user:
                            print("workkkkkkkkkkk")
                            user_ids_to_pass = user.ids
                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                            pendings = self.env['pending.actions'].create(pending_vals)
                            approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                            pendings.write({'email': approve_users_emails})
                            # print("Pendinggg",pendings)
                            activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')],
                                                                                 limit=1)
                            activity_type_id = activity_type.id if activity_type else False
                            res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id
                            for user_id in user_ids_to_pass:
                                activity_values = {
                                    'user_id': user_id,
                                    'res_id': self.id,
                                    'note': "Pending Action",
                                    'summary': "Action",
                                    'activity_type_id': activity_type_id,
                                    'res_model_id': res_model_id,
                                }
                                with self.env.cr.savepoint():
                                    self = self.with_context(mail_activity_quick_update=True)
                                    created_activity = self.env['mail.activity'].create(activity_values)
                print("next user",self.next_approve_user_id_cr)
                subject = "Purchase Request Waiting For APPROVAL: %s" % self.name

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Purchase Request')], limit=1) or False

                url_params = {
                    'id': self.id,
                    'action': self.env.ref('product_purchase.action_product_requests').id,
                    'model': 'product.request',
                    'view_type': 'form',
                    'menu_id': menu_id.id if menu_id else False,
                }

                params = '/web?#%s' % url_encode(url_params)
                url = base_url + params if base_url else "#"

                print(url)

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A new Purchase Request with the name <strong>{self.name} is waiting for Approval.<br>"
                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                )
                if self.next_approve_user_id_cr:
                    for user in self.next_approve_user_id_cr:
                        mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': user.login,
                            'auto_delete': False,
                            'author_id': author.id
                        }
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)
            elif not workflow_data2:
                raise ValidationError(
                    "Sorry,The criteria provided did not match any existing PR workflows,Please contact Administrator.")
            else:
                raise ValidationError(
                    "Sorry,The criteria provided did not match any existing Need for Request workflows,Please contact Administrator.")



        if any(line_item.contract_status == 'new' for line_item in line_items) and any(
                line_item.contract_status == 'in_contract' for line_item in line_items):
            raise UserError("Some products have existing rate contracts while others are new.")


        

        


    def action_reject_review(self):
        self.ensure_one()
        if self.exp_category and self.exp_category.reject_not_possible:
            raise ValidationError(
                "Rejection is not possible for this PR as the linked expense category does not allow rejection."
            )
        print("buyer Rejected PR")
        print("pr",self.id)
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pr_id': self.id},
        }
        # model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        # pending_action = self.env['pending.actions'].sudo().search(
        #     [('model', '=', model.id), ('record', '=', self.id),('status','=','open')], limit=1)
        #
        # if pending_action:
        #     print(pending_action.name)
        #     pending_action.status = 'closed'
        # self.status = 'declined'
        # self.message_post(body=f"{self.env.user.name} Rejected the Purchase Request.")
        # subject = "Purchase Request Rejected: %s" % self.name
        #
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # menu_id = self.env['ir.ui.menu'].sudo().search(
        #     [('name', '=', 'Purchase Request')], limit=1) or False
        #
        # url_params = {
        #     'id': self.id,
        #     'action': self.env.ref('product_purchase.action_product_requests').id,
        #     'model': 'product.request',
        #     'view_type': 'form',
        #     'menu_id': menu_id.id if menu_id else False,
        # }
        #
        # params = '/web?#%s' % url_encode(url_params)
        # url = base_url + params if base_url else "#"
        #
        # print(url)
        #
        # author = self.env['res.partner'].sudo().search(
        #     [('name', '=', 'Administrator')], limit=1)
        #
        # body = (
        #     f"Dear User, "
        #     f"A new Purchase Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
        #     f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
        #     f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
        #     f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        # )
        # if author:
        #     mail_values = {
        #         'subject': subject,
        #         'body_html': body,
        #         'email_to': self.requested_by.login,
        #         'auto_delete': False,
        #         'author_id': author.id
        #     }
        #     mail_record = self.env['mail.mail'].sudo().create(mail_values)


    def action_deligate(self):
        print("deligate")
        for lines in self.pr_approve_line:
            if lines.user_id.id == self.env.user.id:
                print("Founddd User")
                action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_action')
                action['context'] = {'default_request_id': self.id}

                return action
    def action_deligate_cr_need(self):
        print("deligate")
        for lines in self.cr_need_approve_line:
            if lines.user_id.id == self.env.user.id:
                print("Founddd User")
                action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_cr_need_action')
                action['context'] = {'default_request_id': self.id}

                return action
    def action_delegate_admin(self):
        
        # user_ids = [user.id for user in self.next_approve_user_id]
        approve_users = set(self.approve_users.ids)  # Fetch IDs of approve_users
        approved_users = set(self.approved_users.ids)  # Fetch IDs of approved_users

        user_ids = list(approve_users - approved_users)
        
        if not user_ids:
            return

        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_admin_action')
        action['context'] = {
            'default_request_id': self.id,
            'user_ids': user_ids,
            'type_id' : 'pr'
        }

        return action
    def action_delegate_admin_cr_need(self):

        # user_ids = [user.id for user in self.next_approve_user_id]
        approve_users = set(self.approve_users_cr.ids)  # Fetch IDs of approve_users
        approved_users = set(self.approved_users_cr.ids)  # Fetch IDs of approved_users

        user_ids = list(approve_users - approved_users)

        if not user_ids:
            return

        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_admin_action')
        action['context'] = {
            'default_request_id': self.id,
            'user_ids': user_ids,
            'type_id' : 'cr'
        }

        return action
    
    def action_approval_cr_need(self):

        self.write({'approved_users_cr': [(4, self.env.user.id)]})
        approve_users = self.env['cr.need.approve.line'].sudo().search(
            [('product_request_id', '=', self.id), ('user_id', '=', self.env.user.id)], )

        approve_users.write({
            'status': 'accept',
            'approve_date': fields.Date.today()
        })
        # self.message_post(body=f" {approve_users.user_id.name} Approved.")
        # self.message_post(body="Remarks " + self.remarks_ids.replay)

        if self.approved_users_cr == self.approve_users_cr:
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

            if pending_action:
                for rec in pending_action:
                    rec.status = 'closed'
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ])
            if activity:
                for rec in activity:
                    activity.action_feedback(feedback="Activity completed")

            line_items = self.product_request_line_ids
            if all(line_item.contract_status == 'in_contract' for line_item in line_items) and (self.department_id.name == 'HO - IT' or self.department_id.name == 'Branch - IT'):
                self.action_request()
            else:
                # Create tender record if no vendors are found
                tender_record = self.env['tenders'].create({
                    'main_remark':self.main_remark,
                    'user_id': self.requested_by.id,
                    'requested_date' : self.requested_date,
                    'company_ids': [(4, self.company_id.id)],
                    'branch_ids': [(4, self.ship_to.id)],
                    'purchase_plan': self.purchase_plan,
                    'department_id': self.department_id.id,
                    'file_upload': self.file_upload,
                    'total_price': self.total_price,
                    'product_requested_id': self.id,
                    'expense_type': self.expense_type,
                    'exp_category': self.exp_category.id,
                    'product_group': [(6, 0, self.product_group.ids)],
                    'contracts_request_line': [(0, 0, {
                        'product_id': line.product.id,
                        'description': line.description,
                        'unit_price': line.unit_price,
                        'quantity': line.quantity,
                    }) for line in self.product_request_line_ids]
                })
                self.status = 'wait'
                self.message_post(body="A Contract request has been generated, wait for approval.")
                self.attachments_to_contract()
                ################### Initiating PR
                users_line = self.env['res.users.line'].sudo().search(
                    [
                     ('department_id.name', '=', 'SCM'),
                     ('designation', '=', 'Purchase Head')],limit=1)
                print("Purchase head",users_line,users_line.res_user_id.name)
                tender_record.purchase_head = users_line.res_user_id.id
                if users_line and users_line.res_user_id.id:
                    # subject = "New Contract Request Raised: %s" % tender_record.name
                    # print("Name", tender_record.name)
                    # body = ("Dear Buyer, "
                    #         "A new Contract Request with the name %s has been raised against an Purchase Request by %s" % (
                    #             tender_record.name, self.requested_by))

                    # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    # menu_id = self.env['ir.ui.menu'].sudo().search(
                    #     [('name', '=', 'Contract Request')], limit=1) or False

                    # url_params = {
                    #     'id': tender_record.id,
                    #     'action': self.env.ref('product_purchase.action_tender_status').id,
                    #     'model': 'tenders',
                    #     'view_type': 'form',
                    #     'menu_id': menu_id.id if menu_id else False,
                    # }

                    # params = '/web?#%s' % url_encode(url_params)
                    # url = base_url + params if base_url else "#"

                    # print(url)
                    # email_to_list = [user.email if user.email else user.login for user in buyer_users]

                    # author = self.env['res.partner'].sudo().search(
                    #     [('name', '=', 'Administrator')], limit=1)

                    # body = (
                    #     f"Dear Buyer, "
                    #     f"A new Contract Request with the name <strong>{tender_record.name}</strong> has been raised against Purchase Request by <strong>{self.requested_by.name}</strong>.<br>"
                    #     f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                    #     f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                    #     f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                    # )
                    # # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                    # # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                    # # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                    # # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                    # # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                    # # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"
                    # if author:
                    #     mail_values = {
                    #         'subject': subject,
                    #         'body_html': body,
                    #         'email_to': ','.join(email_to_list),
                    #         'auto_delete': False,
                    #         'author_id': author.id
                    #     }
                    #     mail_record = self.env['mail.mail'].sudo().create(mail_values)

                    ########### Creating Pending Actions

                    model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                    pending_vals = {
                        'model': model.id,
                        'name': tender_record.name + " " + "Assign Contract Request ",
                        'record': tender_record.id,
                        'branch': self.bill_to.id,
                        'department_id': tender_record.department_id.id,
                        'exp_category': tender_record.exp_category.id,
                        'Created_doc_date': tender_record.requested_date,
                        'date': date.today(),
                    }



                    user_ids = [user.id for user in users_line.res_user_id]
                    pending_vals['approve_users'] = [(6, 0, user_ids)]
                    pendings = self.env['pending.actions'].create(pending_vals)
                    approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                    pendings.write({'email': approve_users_emails})
                    self.status = 'initiate'
                    self.message_post(body="PR initiated and waiting for Buyer's Approval")
                else:
                    raise UserError("No User found on Buyer group")



        else:
            ## Remaining Users pending action
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
            print("all records", pending_action)
            if pending_action:
                for rec in pending_action:
                    if self.env.user in rec.approve_users:
                        print("record to close", rec)
                        rec.status = 'closed'


            # activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')], limit=1)
            # activity_type_id = activity_type.id if activity_type else False
            # res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                activity.action_feedback(feedback="Activity completed")
            #############################

            approve_users = self.env['cr.need.approve.line'].sudo().search([('product_request_id', '=', self.id)],
                                                                      order='approve_order asc')

            user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
            # print(user_ids)

            order_list = list(set([order_id.approve_order for order_id in approve_users]))
            order_list.sort()
            approve_dict = {}
            print("order_list ", order_list)
            for order in order_list:
                for user in user_ids:
                    if user['order'] == order:
                        if order in approve_dict:
                            approve_dict[order].append({'u_id': user['u_id'], 'order': user['order']})
                        else:
                            approve_dict[order] = [{'u_id': user['u_id'], 'order': user['order']}]

            print("approve_dict ", approve_dict)

            record_to_remove = self.env['res.users'].browse(self.env.user.id)
            self.next_approve_user_id_cr -= record_to_remove

            if not self.next_approve_user_id_cr:
                for order in order_list:
                    for order_list_users in approve_dict[order]:
                        if self.env.user.id == order_list_users['u_id']:
                            try:
                                if approve_dict[order + 1]:
                                    for users in approve_dict[order + 1]:
                                        self.write({'next_approve_user_id_cr': [(4, users['u_id'])]})

                                    ####################### MAil ############################
                                    print(self.next_approve_user_id,
                                          "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                        [('name', '=', 'Purchase Request')], limit=1) or False

                                    url_params = {
                                        'id': self.id,
                                        'action': self.env.ref('product_purchase.action_product_requests').id,
                                        'model': 'product.request',
                                        'view_type': 'form',
                                        # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                        'menu_id': menu_id.id,
                                    }
                                    params = '/web?#%s' % url_encode(url_params)
                                    view_url = base_url + params if base_url else "#"

                                    ##################### URL for Approval #########################

                                    # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    # menu_id = self.env['ir.ui.menu'].sudo().search(
                                    #     [('name', '=', 'Purchase Request')], limit=1) or False
                                    #
                                    # url_params = {
                                    #     'id': self.id,
                                    #     'action': self.env.ref('product_purchase.action_product_requests').id,
                                    #     'model': 'product.request',
                                    #     'view_type': 'form',
                                    #     'menu_id': menu_id.id if menu_id else False,
                                    #     'function': 'action_approval',
                                    # }
                                    #
                                    # params = '/web?#%s' % url_encode(url_params)
                                    # approval_url = base_url + params if base_url else "#"

                                    author = self.env['res.partner'].sudo().search(
                                        [('name', '=', 'Administrator')], limit=1) or False

                                    body = (
                                        f"Dear User,A Purchase request {self.name} is waiting for Approval.<br><br>"
                                        f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                                        # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                                        # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                                        # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                                        # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"

                                    )

                                    for user in self.next_approve_user_id_cr:
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                   limit=1)
                                        pending_vals = {
                                            'model': model.id,
                                            'name': self.name + " " + "Need of Request For Approval",
                                            'record': self.id,
                                            'branch': self.bill_to.id,
                                            'department_id': self.department_id.id,
                                            'exp_category': self.exp_category.id,
                                            'Created_doc_date': self.requested_date,
                                            'date': date.today(),
                                        }
                                        if user:
                                            user_ids_to_pass = user.ids
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            pendings = self.env['pending.actions'].create(pending_vals)
                                            approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                            pendings.write({'email': approve_users_emails})

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Request')], limit=1)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'product.request')]).id
                                            for user_id in user_ids_to_pass:
                                                activity_values = {
                                                    'user_id': user.id,
                                                    'res_id': self.id,
                                                    'note': "Pending Action",
                                                    'summary': "Action",
                                                    'activity_type_id': activity_type_id,
                                                    'res_model_id': res_model_id,
                                                }
                                                with self.env.cr.savepoint():
                                                    self = self.with_context(mail_activity_quick_update=True)
                                                    created_activity = self.env['mail.activity'].create(activity_values)

                                        if user.login:
                                            subject = "Need of Contract -Approval Pending: %s" % self.name
                                            mail_values = {
                                                'subject': subject,
                                                'body_html': body,
                                                'email_to': user.login,
                                                'auto_delete': False,
                                                'author_id': author.id
                                            }
                                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                            # mail_record.send()


                            ####################

                            except:
                                print("order+1 ", order + 1)
                                print("order_list[-1] ", order_list[-1])
                                flag = 0
                                for i in range(order + 1, order_list[-1] + 1):
                                    print("i: ", i)
                                    print("len(order_list) : ", len(order_list))
                                    try:
                                        if approve_dict[i]:
                                            for users in approve_dict[i]:
                                                print("write")
                                                self.write({'next_approve_user_id_cr': [(4, users['u_id'])]})
                                                flag = 1

                                                print(self.next_approve_user_id_cr,
                                                      "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Purchase Request')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref(
                                                        'product_purchase.action_product_requests').id,
                                                    'model': 'product.request',
                                                    'view_type': 'form',
                                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                                    'menu_id': menu_id.id,
                                                }
                                                params = '/web?#%s' % url_encode(url_params)
                                                view_url = base_url + params if base_url else "#"

                                                ##################### URL for Approval #########################

                                                # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                                # menu_id = self.env['ir.ui.menu'].sudo().search(
                                                #     [('name', '=', 'Purchase Request')], limit=1) or False
                                                #
                                                # url_params = {
                                                #     'id': self.id,
                                                #     'action': self.env.ref('product_purchase.action_product_requests').id,
                                                #     'model': 'product.request',
                                                #     'view_type': 'form',
                                                #     'menu_id': menu_id.id if menu_id else False,
                                                #     'function': 'action_approval',
                                                # }
                                                #
                                                # params = '/web?#%s' % url_encode(url_params)
                                                # approval_url = base_url + params if base_url else "#"

                                                author = self.env['res.partner'].sudo().search(
                                                    [('name', '=', 'Administrator')], limit=1) or False

                                                body = (
                                                    f"Dear User,A Purchase request {self.name} is waiting for Approval.<br><br>"
                                                    f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                                                    # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                                                    # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                                                    # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                                                    # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                                                    # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                                                    # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"

                                                )

                                                for user in self.next_approve_user_id_cr:
                                                    model = self.env['ir.model'].sudo().search(
                                                        [('model', '=', self._name)],
                                                        limit=1)
                                                    pending_vals = {
                                                        'model': model.id,
                                                        'name': self.name + " " + "Need for Request For Approval",
                                                        'record': self.id,
                                                        'branch': self.bill_to.id,
                                                        'department_id': self.department_id.id,
                                                        'exp_category': self.exp_category.id,
                                                        'Created_doc_date': self.requested_date,
                                                        'date': date.today(),
                                                    }
                                                    if user:
                                                        user_ids_to_pass = user.ids
                                                        pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                        pendings = self.env['pending.actions'].create(pending_vals)
                                                        approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                                        pendings.write({'email': approve_users_emails})

                                                        activity_type = self.env['mail.activity.type'].sudo().search(
                                                            [('name', '=', 'Pending Request')], limit=1)
                                                        activity_type_id = activity_type.id if activity_type else False
                                                        res_model_id = self.env['ir.model'].sudo().search(
                                                            [('model', '=', 'product.request')]).id
                                                        for user_id in user_ids_to_pass:
                                                            activity_values = {
                                                                'user_id': user.id,
                                                                'res_id': self.id,
                                                                'note': "Pending Action",
                                                                'summary': "Action",
                                                                'activity_type_id': activity_type_id,
                                                                'res_model_id': res_model_id,
                                                            }
                                                            with self.env.cr.savepoint():
                                                                self = self.with_context(mail_activity_quick_update=True)
                                                                created_activity = self.env['mail.activity'].create(
                                                                activity_values)

                                                    if user.login:
                                                        subject = "Need of Contract -Approval Pending: %s" % self.name
                                                        mail_values = {
                                                            'subject': subject,
                                                            'body_html': body,
                                                            'email_to': user.login,
                                                            'auto_delete': False,
                                                            'author_id': author.id
                                                        }
                                                        mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                                        # mail_record.send()

                                                print(self.next_approve_user_id_cr)
                                    except:
                                        print("pass")
                                        pass
                                    if flag:
                                        break
    
    def admin_create_po(self):
        purchase_orders_by_vendor = {}
        for line_item in self.product_request_line_ids:
            print(line_item.vendors)

            for vendor in line_item.vendors:
                if vendor.id not in purchase_orders_by_vendor:
                    # Check if a purchase order already exists for the vendor
                    existing_purchase_order = self.env['purchase.order'].sudo().search([
                        ('partner_id', '=', vendor.id),
                        ('state', '=', 'draft'),
                        ('pr_id', '=', self.id),('company_id','=',self.company_id.id)
                    ], limit=1)

                    picking_id = self.env['stock.picking.type'].sudo().search([
                        ('company_id', '=', self.company_id.id),
                        ('code', '=', 'incoming'),
                    ], limit=1)

                    if existing_purchase_order:
                        purchase_orders_by_vendor[vendor.id] = existing_purchase_order
                    else:
                        # Create a new purchase order if no existing order is found
                        purchase_order_vals = {
                            'partner_id': vendor.id,
                            'company_id': self.company_id.id,
                            'is_auto_po': False,
                            'expense_type': self.expense_type or '',
                            'department_id': self.department_id.id or '',
                            'bill_to': self.bill_to.id,
                            'ship_to': self.ship_to.id,
                            'exp_category': self.exp_category.id,
                            'pr_id': self.id,
                            'user_id': self.requested_by.id,
                            'pr_budget_id': self.budget_details.id,
                            'branch_id': self.ship_to.id,
                            'payment_term_id':line_item.payment_terms.id, 
                            'product_bundle' : self.product_bundle,
                            'is_terms':True,
                            'picking_type_id': picking_id.id,
                            'product_bundle': self.product_bundle,
                            'ct_number': [(6, 0, [line_item.contract.id])],
                        }

                        purchase_order = self.env['purchase.order'].sudo().create(purchase_order_vals)

                        # Store the created purchase order in the dictionary
                        purchase_orders_by_vendor[vendor.id] = purchase_order

                        # purchase_order._onchange_partner_id()

                # Append product to the existing or new purchase order for the vendor
                products = self.env['product.product'].sudo().search([
                    ('product_tmpl_id', '=', line_item.product.id)],
                    limit=1)
                # taxes_ids = products.supplier_taxes_id.id
                # tax = 0
                # for tax_id in taxes_ids:
                #     id = tax_id.id
                #     tax = self.env['account.tax'].sudo().search([
                #     ('id', '=', id),('company_id', '=', self.company_id.id)],
                #     limit=1)

                order_line_vals = {
                    'display_type': False,
                    # 'name': line_item.product.name or '',
                    'name':line_item.description or '',
                    'product_id': products.id,
                    'price_unit': line_item.unit_price,
                    'product_qty': line_item.quantity,
                    'product_uom': line_item.product.uom_po_id.id,
                    'order_id': purchase_orders_by_vendor[vendor.id].id,
                    'company_id': self.company_id.id,
                    # 'taxes_id': taxes_ids
                }

                order_line = self.env['purchase.order.line'].sudo().create(order_line_vals)
                existing_contract_ids = purchase_orders_by_vendor[vendor.id].ct_number.ids
                new_contract_id = line_item.contract.id

                if new_contract_id not in existing_contract_ids:
                    combined_contract_ids = list(set(existing_contract_ids + [new_contract_id]))

                    # Update the purchase order's contract numbers
                    purchase_orders_by_vendor[vendor.id].sudo().write({
                        'ct_number': [(6, 0, combined_contract_ids)]
                    })
                order_line._onchange_product_id()
        purchase_order.button_confirm()

        # Commit the changes to the database
        self.env.cr.commit()

    def action_approval(self):
        self.write({'approved_users': [(4, self.env.user.id)]})
        approve_users = self.env['pr.approve.line'].sudo().search(
            [('product_request_id', '=', self.id), ('user_id', '=', self.env.user.id)], )

        approve_users.write({
            'status': 'accept',
            'approve_date': fields.Date.today()
        })
        #self.message_post(body=f" {approve_users.user_id.name} Approved.")

        if self.approved_users == self.approve_users:
            self.status = 'accepted'
            self.message_post(body="PR Approved and PO generated.")

            author = self.env['res.partner'].sudo().search(
                [('name', '=', 'Administrator')], limit=1) or False
            body = f"Dear {self.requested_by.name},Your Purchase request {self.name} has been Approved."
            vals = {
                'subject': 'PR APPROVED',
                'body_html': body,
                'email_to': self.requested_by.login,
                'auto_delete': False,
                'author_id': author.id
                # 'email_from': ,
            }
            # print(vals)
            mail_id = self.env['mail.mail'].sudo().create(vals)
            # mail_id.sudo().send()

            #######  Pending Actions ################
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id),('status','=','open')], limit=1)

            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close",rec)
                    rec.status = 'closed'
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                ('user_id', '=', self.env.user.id),('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                activity.action_feedback(feedback="Activity completed")
            #############################
            print("Approved")
            purchase_orders_by_vendor = {}
            purchase_order = False
            for line_item in self.product_request_line_ids:
                print(line_item.vendors)

                for vendor in line_item.vendors:
                    if vendor.id not in purchase_orders_by_vendor:
                        # Check if a purchase order already exists for the vendor
                        existing_purchase_order = self.env['purchase.order'].sudo().search([
                            ('partner_id', '=', vendor.id),
                            ('state', '=', 'draft'),
                            ('pr_id', '=', self.id),('company_id','=',self.company_id.id)
                        ], limit=1)
                        picking_id = self.env['stock.picking.type'].sudo().search([
                            ('company_id', '=', self.company_id.id),
                            ('code', '=', 'incoming'),
                        ], limit=1)
                        if existing_purchase_order:
                            existing_contract_ids = existing_purchase_order.ct_number.ids
                            purchase_orders_by_vendor[vendor.id] = existing_purchase_order
                        else:
                            # Create a new purchase order if no existing order is found
                            purchase_order_vals = {
                                'partner_id': vendor.id,
                                'company_id': self.company_id.id,
                                'is_auto_po': False,
                                'expense_type': self.expense_type or '',
                                'department_id': self.department_id.id or '',
                                'bill_to': self.bill_to.id,
                                'ship_to': self.ship_to.id,
                                'exp_category': self.exp_category.id,
                                'pr_id': self.id,
                                'user_id': self.requested_by.id,
                                'pr_budget_id': self.budget_details.id,
                                'branch_id': self.ship_to.id,
                                'payment_term_id':line_item.payment_terms.id,
                                'is_terms':True,
                                'picking_type_id': picking_id.id,
                                'product_bundle': self.product_bundle,
                                'ct_number': [(6, 0, [line_item.contract.id])],
                            }

                            purchase_order = self.env['purchase.order'].sudo().create(purchase_order_vals)

                            # Store the created purchase order in the dictionary
                            purchase_orders_by_vendor[vendor.id] = purchase_order

                    # Append product to the existing or new purchase order for the vendor
                    products = self.env['product.product'].sudo().search([
                        ('product_tmpl_id', '=', line_item.product.id)],
                        limit=1)

                    order_line_vals = {
                        'display_type': False,
                        # 'name': line_item.product.name or '',
                        'name':line_item.description or '',
                        'product_id': products.id,
                        'price_unit': line_item.unit_price,
                        'product_qty': line_item.quantity,
                        'product_uom': line_item.product.uom_po_id.id,
                        'order_id': purchase_orders_by_vendor[vendor.id].id,
                    }

                    order_line = self.env['purchase.order.line'].sudo().create(order_line_vals)

                    existing_contract_ids = purchase_orders_by_vendor[vendor.id].ct_number.ids
                    new_contract_id = line_item.contract.id

                    if new_contract_id not in existing_contract_ids:
                        combined_contract_ids = list(set(existing_contract_ids + [new_contract_id]))

                        # Update the purchase order's contract numbers
                        purchase_orders_by_vendor[vendor.id].sudo().write({
                            'ct_number': [(6, 0, combined_contract_ids)]
                        })


                    order_line._onchange_product_id()
            purchase_order.button_confirm()

            # Commit the changes to the database
            self.env.cr.commit()


        else:
            #######  Pending Actions ################
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id),('status','=','open')])
            if pending_action:
                for rec in pending_action:
                    if self.env.user in rec.approve_users:
                        print("record to close",rec)
                        rec.status = 'closed'

            # activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')], limit=1)
            # activity_type_id = activity_type.id if activity_type else False
            # res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                ('user_id', '=', self.env.user.id),('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                activity.action_feedback(feedback="Activity completed")
            #############################

            approve_users = self.env['pr.approve.line'].sudo().search([('product_request_id', '=', self.id)],
                                                                      order='approve_order asc')

            user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
            # print(user_ids)

            order_list = list(set([order_id.approve_order for order_id in approve_users]))
            order_list.sort()
            approve_dict = {}
            print("order_list ", order_list)
            for order in order_list:
                for user in user_ids:
                    if user['order'] == order:
                        if order in approve_dict:
                            approve_dict[order].append({'u_id': user['u_id'], 'order': user['order']})
                        else:
                            approve_dict[order] = [{'u_id': user['u_id'], 'order': user['order']}]

            print("approve_dict ", approve_dict)

            record_to_remove = self.env['res.users'].browse(self.env.user.id)
            self.next_approve_user_id -= record_to_remove

            if not self.next_approve_user_id:
                for order in order_list:
                    for order_list_users in approve_dict[order]:
                        if self.env.user.id == order_list_users['u_id']:
                            try:
                                if approve_dict[order + 1]:
                                    for users in approve_dict[order + 1]:
                                        self.write({'next_approve_user_id': [(4, users['u_id'])]})

                            ####################### MAil ############################
                                    print(self.next_approve_user_id ,"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                        [('name', '=', 'Purchase Request')], limit=1) or False

                                    url_params = {
                                        'id': self.id,
                                        'action': self.env.ref('product_purchase.action_product_requests').id,
                                        'model': 'product.request',
                                        'view_type': 'form',
                                        # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                        'menu_id': menu_id.id,
                                    }
                                    params = '/web?#%s' % url_encode(url_params)
                                    view_url = base_url + params if base_url else "#"

                                    ##################### URL for Approval #########################

                                    # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    # menu_id = self.env['ir.ui.menu'].sudo().search(
                                    #     [('name', '=', 'Purchase Request')], limit=1) or False
                                    #
                                    # url_params = {
                                    #     'id': self.id,
                                    #     'action': self.env.ref('product_purchase.action_product_requests').id,
                                    #     'model': 'product.request',
                                    #     'view_type': 'form',
                                    #     'menu_id': menu_id.id if menu_id else False,
                                    #     'function': 'action_approval',
                                    # }
                                    #
                                    # params = '/web?#%s' % url_encode(url_params)
                                    # approval_url = base_url + params if base_url else "#"

                                    author = self.env['res.partner'].sudo().search(
                                        [('name', '=', 'Administrator')], limit=1) or False

                                    body = (
                                        f"Dear User,A Purchase request {self.name} is waiting for Approval.<br><br>"
                                        f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                                        # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                                        # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                                        # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                                        # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"

                                    )

                                    for user in self.next_approve_user_id:
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                   limit=1)
                                        pending_vals = {
                                            'model': model.id,
                                            'name': self.name + " " + "Waiting For Approval",
                                            'record': self.id,
                                            'branch': self.bill_to.id,
                                            'department_id': self.department_id.id,
                                            'exp_category': self.exp_category.id,
                                            'Created_doc_date': self.requested_date,
                                            'date': date.today(),
                                        }
                                        if user:
                                            user_ids_to_pass = user.ids
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            pendings = self.env['pending.actions'].create(pending_vals)
                                            approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                            pendings.write({'email': approve_users_emails})

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Request')], limit=1)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'product.request')]).id
                                            for user_id in user_ids_to_pass:
                                                activity_values = {
                                                    'user_id': user.id,
                                                    'res_id': self.id,
                                                    'note': "Pending Action",
                                                    'summary': "Action",
                                                    'activity_type_id': activity_type_id,
                                                    'res_model_id': res_model_id,
                                                }
                                                with self.env.cr.savepoint():
                                                    self = self.with_context(mail_activity_quick_update=True)
                                                    created_activity = self.env['mail.activity'].create(activity_values)

                                        if user.login:
                                            subject = "Purchase Request Waiting For APPROVAL: %s" % self.name
                                            mail_values = {
                                                'subject': subject,
                                                'body_html': body,
                                                'email_to': user.login,
                                                'auto_delete': False,
                                                'author_id': author.id
                                            }
                                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                            # mail_record.send()


                            ####################


                            except:
                                print("order+1 ", order + 1)
                                print("order_list[-1] ", order_list[-1])
                                flag = 0
                                for i in range(order + 1, order_list[-1] + 1):
                                    print("i: ", i)
                                    print("len(order_list) : ", len(order_list))
                                    try:
                                        if approve_dict[i]:
                                            for users in approve_dict[i]:
                                                print("write")
                                                self.write({'next_approve_user_id': [(4, users['u_id'])]})
                                                flag = 1

                                                print(self.next_approve_user_id,
                                                      "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Purchase Request')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref(
                                                        'product_purchase.action_product_requests').id,
                                                    'model': 'product.request',
                                                    'view_type': 'form',
                                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                                    'menu_id': menu_id.id,
                                                }
                                                params = '/web?#%s' % url_encode(url_params)
                                                view_url = base_url + params if base_url else "#"

                                                ##################### URL for Approval #########################

                                                # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                                # menu_id = self.env['ir.ui.menu'].sudo().search(
                                                #     [('name', '=', 'Purchase Request')], limit=1) or False
                                                #
                                                # url_params = {
                                                #     'id': self.id,
                                                #     'action': self.env.ref('product_purchase.action_product_requests').id,
                                                #     'model': 'product.request',
                                                #     'view_type': 'form',
                                                #     'menu_id': menu_id.id if menu_id else False,
                                                #     'function': 'action_approval',
                                                # }
                                                #
                                                # params = '/web?#%s' % url_encode(url_params)
                                                # approval_url = base_url + params if base_url else "#"

                                                author = self.env['res.partner'].sudo().search(
                                                    [('name', '=', 'Administrator')], limit=1) or False

                                                body = (
                                                    f"Dear User,A Purchase request {self.name} is waiting for Approval.<br><br>"
                                                    f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                                                    # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                                                    # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                                                    # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                                                    # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                                                    # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                                                    # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"

                                                )

                                                for user in self.next_approve_user_id:
                                                    model = self.env['ir.model'].sudo().search(
                                                        [('model', '=', self._name)],
                                                        limit=1)
                                                    pending_vals = {
                                                        'model': model.id,
                                                        'name': self.name + " " + "Waiting For Approval",
                                                        'record': self.id,
                                                        'branch': self.bill_to.id,
                                                        'department_id': self.department_id.id,
                                                        'exp_category': self.exp_category.id,
                                                        'Created_doc_date': self.requested_date,
                                                        'date': date.today(),
                                                    }
                                                    if user:
                                                        user_ids_to_pass = user.ids
                                                        pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                        pendings = self.env['pending.actions'].create(pending_vals)
                                                        approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                                        pendings.write({'email': approve_users_emails})

                                                        activity_type = self.env['mail.activity.type'].sudo().search(
                                                            [('name', '=', 'Pending Request')], limit=1)
                                                        activity_type_id = activity_type.id if activity_type else False
                                                        res_model_id = self.env['ir.model'].sudo().search(
                                                            [('model', '=', 'product.request')]).id
                                                        for user_id in user_ids_to_pass:
                                                            activity_values = {
                                                                'user_id': user.id,
                                                                'res_id': self.id,
                                                                'note': "Pending Action",
                                                                'summary': "Action",
                                                                'activity_type_id': activity_type_id,
                                                                'res_model_id': res_model_id,
                                                            }
                                                            with self.env.cr.savepoint():
                                                                self = self.with_context(mail_activity_quick_update=True)
                                                                created_activity = self.env['mail.activity'].create(
                                                                activity_values)

                                                    if user.login:
                                                        subject = "Purchase Request Waiting For APPROVAL: %s" % self.name
                                                        mail_values = {
                                                            'subject': subject,
                                                            'body_html': body,
                                                            'email_to': user.login,
                                                            'auto_delete': False,
                                                            'author_id': author.id
                                                        }
                                                        mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                                        # mail_record.send()

                                                print(self.next_approve_user_id)
                                    except:
                                        print("pass")
                                        pass
                                    if flag:
                                        break
        

    def action_decline(self):
        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
        print("pending action", pending_action)

        if pending_action:
            for pend in pending_action:
                print(pending_action.name)
                pend.status = 'closed'

        activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
        print("type is", self.env.user.id)
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
            ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
            ('activity_type_id', '=', activity_type.id),
        ])
        if activity:
            for act in activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(act.id)
                act.action_feedback(feedback="Activity Declined")
        
        # self.budget_details._compute_remaining_amount()
        self.message_post(body=f"{self.env.user.name} Rejected the Purchase Request.")
        # subject = "Purchase Request Rejected: %s" % self.name

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Purchase Request')], limit=1) or False

        url_params = {
            'id': self.id,
            'action': self.env.ref('product_purchase.action_product_requests').id,
            'model': 'product.request',
            'view_type': 'form',
            'menu_id': menu_id.id if menu_id else False,
        }

        params = '/web?#%s' % url_encode(url_params)
        url = base_url + params if base_url else "#"

        print(url)

        author = self.env['res.partner'].sudo().search(
            [('name', '=', 'Administrator')], limit=1)

        if self.status == 'requested':
            if self.budget_details:
                self.budget_details.amount_used -= self.total_price
                print("budject", self.budget_details.amount_used)
            for line_ids in self.product_request_line_ids:
                vendor_limit = self.env['vendor.limit'].sudo().search(
                    [('vendor_id', '=', line_ids.vendors.ids[0]),('start_date', '<=', line_ids.expected_date),
                        ('end_date', '>=', line_ids.expected_date), ('status', '=', 'active')], limit=1)
                if vendor_limit:
                    vendor_limit.amount_used -= self.total_price
            print("requested")
            body = (
                f"Dear User, "
                f"The Purchase Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
            )
            subject = "Purchase Request Rejected: %s" % self.name
            for approvers in self.pr_approve_line:
                print("approvers", approvers)
                if approvers.user_id.id == self.env.user.id:
                    approvers.write({'status': 'cancel'})

                if approvers.status == 'accept':
                    print("app", approvers.status)
                    if author:
                        mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': approvers.user_id.login,
                            'auto_delete': False,
                            'author_id': author.id
                        }
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)

            if author:
                if self.requested_by:
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': self.requested_by.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    print("mail", mail_record)
            self.status = 'declined'
        if self.status == 'on_check':
            body = (
                f"Dear User, "
                f"The Need For Contract Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
            )
            subject = "Need For Contract Request Rejected: %s" % self.name

            for approvers in self.cr_need_approve_line:
                if approvers.user_id.id == self.env.user.id:
                    approvers.write({'status': 'cancel'})

                if approvers.status == 'accept':
                    print("app", approvers.status)
                    if author:
                        mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': approvers.user_id.login,
                            'auto_delete': False,
                            'author_id': author.id
                        }
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)
            if author:
                if self.requested_by:
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': self.requested_by.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
            self.status = 'declined'
        
    def total_price_calculation(self, result):
        total_price = 0
        # print(self.product_request_line_ids)
        # print(result.product_request_line_ids)
        if self.product_request_line_ids:
            total_price = 0
            for line_product in self.product_request_line_ids:
                print(line_product.unit_price)
                print(line_product.quantity)
                total_price += line_product.unit_price * line_product.quantity
        elif result.product_request_line_ids:
            total_price = 0
            for line_product in result.product_request_line_ids:
                print(line_product.unit_price)
                print(line_product.quantity)
                total_price += line_product.unit_price * line_product.quantity
        else:
            raise ValidationError("Product list is empty!")
        # print("return ", total_price)
        return total_price

    @api.model
    def create(self, vals):
        # Calculating total price
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.request') or 'New'

        result = super(ProductRequest, self).create(vals)
        total_price_sum = self.total_price_calculation(result)
        # if total_price_sum <= 0:
        #     # if self.env.user.has_group('product_purchase.group_initial_approval'):
        #     raise ValidationError("Invalid price/Quantity")
        records = self.env['product.request.line'].sudo().search([('product_request_id', '=', result.id)])
        product_counts = {}
        for rec in records:
            if rec.contract_status == 'new':
                product_counts[rec.product.id] = product_counts.get(rec.product.id, 0) + 1
                if product_counts[rec.product.id] > 1:
                    raise UserError(_("A product of New Contract status cannot be entered more than once"))
        return result

    def write(self, vals):
        result = super(ProductRequest, self).write(vals)

        records = self.env['product.request.line'].sudo().search([('product_request_id', '=', self.id)])
        product_counts = {}
        for rec in records:
            if rec.contract_status == 'new':
                product_counts[rec.product.id] = product_counts.get(rec.product.id, 0) + 1
                if product_counts[rec.product.id] > 1:
                    raise UserError(_("A product of New Contract status cannot be entered more than once"))
        return result
class ProductRequestLine(models.Model):
    _name = "product.request.line"
    _description = "Product Request"

    product = fields.Many2one('product.template', string="Product", store=True, force_save=True,
                              required=True,)
    quantity = fields.Float(string="Quantity", required=True)
    expected_date = fields.Date(string="Need By Date", required=True)
    requirement_status = fields.Selection(
        selection=[('draft', 'Within 30 days'), ('open', 'Within 15 days'), ('immediate', 'Within 5 days')],
        string='Requirement Status',
        default='draft',
        required=True
    )

    payment_terms = fields.Many2one('account.payment.term', "Payment Terms")

    unit_price = fields.Float(string="Unit Price", store=True, force_save=True, digits=(16, 4))
    description = fields.Char(string="Description")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        invisible=True
    )

    is_lease = fields.Boolean(string="Lease")
    end_date = fields.Date("Lease End Date")
    vendors = fields.Many2many('res.partner', string="Vendors")

    status = fields.Selection(
        selection=[('draft', 'Draft'), ('lease', 'LEASED'), ('requested', 'Requested'), ('accepted', 'Accepted'),
                   ('reject', 'Rejected')],
        string='Status',
        default='draft',
        required=True
    )

    contract_status = fields.Selection(
        selection=[('new', 'New'), ('in_contract', 'In Contract')],
        string='Contract Status',
        default='new',
        required=True,store=True,force_save=True
    )

    uom = fields.Many2one('uom.uom', 'UOM', related='product.uom_po_id')
    pack = fields.Float('Pack Size', related='product.pack_size')
    brand = fields.Char('Brand', related='product.brand')
    oem = fields.Char('OEM', related='product.oem')

    stock = fields.Float('Current Stock')
    consumption = fields.Float('Avg Consumption')

    product_request_id = fields.Many2one('product.request', string='Product Request Id',
                                         invisible=True)
    # tender_deadline = fields.Date(string="Contract Deadline")
    from_date = fields.Date(string="Contract Start Date", tracking=True, )
    to_date = fields.Date(string="Contract End Date", tarcking=True, )

    vendors_domain = fields.Char(
        compute="_compute_vendors_domain",
        readonly=True,
        store=False,
    )


    contract_details = fields.Boolean("Contract", compute='compute_contract_status')
    contract = fields.Many2one('product.tender.line', string="Contract",compute="_compute_contract",store=True)

    @api.depends('vendors')
    def _compute_contract(self):
        for rec in self:
            if rec.product:
                contract = self.env['product.tender.line'].sudo().search([
                    ('company_ids', 'in', rec.product_request_id.company_id.id),
                    ('branch_ids', 'in', rec.product_request_id.ship_to.id),
                    ('start_date', '<=', rec.expected_date),
                    ('end_date', '>=', rec.expected_date),
                    ('status', 'in', ('active', 'renew')),
                    ('vendor', 'in', (rec.vendors.ids))
                ])
                if contract:
                    for contract_data in contract:

                        product_contract_line = self.env['product.contracts.line'].sudo().search(
                            [('product_id', '=', rec.product.id), ('products_line', '=', contract_data.id)])
                        if product_contract_line:
                            for data in product_contract_line:
                                rec.contract = contract_data.id
                else:
                    rec.contract = False

    def open_tnr(self):
        for rec in self:
            print("Open ",rec.contract)
            if rec.contract:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Contract',
                    'view_mode': 'form',
                    'res_model': 'product.tender.line',
                    'res_id': rec.contract.id,
                    'target': 'current'
                }

    @api.onchange('vendors')
    def restrict_second_vendor(self):
        if len(self.vendors) > 1:
            error_msg = "Enter a new line for a different vendor "
            self.vendors = self.vendors[:1]  # Keep only the first vendor

            raise ValidationError(error_msg)

    @api.depends('contract_status', 'product','vendors')
    def compute_contract_status(self):
        for rec in self:
            if rec.product and rec.vendors and rec.contract_status == 'in_contract':
                rec.contract_details = True
            else:
                rec.contract_details = False

    def open_contract(self):
        print("ggggg")

    def open_history(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.action_price_history')
        action['context'] = {'default_product': self.product.id,
                             }
        print(action)
        return action

    @api.constrains('expected_date')
    def _check_expected_date(self):
        for record in self:
            if record.expected_date and record.expected_date < fields.Date.today():
                raise ValidationError("Expected date cannot be set in the past.")

    # @api.constrains('from_date')
    # def _check_from_date(self):
    #     for record in self:
    #         if record.from_date and record.from_date < fields.Date.today():
    #             raise ValidationError("Contract Start date cannot be set in the past.")

    @api.constrains('to_date')
    def _check_to_date(self):
        for record in self:
            if record.to_date and record.to_date < fields.Date.today():
                raise ValidationError("Contract End date cannot be set in the past.")

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity == 0:
                raise ValidationError("Quantity should be greater than zero.")


    @api.depends('product','expected_date')
    def _compute_vendors_domain(self):
        #### Setting Domain for Vendor Field to show only vendors in contract or in price list ################
        for rec in self:
            vendors_domain = []
            vendor_ids = []
            if rec.product:
                product_contract_line = self.env['product.contracts.line'].sudo().search(
                    [('product_id', '=', rec.product.id)])
                # print(product_contract_line)
                if product_contract_line:
                    for contract_lines in product_contract_line:
                        product_contract = self.env['product.tender.line'].sudo().search(
                            [('id', '=', contract_lines.products_line.id), ('start_date', '<=',  rec.expected_date),
                             ('end_date', '>=',  rec.expected_date), ('status', 'in', ('active', 'renew')),
                             ('company_ids', 'in', rec.product_request_id.company_id.id),
                             ('branch_ids', 'in', rec.product_request_id.ship_to.id)
                             ])
                        for contract in product_contract:
                            if contract.vendor:
                                vendor_ids.append(contract.vendor.id)
                        unique_vendor_ids = list(set(vendor_ids))
                        if unique_vendor_ids:
                            vendors_domain = [('id', 'in', unique_vendor_ids)]
                        else:
                            product_vendors = self.env['res.partner'].sudo().search([])
                            vendor_list = product_vendors.mapped('id') if product_vendors else []
                            vendors_domain = [('id', 'in', vendor_list)]
                        rec.vendors_domain = json.dumps(vendors_domain)
                else:
                    vendors_domain = []
            else:
                vendors_domain = []

            rec.vendors_domain = json.dumps(vendors_domain)

    @api.onchange('expected_date')
    def change_in_expected_date(self):
        print("onchange",self)
        for rec in self:
            if rec.product.categ_id.name == "Lease/Rent":
                rec.is_lease = True

            product_contract_line = self.env['product.contracts.line'].sudo().search(
                [('product_id', '=', rec.product.id)])

            print("ON CONTRACT LI", product_contract_line)
            if product_contract_line:
                search_date = rec.expected_date or date.today()
                flag=0
                for contract_lines in product_contract_line:
                    print(contract_lines.id, "Expected contract",search_date)
                    product_contract = self.env['product.tender.line'].sudo().search(
                        [('id', '=', contract_lines.products_line.id),
                         ('start_date', '<=', search_date),
                         ('end_date', '>=', search_date),
                         ('status', 'in', ('active', 'renew')),
                         ('company_ids', 'in', self.product_request_id.company_id.id),
                         ('branch_ids', 'in', self.product_request_id.ship_to.id)
                         ])
                    if product_contract:
                        flag=1
                        break
                if flag ==1:
                    print("yess...expect")
                    rec.contract_status = 'in_contract'
                    rec.unit_price = 0
                    rec.vendors = False
                    self._compute_vendors_domain()
                else:
                    print("OOexpexct")
                    rec.contract_status = 'new'
                    rec.unit_price = 0
                    rec.vendors = False
                    
    @api.onchange('product')
    def onchange_in_product(self):
        for rec in self:
            current_date = datetime.today().date()
            if rec.product.categ_id.name == "Lease/Rent":
                rec.is_lease = True
            if not rec.expected_date:
                print("worked")
                rec.expected_date = current_date + timedelta(days=15)

            product_contract_line = self.env['product.contracts.line'].sudo().search(
                [('product_id', '=', rec.product.id)])
            print("ON CONTRACT LINEEEEEEEEEEEEEEEEEEE",product_contract_line)
            if product_contract_line:

                for contract_lines in product_contract_line:
                    print(contract_lines.id,"CONTRACTSSSSSSSSSSSS")
                    product_contract = self.env['product.tender.line'].sudo().search(
                        [('id', '=', contract_lines.products_line.id), ('start_date', '<=', self.expected_date),
                         ('end_date', '>=',  self.expected_date), ('status', 'in', ('active', 'renew')),
                         ('company_ids', 'in', self.product_request_id.company_id.id),
                         ('branch_ids', 'in', self.product_request_id.ship_to.id)
                         ])

                    
                    if product_contract:
                        print("yesSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
                        rec.contract_status = 'in_contract'
                        rec.vendors = False
                        
                        rec.uom = rec.product.uom_id
                        rec.oem = rec.product.oem
                        rec.brand = rec.product.brand
                        rec.unit_price = 0.0
                        
                        rec.consumption = 0
                        rec.stock = 0
                        # rec.expected_date = False
                        
                        return
                    else:
                        print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                        rec.vendors = False
                        rec.unit_price = 0.0
                        
                        rec.from_date = False
                        rec.to_date = False
                        rec.payment_terms = False
                        rec.contract_status = 'new'
                        # rec.expected_date = False
                            
            else:
                rec.contract_status = 'new'
                rec.vendors = False
                # rec.description = None
                rec.uom = rec.product.uom_id
                rec.oem = rec.product.oem
                rec.brand = rec.product.brand
                rec.unit_price = 0.0
                
                rec.consumption = 0
                rec.stock = 0
                # rec.expected_date = False

    def change_valuation(self):
        print('change_valuation', self.product_request_id.id)
        try:
            pr_approve_user = self.env['pr.approve.line'].sudo().search(
                [('product_request_id', '=', int(str(self.product_request_id.id).split('_')[1]))], )
            for item in pr_approve_user:
                print("unlink")
                item.unlink()
        except:
            print("Pass")
            pass


    @api.onchange('vendors','quantity','expected_date')
    def onchange_vendors_quantity(self):
        for rec in self:
            current_date = datetime.today().date()
            if rec.product and rec.vendors:
                contract = self.env['product.tender.line'].sudo().search([
                    ('company_ids','in',rec.product_request_id.company_id.id),
                    ('branch_ids','in',rec.product_request_id.ship_to.id),
                    ('start_date', '<=', rec.expected_date),
                    ('end_date', '>=', rec.expected_date),
                    ('status', 'in', ('active', 'renew')),
                    ('vendor','=',rec.vendors.ids[0])
                ])
                if contract:
                    for contract_data in contract:
                        # print(contract_data)
                        product_contract_line = self.env['product.contracts.line'].sudo().search(
                            [('product_id', '=', rec.product.id), ('products_line', '=', contract_data.id)])
                        for data in product_contract_line:
                            print(data.unit_price)
                            rec.unit_price = data.unit_price
                            rec.payment_terms = contract_data.payment_terms.id
                        if contract_data.lead_time:
                            rec.expected_date = current_date + timedelta(days=contract_data.lead_time)
                        elif not rec.expected_date:
                            rec.expected_date = current_date + timedelta(days=15)
                if not contract:
                    current_date = datetime.today().date()
                    # rec.expected_date = current_date + timedelta(days=15)

    @api.onchange('unit_price')

    def onchange_in_unit_price(self):
        self.unit_price = self.unit_price
        print("Inside unit price")
        if self._origin.unit_price != self.unit_price:
            # Log a message to the chatter using message_post or message_notify depending on the record type
            if self._name == 'product.request':
                # Use message_post for documents
                self.product_request_id.message_post(
                    body=f"Field 'Unit Price' changed from {self._origin.unit_price} to {self.unit_price}")
            else:
                # Use message_notify for non-document records
                self.product_request_id.message_notify(
                    subject="Field 'Unit Price' changed",
                    body=f"Field 'Unit Price' changed from {self._origin.unit_price} to {self.unit_price} in {self.product_request_id.name}",
                    partner_ids=[self.product_request_id.requested_by.partner_id.id]
                )

    @api.onchange('quantity')
    def onchange_in_quantity(self):
        self.quantity = self.quantity
        if self._origin.quantity != self.quantity:
            # Log a message to the chatter using message_post or message_notify depending on the record type
            if self._name == 'product.request':
                # Use message_post for documents
                self.product_request_id.message_post(
                    body=f"Field 'Quantity' changed from {self._origin.quantity} to {self.quantity}")
            else:
                # Use message_notify for non-document records
                self.product_request_id.message_notify(
                    subject="Field 'Quantity' changed",
                    body=f"Field 'Quantity' changed from {self._origin.quantity} to {self.quantity}",
                    partner_ids=[self.product_request_id.requested_by.partner_id.id]
                )




class PrApproveLine(models.Model):
    _name = "pr.approve.line"
    _description = "Approve Line"
    _order = 'approve_order asc'

    product_request_id = fields.Many2one('product.request', string='Product Request Id',
                                         invisible=True)

    user_id = fields.Many2one('res.users', string="User")
    company_id = fields.Many2one('res.company', string="Company")
    branch_id = fields.Many2one('res.branch', string="Branch")
    department_id = fields.Many2one('hr.department', string="Department")
    emp_name = fields.Many2one('hr.employee', string="Employee")
    designation = fields.Many2one('hr.job', string="Designation")
    approve_order = fields.Integer(string="Order")
    status = fields.Selection(
        selection=[('draft', 'Draft'), ('accept', 'Accept'), ('cancel', 'Cancel'), ('deligate', 'Delegated')],
        string='Status',
        default='draft',
        required=True, tracking=True
    )
    approve_date = fields.Date(string="Approval Date", readonly=True)

class CrNeedApproveLine(models.Model):
    _name = "cr.need.approve.line"
    _description = "Contract Request Need Approval Line"
    _order = 'approve_order asc'

    product_request_id = fields.Many2one('product.request', string='Product Request Id',
                                         invisible=True)

    user_id = fields.Many2one('res.users', string="User")
    company_id = fields.Many2one('res.company', string="Company")
    branch_id = fields.Many2one('res.branch', string="Branch")
    department_id = fields.Many2one('hr.department', string="Department")
    emp_name = fields.Many2one('hr.employee', string="Employee")
    designation = fields.Many2one('hr.job', string="Designation")
    approve_order = fields.Integer(string="Order")
    status = fields.Selection(
        selection=[('draft', 'Draft'), ('accept', 'Accept'), ('cancel', 'Cancel'), ('deligate', 'Deligated')],
        string='Status',
        default='draft',
        required=True, tracking=True
    )
    approve_date = fields.Date(string="Approval Date", readonly=True)



class LogMessage(models.TransientModel):
    _name = "log.message.wizard"
    _description = "Log"

    request_id = fields.Many2one(
        'product.request', string='Purchase Order', readonly=True)
    message = fields.Text("Message")
    user = fields.Many2one('res.users', "Requested By", default=lambda self: self.env.user.id , readonly= True)
    # user_ids = fields.Many2many('res.users', "To")
    to_users = fields.Many2many('res.users', 'log_message_res_users__pr_rel', 'log_message_id','res_users_id',"Requested_To", domain=lambda self: self._domain_to_users(), required=True)
    # user_from = fields.Many2many('res.users', "User_From", domain="[('groups_id', 'not in', [44])]", required=True)
    branch_id = fields.Many2many('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')
    email = fields.Char(string='Email', compute='_compute_email')
    cc_email = fields.Char(string='Email', compute='_compute_cc_email')
    user_cc = fields.Many2many('res.users', 'log_message_cc_pr_res_users_rel', 'log_message_id','res_users_id',"Cc", domain=lambda self: self._domain_user_cc())
    concatenated_branch_names = fields.Char(string="Branch Names", compute='_compute_branch_names')

    @api.model
    def _domain_to_users(self):
        return [('id', '!=', self.env.user.id), ('groups_id', 'not in', [44])]

    @api.model
    def _domain_user_cc(self):
        return [('id', '!=', self.env.user.id), ('groups_id', 'not in', [44])]

    @api.depends('to_users')
    def _compute_branch_id(self):
        for rec in self:
            if rec.to_users:
                rec.branch_id = rec.to_users.mapped('branch_id')
            else:
                rec.branch_id = [(5, 0, 0)]

    @api.depends('user_cc')
    def _compute_cc_email(self):
        for rec in self:
            if rec.user_cc:
                rec.cc_email = ', '.join(rec.user_cc.mapped('login'))
            else:
                rec.cc_email = False

    @api.depends('to_users')
    def _compute_email(self):
        for rec in self:
            if rec.to_users:
                rec.email = ', '.join(rec.to_users.mapped('login'))
            else:
                rec.email = False

    @api.depends('branch_id')
    def _compute_branch_names(self):
        for rec in self:
            if rec.branch_id:
                rec.concatenated_branch_names = ', '.join(rec.branch_id.mapped('name'))
            else:
                rec.concatenated_branch_names = ''


    def confirm(self):
        for rec in  self.request_id.pr_rfi_ids:
            if not rec.replay:
                raise UserError(_("Already Request for Information Pending for Reply"))

        print("helloo")
        model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)

        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.request_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_action_ids)

        for pending_action in pending_action_ids:
            #pending_action.status = 'closed'
            new_name = f"{self.request_id.name} Waiting for Request for Information Reply"
            pending_action.sudo().write({'name': new_name})
        for request in self.request_id:
            if self.user and self.message:
                body = (
                    f"{self.env.user.name} has logged a message in {self.request_id.name}.{self.message}"
                )
                base_url = self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Purchase Request')], limit=1) or False

                url_params = {
                    'id': self.request_id.id,
                    'action': self.env.ref(
                        'product_purchase.action_product_requests').id,
                    'model': 'product.request',
                    'view_type': 'form',
                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                    'menu_id': menu_id.id,
                }
                params = '/web?#%s' % url_encode(url_params)
                view_url = base_url + params if base_url else "#"
                print(view_url)

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)
                vals = {
                    'subject': f"Logged a message in {self.request_id.name}",
                    'body_html': body,
                    'email_to': ', '.join(self.to_users.mapped('login')),

                    'email_cc': self.cc_email,
                    'author_id': author.id
                }
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()
                
                # mail_id = self.env['mail.mail'].sudo().create(vals)
                # mail_id.sudo().send()

                subject = "Query was raised against Purchase Request : %s" % self.request_id.name

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A Purchase Request with the name <strong>{self.request_id.name} is Pending at Request For Information where you are "
                    f"a approver.<br>"

                )

                self.request_id.message_post(body=f"<strong>@{self.user.name}</strong>, {self.message}")

                if self.request_id.status == 'on_check' :
                    for user in self.request_id.cr_need_approve_line:
                        if self.env.user.id != user.id and user.status == 'accept':

                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.user_id.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    for user in self.to_users:
                        rfi_vals = {
                            'user_id': self.env.user.id,
                            'to_user': user.id,
                            'message': self.message,
                            'need_cr': True ,
                            # 'user_id':self.env.user.id,
                            'next_pending_ids': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False
                        }
                        new_rfi_vals = self.env['pr.rfi.line'].create(rfi_vals)
                        self.request_id.pr_rfi_ids |= new_rfi_vals

                        model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': "Request For Information" + " " + "on" + " " + self.request_id.name,
                            'record': self.request_id.id,
                            'branch': self.request_id.bill_to.id,
                            'date': date.today(),
                            'record_line': new_rfi_vals.id,
                            'department_id': self.request_id.department_id.id,
                            'exp_category': self.request_id.exp_category.id,
                            'Created_doc_date': self.request_id.requested_date,
                            'approve_users': [(6, 0, [user.id])],
                        }
                        pendings = self.env['pending.actions'].create(pending_vals)
                        print("the pending is", pendings)
                        approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                        pendings.write({'email': approve_users_emails})
                else:
                    for user in self.request_id.pr_approve_line.user_id:
                        if self.env.user.id == user.id:
                            pass
                        else:
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    for user in self.to_users:
                        rfi_vals = {
                            'user_id': self.env.user.id,
                            'to_user': user.id,
                            'message': self.message,
                            # 'user_id':self.env.user.id,
                            'next_pending_ids': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False
                        }

                        new_rfi_vals = self.env['pr.rfi.line'].create(rfi_vals)
                        self.request_id.pr_rfi_ids |= new_rfi_vals

                        model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': "Request For Information" + " " + "on" + " " + self.request_id.name,
                            'record': self.request_id.id,
                            'branch': self.request_id.bill_to.id,
                            'date': date.today(),
                            'department_id': self.request_id.department_id.id,
                            'exp_category': self.request_id.exp_category.id,
                            'Created_doc_date': self.request_id.requested_date,
                            'record_line': new_rfi_vals.id,
                            
                            'approve_users': [(6, 0, [user.id])],
                        }
                        pendings = self.env['pending.actions'].create(pending_vals)
                        print("the pending is", pendings)
                        approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                        pendings.write({'email': approve_users_emails})

                request.status = 'rfi'
        pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id),('name', 'not like', 'waiting for Request for Information reply')], order='id desc', limit=1)
        print("if,,,,,,,,,..pending actions", pending)
        if pending:
            print("if")
            return pending.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

            print("elseeeeeeeee", action)
            return action
class PrRfiLine(models.Model):
    _name = "pr.rfi.line"
    _description = "RFI Line"

    pr_id = fields.Many2one('product.request', string='Product Request Id',
                            invisible=True)

    user_id = fields.Many2one('res.users', string="From")
    to_user = fields.Many2one('res.users', string="To")
    message = fields.Char("Message")
    replay = fields.Char("Reply")
    replayed = fields.Boolean("Is Replayed")
    status = fields.Selection(
        selection=[('open', 'Open'), ('close', 'Closed')],
        string='Status',
        default='open',
        required=True, tracking=True
    )
    is_to_user_id = fields.Boolean(default=False, compute='_get_current_user_details')

    next_pending_ids = fields.Many2many(
        comodel_name='pending.actions',
        string='Pending Action',
        relation='last_pend',
        column1='pr_rfi_lease_id',
        column2='pending_actions_id',
        store=True
    )
    need_cr = fields.Boolean("IS CR")
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Attachments")
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')

    @api.depends('attachment_ids')
    def _compute_attachment_number(self):
     
        attachment_count = {}

        for request in self:
            domain = [('res_model', '=', 'pr.rfi.line'), ('res_id', '=', request.id)]
 
            attachment_data = self.env['ir.attachment'].read_group(domain, ['res_id'], ['res_id'])
    
            attachment_count[request.id] = attachment_data[0]['res_id_count'] if attachment_data else 0

    
        for request in self:
            request.attachment_number = attachment_count.get(request.id, 0)

    def open_attachments(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        # Retrieve the list of attachment IDs
        attachment_ids = self.attachment_ids.ids  # Get the IDs of the attachments
        print("the attachment id is", attachment_ids)
        res['domain'] = [('res_model', '=', 'pr.rfi.line'), ('res_id', '=', self.id)]
        res['context'] = {'default_res_model': 'pr.rfi.line', 'default_res_id': self.id}
        return res

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.to_user.name}"))
        return result

    @api.depends('to_user', 'replayed')
    def _get_current_user_details(self):
        current_user_id = self.env.user.id
        for record in self:
            if record.to_user.id == current_user_id and not record.replayed:
                record.is_to_user_id = True
            else:
                record.is_to_user_id = False
            print("The user is", record.is_to_user_id)


    def send_replay(self):
        unreplied_rfi_record = self.filtered(lambda r: not r.replayed and r.to_user.id == self.env.user.id)
        if unreplied_rfi_record:
            action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_replay_action')
            action['context'] = {'default_message_id': self.id, 'default_message': unreplied_rfi_record.message}
            return action


class LogMessageReplay(models.TransientModel):
    _name = "message.replay.wizard"
    _description = "Log"

    message_id = fields.Many2one(
        'pr.rfi.line', string='Replay', readonly=True)
    message = fields.Char(string="Message", readonly=True)
    replay = fields.Text("Reply", required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Attachments")

    def confirm(self):

        # pending_ids = self.env['pending.actions'].sudo().search([('id', '=', self.message_id.next_pending_ids.ids)])
        
        # for pending_action in pending_ids:
        #     # Create a copy of the pending action record
            
        #     new_action = pending_action.copy()
            
        #     new_action.sudo().write({
        #         'date':date.today(),
        #         'status': 'open',
        #         'name': "Replay for RFI" + " " + "for" + " " + self.message_id.pr_id.name,
        #     })
        model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record_line', '=', self.message_id.id), ('status', '=', 'open')],limit=1)
        print("the pending actions are", pending_action_ids)

        for rec in pending_action_ids:
            if self.env.user in rec.approve_users:
                print("record to close", rec)
                rec.status = 'closed'

        for line in self.message_id:
            line.replay = self.replay
            line.replayed = True
            line.status = 'close'
            if self.attachment_ids:
                new_attachments = self.attachment_ids
                print("the new ", new_attachments)
                for attachment in new_attachments:
                    attachment.write({'res_model': 'pr.rfi.line', 'res_id': line.id})

                line.attachment_ids = new_attachments
                attachment_ids_to_post = [attachment.id for attachment in self.attachment_ids]
                print("test post", attachment_ids_to_post)
            else:
                attachment_ids_to_post = []
            line.pr_id.message_post(
            body=f"<strong>@{self.env.user.name}</strong>,Replied: {self.replay}, to {self.message_id.user_id.name}",attachment_ids=attachment_ids_to_post)

        model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.message_id.pr_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_action_ids)


        all_record_lines_replayed = all(line.replay for line in self.message_id.pr_id.pr_rfi_ids)

        if all_record_lines_replayed:
            for pending_action in pending_action_ids:
                print("all are replayed")
                new_name = f"{self.message_id.pr_id.name} --Replied for Request for Information"
                pending_action.sudo().write({'name': new_name})
                pending_action.sudo().write({'date': fields.Datetime.now()})
            # If all record lines have their 'replay' column filled, change the status to 'requested'
            if self.message_id.need_cr == True :
                self.message_id.pr_id.status = 'on_check'
            else:
                self.message_id.pr_id.status = 'requested'
        pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id),('name', 'not like', 'waiting for Request for Information reply')], order='id desc', limit=1)
        print("if,,,,,,,,,..pending actions", pending)
        if pending:
            print("if")
            return pending.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

            print("elseeeeeeeee", action)
            return action



# class PrRfiLine(models.Model):
#     _name = "pr.rfi.line"
#     _description = "RFI Line"

#     pr_id = fields.Many2one('product.request', string='Product Request Id',
#                             invisible=True)

#     user_id = fields.Many2one('res.users', string="From")
#     to_user = fields.Many2one('res.users', string="To")
#     message = fields.Char("Message")
#     replay = fields.Char("Reply")
#     replayed = fields.Boolean("Is Replayed")
#     status = fields.Selection(
#         selection=[('open', 'Open'), ('close', 'Closed')],
#         string='Status',
#         default='open',
#         required=True, tracking=True
#     )
#     is_to_user_id = fields.Boolean(default=False, compute='_get_current_user_details')

#     next_pending_ids = fields.Many2many(
#         comodel_name='pending.actions',
#         string='Pending Action',
#         relation='last_pend',
#         column1='pr_rfi_lease_id',
#         column2='pending_actions_id',
#         store=True
#     )
#     need_cr = fields.Boolean("IS CR")

#     @api.depends('to_user')
#     def _get_current_user_details(self):
#         current_user_id = self.env.user.id
#         for record in self:
#             if record.to_user and record.to_user.id == current_user_id:
#                 record.is_to_user_id = True
#             else:
#                 record.is_to_user_id = False

#     def send_replay(self):
#         action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_replay_action')
#         action['context'] = {'default_message_id': self.id}
#         return action


# class LogMessageReplay(models.TransientModel):
#     _name = "message.replay.wizard"
#     _description = "Log"

#     message_id = fields.Many2one(
#         'pr.rfi.line', string='Replay', readonly=True)
#     replay = fields.Char("Message", required=True)

#     def confirm(self):

#         # pending_ids = self.env['pending.actions'].sudo().search([('id', '=', self.message_id.next_pending_ids.ids)])
        
#         # for pending_action in pending_ids:
#         #     # Create a copy of the pending action record
            
#         #     new_action = pending_action.copy()
            
#         #     new_action.sudo().write({
#         #         'date':date.today(),
#         #         'status': 'open',
#         #         'name': "Replay for RFI" + " " + "for" + " " + self.message_id.pr_id.name,
#         #     })
#         model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
#         pending_action_ids = self.env['pending.actions'].sudo().search(
#             [('model', '=', model.id), ('record', '=', self.message_id.pr_id.id), ('status', '=', 'open')])
#         print("the pending actions are", pending_action_ids)

#         for pending_action in pending_action_ids:
#             # pending_action.status = 'closed'
#             new_name = f"{self.message_id.pr_id.name} --Replayed for RFI "
#             pending_action.sudo().write({'name': new_name})


#         for line in self.message_id:
#             line.replay = self.replay
#             line.replayed = True
#             line.status = 'close'
#             self.message_id.pr_id.message_post(
#             body=f"<strong>@{self.env.user.name}</strong>,replayed: {self.replay}, to {self.message_id.user_id.name}")

#         model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
#         print(model.id)
#         print(self.message_id.id)
#         pending_action = self.env['pending.actions'].sudo().search(
#             [('model', '=', model.id), ('record_line', '=', self.message_id.id)], limit=1)

#         print(pending_action)
#         if pending_action:
#             pending_action.status = 'closed'
#         all_record_lines_replayed = all(line.replay for line in self.message_id.pr_id.pr_rfi_ids)

#         if all_record_lines_replayed:
#             # If all record lines have their 'replay' column filled, change the status to 'requested'
#             if self.message_id.need_cr == True :
#                 self.message_id.pr_id.status = 'on_check'
#             else:
#                 self.message_id.pr_id.status = 'requested'
#         pending = self.env['pending.actions'].sudo().search(
#                     [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
#         print("if,,,,,,,,,..pending actions", pending)
#         if pending:
#             print("if")
#             return pending.open_record()
#         else:
#             action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

#             print("elseeeeeeeee", action)
#             return action


        # activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
        # print("type is", self.env.user.id)
        # activity = self.env['mail.activity'].search([
        #     ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
        #     ('user_id', '=', self.env.user.id),('res_name', '=', self.name),
        #     ('activity_type_id', '=', activity_type.id),
        # ], limit=1)
        # if activity:
        #     print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
        #     print(activity.id)

        #     activity.action_feedback(feedback="Activity completed")




class ExpenseCategory(models.Model):
    _name = 'expense.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    exp_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')],string='Expense Type', tracking=True,required=True)
    name = fields.Char("Category Name", required=True , tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)
    reject_not_possible = fields.Boolean(string='Rejection Is Not Possible', default=False, tracking=True, store=True)



    def unlink(self):
        referenced_records = self.env['pr.company'].search([('exp_category', 'in', self.ids)])

        if referenced_records:
            referenced_records_names = ", ".join(referenced_records.mapped('name'))
            raise UserError(
                "Cannot delete records because they are referenced in other model(s): %s" % referenced_records_names)

        return super(ExpenseCategory, self).unlink()
        

class Remark(models.TransientModel):
    _name = "remark"
    _description = "Remark"
    _inherit = ['mail.thread']

    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Text("Remark", required=True)
    pr_id = fields.Many2one('product.request', string='Purchase Order', readonly=True)
    cr_need = fields.Boolean("CR Need",default= False)
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('reject', 'Rejected')],
        string='State',

    )
    def confirm_remark(self):


        if self.cr_need and self.pr_id and self.approve_type == 'approve':
            self.pr_id.message_post(body=f" {self.env.user.name} Approved.")
            self.pr_id.message_post(body="Remarks " + self.replay)
            vals = {
                'pr_id':self.pr_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Need for Request",
                'approve_type':'approve',

            }
            remarks_save = self.env['remark.save'].create(vals)
            self.pr_id.action_approval_cr_need()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action
        if self.cr_need and self.pr_id and self.approve_type == 'reject':
            self.pr_id.message_post(body=f" {self.env.user.name} Rejected.")
            self.pr_id.message_post(body="Remarks " + self.replay)
            vals = {
                'pr_id': self.pr_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Need for Request",
                'approve_type': 'reject',

            }
            remarks_save = self.env['remark.save'].create(vals)
            self.pr_id.action_decline()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action
        if self.pr_id and self.approve_type == 'approve' and not self.cr_need:
            self.pr_id.message_post(body=f" {self.env.user.name} Approved.")
            self.pr_id.message_post(body="Remarks " + self.replay)
            vals = {
                'pr_id': self.pr_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Purchase Request",
                'approve_type': 'approve',

            }
            remarks_save = self.env['remark.save'].create(vals)
            self.pr_id.action_approval()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action
        if self.pr_id and self.approve_type == 'reject' and not self.cr_need:
            self.pr_id.message_post(body=f" {self.env.user.name} Rejected.")
            self.pr_id.message_post(body="Remarks " + self.replay)
            vals = {
                'pr_id': self.pr_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Purchase Request",
                'approve_type': 'reject',

            }
            remarks_save = self.env['remark.save'].create(vals)
            self.pr_id.action_decline()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action



class RemarkSave(models.Model):
    _name = "remark.save"
    _description = "Remark"

    pr_id = fields.Many2one('product.request', string='Purchase Order', readonly=True)
    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Text("Remark", required=True)
    for_type = fields.Char("Approval Type")
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('reject', 'Rejected'), ('deligate', 'Delegate')],

        string='State')

class RevertBack(models.Model):
    _name = 'revert.back'
    _description = "Revert"

    pr_id = fields.Many2one(
        'product.request', string='Purchase Order', readonly=True)
    reason = fields.Text("Message")
    revert_from = fields.Many2one(
        'res.users', string='Revert User')