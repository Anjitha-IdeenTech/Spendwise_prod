from datetime import datetime, date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
# import datetime
import base64
import logging
import xlrd
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo.tools.safe_eval import json
import json
import re


_logger = logging.getLogger(__name__)


class Tenders(models.Model):
    _name = "tenders"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Contract Request"
    _order = 'id desc'

    current_date = datetime.now().date()

    name = fields.Char(string="TRN", readonly=True, required=True, copy=False, default='New')

    requested_by = fields.Many2one('res.partner', string="Requested By", store=True, force_save=True, tracking=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor", store=True, force_save=True)
    # total_price = fields.Float(string="Total Price",compute='compute_total_price')
    requested_date = fields.Date(string="Requested Date",default=lambda self: fields.Date.today())
    expected_date = fields.Date(string="Expected Date")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_ids = fields.Many2many('res.company', 'companies_tender_rel', 'tnd_id', 'comp_id',
                                   string="Allowed Companies")

    branch_ids = fields.Many2many('res.branch', 'branches_req_rel', 'contrct_req_id', 'branchs_id',
                                  string="Allowed Branches")

    branch_domain = fields.Char(
        compute="_compute_branch_domain",
        readonly=True,
        store=False,
    )

    # company_ids = fields.Many2many('res.partner', string="Requested To")
    product_requested_id = fields.Many2one('product.request', string="Product Requested ID")
    replacement_method = fields.Selection([
        ('replacement', 'Replacement'),
        ('new_req', 'New requirement at existing location'),
        ('add_upgrade', 'Capacity Addition or upgrade'),
        ('new_location', 'New Location')
    ], string='Purchase Type', tracking=True, related='product_requested_id.replacement_method'
    )

    replacement_reason = fields.Text(string="Why Replacement required", help="Describe the reason for replacement", related='product_requested_id.replacement_reason')
    need_of_oldAsset = fields.Text(string="What are we going to do with old asset", related='product_requested_id.need_of_oldAsset')
    oldAsset_capDate = fields.Date(string="Old asset Capitalisation date", related='product_requested_id.oldAsset_capDate')
    BookValue = fields.Float(string="Book Value", related='product_requested_id.BookValue', default='0.00')
    app_resale_value = fields.Float(string="Approx resale value", related='product_requested_id.app_resale_value')
    rep_photo_upload = fields.Binary("Attachment of existing item photos", related='product_requested_id.rep_photo_upload')
    select_budgeted = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Budgeted', tracking=True, related='product_requested_id.select_budgeted')

    justification = fields.Text(string="Business justification", related='product_requested_id.justification')
    annualBusiness_newAddition = fields.Float(string="Additional annual busines with new addition", related='product_requested_id.annualBusiness_newAddition')
    break_even_period = fields.Integer(string="Break Even Period", related='product_requested_id.break_even_period')

    curr_cap_utilization = fields.Float(string="What is the current capacity utilisation", related='product_requested_id.curr_cap_utilization')
    exp_monthly_revenue = fields.Float(string="Addional monthly revenue expected with additional capacity", related='product_requested_id.exp_monthly_revenue')
    location_detail = fields.Char(string="Location Details", related='product_requested_id.location_detail')

    renew_id = fields.Many2one('product.tender.line', string="Renewal")
    contract_id = fields.Many2one('contract', string='Vendor Response')
    vendor_request_status = fields.Selection([('draft', 'Draft'),
                                              ('accept', 'Accept'),
                                              ('reject', 'reject')], string='Contract Status of Vendor',
                                             default='draft')
    contract_status = fields.Selection([('draft', 'Draft'),
                                        ('accept', 'Accept'),
                                        ('cancel', 'Cancel')], string='Contract Status',
                                       default='draft', tracking=True)
    tender_response_qtn_check = fields.Boolean(string="Tender qtn Comp Check", default=False)
    from_date = fields.Date(string="Contract Start Date", tracking=True, default=current_date)
    to_date = fields.Date(string="Contract End Date", tarcking=True, track_visibility='onchange')
    tender_response_tender_check = fields.Boolean(string="Tender Res Comp Check", default=False)
    user_approve_check = fields.Boolean(string="User Approve check", compute="_compute_total", default=False)
    legal_approve_check = fields.Boolean(string="User Legal Approve check", compute="_compute_legal", default=False)
    approve_check = fields.Boolean(string="Approve Check", default=False)
    payment_terms = fields.Many2one('account.payment.term', "Payment Terms")
    lead_time = fields.Integer("Lead Time in days")

    user_id = fields.Many2one('res.users', string="Requested User", default=lambda self: self.env.user.id)
    vendor_details = fields.Text(string='Vendor Details', tracking=True)
    terms = fields.Text(string='Terms & Conditions', tracking=True)
    compared = fields.Boolean("Compared")
    is_to_user = fields.Boolean(compute='_compute_is_to_user', string='Is To User')

    legal_workflow = fields.Boolean("Legal Workflow", default=False)


    approve_users = fields.Many2many(
        'res.users',
        'tender_approve_users_rel',
        'request_id',
        'user_id',
        string='Approve Users',
        # default=lambda
        #     self: self.env.ref("product_purchase.group_initial_approval").users.ids
    )

    approved_users = fields.Many2many(
        'res.users',
        'tender_approved_users_rel',
        'request_id',
        'user_id',
        string='Approved Users',
    )

    next_approve_user_id = fields.Many2many('res.users', string="Next Approve User ID")

    tender_approve_line = fields.One2many('tender.approve.line',
                                          'tender_id',
                                          string='Tender Approve Line',
                                          tracking=True)
    legal_approve_line = fields.One2many('tender.legal.approve.line',
                                         'approve_tender_legal_id',
                                         string='Tender Legal Approve Line',
                                         tracking=True)

    legal_approve_users = fields.Many2many(
        'res.users',
        'rel_tender_legal_apprvers',
        'tender_id',
        'users',
        string='Legal Approve Users',
    )
    legal_approved_users = fields.Many2many(
        'res.users',
        'approved_legal_tender_relation',
        'tender_approved',
        'user_id',
        string='Legal Approved Users',
    )

    legal_next_approve_user = fields.Many2many(
        'res.users',
        'next_tender_legal_approved',
        'next_tender',
        'users_id',
        string='Legal Next Approver', )

    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('vendor_approval','Vendor Quotation Pending'),
                   ('vendor_approved', 'Vendor Quotation Submitted'),
                   ('vendor_rejected', 'Vendor Quotation Rejected'),
                   ('rfq','Multi-RFQ'),
                   ('deadline_reach','Deadline Reached'),
                   ('confirm', 'Shortlisted for approval'),
                   ('approve', 'Approved'),
                   ('legal_approve','Legal Approve'),
                   ('reject','Reject'),
                   ('cancel','Not Shortlisted'),
                   ('rfi','REQUEST FOR INFORMATION'),('terminate', 'Terminated')],
        string='Status',
        default='draft',
        required=True,tracking=True
    )

    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True,
                                    required=True)

    exp_category = fields.Many2one('expense.category', 'Expense Category', required=True)

    exp_category_domain = fields.Char(
        compute="_compute_exp_category_domain",
        readonly=True,
        store=False,
    )

    contracts_request_line = fields.One2many('contract.request.lines',
                                             'contracts_lines',
                                             string='Products Request Line',
                                             tracking=True)
    product_group = fields.Many2many('products.group', 'groups_contract_req_rel', 'contrcts_id', 'group_id',
                                     string="Product Group")

    contracting_method = fields.Selection([
        ('multi', 'Multi RFQ'),
        ('nego', 'Negotiation'),
        ('bidding', 'Bidding'),
    ], string='Contract Method',
        help="Select the method for contracting:\n"
             "- Multi RFQ: Multiple requests for contracts.\n"
             "- Negotiation: Direct negotiation with vendors.\n"
             "- Bidding: Calling for Tender."
    )

    total_price = fields.Float(string="Total Contract Value (excluding GST)", compute="compute_total_amount")
    total_vendor_price = fields.Float(string="Total Contract Value,(excluding GST)", compute="compute_total_vendor_amount")


    rfq_heads = fields.Many2many('tenders','multi_rfq_rel', 'rqst_id', 'rfq_id',
                                     string="Contracts")

    main_rfq = fields.Many2one('tenders','Request')

    vendor_ids = fields.Many2many(
        'res.partner',
        'requested_partners_rel',
        'c_request_id',
        'partner_id',
        string='Vendors',
    )
    multi_rfq_negotiation_no = fields.Integer(string="No of negotiation", default='0')
    vendor_selection = fields.Boolean(default=False)
    purchase_plan = fields.Selection([
        ('monthly', 'Monthly '),
        ('one_time', 'One Time'),('yearly','Yearly')
    ], string="Purchase Plan")
    department_id = fields.Many2one('hr.department', string="Department")
    deadline = fields.Datetime(string="Deadline ")
    deligated_user = fields.Many2one(
        'res.users', string='User Deligated', tracking=True, compute="_compute_user_id")
    pr_rfi_ids_cr = fields.One2many('pr.rfi.line.cr',
                                 'cr_id',
                                 string='Contract Request Line',
                                 tracking=True)
    file_upload = fields.Binary("Attachment")
    remarks_ids = fields.One2many('remark.save.cr',
                                  'cr_id',
                                  string='Remarks',
                                  tracking=True)
    main_remark = fields.Text(string="Remark")

    revert_reason = fields.One2many('revert.contract.back',
                                    'tender_id',
                                    string='Revert ReasonLine',
                                    tracking=True)
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    attachment_ids = fields.Many2many('ir.attachment', 'class_ir_attachments_vendor_rel', 'class_id', 'attachment_id',
                                      'Vendor Attachments')
    reference_doc = fields.Many2many('ir.attachment', 'class_ir_client_contract_rel', 'class_id', 'attachment_id',
                                     'Reference Doc for Vendor')
    name_sequence = fields.Integer(string="Name Sequence", default=1)
    name_array = fields.Text(string="Name Array", default="[]")
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)
    assigned = fields.Boolean(string='Assign', default=False)
    assigned_to = fields.Many2many(
        'res.users',
        'assigned_user_rel',
        'tender_id',
        'user_id', 
        string='Buyer'
    )
    purchase_head = fields.Many2one('res.users', string='Purchase Head')
    is_purchase_head = fields.Boolean(string='Is Purchase Head',compute='_compute_purchase_head')
    attachment_vendor_ids = fields.Many2many('ir.attachment', 'class_ir_attachments_tender_rel', 'class_id', 'attachment_id',
                                      'Attachments')
    user_in_vendor_group = fields.Boolean(compute='_compute_user_in_vendor_group')


    price_history_ids = fields.One2many('contract.price.history', 'contract_id', string="Price History")

    negotiation_true = fields.Boolean(string='negotiation true')
    description = fields.Html(string="Attachments")

    vendor_addresss = fields.Html(string="Vendor Address", store=True)
    vendor_change_name = fields.Text(string="Vendor Name", store=True)

    is_visible_create_contract_button = fields.Boolean(
        string="Visible Create Contract Button",
        compute="_compute_is_visible_create_contract_button"
    )

    total_percentage_difference = fields.Float(
        string="Total Percentage Difference",
        compute="_compute_total_percentage_difference",
        store=True
    )

    recuring_payment = fields.Boolean(string="Recurring Payment",default=False)

    termination_date = fields.Date(string="Termination date")

    @api.onchange('recuring_payment')
    def _onchange_recuring_payment(self):
            return {
                'warning': {
                    'title': "Confirmation",
                    'message': "You have changed the Recurring Payment field. Please confirm in the form to proceed.",
                }
            }



    def generate_contract_po(self):
        current_date = datetime.now().date()
        batch_size = 50  # Process contracts in batches to avoid congestion

        # Fetch all eligible contracts in one query
        contracts = self.env['tenders'].sudo().search([
            ('recuring_payment', '=', True),
            ('state', '=', 'approve'),
            ('from_date', '<=', current_date),
            ('to_date', '>=', current_date),
            ('purchase_plan', '=', 'monthly')
        ])
        print(f"Total contracts to process: {len(contracts)}")

        # Process contracts in batches
        for batch_start in range(0, len(contracts), batch_size):
            batch_contracts = contracts[batch_start:batch_start + batch_size]
            for con in batch_contracts:
                rate_con = self.env['product.tender.line'].sudo().search([
                    ('request_no', '=', con.id),
                ])
                print(f"Processing contract: {con.id}, Rate Contract: {rate_con.ids}")

                for branch in con.branch_ids:
                    for company in con.company_ids:
                        order_lines = []

                        for line in con.contracts_request_line:
                            product = self.env['product.product'].sudo().search(
                                [('product_tmpl_id', '=', line.product_id.id)], limit=1
                            )

                            existing_po_line = self.env['purchase.order.line'].sudo().search([
                                ('order_id.bill_to', '=', branch.id),
                                ('order_id.ct_number', 'in', rate_con.ids),
                                ('product_id', '=', product.id),
                            ])

                            order_lines.append((0, 0, {
                                'product_id': product.id,
                                'product_qty': line.quantity,
                                'price_unit': line.unit_price,
                            }))

                        total_existing_taxed = sum(
                            pos.order_id.amount_total for pos in existing_po_line
                        )
                        print(
                            f"Branch {branch.name}, Existing Total: {total_existing_taxed}, Contract Total: {con.total_price}")

                        if total_existing_taxed >= con.total_price:
                            print(f"Skipping branch {branch.name} as quantities match.")
                            continue

                        if order_lines:
                            po_vals = {
                                'partner_id': con.vendor_id.id,
                                'date_order': current_date,
                                'ct_number': [(6, 0, rate_con.ids)],
                                'bill_to': branch.id,
                                'ship_to': branch.id,
                                'company_id': company.id,
                                'is_auto_po': True,
                                'exp_category': con.exp_category.id,
                                'order_line': order_lines,
                                'expense_type': con.expense_type,
                                'department_id': con.department_id.id,
                                'branch_id':  branch.id,
                            }

                            try:
                                new_po = self.env['purchase.order'].sudo().create(po_vals)
                                self.env.cr.commit()  # Commit after successful PO creation
                                print(f"New Purchase Order Created: {new_po.name}")
                            except Exception as e:
                                print(f"Error creating Purchase Order: {str(e)}")
                                self.env.cr.rollback()  # Rollback to maintain consistency
                                continue

                            # Assign purchase head
                            users_line = self.env['res.users.line'].sudo().search([
                                ('department_id.name', '=', 'SCM'),
                                ('designation', '=', 'Purchase Head')
                            ], limit=1)

                            if users_line:
                                new_po.purchase_head = users_line.res_user_id.id
                                print(f"Assigned Purchase Head: {users_line.res_user_id.name}")

                                # Create pending action
                                model = self.env['ir.model'].sudo().search([
                                    ('model', '=', 'purchase.order')
                                ], limit=1)

                                for rc in rate_con:  # Iterate to handle multiple records
                                    pending_vals = {
                                        'model': model.id,
                                        'name': f"{rc.name} - Assign The User To The Purchase Order",
                                        'record': new_po.id,
                                        'date': date.today(),
                                        'branch': new_po.bill_to.id,
                                        'department_id': new_po.department_id.id,
                                        'exp_category': new_po.exp_category.id,
                                        'Created_doc_date': new_po.date_order,
                                        'approve_users': [(6, 0, [users_line.res_user_id.id])]
                                    }

                                    self.env['pending.actions'].sudo().create(pending_vals)
                                    self.env.cr.commit()  # Commit after pending action creation
                                    print("Pending Action Created:", pending_vals)

                con.message_post(body=f"{self.env.user.name} generated a Purchase Order.")

    def purchase_plan_assign(self):
        current_date = datetime.now().date()
        contracts = self.env['tenders'].sudo().search([
            ('state', '=', 'approve'),
            ('from_date', '<=', current_date),
            ('to_date', '>=', current_date),
            ('purchase_plan', '=', 'monthly')
        ])
        for contract in contracts:
            contract.sudo().write({'recuring_payment': True})

    # def purchase_plan_assign(self):
    #     current_date = datetime.now().date()
    #     contracts = self.env['tenders'].sudo().search([
    #         ('from_date', '<=', current_date),
    #         ('recuring_payment', '=', True),
    #     ])
    #     for contract in contracts:
    #         contract.sudo().write({'recuring_payment': False})

    @api.depends('contracts_request_line.unit_price')
    def _compute_total_percentage_difference(self):
        for record in self:
            filtered_lines = [line for line in record.contracts_request_line if line.pr_rate != 0]
            total_unit_price = sum(line.unit_price * line.quantity for line in filtered_lines)
            total_previous_rate = sum(line.pr_rate * line.quantity for line in filtered_lines)
            if total_previous_rate == 0:
                total_difference = 0 
            else:
                total_difference = ((total_unit_price - total_previous_rate) / total_previous_rate) * 100
            record.total_percentage_difference = total_difference

    @api.depends('exp_category')
    def _compute_is_visible_create_contract_button(self):
        for record in self:
            if record.exp_category and record.exp_category.name in ['Maruti Insurance (MI)', 'Non-Maruti Insurance (Non-MI)']:
                record.is_visible_create_contract_button = True
            else:
                record.is_visible_create_contract_button = False

    def action_call_create_contract_req(self):
        for line in self.contracts_request_line:
            line.action_create_contract_req()

    def generate_monthly_po(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Branches',
            'res_model': 'po.branch.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_branch_ids': self.branch_ids.ids,  # Pre-select branches if needed
                'default_tender_id': self.id,  # Pass the current record's ID
            },
        }


    @api.onchange('company_ids')
    def _check_single_company(self):
        for record in self:
            if len(record.company_ids) > 1:
                raise ValidationError("You cannot add more than one company to the Allowed Companies field.")



    @api.onchange('vendor_id')
    def _onchange_partner_id(self):
        """Fetch and update the full vendor's address when the vendor changes."""
        for record in self:
            if record.vendor_id:
                # Construct the full address
                record.vendor_change_name = record.vendor_id.name or ""
                address_lines = "<br/>".join(filter(None, [
                    f"(Partner Code: {record.vendor_id.ref or ''})",
                    f"GST No: {record.vendor_id.vat or ''}",
                    f"{record.vendor_id.street or ''}, {record.vendor_id.street2 or ''}",
                    f"{record.vendor_id.city or ''}, {record.vendor_id.state_id.name or ''}, {record.vendor_id.country_id.name or ''}" 
                    f"Pin: {record.vendor_id.zip or ''}".strip(", "),
                    f"Phone: {record.vendor_id.phone or ''}",
                    f"Email: {record.vendor_id.email or ''}"
                ]))
                record.vendor_addresss = address_lines
            else:
                record.vendor_addresss = False

    @api.depends('user_id')
    def _compute_user_in_vendor_group(self):
        vendor_group = self.env.ref('vendor_portal.group_vendor_portal_user')
        for record in self:
            print("for the checking purpose",record.user_id.name)
            record.user_in_vendor_group = vendor_group in self.env.user.groups_id

    @api.depends("is_purchase_head")
    def _compute_purchase_head(self):
        print('Inside Purchase head')
        for rec in self:
            if rec.purchase_head:
                if self.env.user.id == rec.purchase_head.id:
                    rec.is_purchase_head = True
                else:
                    rec.is_purchase_head = False
            else:
                rec.is_purchase_head = False
            print("purchse",rec.is_purchase_head)
    def assign_buyer(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.view_assign_buyer_action')
        action['context'] = {'default_current_cr': self.id
                             }
        print(action)
        return action

    @api.depends('pr_rfi_ids_cr')
    def _compute_is_to_user(self):
        current_user_id = self.env.user.id
        for record in self:
            record.is_to_user = any(not rfi.replayed and rfi.to_user.id == current_user_id for rfi in record.pr_rfi_ids_cr)
            print("the user is", record.is_to_user)

    def send_replay(self):
        print("i am in replay")
        unreplied_rfi_record = self.pr_rfi_ids_cr.filtered(lambda r: not r.replayed and r.to_user.id == self.env.user.id)
        print("the rfi record", unreplied_rfi_record)
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_replay_cr_action')
        action['context'] = {'default_message_id': unreplied_rfi_record.id,
                             'default_message': unreplied_rfi_record.message}
        return action

    def deadline_extension(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.view_deadline_extend_action')
        action['context'] = {'default_contract': self.id
                             }
        print(action)
        return action
    
    def action_reject(self):
        self.ensure_one()
        if self.exp_category and self.exp_category.reject_not_possible:
            raise ValidationError(
                "Rejection is not possible for this Contract as the linked expense category does not allow rejection."
            )
        print("i am in cancel")
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ctr_id': self.id},
        }


    def _compute_attachment_number(self):
        domain = [('res_model', '=', 'tenders'), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment'].read_group(domain, ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for request in self:
            request.attachment_number = attachment.get(request.id, 0)

    def action_open_attachments_contract(self):
        print("kkkkkkkk")
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'tenders'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'tenders', 'default_res_id': self.id}
        return res
    def action_remark_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_approve_action_cr')
        action['context'] = {'default_cr_id': self.id,
                             'default_approve_type':'approve',
                             'default_work_flow_type': 'tender',
                             }
        print(action)
        return action
    def action_remark_legal_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_approve_action_cr')
        action['context'] = {'default_cr_id': self.id,
                             'default_approve_type':'approve',
                             'default_work_flow_type': 'legal',
                             }
        print(action)
        return action
    def action_remark_reject(self):
        self.ensure_one()
        if self.exp_category and self.exp_category.reject_not_possible:
            raise ValidationError(
                "Rejection is not possible for this Contract as the linked expense category does not allow rejection."
            )
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_approve_action_cr')
        action['context'] = {'default_cr_id': self.id,
                             'default_approve_type':'reject',
                             'default_work_flow_type': 'tender',
                             }
        print(action)
        return action

    def action_withdraw_rfq(self):
        for rec in self:
            print("wid",rec.name)
            if rec.state in ('confirm', 'cancel') and rec.main_rfq:
                flag = 0
                print("wid", rec.name)
                for line in rec.tender_approve_line:
                    if line.status != 'draft':
                        flag = 1
                        break
                if flag == 0:
                    rec.state = 'rfq'
                    rec.tender_approve_line.unlink()
                    rec.write({'approve_users': [(5, 0, 0)]})
                    rec.write({'approved_users': [(5, 0, 0)]})
                    rec.write({'next_approve_user_id': [(5, 0, 0)]})
                    print("approvers,approved,next", rec.approve_users, rec.approved_users, rec.next_approve_user_id)

                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')], limit=1)
                    activity = self.env['mail.activity'].search([
                        ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                        ('res_name', '=', rec.name),
                        ('activity_type_id', '=', activity_type.id),
                    ])
                    if activity:
                        for reco in activity:
                            reco.action_feedback(feedback="Contract request Withdraw")

                    model = self.env['ir.model'].sudo().search([('model', '=', rec._name)], limit=1)
                    pending_action = self.env['pending.actions'].sudo().search(
                        [('model', '=', model.id), ('record', '=', rec.id), ('status', '=', 'open')])

                    if pending_action:
                        print(pending_action.name)
                        pending_action.status = 'closed'

                else:
                    raise ValidationError(_("Approvers states are not on draft"))

    def action_withdraw(self):
        if self.state == 'confirm'  and not self.main_rfq:
            flag = 0
            for line in self.tender_approve_line:
                if line.status != 'draft':
                    flag = 1
                    break
            if flag == 0:
                self.state = 'draft'
                self.tender_approve_line.unlink()
                self.write({'approve_users': [(5, 0, 0)]})
                self.write({'approved_users': [(5, 0, 0)]})
                self.write({'next_approve_user_id': [(5, 0, 0)]})
                print("approvers,approved,next",self.approve_users,self.approved_users,self.next_approve_user_id)

                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id), ('res_name', '=', self.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        
                        rec.action_feedback(feedback="Contract request Withdraw")
                        
                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

                if pending_action:
                    for rec in pending_action:
                        
                        rec.status = 'closed'

            else:
                raise ValidationError(_("Approvers states are not on draft"))
    def action_add_approver_admin(self):
        user_ids = [user.id for user in self.next_approve_user_id]
        if not user_ids:
            return
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')
        action['context'] = {'default_cr_id': self.id,
                             'default_admin_add': True

                             }
        print(action)
        return action
    def action_add_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')
        action['context'] = {'default_cr_id': self.id,

                             }
        print(action)
        return action
    def action_add_new_branch(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Branches',
            'res_model': 'add.branch.wizard',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {
            #     'default_company_ids': self.company_ids.ids,
            # },
        }
    def _compute_user_id(self):
        for rec in self:
            rec.deligated_user = self.env.user.id

    def action_cr_deligate(self):
        print("deligate")
        for lines in self.tender_approve_line:
            if lines.user_id.id == self.env.user.id:
                print("Founddd User")
                action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_cr_deligate_user_action')
                action['context'] = {'default_cr_id': self.id}
                return action

    def action_delegate_admin_cr(self):
        print("i am in delegate")

        # user_ids = [user.id for user in self.next_approve_user_id]
        approve_users = set(self.approve_users.ids)  # Fetch IDs of approve_users
        approved_users = set(self.approved_users.ids)  # Fetch IDs of approved_users

        user_ids = list(approve_users - approved_users)
        print("the user id",user_ids)

        if not user_ids:
            return

        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_admin_action')
        action['context'] = {
            'default_request_contract_id': self.id,
            'user_ids': user_ids,
            'type_id' : 'tn'
        }

        return action

    def action_revert(self):
        print("the self", self.user_id.id)
        print("hi")
        return {
            'name': 'Roll back to initiator',
            'view_mode': 'form',
            'view_id': self.env.ref('product_purchase.view_revert_back_tender_form').id,
            'view_type': 'form',
            'res_model': 'revert.back.tender.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_revert_from': self.env.user.id,
                'default_tender_id': self.id,
                'default_initiator': self.user_id.id,
            },
        }

    @api.model
    def update_status(self):
        for record in self:
            if record.deadline <= fields.Datetime.now() and  record.state == 'vendor_approval':
                record.state = 'deadline_reach'
                record.contract_id.state = 'expire'

    def action_log_message_cr(self):
        default_user_ids = self.approve_users.ids
        print(default_user_ids, "Usersssss")
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_message_cr_action')
        action['context'] = {'default_tenders_id': self.id,
                             }
        print(action)
        return action

    def action_make_initiator(self):
        # user_group = self.env.ref('product_purchase.group_pr_initiator')
        # approver_group = self.env.ref('product_purchase.group_approvers')
        # existing_users = self.env['res.users'].sudo().search([], offset=320, limit=100)
        # users_to_add = [(4, user.id) for user in existing_users]
        # if users_to_add:
        #     user_group.write({'users': users_to_add})
        #     approver_group.write({'users': users_to_add})

        # existing_user = self.env['res.users'].sudo().search([])
        # for users in existing_user:
        #     if users.partner_id:
        #         users.partner_id.email = users.login
        #     else:
        #         pass
        approver_group = self.env.ref('product_purchase.group_approvers')
        user_group = self.env.ref('product_purchase.group_pr_initiator')
        # approver_group = self.env.ref('product_purchase.group_approvers')
        existing_users = self.env['res.users'].sudo().search([])
        existing_users_count = self.env['res.users'].sudo().search_count([])
        print("Count of users ",existing_users_count)
        for offset in range(0, existing_users_count, 10):
            existing_users_batch = self.env['res.users'].sudo().search([], offset=offset, limit=10)

            # Assign users to groups
            user_ids = existing_users_batch.ids
            user_group.write({'users': [(4, user_id) for user_id in user_ids]})
            approver_group.write({'users': [(4, user_id) for user_id in user_ids]})

            print("Processed {} users".format(len(existing_users_batch)))

    def action_vendor_selection(self):

        if self.product_requested_id:
            for rec in self.product_requested_id.product_request_line_ids:
                if not (rec.expected_date >= self.from_date and rec.expected_date <= self.to_date):
                    raise ValidationError(
                        _("Contract Period Do Not Match the Need by Date of PR: Expected Date {}").format(
                            rec.expected_date)
                    )
        if self.to_date == False and self.payment_terms == False:
            raise ValidationError(_("Required cannot be empty on Vendor Selection and Contact Request Creation"))
        for line in self.contracts_request_line:
            if line.suggested_unit_price == False:
                raise ValidationError(_("Suggested Unit Price cannot be Empty"))
        return {
            'name': 'Vendor Selection',
            'view_mode': 'form',
            'view_id': self.env.ref('product_purchase.view_product_category_wizard_form').id,
            'view_type': 'form',
            'res_model': 'product.category.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                # 'default_template_id': self.env.ref('School.student_invoice_template').id,
                'default_current_cr': self.id,

            },
        }
    def action_rfq_negotiation(self):
        if self.deadline < datetime.today():
            raise UserError(_("Change the Deadline first"))
        self.contract_id.state = 'negotiation'
        self.multi_rfq_negotiation_no += 1
        nego_no = str(self.multi_rfq_negotiation_no)
        self.message_post(
            body="Negotiation Number %s " % nego_no,
            message_type='notification',
        )
        self.state = 'vendor_approval'
        self.negotiation_true = True

        subject = "Negotiation Request for %s requested by: %s" % (self.contract_id.name, self.user_id.name)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'My Contract Requests')], limit=1) or False

        url_params = {
            'id': self.contract_id.id,
            'action': self.env.ref('product_purchase.action_contract_requests').id,
            'model': 'contract',
            'view_type': 'form',
            'menu_id': menu_id.id if menu_id else False,
        }

        params = '/web?#%s' % url_encode(url_params)
        url = base_url + params if base_url else "#"

        print(url)
        author = self.env['res.partner'].sudo().search(
            [('name', '=', 'Administrator')], limit=1)
        # Create a draft email using the rendered body
        body = (
            f"Dear {self.vendor_id.name}, "
            f"A new Negotiation Request for Contract Request name <strong>{self.contract_id.name} is waiting for Approval.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.vendor_id.email,
            'auto_delete': False,
            'author_id': author.id
        }
        mail_record = self.env['mail.mail'].sudo().create(mail_values)

    def action_send_multi_rfq_tree(self):
        msg =0
        for rec in self:
            if rec.state == 'rfq':
                rec.action_send_multi_rfq()
            else:
                msg = "CTR are present not in state MULTI-RFQ"
        if msg:
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

    def action_send_multi_rfq(self):
        if self.product_requested_id:
            for rec in self.product_requested_id.product_request_line_ids:
                if not (rec.expected_date >= self.from_date and rec.expected_date <=  self.to_date):
                    raise ValidationError(_("Contract Period Do Not Match the Need by Date of PR"))

        for lines in self.contracts_request_line:
            if not lines.quantity:
                raise ValidationError(_("The quantity cannot be zero. Please specify a valid quantity before proceeding."))
        record = self.env["res.users"].sudo().search([('name', '=', self.vendor_id.name)],limit=1)
        print(record)
        if not self.main_rfq:
            self.main_rfq = self.id
            print(self.main_rfq)
        if record:
            print("workkkkk")
            print(record, "user id",record,id)
        else:
            print("Error")
            raise ValidationError(_("%s has no login") % self.vendor_id.name)
        vendor_vals = {
            'tender_id': self.id,
            'main_remark': self.main_remark,
            'reference_doc':[(6, 0, self.reference_doc.ids)],
            'vendor_id': self.vendor_id.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'expense_type': self.expense_type,
            'lead_time': self.lead_time,
            'payment_terms': self.payment_terms.id,
            'purchase_plan': self.purchase_plan,
            'deadline': self.deadline,
            'requested_date': self.requested_date,
            'user_id': record.id,
            'company_ids': [(6, 0, self.company_ids.ids)],
            'branch_ids': [(6, 0, self.branch_ids.ids)],
            'terms': self.terms,
            # 'rfq_heads': [(6, 0, new_rfq_heads)],
            'main_rfq': self.main_rfq.id,
            'state': 'pending',
            'product_requested_id': self.product_requested_id.id,
            'requested':self.user_id.id,
        }
        print(vendor_vals)
        vendor_request = self.env['contract'].sudo().create(vendor_vals)
        print(vendor_request)
        self.contract_id = vendor_request.id
        vendor_request_lines_vals = []
        for lines in self.contracts_request_line:
            line_val = {
                'tender_line_id':lines.id,
                'vendor_lines': vendor_request.id,
                'product_id': lines.product_id.id,
                'quantity': lines.quantity,
                'unit_price': lines.unit_price,
                'product_group': lines.product_group,
            }
            vendor_request_lines_vals.append(line_val)
        self.env['vendor.contract.lines'].sudo().create(vendor_request_lines_vals)
        self.state = 'vendor_approval'


        # Reference the existing email template by its XML ID
        subject = "Contract Request Generated For APPROVAL: %s" % self.contract_id.name
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'My Contract Requests')], limit=1) or False

        url_params = {
            'id': vendor_request.id,
            'action': self.env.ref('product_purchase.action_contract_requests').id,
            'model': 'contract',
            'view_type': 'form',
            'menu_id': menu_id.id if menu_id else False,
        }

        params = '/web?#%s' % url_encode(url_params)
        url = base_url + params if base_url else "#"

        print(url)
        author = self.env['res.partner'].sudo().search(
            [('name', '=', 'Administrator')], limit=1)
        # Create a draft email using the rendered body
        body = (
            f"Dear {self.vendor_id.name}, "
            f"A new Contract Request with the name <strong>{self.contract_id.name} is waiting for Approval.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.vendor_id.email,
            'auto_delete': False,
            'author_id': author.id
        }
        mail_record = self.env['mail.mail'].sudo().create(mail_values)

    def action_compare(self):
        # for tender in self:
        #     if tender.state not in ('vendor_approved','approve','confirm','cancel'):
        #         raise ValidationError(_("Only vendor approved,review,confirmed can be compared"))
        id_list = []
        for rec in self:
            print(rec,rec.name)
            for price in rec.contracts_request_line:
                if price.vendor_price != 0:
                    print("added record",rec.total_vendor_price,rec.name)
                    id_list.append(rec.id)
                    break
        print(id_list)
        tender_record = self.env['tenders'].sudo().search([('id', 'in', id_list)])
        print("tender_rec",tender_record)
        line_id_list = []
        for rec in tender_record:
            for r in rec.contracts_request_line:
                line_id_list.append((r.id))
        print("line ids",line_id_list)


        records = self.env['contract.request.lines'].search([('id', 'in', line_id_list)])
        print("records",records)
        for i in records:
            ids = self.env['contract.request.lines'].search([('id', 'in', line_id_list),('product_id', '=', i.product_id.id)])
            print("Same product",ids)
            smallest_price = float('inf')  # Initialize with positive infinity
            second_smallest_price = float('inf')
            for record in ids:
                print("same",record)
                if record.vendor_price < smallest_price:
                    second_smallest_price = smallest_price
                    smallest_price = record.vendor_price
                    print(smallest_price)
                elif record.vendor_price < second_smallest_price and record.vendor_price != smallest_price:
                    second_smallest_price = record.vendor_price
            for record in ids:
                # record.smallest = smallest_price
                # record.second_smallest = second_smallest_price
                print(smallest_price)

        return {
            'name': _('Comparison'),
            'view_mode': 'tree',
            'res_model': 'contract.request.lines',
            'type': 'ir.actions.act_window',
            'context': {
                'group_by': 'vendor',
                },
            'domain': [('contracts_lines', 'in', id_list)],
            'target': 'current',
        }
    def action_view_multi_rfq(self):
        print("selfffffff")
        if self.main_rfq.id:
            branch = self.env['tenders'].sudo().search([
                ('main_rfq', '=', self.main_rfq.id),
            ])
            print("Multi RFQS",branch)
            if branch:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Multi RFQ-(Contract Requests)',
                    'view_mode': 'tree,form',
                    'res_model': 'tenders',
                    'domain': [('main_rfq', '=', self.main_rfq.id)],
                    'target': 'current'
                }

    def action_view_bidding_prices(self):
        if self.main_rfq:
            branch = self.env['bidding'].sudo().search([
                ('contract.main_rfq', '=', self.main_rfq.id),
            ])
            print("Multi RFQS", branch)
            if branch:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Multi RFQ-(Bidding Requests)',
                    'view_mode': 'tree,form',
                    'res_model': 'bidding',
                    'domain': [('contract.main_rfq', '=', self.main_rfq.id)], 
                    'target': 'current'
                }
            else:
                return None

    @api.onchange('contracts_request_line','purchase_plan','to_date')
    def compute_total_amount(self):
        for record in self:
            total_amount = 0
            if record.purchase_plan == 'monthly':
                months = 1
                if record.from_date and record.to_date:
                    from_date = datetime.strptime(str(record.from_date), '%Y-%m-%d')
                    to_date = datetime.strptime(str(record.to_date), '%Y-%m-%d')
                    months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)

                for line in record.contracts_request_line:
                    total_amount += line.unit_price * line.quantity * months
            else:
                for line in record.contracts_request_line:
                    total_amount += line.quantity * line.unit_price

            record.total_price = total_amount

    @api.depends('contracts_request_line')
    def compute_total_vendor_amount(self):
        for record in self:
            total_vendor_amount = 0
            if record.purchase_plan == 'monthly':
                months = 1
                if record.from_date and record.to_date:
                    from_date = datetime.strptime(str(record.from_date), '%Y-%m-%d')
                    to_date = datetime.strptime(str(record.to_date), '%Y-%m-%d')
                    months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)

                for line in record.contracts_request_line:
                    total_vendor_amount += line.vendor_price * line.quantity * months

            else:
                for line in record.contracts_request_line:
                    total_vendor_amount += line.quantity * line.vendor_price

            record.total_vendor_price = total_vendor_amount
    def action_create_multi_rfq(self):
        print("ggggggggggggggggg")
        if self.product_requested_id:
            for rec in self.product_requested_id.product_request_line_ids:
                if not (rec.expected_date >= self.from_date and rec.expected_date <=  self.to_date):
                    raise ValidationError(
                        _("Contract Period Do Not Match the Need by Date of PR: Expected Date {}").format(
                            rec.expected_date)
                    )
        if self.contract_id:
            if self.contract_id.state == 'pending':
                self.state = 'vendor_approval'
            elif self.contract_id.state == 'accept':
                self.state = 'vendor_approved'
            else:
                self.state = 'vendor_rejected'
        else:
            self.state = 'rfq'
        if not self.main_rfq:
            self.main_rfq = self.id
            name = self.main_rfq.name
            self.name = f"{name}-A"

        existing_rfq_heads = self.rfq_heads.ids

        new_rfq_heads = existing_rfq_heads + [self.id]

        base_name = self.main_rfq.name.split('-')[0]

        related_contracts = self.env['tenders'].search([('name','like',base_name)])
        max_seq = 0

        for contract in related_contracts:
            match = re.search(rf"{base_name }-([A-Z])$", contract.name)
            if match:
                seq_letter = match.group(1)
                seq_number = ord(seq_letter) - ord('A')
                if seq_number > max_seq:
                    max_seq = seq_number
    
        # base_name = self.main_rfq.name
        self.name_array = []

        self.name_sequence = max_seq+1
        new_name = f"{base_name}-{chr(65 + self.name_sequence)}"
     
        if isinstance(self.name_array, list):
            self.name_array.append(new_name)
            self.name_array = json.dumps(self.name_array)
        else:
            print("Name array is not a list. It is of type:", type(self.name_array))

        contract_request_vals = {
            'name': new_name,
            'contracting_method': self.contracting_method,

            'from_date': self.from_date,
            'to_date': self.to_date,
            'replacement_method': self.replacement_method,
            'replacement_reason': self.replacement_reason,
            'justification': self.justification,
            'location_detail': self.location_detail,
            'exp_monthly_revenue': self.exp_monthly_revenue,
            'curr_cap_utilization': self.curr_cap_utilization,
            'break_even_period': self.break_even_period,
            'annualBusiness_newAddition': self.annualBusiness_newAddition,
            'select_budgeted': self.select_budgeted,
            'rep_photo_upload': self.rep_photo_upload,
            'app_resale_value': self.app_resale_value,
            'BookValue': self.BookValue,
            'oldAsset_capDate': self.oldAsset_capDate,
            'need_of_oldAsset': self.need_of_oldAsset,
            'expense_type': self.expense_type,
            'exp_category':self.exp_category,
            'lead_time': self.lead_time,
            'payment_terms': self.payment_terms.id,
            'deadline': self.deadline,
            'requested_date': self.requested_date,
            'purchase_plan': self.purchase_plan,
            'user_id': self.user_id.id,
            'company_ids': [(6, 0, self.company_ids.ids)],
            'branch_ids': [(6, 0, self.branch_ids.ids)],
            'terms': self.terms,
            'rfq_heads': [(6, 0, new_rfq_heads)],
            'main_rfq': self.main_rfq.id,
            'state': 'rfq',
            'product_requested_id': self.product_requested_id.id,
        }
        contract_request = self.env['tenders'].sudo().create(contract_request_vals)

        contract_request_lines_vals = []
        for line in self.contracts_request_line:
            line_vals = {
                'contracts_lines': contract_request.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'unit_price': line.unit_price,
                'product_group': line.product_group,
            }
            contract_request_lines_vals.append(line_vals)
        self.env['contract.request.lines'].create(contract_request_lines_vals)



        return {
            'name': 'Contract Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'tenders',
            'view_mode': 'form',
            'res_id': contract_request.id,
            'view_id': False,
            'target': 'current',
        }

    def action_add_vendor(self):
        contract_request_vals = {
            'contracting_method': self.contracting_method,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'replacement_method': self.replacement_method,
            'replacement_reason': self.replacement_reason,
            'justification': self.justification,
            'location_detail': self.location_detail,
            'exp_monthly_revenue': self.exp_monthly_revenue,
            'curr_cap_utilization': self.curr_cap_utilization,
            'break_even_period': self.break_even_period,
            'annualBusiness_newAddition': self.annualBusiness_newAddition,
            'select_budgeted': self.select_budgeted,
            'rep_photo_upload': self.rep_photo_upload,
            'app_resale_value': self.app_resale_value,
            'BookValue': self.BookValue,
            'oldAsset_capDate': self.oldAsset_capDate,
            'need_of_oldAsset': self.need_of_oldAsset,
            'expense_type': self.expense_type,
            'exp_category': self.exp_category,
            'lead_time': self.lead_time,
            'payment_terms': self.payment_terms.id,
            'deadline': self.deadline,
            'requested_date': self.requested_date,
            'purchase_plan': self.purchase_plan,
            'user_id': self.user_id.id,
            'company_ids': [(6, 0, self.company_ids.ids)],
            'branch_ids': [(6, 0, self.branch_ids.ids)],
            'terms': self.terms,
            # 'main_rfq': self.main_rfq.id,
            'state': 'draft',
            'product_requested_id': self.product_requested_id.id,
        }
        contract_request = self.env['tenders'].sudo().create(contract_request_vals)

        contract_request_lines_vals = []
        for line in self.contracts_request_line:
            line_vals = {
                'contracts_lines': contract_request.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'unit_price': line.unit_price,
                'product_group': line.product_group,
            }
            contract_request_lines_vals.append(line_vals)
        self.env['contract.request.lines'].create(contract_request_lines_vals)

        print("")


        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action_vals = {
            'model': model.id,
            'name': contract_request.name + " " + "Generate Multi Vendor Contract" + " " + "From"+" "+ self.name,
            'record': contract_request.id,  # Link to the newly created contract record
            'branch': contract_request.branch_ids[0].id if contract_request.branch_ids else False,
            'date': fields.Date.today(),
            'approve_users': [(4, self.env.user.id)],  # Adding the current user
            'department_id': self.department_id.id,
            'exp_category': contract_request.exp_category.id,
            'Created_doc_date': contract_request.requested_date,
        }
        pending_action = self.env['pending.actions'].sudo().create(pending_action_vals)

        return {
            'name': 'Contract Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'tenders',
            'view_mode': 'form',
            'res_id': contract_request.id,
            'view_id': False,
            'target': 'current',
        }

    # def action_create_multi_rfq(self):
    #     print("ggggggggggggggggg")
    #
    #     contract_request_vals = {
    #         'contracting_method': self.contracting_method,
    #         'from_date': self.from_date,
    #         'to_date': self.to_date,
    #         'expense_type': self.expense_type,
    #         'lead_time': self.lead_time,
    #         'payment_terms': self.payment_terms.id,
    #         'requested_date': self.requested_date,
    #         'user_id': self.user_id.id,
    #         'company_ids': self.company_ids.ids,
    #         'branch_ids': self.branch_ids.ids,
    #         'terms': self.terms,
    #         'contracts_request_line': self.contracts_request_line,
    #         'state': 'rfq'
    #
    #     }
    #     contract_request = self.env['tenders'].create(contract_request_vals)
    #     self.state = 'rfq'
    #     return {
    #         'name': 'Contract Requests',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'tenders',
    #         'view_mode': 'form',
    #         'res_id': contract_request.id,
    #         'view_id': False,
    #         'target': 'current',
    #     }


    def action_create_bidding(self):
        print("lllllllllll")

    @api.onchange('product_group')
    def _onchange_product_group_ids(self):
        for rec in self:
            if rec.product_group:
                lines = [(5, 0, 0)]
                for line in rec.product_group.products_line:
                    val = {
                        'product_id': line.product_id.id,
                        'uom': line.uom.id,
                        'product_group': rec.product_group[0].name,

                    }
                    lines.append((0, 0, val))
                rec.contracts_request_line = lines
            else:
                rec.contracts_request_line = [(5, 0, 0)]

    @api.depends('company_ids')
    def _compute_branch_domain(self):
        for rec in self:
            branch_domain = []
            if rec.company_ids:
                branch = self.env['res.branch'].sudo().search([
                    ('company_id', 'in', rec.company_ids.ids),
                ])

                branch_list = []
                branch_list = branch.mapped('id') if branch else []
                branch_domain = [('id', 'in', branch_list)]
            rec.branch_domain = json.dumps(branch_domain)

    # @api.constrains('from_date')
    # def _check_from_date(self):
    #     for record in self:
    #         if record.from_date and record.from_date < fields.Date.today():
    #             raise ValidationError("From date cannot be set in the past.")

    @api.constrains('to_date')
    def _check_to_date(self):
        for record in self:
            if record.to_date and record.to_date < fields.Date.today():
                raise ValidationError("To date cannot be set in the past.")


    def action_vendor_contract_request(self):
        branch = self.env['contract'].sudo().search([
            ('tender_id', '=', self.id),
        ])
        print(branch)
        if branch:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Vendor Contract Requests',
                'view_mode': 'tree,form',
                'res_model': 'contract',
                'domain': [('tender_id', '=', self.id),
                           ],
                'target': 'current'
            }

    def action_open_contract(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rate Contracts',
            'view_mode': 'tree,form',
            'res_model': 'product.tender.line',
            'domain': [('request_no', '=', self.id),
                       ],
            'target': 'current'
        }

    def action_open_pur_req(self):
        branch = self.env['product.request'].sudo().search([
            ('id', '=', self.product_requested_id.id),
        ])
        print(branch)
        if branch:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Requests',
                'view_mode': 'tree,form',
                'res_model': 'product.request',
                'domain': [('id', '=', self.product_requested_id.id),
                           ],
                'target': 'current'
            }

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

    # @api.depends('expense_type')
    # def _compute_company_ids_domain(self):
    #     for rec in self:
    #         category_domain = []
    #         if rec.requested_to:
    #             companies = self.env['res.company'].sudo().search([
    #
    #             ])
    #             if companies:
    #                 company_ids = companies.mapped('id')
    #                 if company_ids:
    #                     category_domain = [('id', 'in', company_ids)]
    #
    #         rec.company_ids_domain = json.dumps(category_domain)

    # @api.depends('quantity','unit_price')
    # def compute_total_price(self):
    #     for record in self:
    #         if record.quantity and record.unit_price:
    #             record.total_price = record.quantity * record.unit_price
    #         else:
    #             record.total_price =0


    def confirm_renewal(self):
        print("confirm")


    def action_review_request(self):
        print("review")
        for line in self.contracts_request_line:
            if line.quantity == 0:
                raise UserError(_("Quantity Cannot be zero"))
            if self.contracting_method != 'multi' and line.unit_price ==0:
                raise UserError(_("Unit Price - Cannot be zero"))
        if self.product_requested_id:
            for rec in self.product_requested_id.product_request_line_ids:
                if not (rec.expected_date >= self.from_date and rec.expected_date <=  self.to_date):
                    raise ValidationError(
                        _("Contract Period Do Not Match the Need by Date of PR: Expected Date {}").format(
                            rec.expected_date)
                    )

        contracts = self.env['product.tender.line'].sudo().search([
            ('company_ids', 'in', self.company_id.id),
            ('status', 'in', ('active', 'renew')),
            ('vendor', '=', self.vendor_id.id),
            ('branch_ids', 'in', self.branch_ids.ids)
        ],limit=1)
        print(contracts)
        print("end date", self.to_date)

        for line in self.contracts_request_line:
            print("the line is", line)
            print("product", line.product_id.id)
            # Check for duplicate product in the contracts
            for contract in contracts:
                print("con", contract.product_product_line)
                duplicate = contract.product_product_line.filtered(lambda p: p.product_id.id == line.product_id.id)
                print(duplicate)
                if duplicate:
                    conflicting_branches = self.branch_ids.filtered(lambda b: b.id in contract.branch_ids.ids)
                    if conflicting_branches:
                        branch_names = ', '.join(conflicting_branches.mapped('name'))
                        if (self.from_date <= contracts.start_date <= self.to_date) or \
                                (self.from_date <= contracts.end_date <= self.to_date) or \
                                (contracts.start_date <= self.from_date <= contracts.end_date):
                            raise ValidationError(
                                "The product {} already has a contract with vendor {} in branch(es) {}. Contract Number: {}".format(
                                    line.product_id.name, self.vendor_id.name, branch_names,contract.name
                                )
                            )

        tenders = self.env['tenders'].sudo().search([
            ('company_ids', 'in', self.company_id.id),
            ('state', '=', 'confirm'),
            ('vendor_id', '=', self.vendor_id.id),
            ('branch_ids', 'in', self.branch_ids.ids)
        ],limit=1)
        print(contracts)
        print("end date", self.to_date)

        for line in self.contracts_request_line:
            print("the line is", line)
            print("product", line.product_id.id)
            # Check for duplicate product in the contracts
            for contract in tenders:
                print("con", contract.contracts_request_line)
                duplicate = contract.contracts_request_line.filtered(lambda p: p.product_id.id == line.product_id.id)
                print(duplicate)
                if duplicate:
                    conflicting_branches = self.branch_ids.filtered(lambda b: b.id in contract.branch_ids.ids)
                    if conflicting_branches:
                        branch_names = ', '.join(conflicting_branches.mapped('name'))
                        if (self.from_date <= tenders.from_date <= self.to_date) or \
                                (self.from_date <= tenders.to_date <= self.to_date) or \
                                (tenders.from_date <= self.from_date <= tenders.to_date):
                            raise ValidationError(
                                "The product {} already has a contract Request with vendor {} in branch(es) {}. Contract Request Number: {}".format(
                                    line.product_id.name, self.vendor_id.name, branch_names,contract.name
                                )
                            )

        # record = self.env["res.users"].sudo().search([('name', '=', self.vendor_id.name)], limit=1)
        # if not record:
        #     print("Error")
        #     raise ValidationError(_("%s has no login") % self.vendor_id.name)
        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id)], limit=1)

        if pending_action:
            pending_action.status = 'closed'
        # department_records = self.env['hr.department'].sudo().search([('name', 'in', ('Service', 'Sales'))])
        # print(department_records)
        # if self.department_id in department_records:
        #     approval_flow = self.env['pr.company'].sudo().search(
        #         [

        #          ('from_amount', '<=', self.total_vendor_price),
        #          ('to_amount', '>=', self.total_vendor_price),
        #          ('expense_type', '=', self.expense_type),
        #          ('department_id','=',self.department_id.id),
        #          ('type', '=', 'contract')],
        #         limit=1)
        # else:
        #     approval_flow = self.env['pr.company'].sudo().search(
        #         [

        #             ('from_amount', '<=', self.total_price),
        #             ('to_amount', '>=', self.total_price),
        #             ('expense_type', '=', self.expense_type),

        #             ('type', '=', 'contract')],
        #             limit=1)
        if self.product_requested_id:
            pr_budget = self.env['product.request.budget'].sudo().search(
                                [('company_id', '=', self.product_requested_id.company_id.id),
                                ('branch_id', '=', self.product_requested_id.bill_to.id),
                                ('department_id', '=', self.product_requested_id.department_id.id),
                                ('expense_type', '=', self.product_requested_id.expense_type),
                                ('exp_category', '=', self.product_requested_id.exp_category.id),
                                ('from_date', '<=', date.today()),
                                ('to_date', '>=', date.today()),
                                ], limit=1)
            if self.product_requested_id.department_id.name == 'HO - IT' and not("CAPEX N/A" in self.product_requested_id.exp_category.name):
                if pr_budget and not self.contracting_method == 'multi':
                    if self.total_price > pr_budget.amount_available:
                        
                        msg = "Budget Amount Exceeded"
                        self.product_requested_id.message_post(
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
                elif pr_budget and self.contracting_method == 'multi':
                    if self.total_vendor_price > pr_budget.amount_available:
                        
                        msg = "Budget Amount Exceeded"
                        self.product_requested_id.message_post(
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
            workflow_data = self.env['pr.company'].sudo().search([('company_id', '=', self.product_requested_id.company_id.id),
                                                                  #   ('branch_id', '=', self.ship_to.id),
                                                                  ('department_id', '=', self.product_requested_id.department_id.id),
                                                                  ('from_amount', '<=', self.total_price),
                                                                  ('to_amount', '>=', self.total_price),
                                                                  ('expense_type', '=', self.product_requested_id.expense_type),
                                                                  ('exp_category', '=', self.product_requested_id.exp_category.id),
                                                                  ('type', '=', 'pr')], limit=1)
            print("pr_company_data : ", workflow_data)
            if workflow_data:
                approve_user_ids = []
                workflow_line_data = self.env['pr.approve.users'].sudo().search(
                    [('pr_company_id', '=', workflow_data.id)])  # searching in workflow line
                print('pr_company_line_data : ', workflow_line_data)

                ### First Check And then only Approval flow Commit


                for approvers in workflow_line_data:
                    if approvers.branch_id.code == "COR":
                        ser_branch = approvers.branch_id.id
                        ser_branch_record = approvers.branch_id
                    else:
                        ser_branch = self.product_requested_id.bill_to.id
                        ser_branch_record = self.product_requested_id.bill_to
                    users_line = self.env['res.users.line'].sudo().search(
                        [('company_id', '=', approvers.company_id.id), ('branch_id', '=', ser_branch),
                         ('department_id', '=', approvers.department_id.id),
                         ('designation', '=', approvers.designation.id)])  # searching user in users line
                    print(users_line, "PR USERS")
                    if users_line and users_line.res_user_id:
                        pass
                    else:
                        raise ValidationError(
                            _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                approvers.designation.name, approvers.department_id.name,
                                ser_branch_record.name, approvers.company_id.name))
            else:
                raise ValidationError(
                    "Sorry,The criteria provided did not match any existing PR workflows,Please contact Administrator.")
                    
        if self.vendor_id:
            # if self.exp_category.name == "Security/Housekeeping":
            if self.contracting_method == 'multi':
                approval_flow = False
                approval_flow = self.env['pr.company'].sudo().search(
                    [
                        # ('department_id', '=', self.exp_category.id),
                        ('company_id', 'in', self. company_ids.ids),
                        ('exp_category', '=', self.exp_category.id),
                        ('expense_type', '=', self.expense_type),
                        ('from_amount', '<=', self.total_vendor_price),
                        ('to_amount', '>=', self.total_vendor_price),
                        ('type', '=', 'contract')],
                    limit=1)
                if approval_flow:
                    pass
                else:
                    # else:
                    # # To add contract condition for washing
                    approval_flow = self.env['pr.company'].sudo().search(
                        [
                            # ('department_id', '=', "ALL"),
                            ('company_id', 'in', self. company_ids.ids),
                            ('exp_category', '=', "NILL"),
                            ('from_amount', '<=', self.total_vendor_price),
                            ('to_amount', '>=', self.total_vendor_price),
                            ('expense_type', '=', self.expense_type),
                            ('type', '=', 'contract')],
                        limit=1)

                if self.legal_workflow:
                    approval_flow2 = self.env['pr.company'].sudo().search([
                        # ('company_id', '=', self.company_id.id),
                        # ('department_id', '=', self.department_id.id),
                        ('company_id', 'in', self. company_ids.ids),
                        ('expense_type', '=', self.expense_type),
                        ('exp_category', '=', self.exp_category.id),
                        ('from_amount', '<=', self.total_vendor_price),
                        ('to_amount', '>=', self.total_vendor_price),
                        ('type', '=', 'legal_workflow')],
                        limit=1)
                    if not approval_flow2:
                        approval_flow2 = self.env['pr.company'].sudo().search(
                            [
                                # ('department_id', '=', "ALL"),
                                ('company_id', 'in', self. company_ids.ids),
                                ('exp_category', '=', "NILL"),
                                ('from_amount', '<=', self.total_vendor_price),
                                ('to_amount', '>=', self.total_vendor_price),
                                ('expense_type', '=', self.expense_type),
                                ('type', '=', 'legal_workflow')],
                            limit=1)
            else:
                approval_flow = False
                approval_flow = self.env['pr.company'].sudo().search(
                    [
                        # ('department_id', '=', self.exp_category.id),
                        ('company_id', 'in', self. company_ids.ids),
                        ('exp_category', '=', self.exp_category.id),
                        ('expense_type', '=', self.expense_type),
                        ('from_amount', '<=', self.total_price),
                        ('to_amount', '>=', self.total_price),
                        ('type', '=', 'contract')],
                    limit=1)
                if approval_flow:
                    pass
                else:
                    # else:
                    # # To add contract condition for washing
                    approval_flow = self.env['pr.company'].sudo().search(
                        [
                            # ('department_id', '=', "ALL"),
                            ('company_id', 'in', self. company_ids.ids),
                            ('exp_category', '=', "NILL"),
                            ('from_amount', '<=', self.total_price),
                            ('to_amount', '>=', self.total_price),
                            ('expense_type', '=', self.expense_type),
                            ('type', '=', 'contract')],
                        limit=1)

                if self.legal_workflow:
                    approval_flow2 = self.env['pr.company'].sudo().search([
                        # ('company_id', '=', self.company_id.id),
                        # ('department_id', '=', self.department_id.id),
                        ('company_id', 'in', self. company_ids.ids),
                        ('expense_type', '=', self.expense_type),
                        ('exp_category', '=', self.exp_category.id),
                        ('from_amount', '<=', self.total_price),
                        ('to_amount', '>=', self.total_price),
                        ('type', '=', 'legal_workflow')],
                        limit=1)
                    if not approval_flow2:
                        approval_flow2 = self.env['pr.company'].sudo().search(
                            [
                                # ('department_id', '=', "ALL"),
                                ('company_id', 'in', self. company_ids.ids),

                                ('exp_category', '=', "NILL"),
                                ('from_amount', '<=', self.total_price),
                                ('to_amount', '>=', self.total_price),
                                ('expense_type', '=', self.expense_type),
                                ('type', '=', 'legal_workflow')],
                            limit=1)
        else:
            raise ValidationError(
                "No Vendor Found.")
        if self.legal_workflow:
            if approval_flow2:
                for ctr_approve_users in approval_flow2.pr_approve_users_id:
                    users_line = self.env['res.users.line'].sudo().search(
                        [('company_id', '=', ctr_approve_users.company_id.id),
                         ('branch_id', '=', ctr_approve_users.branch_id.id),
                         ('department_id', '=', ctr_approve_users.department_id.id),
                         ('designation', '=', ctr_approve_users.designation.id)])
                    if users_line and users_line.res_user_id:
                        pass
                    else:
                        raise ValidationError(
                            _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                ctr_approve_users.designation.name, ctr_approve_users.department_id.name,
                                ctr_approve_users.branch_id.name, ctr_approve_users.company_id.name))
            else:
                raise ValidationError(
                    "No Legal Workflow was found based on these criteria for contract creation.")
        if approval_flow:
            print(approval_flow)
            approve_user_ids = []

            ### First Check And then only Approval flow Commit

            for ctr_approve_users in approval_flow.pr_approve_users_id:
                users_line = self.env['res.users.line'].sudo().search(
                    [('company_id', '=', ctr_approve_users.company_id.id),
                     ('branch_id', '=', ctr_approve_users.branch_id.id),
                     ('department_id', '=', ctr_approve_users.department_id.id),
                     ('designation', '=', ctr_approve_users.designation.id)])
                if users_line and users_line.res_user_id:
                    pass
                else:
                    raise ValidationError(
                        _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                            ctr_approve_users.designation.name, ctr_approve_users.department_id.name,
                            ctr_approve_users.branch_id.name, ctr_approve_users.company_id.name))

            ## For Approval execution(else partial flow will be executed)
            for ctr_approve_users in approval_flow.pr_approve_users_id:
                users_line = self.env['res.users.line'].sudo().search(
                    [('company_id', '=', ctr_approve_users.company_id.id), ('branch_id', '=', ctr_approve_users.branch_id.id),
                     ('department_id', '=', ctr_approve_users.department_id.id),
                     ('designation', '=', ctr_approve_users.designation.id)])
                print("User Line",users_line)
                if users_line:
                    print("Tendor Approver",users_line)
                    self.write({'approve_users': [(4, users_line.res_user_id.id)]})
                    vals = {
                        'user_id': users_line.res_user_id.id,
                        'company_id': ctr_approve_users.company_id.id,
                        'branch_id': ctr_approve_users.branch_id.id,
                        'department_id': ctr_approve_users.department_id.id,
                        'designation': ctr_approve_users.designation.id,
                        'approve_order': ctr_approve_users.approve_order,
                        'tender_id': self.id
                    }
                    approve_user_ids.append({'user_id': users_line.res_user_id.id,
                                             'approve_order': ctr_approve_users.approve_order})

                    pr_approve_line = self.env['tender.approve.line'].create(vals)
                    self.env.cr.commit()
                    print("approve_user_ids : ", approve_user_ids)
                else:
                    raise ValidationError(_("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                    ctr_approve_users.designation.name, ctr_approve_users.department_id.name,
                    ctr_approve_users.branch_id.name, ctr_approve_users.company_id.name))
            if self.contracting_method == 'nego':
                if self.vendor_id.login:
                    mylist = sorted(approve_user_ids, key=lambda k: k['approve_order'])
                    largest_order = mylist[-1]['approve_order']
                    new_line_vals = {
                        'user_id': self.vendor_id.login.id,
                        'approve_order': largest_order+1,
                    }
                    self.tender_approve_line |= self.env['tender.approve.line'].create(new_line_vals)
                    # self.message_post(body="Wait for Vendor acknowledgement")
                    self.write({'approve_users': [(4, self.vendor_id.login.id)]})
                    approve_user_ids.append({'user_id': self.vendor_id.login.id,
                                             'approve_order': largest_order+1})
            if approve_user_ids:
                mylist = sorted(approve_user_ids, key=lambda k: (k['approve_order']))
                order = mylist[0]['approve_order']
                print("mylist : ", mylist)
                print("order : ", order)
                for users in mylist:
                    if users['approve_order'] == order:
                        self.write({'next_approve_user_id': [(4, users['user_id'])]})

            for user in self.next_approve_user_id:
                model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                pending_vals = {
                    'model': model.id,
                    'name': self.name + " " + "Contract Request For Approval",

                    'record': self.id,
                    'date': date.today(),
                    'department_id': self.department_id.id,
                    'exp_category': self.exp_category.id,
                    'Created_doc_date': self.requested_date,

                }
                if approve_user_ids:
                    pass
                else:
                    raise ValidationError("No workflow was found based on these criteria for contract creation.")

                if approve_user_ids:
                    user_ids_to_pass = user.ids
                    if self.branch_ids:
                        first_branch_id = self.branch_ids[0].id
                        pending_vals['branch'] = first_branch_id
                    pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                    pendings = self.env['pending.actions'].create(pending_vals)
                    

                    approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                    pendings.write({'email': approve_users_emails})

                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')], limit=1)
                    activity_type_id = activity_type.id if activity_type else False
                    res_model_id = self.env['ir.model'].sudo().search(
                        [('model', '=', 'tenders')]).id
                    for user_id in user_ids_to_pass:
                        user = self.env['res.users'].sudo().browse(user_id)
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

            ############# Mail Body ###############

                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Contracts/Agreements')], limit=1) or False

                    url_params = {
                        'id': self.id,
                        'action': self.env.ref('product_purchase.action_tender_status').id,
                        'model': 'tenders',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1) or False

                    body = (
                        f"Dear User, a contract request for {self.name} is currently pending approval.<br><br>"
                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                    )
                    # if vendor.email:
                    mail_values = {
                        'subject': 'New Contract Request',
                        'body_html': body,
                        'email_to': ','.join(
                            self.env['res.users'].sudo().browse(user_ids_to_pass).mapped('login')),
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
        else:
            raise ValidationError(
                "No workflow was found based on these criteria for contract creation.")

        self.state='confirm'


        ########## vendor with login #########
        # print("self.requested_date:", self.requested_date)
        # vals = {
        #     'product': self.product.id,
        #     'vendor_id': self.vendor_id.id,
        #     'payment_terms': self.payment_terms.id or "",
        #     'user': self.user_id.id,
        #     'company_id': self.company_id.id,
        #     'quantity': self.quantity,
        #     'unit_price': self.unit_price,
        #     'total_price': self.quantity * self.unit_price,
        #     'requested_date': self.requested_date,
        #     # 'requested_date': self.requested_date.strftime('%m-%d-%Y'),
        #     'from_date': self.from_date,
        #     'to_date': self.to_date,
        #     # 'customer': vendors.id,
        #     'user_id': self.requested_to.login.id,
        #     'request_check': False,
        #     'vendor_request_check': False,
        #     'product_requested_id': self.product_requested_id.id or "",
        #     'contract_request': self.id,
        #     'lead_time': self.lead_time,
        #     # 'product_request_line_id': item.id,
        #     'expected_date': self.expected_date or ""
        # }
        # print("vals : ", vals)
        # contract_record = self.env['contract'].create(vals)
        #
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # menu_id = self.env['ir.ui.menu'].sudo().search(
        #     [('name', '=', 'Contracts/Agreements')], limit=1) or False
        #
        # url_params = {
        #     'id': contract_record.id,
        #     'action': self.env.ref('product_purchase.action_contract_requests').id,
        #     'model': 'contract',
        #     'view_type': 'form',
        #     'menu_id': menu_id.id if menu_id else False,
        # }
        #
        # params = '/web?#%s' % url_encode(url_params)
        # url = base_url + params if base_url else "#"
        #
        # print(url)
        # author = self.env['res.partner'].sudo().search(
        #     [('name', '=', 'Administrator')], limit=1) or False
        #
        # body = (
        #     f"Dear User, a contract request for {self.name} is currently pending approval for {self.product.name}..<br><br>"
        #     f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
        #     f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
        #     f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
        # )
        # # if vendor.email:
        # mail_values = {
        #     'subject': 'New Contract Request',
        #     'body_html': body,
        #     'email_to':self.vendor_id.email,
        #     'auto_delete': False,
        #     'author_id': author.id
        # }
        # mail_record = self.env['mail.mail'].sudo().create(mail_values)






    @api.model
    def create(self, vals):

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tenders') or 'New'
        
        if isinstance(vals.get('exp_category'), models.Model):
            vals['exp_category'] = vals['exp_category'].id

        result = super(Tenders, self).create(vals)
        buyer_group = self.env.ref(
            'product_purchase.group_buyers')
        buyer_users = buyer_group.users
        if buyer_users:
            subject = "New Contract Request Created: %s" % result.name
            # body = "A new contract request with the name %s has been created." % result.name

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'Contracts/Agreements')], limit=1) or False

            url_params = {
                'id': result.id,
                'action': self.env.ref('product_purchase.action_tender_status').id,
                'model': 'tenders',
                'view_type': 'form',
                'menu_id': menu_id.id if menu_id else False,
            }

            params = '/web?#%s' % url_encode(url_params)
            url = base_url + params if base_url else "#"

            print(url)
            body = (
                f"Dear User, A new contract request {result.name}  has been created .<br><br>"
                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
            )

            email_to_list = [user.email if user.email else user.login for user in buyer_users]

            author = self.env['res.partner'].sudo().search(
                [('name', '=', 'Administrator')], limit=1)

            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': ','.join(email_to_list),
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)
            else:
                print("helloo")
        records = self.env['contract.request.lines'].sudo().search([('contracts_lines', '=', result.id)])
        product_counts = {}
        for rec in records:

            product_counts[rec.product_id.id] = product_counts.get(rec.product_id.id, 0) + 1
            if product_counts[rec.product_id.id] > 1:
                raise UserError(_("A product of cannot be entered more than once"))
        return result
        
    def write(self, vals):
        result = super(Tenders, self).write(vals)
        records = self.env['contract.request.lines'].sudo().search([('contracts_lines', '=', self.id)])
        product_counts = {}
        for rec in records:

            product_counts[rec.product_id.id] = product_counts.get(rec.product_id.id, 0) + 1
            if product_counts[rec.product_id.id] > 1:
                raise UserError(_("A product cannot be entered more than once"))
        if 'reference_doc' in vals and self.contract_id:
            reference_docs = vals.get('reference_doc')
            print("doc",self.contract_id.reference_doc)
            self.contract_id.sudo().write({'reference_doc': [(6, 0, self.reference_doc.ids)]})

            subject = "Attachment Updation in: %s" % self.contract_id.name
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'My Contract Requests')], limit=1) or False

            url_params = {
                'id': self.contract_id.id,
                'action': self.env.ref('product_purchase.action_contract_requests').id,
                'model': 'contract',
                'view_type': 'form',
                'menu_id': menu_id.id if menu_id else False,
            }

            params = '/web?#%s' % url_encode(url_params)
            url = base_url + params if base_url else "#"

            print(url)
            author = self.env['res.partner'].sudo().search(
                [('name', '=', 'Administrator')], limit=1)
            # Create a draft email using the rendered body
            body = (
                f"Dear {self.vendor_id.name}, "
                f"A new Attachment Updation has been made in Contract Request with the name <strong>{self.contract_id.name} .<br>"
                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
            )
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': self.vendor_id.email,
                'auto_delete': False,
                'author_id': author.id
            }
            mail_record = self.env['mail.mail'].sudo().create(mail_values)
        return result

    @api.depends("user_approve_check")
    def _compute_total(self):
        print('Inside user_approve_check')
        for rec in self:
            if rec.next_approve_user_id:
                if self.env.user in rec.next_approve_user_id:
                    rec.user_approve_check = True
                else:
                    rec.user_approve_check = False
            else:
                rec.user_approve_check = False

    @api.depends("legal_approve_check")
    def _compute_legal(self):
        print('Inside user_approve_check')
        for rec in self:
            if rec.legal_next_approve_user:
                if self.env.user in rec.legal_next_approve_user:
                    rec.legal_approve_check = True
                else:
                    rec.legal_approve_check = False
            else:
                rec.legal_approve_check = False

    def action_create_tender(self):
        tender_lines = []
        for line in self.contracts_request_line:
            if self.contracting_method == 'multi':
                if line.status == 'select':
                    tender_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'unit_price': line.vendor_price,
                        'product_group': line.product_group,
                    }))
            else:
                tender_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'unit_price': line.unit_price,
                    'product_group': line.product_group,
                }))
        branch_ids = self.branch_ids.ids if self.branch_ids else []
        attachment_ids = self.attachment_vendor_ids.ids if self.attachment_vendor_ids else []

        if not branch_ids and self.company_ids:
            branches = self.env['res.branch'].sudo().search([('company_id', 'in', self.company_ids.ids)])
            branch_ids = branches.ids

        tender_record = self.env['product.tender.line'].sudo().create({
            'vendor': self.vendor_id.id,
            'start_date': self.from_date,
            'end_date': self.to_date,
            'lead_time': self.lead_time,
            'payment_terms': self.payment_terms.id,
            'user_id': self.user_id.id,
            'company_ids': [(4, company_id) for company_id in self.company_ids.ids],
            'branch_ids': [(4, branch_id) for branch_id in branch_ids],
            'request_no': self.id,
            'delivery_terms': self.terms,
            'status': 'active',
            'product_product_line': tender_lines,
            'exp_category': self.exp_category.id,
            'purchase_plan': self.purchase_plan,
            'attachment_vendor_ids': [(6, 0, attachment_ids)] if attachment_ids else False,
        })
        tender_record._onchange_partner_id()
        self.env.cr.commit()
        self.tender_response_tender_check = True

        subject = "Contract %s Created " % tender_record.name
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # menu_id = self.env['ir.ui.menu'].sudo().search(
        #     [('name', '=', 'My Contract Requests')], limit=1) or False

        # url_params = {
        #     'id': self.contract_id.id,
        #     'action': self.env.ref('product_purchase.action_contract_requests').id,
        #     'model': 'contract',
        #     'view_type': 'form',
        #     'menu_id': menu_id.id if menu_id else False,
        # }

        # params = '/web?#%s' % url_encode(url_params)
        # url = base_url + params if base_url else "#"

        # print(url)
        author = self.env['res.partner'].sudo().search(
            [('name', '=', 'Administrator')], limit=1)
        # Create a draft email using the rendered body
        body = (
            f"Dear {self.vendor_id.name}, "
            f"A new Contract is created in name <strong>{tender_record.name}.+<br>"
            # f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            # f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.vendor_id.email,
            'auto_delete': False,
            'author_id': author.id
        }
        mail_record = self.env['mail.mail'].sudo().create(mail_values)
    # def action_create_tender(self):
    #     tender_record = self.env['product.tender.line'].create({
    #         'vendor': self.vendor_id.id,
    #         'start_date': self.from_date,
    #         'end_date': self.to_date,
    #         'lead_time': self.lead_time,
    #         'payment_terms': self.payment_terms.id,
    #         'user_id': self.user_id.id,
    #         'company_ids': [(4, company_id) for company_id in self.company_ids.ids],
    #         'branch_ids': [(4, branch_id) for branch_id in self.branch_ids.ids],
    #         'request_no': self.id,
    #         'delivery_terms': self.terms,
    #         'status': 'active',
    #         'product_product_line': [(0, 0, {
    #             'product_id': line.product_id.id,
    #             'unit_price': line.unit_price,
    #             'product_group': line.product_group,
    #         }) for line in self.contracts_request_line]
    #     })
    #     self.env.cr.commit()
    #     self.tender_response_tender_check = True

    def action_cancel(self):
        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

        if pending_action:
            for rec in pending_action:
                print(rec.name)
                rec.status = 'closed'

        activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)

        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
            ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
            ('activity_type_id', '=', activity_type.id),
        ])
        if activity:

            for act in activity:

                act.action_feedback(feedback="Activity Declined")

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Contracts/Agreements')], limit=1) or False

        url_params = {
            'id': self.id,
            'action': self.env.ref('product_purchase.action_tender_status').id,
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
            f"The Contract Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        subject = "Contract Request Has Been Rejected: %s" % self.name
        for approvers in self.tender_approve_line:
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
        buyer_group = self.env.ref('product_purchase.group_buyers')
        buyer_users = buyer_group.users
        if buyer_users:
            # Create and send emails to each user
            for user in buyer_users:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': user.login,  # Assuming the email is stored in the partner record
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)
        if self.requested_by:
            print("req", self.user_id)
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': self.requested_by.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)
        self.contract_status = 'cancel'
        self.state = 'cancel'
        self.tender_response_tender_check = True

    def change_in_product(self):
        print("product Function")
        for product in self.contracts_request_line:
            flag= 0
            print("ctr product",product.product_id.name)
            product_request_line = self.env['product.request.line'].sudo().search([
                ('product_request_id', '=', self.product_requested_id.id),
            ])
            for rec in product_request_line:
                print("pr product",rec.product.name)
                if product.product_id.id == rec.product.id:
                    print("Present in BOTH", rec.product.name)
                    rec.sudo().write({'quantity': product.quantity, 'description': product.description})
                    flag= 1
                    break
            if flag != 1:
                vals = {
                    'product': product.product_id.id,
                    'description': product.description or '',  # Ensure all fields are populated correctly
                    'quantity': product.quantity or 0,
                    'expected_date': self.to_date,
                    'product_request_id': self.product_requested_id.id,
                }
                print("creation",vals)
                product_record = self.env['product.request.line'].sudo().create(vals)

    def action_approval(self):
        self.write({'approved_users': [(4, self.env.user.id)]})
        approve_users = self.env['tender.approve.line'].sudo().search(
            [('tender_id', '=', self.id), ('user_id', '=', self.env.user.id)], )

        approve_users.write({
            'status': 'accept',
            'approve_date': fields.Date.today()
        })

        if self.approved_users == self.approve_users:

            # if not self.company_ids:
            #     self.message_post(body=f"{self.env.user.name} Rejected the Purchase Request.")
            # self.state ='approve'
            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id),('status','=','open')])
            if pending_action:
                for rec in pending_action:
                    rec.status = 'closed'
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                ('user_id', '=', self.env.user.id),('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                activity.action_feedback(feedback="Approved")

            subject = "Everyone has approved the contract request: %s" % self.name
            print("Name", self.name)
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'Contracts/Agreements')], limit=1) or False

            url_params = {
                'id': self.id,
                'action': self.env.ref('product_purchase.action_tender_status').id,
                'model': 'tenders',
                'view_type': 'form',
                'menu_id': menu_id.id if menu_id else False,
            }

            params = '/web?#%s' % url_encode(url_params)
            url = base_url + params if base_url else "#"

            body = (
                f"Dear User," 
                f"Everyone has approved the contract request <strong>{self.name}</strong> .The Rate contract has been created. <strong></strong>.<br>"
                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
            )

            print(url)

            author = self.env['res.partner'].sudo().search(
                [('name', '=', 'Administrator')], limit=1)

            if author and self.assigned_to:
                for user in self.assigned_to:
                    if user.login:
                        mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': user.login,
                            'email_cc':  'cor.orders@popularv.com',
                            'auto_delete': False,
                            'author_id': author.id
                        }
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)


            
            if self.legal_workflow:
                self.state = 'legal_approve'
                if self.contracting_method == 'multi':
                    pr_company_data2 = self.env['pr.company'].sudo().search([
                                                                                # ('company_id', '=', self.company_id.id),
                                                                             # ('department_id', '=', self.department_id.id),
                                                                             ('expense_type', '=', self.expense_type),
                                                                             ('exp_category', '=', self.exp_category.id),
                                                                             ('from_amount', '<=', self.total_vendor_price),
                                                                             ('to_amount', '>=', self.total_vendor_price),
                                                                             ('type', '=', 'legal_workflow')],
                                                                            limit=1)
                    print("the datas are",self.company_id.name,self.expense_type,self.exp_category.name)
                    if not pr_company_data2:
                        pr_company_data2 = self.env['pr.company'].sudo().search(
                            [
                                # ('department_id', '=', "ALL"),
                                ('exp_category', '=', "NILL"),
                                ('from_amount', '<=', self.total_vendor_price),
                                ('to_amount', '>=', self.total_vendor_price),
                                ('expense_type', '=', self.expense_type),
                                ('type', '=', 'legal_workflow')],
                            limit=1)

                else:
                    pr_company_data2 = self.env['pr.company'].sudo().search([
                                                                                # ('company_id', '=', self.company_id.id),
                                                                             # ('department_id', '=', self.department_id.id),
                                                                             ('expense_type', '=', self.expense_type),
                                                                             ('exp_category', '=', self.exp_category.id),
                                                                             ('from_amount', '<=', self.total_price),
                                                                             ('to_amount', '>=', self.total_price),
                                                                             ('type', '=', 'legal_workflow')],
                                                                            limit=1)
                    print("the datas are",self.company_id.name,self.expense_type,self.exp_category.name)
                    if not pr_company_data2:
                        pr_company_data2 = self.env['pr.company'].sudo().search(
                            [
                                # ('department_id', '=', "ALL"),
                                ('exp_category', '=', "NILL"),
                                ('from_amount', '<=', self.total_price),
                                ('to_amount', '>=', self.total_price),
                                ('expense_type', '=', self.expense_type),
                                ('type', '=', 'legal_workflow')],
                            limit=1)
                if pr_company_data2:
                    print("hlw i am in legal")
                    legal_lines = []
                    for approvers in pr_company_data2.pr_approve_users_id:
                        print("the approvers2 are", approvers)
                        for details in approvers:
                            print(details.company_id.id, details.branch_id.id, details.department_id.id,
                                  details.designation.id)
                            corresponding_approval_flow = self.env['res.users.line'].sudo().search([
                                ('company_id', '=', details.company_id.id),
                                ('branch_id', '=', details.branch_id.id),
                                ('department_id', '=', details.department_id.id),
                                ('designation', '=', details.designation.id)
                            ])
                            print("cores approval2", corresponding_approval_flow)
                            print("corresponding approval flows2:", corresponding_approval_flow.res_user_id.id)
                            if not corresponding_approval_flow.res_user_id:
                                raise ValidationError(
                                    _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                        details.designation.name, details.department_id.name,
                                        details.branch_id.name, details.company_id.name))
                            else:
                                self.legal_approve_users |= corresponding_approval_flow.mapped('res_user_id')
                                print("the approval users are2", self.approve_users.ids)

                                vals = {
                                    'user_id': corresponding_approval_flow.res_user_id.id,
                                    'company_id': corresponding_approval_flow.company_id.id,
                                    'department_id': corresponding_approval_flow.department_id.id,
                                    'designation': corresponding_approval_flow.designation.id,
                                    'approve_order': details.approve_order,
                                }

                                legal_lines.append((0, 0, vals))
                                print("the legal line",legal_lines)

                    if legal_lines:
                        self.legal_approve_line = legal_lines

                    first_approver = self.legal_approve_line.filtered(lambda l: l.approve_order == 1).mapped('user_id')
                    vendor_users = first_approver

                    for vendor_user in vendor_users:
                        print("Creating pending action for the first approver:", vendor_user.id)
                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                        pending_action_vals = {
                            'model': model.id,
                            'name': self.name + " " + "Waiting For Approval",
                            'record': self.id,
                            'branch': self.branch_ids[0].id,
                            'date': fields.Date.today(),
                            'department_id': self.department_id.id,
                            'exp_category': self.exp_category.id,
                            'Created_doc_date': self.requested_date,
                            'approve_users': [(4, vendor_user.id)],
                        }
                        pending_action = self.env['pending.actions'].sudo().create(pending_action_vals)
                        print("the pending action", pending_action)
                        approve_users_emails = ', '.join(pending_action.approve_users.mapped('login'))

                        pending_action.write({'email': approve_users_emails})

                        activity_type = self.env['mail.activity.type'].sudo().search(
                            [('name', '=', 'Pending Request')], limit=1)
                        activity_type_id = activity_type.id if activity_type else False
                        res_model_id = self.env['ir.model'].sudo().search(
                            [('model', '=', 'tenders')]).id

                        activity_values = {
                            'user_id': vendor_user.id,
                            'res_id': self.id,
                            'note': "Pending Action",
                            'activity_type_id': activity_type_id,
                            'res_model_id': res_model_id,
                        }
                        with self.env.cr.savepoint():
                            self = self.with_context(mail_activity_quick_update=True)
                            created_activity = self.env['mail.activity'].sudo().create(activity_values)

                        subject = "New Contract Request Raised: %s" % self.name
                        print("Name", self.name)
                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        menu_id = self.env['ir.ui.menu'].sudo().search(
                            [('name', '=', 'Pending Actions')], limit=1) or False

                        url_params = {
                            'id': self.id,
                            'action': self.env.ref('pending_actions.action_pending_actions').id,
                            'model': 'tenders',
                            'view_type': 'form',
                            'menu_id': menu_id.id if menu_id else False,
                        }

                        params = '/web?#%s' % url_encode(url_params)
                        url = base_url + params if base_url else "#"

                        body = (
                            f"Dear User,"
                            f"A new Contract Request with the name <strong>{self.name}</strong> has been raised by <strong></strong>.<br>"
                            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                        )

                        print(url)

                        author = self.env['res.partner'].sudo().search(
                            [('name', '=', 'Administrator')], limit=1)

                        if author:
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': vendor_user.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)

                    legal_next_approver_user_ids = [
                        legal_next_approver.user_id.id
                        for legal_next_approver in self.legal_approve_line
                        if legal_next_approver.approve_order == 1
                    ]
                    print(legal_next_approver_user_ids, "This print")
                    if legal_next_approver_user_ids:
                        result = self.write({'legal_next_approve_user': [(6, 0, legal_next_approver_user_ids)]})
                        # self.state = 'request'
                        print("the result is",result)
                    print("name is", self._name)

                else:
                    raise ValidationError(
                        "Sorry,The criteria provided did not match any existing Legal workflows,Please contact Administrator.")

            else:
                self.state = 'approve'

            



            if not self.renew_id:
                if self.product_requested_id:
                    self.product_requested_id.ensure_one()
                    print(self.product_requested_id)
                    print(self.product_requested_id.name)
                    self.change_in_product()
                    self.product_requested_id.message_post(body="Contract Created.")
                    self.action_create_tender()
                    self.env.cr.commit()
                    # self.product_requested_id.product_request_line_ids.onchange_in_product()
#############
                    # self.product_requested_id.product_request_line_ids.onchange_in_unit_price()
                    print("YESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
                    # Search for all contracts related to the product
                    for rec in self.product_requested_id.product_request_line_ids:
                        contract_lines = self.env['contract.request.lines'].sudo().search([
                            ('product_id', '=', rec.product.id),
                            ('contracts_lines', '=', self.id)  # Ensures only relevant contracts are checked
                        ])
                        if contract_lines:
                            rec.onchange_in_product()
                            rec.vendors = self.vendor_id
                        # rec.onchange_in_product()
                        # unit_price = []
                        # vendor_list = []
                        # lowest_unit_price = float('inf')  # Initialize with positive infinity

                        # product_contract_lines = self.env['product.contracts.line'].sudo().search([
                        #     ('product_id', '=', rec.product.id)
                        # ])

                        # for contract_line in product_contract_lines:
                        #     product_tender_lines = self.env['product.tender.line'].sudo().search([
                        #         ('id', '=', contract_line.products_line.id),
                        #         ('start_date', '<=', fields.Date.today()),
                        #         ('end_date', '>=', fields.Date.today()),
                        #         ('status', 'in', ('active', 'renew')),
                        #         ('company_ids', 'in', self.product_requested_id.company_id.ids),
                        #         ('branch_ids', 'in', self.product_requested_id.ship_to.ids)
                        #     ])

                        #     for tender_line in product_tender_lines:
                        #         unit_price.append(tender_line.unit_price)
                        #         if tender_line.unit_price < lowest_unit_price:
                        #             lowest_unit_price = tender_line.unit_price
                        #             vendor_list = [tender_line.vendor.id]
                        #         elif tender_line.unit_price == lowest_unit_price:
                        #             vendor_list.append(tender_line.vendor.id)

                        # if vendor_list:  # Ensure there are vendors
                        #     # Get the vendor object with the lowest unit price
                        #     lowest_vendor = self.env['res.partner'].browse(vendor_list[0])
                        # rec.vendors = self.vendor_id
                    self.env.cr.commit()

                    line_items = self.product_requested_id.product_request_line_ids
                    if all(line_item.contract_status == 'in_contract' for line_item in line_items):
                        print("HELLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLOOOOOOOOOOOOOOOOOOOOOOO")
                        self.product_requested_id.product_request_line_ids.onchange_vendors_quantity()
                        self.product_requested_id.action_request()
                        self.ensure_one()
                        self.product_requested_id.product_request_line_ids._compute_contract()

                # if self.product_requested_id:
                #     print(self.product_requested_id)
                #     print(self.product_requested_id.name)
                #
                #     print("HELLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLOOOOOOOOOOOOOOOOOOOOOOO")
                #     self.action_create_tender()
                #     # self.env.cr.commit()
                #     self.product_requested_id.product_request_line_ids.onchange_vendors_quantity()
                #
                #     line_items = self.product_requested_id.product_request_line_ids
                #     print(line_items)
                #     if all(line_item.contract_status == 'in_contract' for line_item in line_items):
                #         self.product_requested_id.action_request()

                    # self.product_requested_id.action_request()
                    # self.product_requested_id.status = 'requested'
                else:
                    self.action_create_tender()
                    self.env.cr.commit()

            else:
                print("renewal")      # Renewal
                # tender_record = self.env['product.tender.line'].sudo().create({
                #     'vendor': self.vendor_id.id,
                #     # 'purchase_representative': user_id,
                #     'product_template_id': self.product.id,
                #     'company_id': self.requested_by.id,
                #     'quantity': self.quantity,
                #     'unit_price': self.unit_price,
                #     'total': self.total_price,
                #     'start_date': self.from_date,
                #     'end_date': self.to_date,
                #     'user_id': self.user_id.id,
                #     'lead_time': self.lead_time,
                #     'payment_terms': self.payment_terms.id,
                #     'status': 'active'
                # })
                # self.tender_response_tender_check = True
        else:
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
            print("the pending actions are the", pending_action)

            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close", rec)
                    rec.status = 'closed'

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                ('user_id', '=', self.env.user.id),('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("Complete")
                print(activity.id)
                activity.action_feedback(feedback="Approved")

            approve_users = self.env['tender.approve.line'].sudo().search([('tender_id', '=', self.id)],
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

                                    for user in self.next_approve_user_id:
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                    limit=1)

                                        user_type = 'vendor' if user.has_group(
                                            'vendor_portal.group_vendor_portal_user') else None
                                        print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
                                        pending_vals = {
                                            'model': model.id,
                                            'name': self.name + " " + "Waiting For Approval",
                                            'department_id': self.department_id.id,
                                            'exp_category': self.exp_category.id,
                                            'Created_doc_date': self.requested_date,

                                            'record': self.id,
                                            'date': date.today(),
                                            'user' : user_type,
                                        }
                                        if user:
                                            user_ids_to_pass = user.ids
                                            if self.branch_ids:
                                                first_branch_id = self.branch_ids[0].id
                                                pending_vals['branch'] = first_branch_id
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            pendings = self.env['pending.actions'].create(pending_vals)
                                            approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                            pendings.write({'email': approve_users_emails})

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Request')], limit=1)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'tenders')]).id
                                            for user_id in user_ids_to_pass:
                                                activity_values = {
                                                    'user_id': user.id,
                                                    'res_id': self.id,
                                                    'summary': "Action",
                                                    'note': "Pending Action",
                                                    'activity_type_id': activity_type_id,
                                                    'res_model_id': res_model_id,
                                                }
                                                with self.env.cr.savepoint():
                                                    self = self.with_context(mail_activity_quick_update=True)
                                                    created_activity = self.env['mail.activity'].create(
                                                    activity_values)
                                            subject = "New Contract Request Created: %s" % self.name
                                            # body = "A new contract request with the name %s has been created." % result.name

                                            base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                'web.base.url')
                                            menu_id = self.env['ir.ui.menu'].sudo().search(
                                                [('name', '=', 'Contracts/Agreements')], limit=1) or False

                                            url_params = {
                                                'id': self.id,
                                                'action': self.env.ref(
                                                    'product_purchase.action_tender_status').id,
                                                'model': 'tenders',
                                                'view_type': 'form',
                                                'menu_id': menu_id.id if menu_id else False,
                                            }

                                            params = '/web?#%s' % url_encode(url_params)
                                            url = base_url + params if base_url else "#"

                                            print(url)
                                            body = (
                                                f"Dear User, A new contract request {self.name} waiting for Approval .<br><br>"
                                                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                            )
                                            # email_to_list = [user.email if user.email else user.login for user
                                            #                  in buyer_users]
                                            author = self.env['res.partner'].sudo().search(
                                                [('name', '=', 'Administrator')], limit=1)

                                            if author:
                                                mail_values = {
                                                    'subject': subject,
                                                    'body_html': body,
                                                    'email_to': user.login,
                                                    'auto_delete': False,
                                                    'author_id': author.id
                                                }
                                                mail_record = self.env['mail.mail'].sudo().create(mail_values)

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
                                                print("hellooooooooooooooooooooooooooooooooo")

                                            for user in self.next_approve_user_id:
                                                model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                           limit=1)
                                                print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
                                                pending_vals = {
                                                    'model': model.id,
                                                    'name': self.name + " " + "Waiting For Approval",
                                                    'department_id': self.department_id.id,
                                                    'exp_category': self.exp_category.id,
                                                    'Created_doc_date': self.requested_date,

                                                    'record': self.id,
                                                    'date': date.today(),
                                                }
                                                if user:
                                                    user_ids_to_pass = user.ids
                                                    if self.branch_ids:
                                                        first_branch_id = self.branch_ids[0].id
                                                        pending_vals['branch'] = first_branch_id
                                                    pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                    pendings = self.env['pending.actions'].create(pending_vals)

                                                    approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                                    pendings.write({'email': approve_users_emails})

                                                    activity_type = self.env['mail.activity.type'].sudo().search(
                                                        [('name', '=', 'Pending Request')], limit=1)
                                                    activity_type_id = activity_type.id if activity_type else False
                                                    res_model_id = self.env['ir.model'].sudo().search(
                                                        [('model', '=', 'tenders')]).id
                                                    for user_id in user_ids_to_pass:
                                                        activity_values = {
                                                            'user_id': user.id,
                                                            'res_id': self.id,
                                                            'summary': "Action",
                                                            'note': "Pending Action",
                                                            'activity_type_id': activity_type_id,
                                                            'res_model_id': res_model_id,
                                                        }
                                                        with self.env.cr.savepoint():
                                                            self = self.with_context(mail_activity_quick_update=True)
                                                            created_activity = self.env['mail.activity'].create(
                                                            activity_values)
                                                    subject = "New Contract Request Created: %s" % self.name
                                                    # body = "A new contract request with the name %s has been created." % result.name

                                                    base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                        'web.base.url')
                                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                                        [('name', '=', 'Contracts/Agreements')], limit=1) or False

                                                    url_params = {
                                                        'id': self.id,
                                                        'action': self.env.ref(
                                                            'product_purchase.action_tender_status').id,
                                                        'model': 'tenders',
                                                        'view_type': 'form',
                                                        'menu_id': menu_id.id if menu_id else False,
                                                    }

                                                    params = '/web?#%s' % url_encode(url_params)
                                                    url = base_url + params if base_url else "#"

                                                    print(url)
                                                    body = (
                                                        f"Dear User, A new contract request {self.name} waiting for Approval .<br><br>"
                                                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                                                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                                    )
                                                    # email_to_list = [user.email if user.email else user.login for user
                                                    #                  in buyer_users]
                                                    author = self.env['res.partner'].sudo().search(
                                                        [('name', '=', 'Administrator')], limit=1)

                                                    if author:
                                                        mail_values = {
                                                            'subject': subject,
                                                            'body_html': body,
                                                            'email_to': user.login,
                                                            'auto_delete': False,
                                                            'author_id': author.id
                                                        }
                                                        mail_record = self.env['mail.mail'].sudo().create(mail_values)

                                    except:
                                        print("pass")
                                        pass
                                    if flag:
                                        break

    
    def action_legal_approval(self):
        self.write({'legal_approved_users': [(4, self.env.user.id)]})
        approve_users = self.env['tender.legal.approve.line'].sudo().search(
            [('approve_tender_legal_id', '=', self.id), ('user_id', '=', self.env.user.id)], )

        approve_users.write({
            'status': 'approve'
        })

        if self.legal_approved_users == self.legal_approve_users:

            # if not self.company_ids:
            #     self.message_post(body=f"{self.env.user.name} Rejected the Purchase Request.")
            self.state = 'approve'
            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close", rec)
                    rec.status = 'closed'
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                activity.action_feedback(feedback="Approved")
        else:
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close", rec)
                    rec.status = 'closed'

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("Complete")
                print(activity.id)
                activity.action_feedback(feedback="Approved")

            approve_users = self.env['tender.legal.approve.line'].sudo().search([('approve_tender_legal_id', '=', self.id)],
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
            self.legal_next_approve_user -= record_to_remove

            if not self.legal_next_approve_user:
                for order in order_list:
                    for order_list_users in approve_dict[order]:
                        if self.env.user.id == order_list_users['u_id']:
                            try:
                                if approve_dict[order + 1]:
                                    for users in approve_dict[order + 1]:
                                        self.write({'legal_next_approve_user': [(4, users['u_id'])]})

                                        for user in self.legal_next_approve_user:
                                            model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                       limit=1)
                                            print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
                                            pending_vals = {
                                                'model': model.id,
                                                'name': self.name + " " + "Waiting For Approval",
                                                'department_id': self.department_id.id,
                                                'exp_category': self.exp_category.id,
                                                'Created_doc_date': self.requested_date,

                                                'record': self.id,
                                                'date': date.today(),
                                            }
                                            if user:
                                                user_ids_to_pass = user.ids
                                                if self.branch_ids:
                                                    first_branch_id = self.branch_ids[0].id
                                                    pending_vals['branch'] = first_branch_id
                                                pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                pendings = self.env['pending.actions'].create(pending_vals)
                                                approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                                pendings.write({'email': approve_users_emails})

                                                activity_type = self.env['mail.activity.type'].sudo().search(
                                                    [('name', '=', 'Pending Request')], limit=1)
                                                activity_type_id = activity_type.id if activity_type else False
                                                res_model_id = self.env['ir.model'].sudo().search(
                                                    [('model', '=', 'tenders')]).id
                                                for user_id in user_ids_to_pass:
                                                    activity_values = {
                                                        'user_id': user.id,
                                                        'res_id': self.id,
                                                        'summary': "Action",
                                                        'note': "Pending Action",
                                                        'activity_type_id': activity_type_id,
                                                        'res_model_id': res_model_id,
                                                    }
                                                    with self.env.cr.savepoint():
                                                        self = self.with_context(mail_activity_quick_update=True)
                                                        created_activity = self.env['mail.activity'].create(
                                                            activity_values)
                                                subject = "New Contract Request Created: %s" % self.name
                                                # body = "A new contract request with the name %s has been created." % result.name

                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Contracts/Agreements')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref(
                                                        'product_purchase.action_tender_status').id,
                                                    'model': 'tenders',
                                                    'view_type': 'form',
                                                    'menu_id': menu_id.id if menu_id else False,
                                                }

                                                params = '/web?#%s' % url_encode(url_params)
                                                url = base_url + params if base_url else "#"

                                                print(url)
                                                body = (
                                                    f"Dear User, A new contract request {self.name} waiting for Approval .<br><br>"
                                                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                                )
                                                # email_to_list = [user.email if user.email else user.login for user
                                                #                  in buyer_users]
                                                author = self.env['res.partner'].sudo().search(
                                                    [('name', '=', 'Administrator')], limit=1)

                                                if author:
                                                    mail_values = {
                                                        'subject': subject,
                                                        'body_html': body,
                                                        'email_to': user.login,
                                                        'auto_delete': False,
                                                        'author_id': author.id
                                                    }
                                                    mail_record = self.env['mail.mail'].sudo().create(mail_values)

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
                                                self.write({'legal_next_approve_user': [(4, users['u_id'])]})
                                                flag = 1
                                                print("hellooooooooooooooooooooooooooooooooo")

                                            for user in self.legal_next_approve_user:
                                                model = self.env['ir.model'].sudo().search(
                                                    [('model', '=', self._name)],
                                                    limit=1)
                                                print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
                                                pending_vals = {
                                                    'model': model.id,
                                                    'name': self.name + " " + "Waiting For Approval",
                                                    'department_id': self.department_id.id,
                                                    'exp_category': self.exp_category.id,
                                                    'Created_doc_date': self.requested_date,

                                                    'record': self.id,
                                                    'date': date.today(),
                                                }
                                                if user:
                                                    user_ids_to_pass = user.ids
                                                    if self.branch_ids:
                                                        first_branch_id = self.branch_ids[0].id
                                                        pending_vals['branch'] = first_branch_id
                                                    pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                    pendings = self.env['pending.actions'].create(pending_vals)
                                                    approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                                    pendings.write({'email': approve_users_emails})

                                                    activity_type = self.env['mail.activity.type'].sudo().search(
                                                        [('name', '=', 'Pending Request')], limit=1)
                                                    activity_type_id = activity_type.id if activity_type else False
                                                    res_model_id = self.env['ir.model'].sudo().search(
                                                        [('model', '=', 'tenders')]).id
                                                    for user_id in user_ids_to_pass:
                                                        activity_values = {
                                                            'user_id': user.id,
                                                            'res_id': self.id,
                                                            'summary': "Action",
                                                            'note': "Pending Action",
                                                            'activity_type_id': activity_type_id,
                                                            'res_model_id': res_model_id,
                                                        }
                                                        with self.env.cr.savepoint():
                                                            self = self.with_context(
                                                                mail_activity_quick_update=True)
                                                            created_activity = self.env['mail.activity'].create(
                                                                activity_values)
                                                    subject = "New Contract Request Created: %s" % self.name
                                                    # body = "A new contract request with the name %s has been created." % result.name

                                                    base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                        'web.base.url')
                                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                                        [('name', '=', 'Contracts/Agreements')], limit=1) or False

                                                    url_params = {
                                                        'id': self.id,
                                                        'action': self.env.ref(
                                                            'product_purchase.action_tender_status').id,
                                                        'model': 'tenders',
                                                        'view_type': 'form',
                                                        'menu_id': menu_id.id if menu_id else False,
                                                    }

                                                    params = '/web?#%s' % url_encode(url_params)
                                                    url = base_url + params if base_url else "#"

                                                    print(url)
                                                    body = (
                                                        f"Dear User, A new contract request {self.name} waiting for Approval .<br><br>"
                                                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                                                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                                    )
                                                    # email_to_list = [user.email if user.email else user.login for user
                                                    #                  in buyer_users]
                                                    author = self.env['res.partner'].sudo().search(
                                                        [('name', '=', 'Administrator')], limit=1)

                                                    if author:
                                                        mail_values = {
                                                            'subject': subject,
                                                            'body_html': body,
                                                            'email_to': user.login,
                                                            'auto_delete': False,
                                                            'author_id': author.id
                                                        }
                                                        mail_record = self.env['mail.mail'].sudo().create(
                                                            mail_values)

                                    except:
                                        print("pass")
                                        pass
                                    if flag:
                                        break
        


        
    class PrApproveLine(models.Model):
        _name = "tender.approve.line"
        _description = "Tender Approve Line"
        _order = 'approve_order asc'

        tender_id = fields.Many2one('tenders', string='Product Request Id',
                                    invisible=True)

        user_id = fields.Many2one('res.users', string="User")
        company_id = fields.Many2one('res.company', string="Company")
        location = fields.Many2one('res.company', string="Location")
        branch_id = fields.Many2one("res.branch","Branch")
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

    class LeaseApprovelegalLine(models.Model):
        _name = "tender.legal.approve.line"
        _description = "Approve Legal Lines"
        _order = 'approve_order asc'

        approve_tender_legal_id = fields.Many2one('tenders', string='Tender Approve',
                                           invisible=True)

        user_id = fields.Many2one('res.users', string="User")
        company_id = fields.Many2one('res.company', string="Company")
        location = fields.Many2one('res.company', string="Location")
        department_id = fields.Many2one('hr.department', string="Department")
        emp_name = fields.Many2one('hr.employee', string="Employee")
        designation = fields.Many2one('hr.job', string="Designation")
        approve_order = fields.Integer(string="Order")
        status = fields.Selection(
            selection=[('draft', 'Draft'), ('approve', 'Approved'), ('cancel', 'Cancel'), ('deligate', 'Deligated')],
            string='Status',
            default='draft',
            required=True, tracking=True
        )



    class ContractRequestLine(models.Model):
        _name = "contract.request.lines"
        _rec_name = "product_id"
        contracts_lines = fields.Many2one('tenders', string='Contract Request')

        product_id = fields.Many2one('product.template', string='Product')
        description = fields.Char(string="Description")
        brand = fields.Char('Brand', related='product_id.brand')
        oem = fields.Char('OEM', related='product_id.oem')
        uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_po_id')
        pack = fields.Float('Pack Size', related='product_id.pack_size')
        quantity = fields.Float(string='Quantity')
        avg_quantity_period = fields.Float(string='Contract Period Avg Qty',compute='_compute_avg_quantity_period')
        unit_price = fields.Float(string='Unit Price',digits=(16, 4))
        suggested_unit_price = fields.Float(string="Suggested Unit Price" ,store=True ,force_save=True)
        vendor_price = fields.Float(string="Vendor Pricing" ,store=True ,force_save=True)
        product_group = fields.Char("Product Group")
        total_vendor_price = fields.Float(string="Total Vendor Pricing" ,store=True ,compute='_compute_total_vendor_price')

        vendor = fields.Many2one("res.partner","Vendor",related='contracts_lines.vendor_id', store=True)
        payment_terms = fields.Many2one('account.payment.term', "Payment Terms",related='contracts_lines.payment_terms')
        lead_time = fields.Integer("Lead Time in days", related='contracts_lines.lead_time')
        terms = fields.Text(string='Terms & Conditions',related='contracts_lines.terms')
        selected_line = fields.Boolean("Line Selected")
        smallest = fields.Float(string="Smallest Pricing")
        second_smallest = fields.Float(string="Second Smallest Pricing")
        status = fields.Selection([('select', 'Product Shortlisted'),
                                            ('reject', 'Product Not Shortlisted'),
                                            ], string='Comparison Status',
                                           tracking=True)
        related_branch = fields.Many2one('res.branch', string="Bill To", compute='_compute_related_branch',store=True)

        available_branch_ids = fields.Many2many(
            'res.branch',
            compute='_compute_available_branch_ids',
            store=False, 
            string="Available Branches"
        )

        branch_ids = fields.Many2many(
            'res.branch',
            string="Branches",
            domain="[('id', 'in', available_branch_ids)]"
        )

        previous_rate = fields.Float(
            string="Previous Rate",
            related="product_id.list_price",
            store=True  
        )

        cost_analysis = fields.Float(
            string="Cost Analysis",
            compute="_compute_cost_analysis",
            store=True
        )
        pr_rate = fields.Float(
            string="Previous Rate",
            compute="_compute_previous_rate",
            store=True
        )


        billing_price = fields.Float(
            string="Billing price",
            store=True
        )

        difference_analysis = fields.Float(string="Difference Analysis")
        percentage_analysis = fields.Float(string="Percentage Analysis")

        @api.depends('product_id', 'contracts_lines.branch_ids')
        def _compute_previous_rate(self):
            for line in self:
                line.pr_rate = 0.0
                print("the rate", line.product_id, line.contracts_lines.branch_ids)
                if not line.product_id or not  line.contracts_lines.branch_ids:
                    line.pr_rate = 0.0
                    continue


                tender_lines = self.env['product.tender.line'].search([
                    # ('vendor', '=', line.contracts_lines.vendor_id.id),
                    ('branch_ids', 'in', line.contracts_lines.branch_ids.ids),
                    # ('status', '=', 'active'),  # Include only active tenders
                ])

                previous_rate = 0.0
                for contract in tender_lines:
                    duplicate = contract.product_product_line.filtered(lambda p: p.product_id.id == line.product_id.id)
                    if duplicate:
                        sorted_lines = duplicate.sorted(key=lambda p: p.create_date, reverse=True)
                        if sorted_lines:
                            previous_rate = sorted_lines[0].unit_price
                line.pr_rate = previous_rate
                # print("The most recent rate for", line.product_id.name, "is", previous_rate)

                # for contract in tender_lines:
                #     print("con", contract.product_product_line)

                #     duplicate = contract.product_product_line.filtered(lambda p: p.product_id.id == line.product_id.id)

                #     print("the duplicate product is",duplicate)
                #     sorted_lines = duplicate.sorted(key=lambda p: p.create_date, reverse=True)
                #     if sorted_lines:
                #         previous_rate = sorted_lines[0].unit_price
                #         break

                #     print("the previous rate is",previous_rate)
                # line.pr_rate = previous_rate


        @api.depends('unit_price', 'pr_rate')
        def _compute_cost_analysis(self):
            for line in self:
                difference = 0.0
                percentage_change = 0.0

                if line.pr_rate and line.unit_price:
                    difference =  line.unit_price - line.pr_rate

                    if line.pr_rate != 0:
                        percentage_change = ((line.unit_price - line.pr_rate) / line.pr_rate) * 100
                    else:
                        percentage_change = 0.0

                # Store both the difference and percentage change in the cost analysis field
                # line.cost_analysis = {
                #     'difference': difference,
                #     'percentage': percentage_change
                # }

                # You can store these separately if you prefer to show them in separate fields
                line.difference_analysis = difference
                line.percentage_analysis = percentage_change

       
        # @api.depends('unit_price', 'previous_rate')
        # def _compute_cost_analysis(self):
        #     for line in self:
               
        #         if line.previous_rate and line.unit_price:
        #             line.cost_analysis = line.previous_rate - line.unit_price
        #         else:
        #             line.cost_analysis = 0.0

        @api.depends('contracts_lines')
        def _compute_available_branch_ids(self):
            for record in self:
              
                record.available_branch_ids = record.contracts_lines.branch_ids

        @api.depends('contracts_lines.product_requested_id')
        def _compute_related_branch(self):
            for record in self:
                if record.contracts_lines and record.contracts_lines.product_requested_id:
                    record.related_branch = record.contracts_lines.product_requested_id.bill_to
                else:
                    record.related_branch = False

        @api.depends('vendor_price','quantity')
        def _compute_total_vendor_price(self):
            for record in self:
                if record.vendor_price and record.quantity:
                    record.total_vendor_price = record.vendor_price * record.quantity
                else:
                    record.total_vendor_price = 0.0

        # def action_select_products(self):
        #     for record in self:
        #         record.selected_line = True
        #         record.status = 'select'
        #         print(record.contracts_lines.name)
        #
        # def action_remove_products(self):
        #     for record in self:
        #         record.selected_line = False
        #         record.status = 'reject'
        # @api.onchange('quantity','contracts_lines.to_date')
        # def _compute_avg_quantity_period(self):
        #     if self.contracts_lines.purchase_plan == 'monthly':
        #         print("if working")
        #         try:
        #             contract_ids = str(self.contracts_lines.id).split('_')[1],
        #         except:
        #             contract_ids = self.contracts_lines.id
        #         contract_ids =int(contract_ids)
        #         if contract_ids:
        #             contract = self.env['tenders'].browse(contract_ids)
        #             print(contract)
        #             if contract.from_date and contract.to_date:
        #                 print("if working",contract.from_date,contract.to_date)
        #                 from_date = datetime.strptime(str(contract.from_date), '%Y-%m-%d')
        #                 to_date = datetime.strptime(str(contract.to_date), '%Y-%m-%d')
        #                 months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)
        #                 self.avg_quantity_period = self.quantity*(months+1)
        #
        #     else:
        #         self.avg_quantity_period = self.quantity

        def open_history(self):
            action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.action_price_history')
            action['context'] = {'default_product': self.product_id.id,
                                 'default_related_branch': self.related_branch.id,
                                 }
            print(self.related_branch)
            print(action)
            return action
        def action_create_contract_req(self):
            id_list = []  # SELECTED CONTRACTS LIST
            line_id_list = []  # SELECTED LINE ITEMS LIST
            for record in self:
                record.status = 'select'
                if record.contracts_lines.state in ('confirm', 'approve', 'cancel'):
                    raise UserError("Selected Contract Requested is not in a Updatable state")

            # tender_ids = self.env['tenders'].search([('main_rfq', '=', self.contracts_lines.main_rfq.id)])
            # if tender_ids:
            #     model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
            #     for rec in tender_ids:

            #         pending_action = self.env['pending.actions'].sudo().search(
            #             [('model', '=', model.id), ('record', '=', rec.id), ('status', '=', 'open')], limit=1)

            #         if pending_action:
            #             for ids in pending_action:
            #                 ids.status = 'closed'

                # if not (record.selected_line == True):
                #     raise UserError("Please Select added products")

                # if record.product_id

                line_id_list.append(record.id)
                selected_contracts = self.env['tenders'].search([('contracts_request_line', '=', record.id)])
                if selected_contracts.id not in id_list:
                    id_list.append(selected_contracts.id)

                # ALL CONTRACT REQUEST LIST ################################
                contracts_in_compare = self.env['tenders'].search([('main_rfq', '=', record.contracts_lines.main_rfq.id)])
                contract_ids = contracts_in_compare.mapped('id')

                tender_ids = self.env['tenders'].search([('main_rfq', '=', self.contracts_lines.main_rfq.id)])
                if tender_ids:
                    model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                    for rec in tender_ids:

                        pending_action = self.env['pending.actions'].sudo().search(
                            [('model', '=', model.id), ('record', '=', rec.id), ('status', '=', 'open')], limit=1)

                        if pending_action:
                            for ids in pending_action:
                                ids.status = 'closed'

            all_line_id_list = []
            for contract_id in contract_ids:
                contract_lines = self.env['contract.request.lines'].search([('contracts_lines', '=', contract_id)])
                for line in contract_lines:
                    all_line_id_list.append(line.id)

            # print(all_line_id_list, "ALL CONTRACT LINES")
            # print(line_id_list, "SELECTED CONTRACT LINES")

            ############## REMOVE LINE ITEM NOT SELECTED #################

            difference_ids = list(set(all_line_id_list) - set(line_id_list))
            # print(difference_ids)
            if difference_ids:
                for id in difference_ids:
                    contract_lines_to_remove = self.env['contract.request.lines'].search([('id', '=', id)])
                    print(contract_lines_to_remove.id)
                    contract_lines_to_remove.unit_price = 0.00
                    # contract_lines_to_remove.quantity = 0.00
                    contract_lines_to_remove.status = 'reject'

            ############## REMOVE CONTRACT NOT SELECTED #################

            difference_id = list(set(contract_ids) - set(id_list))
            # print(difference_id)
            if difference_id:
                for id in difference_id:
                    contract_request_to_cancel = self.env['tenders'].search([('id', '=', id)])
                    # print(contract_request_to_cancel.name)
                    contract_request_to_cancel.state = 'cancel'
                    contract_request_to_cancel.contract_id.state = 'expire'

            if id_list:
                for id in id_list:
                    contract_to_review = self.env['tenders'].search([('id', '=', id)])
                    if contract_to_review:
                        contract_to_review.action_review_request()

            


            # for items in contract_ids:
            #     all_contracts = self.env['tenders'].search([('id', '=', items)])
            #
            #     print(all_contracts)

                # for unique_name in all_tender:
                # print(unique_tendor_names)

                # selected_ids = self.env.context.get('active_ids', [])
                # selected_records = self.env['contract.request.lines'].browse(selected_ids)
                # for recs in selected_records:
                #     print(recs.contracts_lines.name)

                # vendor = record.vendor
                # # Check if there's an existing tender with the same vendor
                # existing_tender = self.env['tenders'].search([('vendor_id', '=', vendor.id),('compared','=',True)], limit=1)
                #
                # if existing_tender:
                #     print(existing_tender.name)
                #     # Update existing tender with new line items
                #     contract_request_line = {
                #         'contracts_request_line': [(0, 0, {
                #             'product_id': record.product_id.id,
                #             'quantity': record.quantity,
                #             'unit_price': record.unit_price,
                #             'product_group': record.product_group,
                #         })],
                #     }
                #     existing_tender.write(contract_request_line)
                # else:
                #     # Create a new tender
                #     contract_request_vals = {
                #         'contracting_method': 'nego',
                #         'compared': True,
                #         'vendor_id': vendor.id,
                #         'from_date': record.contracts_lines.from_date,
                #         'to_date': record.contracts_lines.to_date,
                #         'expense_type': record.contracts_lines.expense_type,
                #         'lead_time': record.contracts_lines.lead_time,
                #         'payment_terms': record.contracts_lines.payment_terms.id,
                #         'requested_date': record.contracts_lines.requested_date,
                #         'user_id': record.contracts_lines.user_id.id,
                #         'company_ids': [(6, 0, record.contracts_lines.company_ids.ids)],
                #         'branch_ids': [(6, 0, record.contracts_lines.branch_ids.ids)],
                #         'terms': record.contracts_lines.terms,
                #         'main_rfq': record.contracts_lines.id,
                #         'product_requested_id': record.contracts_lines.product_requested_id.id,
                #         'contracts_request_line': [(0, 0, {
                #             'product_id': record.product_id.id,
                #             'quantity': record.quantity,
                #             'unit_price': record.unit_price,
                #             'product_group': record.product_group,
                #         })],
                #     }
                #     self.env['tenders'].create(contract_request_vals)

    class LogMessage(models.TransientModel):
        _name = "log.message.cr.wizard"
        _description = "Log"

        tenders_id = fields.Many2one(
            'tenders', string='Tenders', readonly=True)
        message = fields.Text("Message")
        user = fields.Many2one('res.users', "Requested By", default=lambda self: self.env.user.id,readonly=True)
        # user_ids = fields.Many2many('res.users', "To")
        to_users = fields.Many2many('res.users', 'log_message_cr_users_rel', 'log_message_id', 'res_users_id',
                                    "Requested_To", domain=lambda self: self._domain_to_users(), required=True)
        # user_from = fields.Many2many('res.users', "User_From", domain="[('groups_id', 'not in', [44])]", required=True)
        branch_id = fields.Many2many('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')
        email = fields.Char(string='Email', compute='_compute_email')
        cc_email = fields.Char(string='Email', compute='_compute_cc_email')
        user_cc = fields.Many2many('res.users', 'log_message_cc_cr_users_rel', 'log_message_cc_id', 'res_users_cc_id',
                                   "Cc", domain=lambda self: self._domain_user_cc())
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
            print("helloo")
            for rec in self.tenders_id.pr_rfi_ids_cr:
                if not rec.replay:
                    raise UserError(_("Already Request for Information Pending for Reply"))
            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)

            pending_action_ids = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.tenders_id.id), ('status', '=', 'open')])
            print("the pending actions are", pending_action_ids)
            for pending_action in pending_action_ids:
            #     pending_action.status = 'closed'
                new_name = f"{self.tenders_id.name} Waiting for Request for Information Reply"
                pending_action.sudo().write({'name': new_name,'date': date.today()})

            for request in self.tenders_id:
                if self.user and self.message:
                    body = (
                        f"{self.env.user.name} has logged a message in {self.tenders_id.name}.{self.message}"
                    )
                    base_url = self.env['ir.config_parameter'].sudo().get_param(
                        'web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Contracts/Agreements')], limit=1) or False

                    url_params = {
                        'id': self.tenders_id.id,
                        'action': self.env.ref(
                            'product_purchase.action_tender_status').id,
                        'model': 'tenders',
                        'view_type': 'form',
                        # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                        'menu_id': menu_id.id if menu_id else False,
                    }
                    params = '/web?#%s' % url_encode(url_params)
                    view_url = base_url + params if base_url else "#"
                    print(view_url)
                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)
                    vals = {
                        'subject': f"Logged a message in {self.tenders_id.name}",
                        'body_html': body,
                        'email_to': ', '.join(self.to_users.mapped('login')),
                        'email_cc': self.cc_email,
                        'author_id': author.id
                    }
                    mail_id = self.env['mail.mail'].sudo().create(vals)
                    mail_id.sudo().send()

                    ### Query Raised against CTR , Notified the approvers
                    subject = "Query was raised against Contract Request : %s" % self.tenders_id.name

                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)

                    body = (
                        f"Dear User, "
                        f"A Contract Request with the name <strong>{self.tenders_id.name} is Pending at Request For Information where you are "
                        f"a approver.<br>"

                    )
                    if self.tenders_id.state == 'confirm':
                        for user in self.tenders_id.tender_approve_line:
                            if self.env.user.id != user.id and user.status == 'approve':

                                mail_values = {
                                    'subject': subject,
                                    'body_html': body,
                                    'email_to': user.user_id.login,
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)

                        self.sudo().tenders_id.message_post(body=f"<strong>@{self.user.name}</strong>, {self.message}")
                        for user in self.to_users:
                            rfi_vals = {
                                'user_id': self.env.user.id,
                                'to_user': user.id,
                                'message': self.message,
                                # 'user_id':self.env.user.id,
                                'next_pending_ids_cr': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False
                            }

                            new_rfi_vals = self.env['pr.rfi.line.cr'].sudo().create(rfi_vals)
                            self.tenders_id.pr_rfi_ids_cr |= new_rfi_vals

                            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                            pending_vals = {
                                'model': model.id,
                                'name': "Request For Information" + " " + "on" + " " + self.tenders_id.name,
                                'record': self.tenders_id.id,
                                'department_id': self.tenders_id.department_id.id,
                                'exp_category': self.tenders_id.exp_category.id,
                                'Created_doc_date': self.tenders_id.requested_date,

                                'date': date.today(),
                                'record_line': new_rfi_vals.id,
                                'approve_users': [(6, 0, [user.id])],
                            }
                            if self.tenders_id.branch_ids:
                                first_branch_id = self.tenders_id.branch_ids[0].id
                                pending_vals['branch'] = first_branch_id
                            pendings = self.env['pending.actions'].sudo().create(pending_vals)
                            approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                            pendings.write({'email': approve_users_emails})
                        request.state = 'rfi'
                    if self.tenders_id.state == 'legal_approve':
                        for user in self.tenders_id.legal_approve_line:
                            if self.env.user.id != user.id and user.status == 'approve':
                                mail_values = {
                                    'subject': subject,
                                    'body_html': body,
                                    'email_to': user.user_id.login,
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)

                        self.sudo().tenders_id.message_post(body=f"<strong>@{self.user.name}</strong>, {self.message}")
                        for user in self.to_users:
                            rfi_vals = {
                                'user_id': self.env.user.id,
                                'to_user': user.id,
                                'message': self.message,
                                # 'user_id':self.env.user.id,
                                'legal': True,
                                'next_pending_ids_cr': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False
                            }

                            new_rfi_vals = self.env['pr.rfi.line.cr'].sudo().create(rfi_vals)
                            self.tenders_id.pr_rfi_ids_cr |= new_rfi_vals

                            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                            pending_vals = {
                                'model': model.id,
                                'name': "Request For Information" + " " + "on" + " " + self.tenders_id.name,
                                'record': self.tenders_id.id,
                                'department_id': self.tenders_id.department_id.id,
                                'exp_category': self.tenders_id.exp_category.id,
                                'Created_doc_date': self.tenders_id.requested_date,

                                'date': date.today(),
                                'record_line': new_rfi_vals.id,
                                'approve_users': [(6, 0, [user.id])],
                            }
                            if self.tenders_id.branch_ids:
                                first_branch_id = self.tenders_id.branch_ids[0].id
                                pending_vals['branch'] = first_branch_id
                            pendings = self.env['pending.actions'].sudo().create(pending_vals)
                            approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                            pendings.write({'email': approve_users_emails})
                        request.state = 'rfi'
            pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id),('name', 'not like', 'waiting for Request for Information reply')], order='id desc', limit=1)
            print("if,,,,,,,,,..pending actions", pending)
            if pending:
                print("if")
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

                return action

    class PrRfiLine(models.Model):
        _name = "pr.rfi.line.cr"
        _description = "RFI Line"

        cr_id = fields.Many2one('tenders', string='Contract Request Id',
                                invisible=True)

        user_id = fields.Many2one('res.users', string="From")
        to_user = fields.Many2one('res.users', string="To")
        message = fields.Char("Message")
        replay = fields.Char("Reply")
        replayed = fields.Boolean("Is Replyed")
        status = fields.Selection(
            selection=[('open', 'Open'), ('close', 'Closed')],
            string='Status',
            default='open',
            required=True, tracking=True
        )
        is_to_user_id = fields.Boolean(default=False, compute='_get_current_user_details')
        next_pending_ids_cr = fields.Many2many(
            comodel_name='pending.actions',
            string='Pending Action',
            relation='last_pend_cr',
            column1='cr_rfi_lease_id',
            column2='pending_actions_id_cr',
            store=True
        )
        legal = fields.Boolean("IS LE")
        attachment_ids = fields.Many2many(
            'ir.attachment', string="Attachments")
        attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')

        @api.depends('attachment_ids')
        def _compute_attachment_number(self):
        
            attachment_count = {}
        
            for request in self:
                domain = [('res_model', '=', 'pr.rfi.line.cr'), ('res_id', '=', request.id)]
            
                attachment_data = self.env['ir.attachment'].read_group(domain, ['res_id'], ['res_id'])
           
                attachment_count[request.id] = attachment_data[0]['res_id_count'] if attachment_data else 0

     
            for request in self:
                request.attachment_number = attachment_count.get(request.id, 0)

        
        def open_attachments(self):
            self.ensure_one()
            res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
            # Retrieve the list of attachment IDs
            attachment_ids = self.attachment_ids.ids  # Get the IDs of the attachments
            print("the attachment id is",attachment_ids)
            res['domain'] = [('res_model', '=', 'pr.rfi.line.cr'), ('res_id', '=', self.id)]
            res['context'] = {'default_res_model': 'pr.rfi.line.cr', 'default_res_id': self.id}
            return res

        @api.depends('to_user', 'replayed')
        def _get_current_user_details(self):
            current_user_id = self.env.user.id
            for record in self:
                if record.to_user.id == current_user_id and not record.replayed:
                    record.is_to_user_id = True
                else:
                    record.is_to_user_id = False
                print("The user is", record.is_to_user_id)
        # def send_replay(self):
        #     action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_replay_cr_action')
        #     action['context'] = {'default_message_id': self.id}
        #     return action
        def send_replay(self):
            unreplied_rfi_record = self.filtered(lambda r: not r.replayed and r.to_user.id == self.env.user.id)
            if unreplied_rfi_record:
                action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_replay_cr_action')
                action['context'] = {'default_message_id': self.id, 'default_message': unreplied_rfi_record.message}
                return action

    class LogMessageReplay(models.TransientModel):
        _name = "message.replay.cr.wizard"
        _description = "Log"

        message_id = fields.Many2one(
            'pr.rfi.line.cr', string='Reply', readonly=True)
        message = fields.Char(string="Message", readonly=True)
        replay = fields.Text("Reply", required=True)
        attachment_ids = fields.Many2many(
            'ir.attachment', string="Attachments")

        def confirm(self):
            
            # pending_ids = self.env['pending.actions'].sudo().search([('id', '=', self.message_id.next_pending_ids_cr.ids)])
            # print('first', pending_ids)
            # for pending_action in pending_ids:
            #     # Create a copy of the pending action record
            #     print("Reply next pending",pending_action)
            #     new_action = pending_action.copy()
            #     print("new action",new_action)
            #     new_action.sudo().write({
            #         'date':date.today(),
            #         'status': 'open',
            #         'name': "Replay for RFI" + " " + "for" + " " + self.message_id.cr_id.name,
            #     })
            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
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
                    print("the new ",new_attachments)
                    for attachment in new_attachments:
                        attachment.write({'res_model': 'pr.rfi.line.cr', 'res_id': line.id})

                    line.attachment_ids = new_attachments
                    attachment_ids_to_post = [attachment.id for attachment in self.attachment_ids]
                    print("test post",attachment_ids_to_post)
                else:
                    attachment_ids_to_post = []

                line.cr_id.message_post(
                    body=f"<strong>@{self.env.user.name}</strong>, Replied: {self.replay}, to {line.user_id.name}",
                    attachment_ids=attachment_ids_to_post 
                )

            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
            print(model.id)
            print(self.message_id.id)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.message_id.cr_id.id),('status', '=', 'open')])


            all_record_lines_replayed = all(line.replay for line in self.message_id.cr_id.pr_rfi_ids_cr)

            if all_record_lines_replayed:
                if self.message_id.legal == True:
                    self.message_id.cr_id.state = 'legal_approve'
                else:
                    self.message_id.cr_id.state = 'confirm'
                for pending_action in pending_action:
                    print("all are approved")
                    print("mesg",self.message_id.cr_id.name)
                    # pending_action.status = 'closed'
                    new_name = f"{self.message_id.cr_id.name} --Replied for Request for Information "
                    pending_action.sudo().write({'name': new_name, 'date': date.today()})
                # If all record lines have their 'replay' column filled, change the status to 'requested'
                # self.message_id.cr_id.state = 'confirm'
            pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id),('name', 'not like', 'waiting for Request for Information reply')], order='id desc', limit=1)
            
            if pending:
                
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

                
                return action


    class Remark(models.TransientModel):
        _name = "remark.cr"
        _description = "Remark"
        _inherit = ['mail.thread']

        from_user = fields.Many2one('res.users', string="Approval by")
        replay = fields.Char("Remark", required=True)
        cr_id = fields.Many2one('tenders', string='Contract Requests', readonly=True)
        cr_need = fields.Boolean("CR Need", default=False)
        approve_type = fields.Selection(
            selection=[('approve', 'Approved'), ('reject', 'Rejected')],
            string='State',

        )
        work_flow_type = fields.Selection(
            selection=[('tender', 'tender'), ('legal', 'legal')],
            string='Work Flow')

        def confirm_remark(self):
            print("workikkk")
            if self.cr_id and self.approve_type == 'approve' and self.work_flow_type == 'tender':
                print("workinggggggg...")
                self.sudo().cr_id.message_post(body=f" {self.env.user.name} Approved.")
                self.sudo().cr_id.message_post(body="Remarks " + self.replay)
                vals = {
                    'cr_id': self.cr_id.id,
                    'from_user': self.env.user.id,
                    'replay': self.replay,
                    'for_type': "Purchase Request",
                    'approve_type': 'approve',

                }
                remarks_save = self.env['remark.save.cr'].create(vals)
                self.cr_id.action_approval()
                pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
                print("if,,,,,,,,,..pending actions", pending)
                if pending:
                    print("if")
                    return pending.open_record()
                else:
                    action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

                    print("elseeeeeeeee", action)
                    return action
            if self.cr_id and self.approve_type == 'reject' and self.work_flow_type == 'tender':
                self.sudo().cr_id.message_post(body=f" {self.env.user.name} Rejected.")
                self.sudo().cr_id.message_post(body="Remarks " + self.replay)
                vals = {
                    'cr_id': self.cr_id.id,
                    'from_user': self.env.user.id,
                    'replay': self.replay,
                    'for_type': "Purchase Request",
                    'approve_type': 'reject',

                }
                remarks_save = self.env['remark.save.cr'].create(vals)
                self.cr_id.action_cancel()
                pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
                print("if,,,,,,,,,..pending actions", pending)
                if pending:
                    print("if")
                    return pending.open_record()
                else:
                    action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

                    print("elseeeeeeeee", action)
                    return action
            if self.cr_id and self.approve_type == 'approve' and self.work_flow_type == 'legal':
                print("workinggggggg...")
                self.sudo().cr_id.message_post(body=f" {self.env.user.name} Legal Team Approved.")
                self.sudo().cr_id.message_post(body="Remarks " + self.replay)
                vals = {
                    'cr_id': self.cr_id.id,
                    'from_user': self.env.user.id,
                    'replay': self.replay,
                    'for_type': "Purchase Request",
                    'approve_type': 'approve',

                }
                remarks_save = self.env['remark.save.cr'].create(vals)
                self.cr_id.action_legal_approval()
                pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
                print("if,,,,,,,,,..pending actions", pending)
                if pending:
                    print("if")
                    return pending.open_record()
                else:
                    action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

                    print("elseeeeeeeee", action)
                    return action

    class RemarkSave(models.Model):
        _name = "remark.save.cr"
        _description = "Remark"

        cr_id = fields.Many2one('tenders', string='Contract Requests', readonly=True)
        from_user = fields.Many2one('res.users', string="Approval by")
        replay = fields.Char("Remark", required=True)
        for_type = fields.Char("Approval Type")
        approve_type = fields.Selection(
            selection=[('approve', 'Approved'), ('reject', 'Rejected'),('deligate','Deligate')],
            string='State')

    class RevertBack(models.Model):
        _name = 'revert.contract.back'
        _description = "Revert"

        tender_id = fields.Many2one(
            'tenders', string='Contract', readonly=True)
        reason = fields.Text("Message")
        revert_from = fields.Many2one(
            'res.users', string='Revert User')

    
    class ContractPriceHistory(models.Model):
        _name = "contract.price.history"
        _description = "Contract Total Price History"

        contract_id = fields.Many2one('tenders', string="Contract Request", required=True, ondelete='cascade')
        main_rfq = fields.Many2one('tenders', string="Main RFQ", ondelete='cascade')
        contract_request_id = fields.Many2one('contract', string="Vendor Contract Request", required=True, ondelete='cascade')
        total_price = fields.Float(string="Updated Total Vendor Price", required=True)
        vendor_id = fields.Many2one('res.partner', string="Vendor", required=True)
        date_updated = fields.Datetime(string="Date Updated", default=fields.Datetime.now, required=True)


