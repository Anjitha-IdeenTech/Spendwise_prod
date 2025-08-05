from datetime import datetime , timedelta
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo.tools.safe_eval import json
from odoo.http import request
from dateutil.relativedelta import relativedelta


from werkzeug.urls import url_encode
from collections import defaultdict


import logging

_logger = logging.getLogger(__name__)

class ProductLease(models.Model):
    _name = "product.lease"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Lease Request"

    name = fields.Char(string="Request No", readonly=True, required=True, copy=False, default='New')
    original_lease_id = fields.Many2one('product.lease', string='Original Lease')
    mail_send_reminder = fields.Boolean("Mail Send Reminder")
    renew_visible = fields.Boolean("Renew Visible", default=False)
    product_lease_request_line_ids = fields.One2many('product.lease.request.line',
                                               'product_lease_request_id',
                                               string='Product Request Line',
                                               tracking=True,required=True,ondelete='cascade')
    vendor_lease_request_line_ids = fields.One2many('vendor.lease.request.line',
                                                     'vendor_lease_request_id',
                                                     string='Vendor Request Line',
                                                     tracking=True,store=True,required=True,ondelete='cascade')



    requested_date = fields.Datetime(string="Date", default=datetime.today(), readonly=True)
    product_id = fields.Many2one('product.template',string="Product",domain="[('categ_id.name', '=', 'Lease/Rent')]")
    vendor_id = fields.Many2one('res.partner',string="Vendor")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', 'Requested By', default=lambda self: self.env.user, readonly=True)

    pending_action_update = fields.Many2many('log.message', string='Pending Actions Before RFI')

    product_uom = fields.Many2one("uom.uom", "UOM", related="product_id.uom_id")
    auto_po = fields.Boolean("Auto Generate PO",default = True , readonly = True)
    auto_invoice = fields.Boolean("Auto Generate Invoice",default = True )
    with_gst = fields.Boolean("With Tax")
    tax = fields.Many2one("account.tax","Tax")
    upload_po = fields.Binary("Upload Invoice")
    responsible_person = fields.Many2one('res.users',string="Responsible Person")

    revert_reason = fields.One2many('revert.lease.back',
                                    'lease_id',
                                    string='Revert Lease ReasonLine',
                                    tracking=True)

    pr_rfi_ids = fields.One2many('pr.lease.rfi',
                                 'lease_id',
                                 string='Product Request Line',
                                 tracking=True)
    
    is_to_user = fields.Boolean(compute='_compute_is_to_user', string='Is To User')

    remarks_ids = fields.One2many('remark.lease.save',
                                  'lease_id',
                                  string='Remark Line',
                                  tracking=True)


    state = fields.Selection(
        selection=[('draft', 'Draft'), ('request', 'Requested'), ('approve', 'Approved'),
                   ('reject', 'Rejected'),('expire', 'Expired'),('po','Purchase Order'),('rfi','Request for Information'),('revert','Revert'),('legal_approve','Legal Approve'),('renew','Renew'),('terminate','Terminate')],
        string='State',
        default='draft',
        required=True
    )
    approve_line = fields.One2many('lease.approve.line',
                                   'approve_lease_id',
                                   string='Lease Approve Line',
                                   tracking=True)
    legal_approve_line = fields.One2many('lease.legal.approve.line',
                                   'approve_lease_legal_id',
                                   string='Lease Legal Approve Line',
                                   tracking=True)

    reccuring_line = fields.One2many('lease.recurring.po',
                                   'recurring_lease_id',
                                   string='Lease Recurring Line',
                                   tracking=True)



    approve_users = fields.Many2many(
        'res.users',
        'rel_lease_apprvers',
        'lease_id',
        'users',
        string='Approve Users',
    )
    approved_users = fields.Many2many(
        'res.users',
        'approved_lease_relation',
        'lease_apprved',
        'user_id',
        string='Approved Users',
    )

    next_approve_user = fields.Many2many(
        'res.users',
        'next_aprved_lease',
        'next_lease',
        'users_id',
        string='Next Approver',)


    legal_approve_users = fields.Many2many(
        'res.users',
        'rel_lease_legal_apprvers',
        'lease_id',
        'users',
        string='Approve Users',
    )
    legal_approved_users = fields.Many2many(
        'res.users',
        'approved_legal_lease_relation',
        'lease_apprved',
        'user_id',
        string='Approved Users',
    )

    legal_next_approve_user = fields.Many2many(
        'res.users',
        'next_legal_aprved_lease',
        'next_lease',
        'users_id',
        string='Next Approver',)

    is_an_approver = fields.Boolean("Approver",compute='compute_is_an_approver')
    is_an_legal_approver = fields.Boolean("Approver",compute='compute_is_an_legal_approver')
    user_approved = fields.Boolean("Approved",compute='compute_approved_user')
    user_legal_approved = fields.Boolean("Approved", compute='compute_legal_approved_user')
    compute_state = fields.Boolean("State",compute='compute_states')
    product_request_id = fields.Many2one("product.request","Request",store=True)
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    qty = fields.Float("Quantity")
    price = fields.Float("Unit Price")
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True, readonly=True, default = 'op')
    location = fields.Char(string='Location', tracking=True)
    address1 = fields.Char(string='Address 1', tracking=True)
    address2 = fields.Char(string='Address 2', tracking=True)
    city = fields.Char(string='City', tracking=True)
    state_name = fields.Char(string='State', tracking=True)
    security = fields.Float(string='Security Deposit', tracking=True)
    terms = fields.Text("Terms & Conditions")
    # total_rent = fields.Float(string='Total Rent', tracking=True , compute="compute_total_rent")
    total = fields.Float(string="Total Amount", compute="compute_total_amount",tracking=True,required=True)
    deligated_user = fields.Many2one(
        'res.users', string='User Deligated', tracking=True, compute="_compute_user_id")

    increment_method = fields.Selection([
        ('year', 'Annually'),
        ('biennial', 'Biennially'),
        ('triennial', 'Triennially'),
        ('custom', 'Custom Date'),
    ], 'Increment Method')

    increment_amount = fields.Selection([
        ('total', 'Total'),
        ('custom', 'Custom Amount'),
    ], 'Increment Based On')

    increment_by = fields.Selection([
        ('amount', 'Amount'),
        ('percent', '%'),
    ], 'Increment By')
    inc_date = fields.Date("Increment Date", store = True)
    inc_value = fields.Float("Monthly Value" ,store = True)
    inc_period_value = fields.Float("Increment Period Value" ,store = True, compute='compute_inc_period_increment')
    inc_amount = fields.Float("Rate")
    total_increment_value = fields.Float("Amount Monthly Incremented", compute='compute_total_increment',store=True)
    is_increment = fields.Boolean("Increment", default=False)
    amount_payable = fields.Float("Total Amount Payable ")

    ############## Not in Use #############

    bill_to = fields.Many2one('res.branch', "Bill To")
    ship_to = fields.Many2one('res.branch', "Ship To")
    # expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True)
    product_lines = fields.One2many('lease.product.line',
                                    'lease_id',
                                    string='Product Lease Line',
                                    tracking=True)

    exp_category = fields.Many2one('expense.category','Expense Category',required=True)

    exp_category_domain = fields.Char(
        compute="_compute_exp_category_domain",
        readonly=True,
        store=False,
    )

    check_requested_by = fields.Boolean(string="User Requested check", compute="_compute_requested_by", default=False)


    vendor_user = fields.Many2many(
        'res.users',
        string='Vendor User',
        compute='_compute_corresponding_vendor_user',
        store=True,
    )

    auto_po_last_generated_date = fields.Date(
        string='Last Generated PO Date',
        help='Date of the last auto-generated purchase order for this lease',
        default=False
    )
    TDS = fields.Many2one("tds.master",string="TDS Amount")

    signed_copy = fields.Many2many('ir.attachment', 'class_ir_client_lease_rel', 'lease_id', 'attachment_id',
                                     'Signed Copy')

    agreement_copy = fields.Many2many('ir.attachment', 'class_ir_client_lease_rel_ag', 'lease_id', 'attachment_id',
                                     'Agreement Copy')
    main_remark = fields.Text(string="Remark")
    rent_free = fields.Boolean(string="Rent Free Period" , default=False)

    rent_free_start_date = fields.Date(string="Rent Free Start Date", compute="_compute_rent_free_start_date")
    rent_free_end_date = fields.Date(string="Rent Free End Date")

    lock_period = fields.Boolean(string="Lock Period", default=False)
    lock_start_date = fields.Date(string="Lock Period Start Date")
    lock_end_date = fields.Date(string="Lock Period End Date")
    lessee_period = fields.Char(string="Lessee Notice Period")
    lessor_period = fields.Char(string="Lessor Notice Period")
    termination_details = fields.Html(string="Termination Details")


    # @api.onchange('TDS')
    # def _compute_reduced_amount(self):
    #     if self.total > 1:
    #         total_amount = 0
    #         for total in self:
    #             for lines in total.product_lease_request_line_ids:
    #                 total_amount += lines.amount
    #         # print("total_amount ", total_amount)
    #         self.total = total_amount - self.TDS

    @api.depends('start_date', 'rent_free')
    def _compute_rent_free_start_date(self):
        for record in self:
            if record.rent_free:
                record.rent_free_start_date = record.start_date
            else:
                record.rent_free_start_date = False


    @api.depends('pr_rfi_ids')
    def _compute_is_to_user(self):
        current_user_id = self.env.user.id
        for record in self:
            record.is_to_user = any(not rfi.replayed and rfi.to_user.id == current_user_id for rfi in record.pr_rfi_ids)
            print("the user is", record.is_to_user)


    @api.constrains('product_lease_request_line_ids', 'vendor_lease_request_line_ids')
    def _check_lines(self):
        for record in self:
            if not record.product_lease_request_line_ids or not record.vendor_lease_request_line_ids:
                raise ValidationError("At least one product line or one vendor line must be added.")

    @api.depends('vendor_lease_request_line_ids')
    def _compute_corresponding_vendor_user(self):
        for record in self:
            if record.vendor_lease_request_line_ids:
                vendor_users = self.env['res.users'].sudo().search(
                    [('partner_id', 'in', record.vendor_lease_request_line_ids.mapped('vendor_id').ids)])
                record.vendor_user = vendor_users
            else:
                record.vendor_user = False

    @api.depends('vendor_lease_request_line_ids')
    def _compute_vendors(self):
        for record in self:
            vendors = record.vendor_lease_request_line_ids.mapped('vendor_id')
            record.vendor_id = [(6, 0, vendors.ids)]
            print("the field vendor",record.vendor_id)

    @api.depends('user_id')
    def _compute_requested_by(self):
        print("Inside requesed by check")
        current_user = self.env.user
        for record in self:
            print("check",record.user_id)
            print("check cu",current_user)
            if current_user == record.user_id:
                record.check_requested_by = True
            else:
                record.check_requested_by = False
            print("req", record.check_requested_by)

    def _compute_user_id(self):
        for rec in self:
            rec.deligated_user = self.env.user.id

    def search(self, args, offset=0, limit=None, order=None, count=False):
        _logger.debug("Search method called with arguments: %s", args)


        current_user = self.env.user
        _logger.debug("Current user: %s", current_user)


        return super(ProductLease, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.constrains('increment_method')
    def _check_increment_method(self):
        for record in self:
            if not record.increment_method:
                raise ValidationError("Increment (For the Auto invoice Generation) must be selected.")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                # if record.start_date < datetime.today().date():
                #     raise ValidationError("Start date must be greater than or equal to today's date.")
                print("the staert date",record.start_date,record.end_date)
                if record.end_date < record.start_date:
                    raise ValidationError("End date must be greater than start date.")

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

    # @api.depends('inc_amount', 'inc_value', 'increment_by')
    # def compute_total_increment(self):
    #     for record in self:
    #         print("the records are",record.total_increment_value)
    #         if record.inc_value and record.inc_amount and record.increment_by:
    #             print("the increments  check are",record.inc_value,record.inc_amount,record.increment_by)
    #             if record.increment_by == 'amount':
    #                 print("i am in amount")
    #                 record.total_increment_value = record.inc_amount + record.inc_value
    #                 print("the otl",record.total_increment_value)
    #             elif record.increment_by == 'percent':
    #                 percentage = record.inc_amount / 100
    #                 record.total_increment_value = record.inc_value + (record.inc_value * percentage)
    #
    #             else:
    #                 record.total_increment_value = 0
    #         else:
    #             record.total_increment_value = 0

    # @api.depends('total_increment_value', 'increment_method')
    # def compute_inc_period_increment(self):
    #     for record in self:
    #         if record.total_increment_value and record.increment_method:
    #             print("the increments are", record.increment_method, record.total_increment_value)
    #             if record.increment_method == 'year':
    #                 record.inc_period_value = record.total_increment_value * 12
    #             elif record.increment_method == 'biennial':
    #                 record.inc_period_value = record.total_increment_value * 24
    #                 print(record.inc_period_value)
    #             elif record.increment_method == 'triennial':
    #                 record.inc_period_value = record.total_increment_value * 36
    #             elif record.increment_method == 'custom' and record.inc_date:
    #                     today = date.today()
    #                     inc_date = record.inc_date
    #
    #                     # Since inc_date is always greater than today, ensure correct calculation
    #                     delta = relativedelta(inc_date, today)  # inc_date first since it is in the future
    #                     print("The delta is", delta)
    #                     months = delta.years * 12 + delta.months
    #                     print("The months are", months)
    #                     record.inc_period_value = record.total_increment_value * months
    #         else:
    #             if not record.total_increment_value:
    #                 record.total_increment_value = 0

    def action_lease_termination(self):
        if self.lock_period == True:
            today = date.today()
            if self.lock_start_date and self.lock_end_date:
                start_date = fields.Date.from_string(self.lock_start_date)
                end_date = fields.Date.from_string(self.lock_end_date)
                if start_date <= today <= end_date:
                    raise ValidationError("The Lease Agreement cannot be terminated because it is within the lock period.")

        print("kkkk")
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.termination_lease_action')
        action['context'] = {'default_lease_id': self.id}
        # self.status="terminate"
        return action

    def auto_lease_check(self):
        current_date = date.today()
        # leases = self.env['product.lease'].sudo().search([])
        leases = self.env['product.lease'].sudo().search(['|', ('state', '=', 'approve'), ('state', '=', 'legal_approve')])
        print("The leases are:", leases)

        for rec in leases:
            if rec.is_increment:
                if current_date >= rec.inc_date:
                    # if not rec.amount_payable:
                    #     rec.amount_payable = rec.total
                    if rec.is_increment:
                        new_inc_date = rec.inc_date
                        print("the new",new_inc_date)
                        if rec.increment_method == 'year':
                            new_inc_date += relativedelta(years=1)
                        elif rec.increment_method == 'biennial':
                            new_inc_date += relativedelta(years=2)
                        elif rec.increment_method == 'triennial':
                            new_inc_date += relativedelta(years=3)
                        elif rec.increment_method == 'custom':
                            new_inc_date = rec.inc_date
                        if new_inc_date <= rec.end_date:
                            rec.inc_date = new_inc_date
                            print("last",rec.inc_date)
                            incremented_value = sum(
                            line.total_increment_value for line in rec.product_lease_request_line_ids)
                            rec.total = incremented_value
                            print("Updated total:", rec.total)
                        for product_line in rec.product_lease_request_line_ids:

                            price_unit = product_line.total_increment_value/product_line.quantity

                            product_line.unit_price = price_unit

                            # rec.total = rec.total_increment_value
                            # print("the text",rec.total)
                            product_line.inc_value = product_line.amount
                            product_line.increment_by = product_line.increment_by
                            product_line.inc_amount = product_line.inc_amount
                            if product_line.increment_by == 'amount':
                                print("i am in amount")
                                product_line.total_increment_value = product_line.inc_amount + product_line.inc_value
                                print("the otl", rec.total_increment_value)
                            elif product_line.increment_by == 'percent':
                                percentage = product_line.inc_amount / 100
                                product_line.total_increment_value = product_line.inc_value + (product_line.inc_value * percentage)


    @api.constrains('inc_value')
    def _constrains_inc_value(self):
        for record in self:
            if record.inc_value and record.inc_value < record.total:
                raise ValidationError("The increment value must be greater than or equal to the total value.")

    @api.constrains('inc_date', 'end_date')
    def _constrains_inc_date(self):
        for record in self:
            if record.inc_date and record.end_date:
                if record.inc_date > record.end_date:
                    raise ValidationError("The increment date must be less than or equal to the end date.")

    @api.constrains('rent_free_start_date')
    def _constrains_inc_date(self):
        for record in self:
            if record.rent_free_start_date and record.start_date:
                if record.rent_free_start_date < record.start_date:
                    raise ValidationError("The Rent Free start date must be greater than or equal to the start date.")

    @api.constrains('rent_free_end_date')
    def _constrains_inc_date(self):
        for record in self:
            if record.rent_free_end_date and record.end_date:
                if record.rent_free_end_date > record.end_date:
                    raise ValidationError("The Rent Free End date must be less than or equal to the End date.")

    @api.onchange('start_date','increment_method')
    def onchange_increment_method(self):
        if self.start_date and self.increment_method == 'year':
            self.inc_date = self.start_date + relativedelta(years=1)
        if self.start_date and self.increment_method == 'biennial':
            self.inc_date = self.start_date + relativedelta(years=2)
        if self.start_date and self.increment_method == 'triennial':
            self.inc_date = self.start_date + relativedelta(years=3)
        if self.start_date and self.increment_method == 'custom':
            self.inc_date = ""

    @api.onchange('increment_amount','total','qty','price')
    def onchange_increment_amount(self):
        print("kkk")
        if self.increment_amount == 'total':
            print("hai")
            self.inc_value = self.total




    def _compute_attachment_number(self):
        domain = [('res_model', '=', 'product.lease'), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment'].read_group(domain, ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for request in self:
            request.attachment_number = attachment.get(request.id, 0)

    def action_generate_po(self):
        today = self.start_date


        last_day_of_month = today.replace(day=28) + timedelta(days=4)
        last_day_of_month = last_day_of_month - timedelta(days=last_day_of_month.day)

        remaining_days = (last_day_of_month - today).days
        print("the last day of month",last_day_of_month)

        print("the remaining days are", remaining_days)

        # Group product lines by vendor
        vendor_product_map = defaultdict(list)
        for vendor_line in self.vendor_lease_request_line_ids:
            for product_line in self.product_lease_request_line_ids:
                # product = product_line.product
                product = self.env['product.product'].sudo().search([('product_tmpl_id', '=', product_line.product.id)], limit=1)
                print("the product is",product)
                price_unit = 0.0
                if today < self.inc_date:
                    price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
                    price_unit = (price_units / last_day_of_month.day) * remaining_days
                else:
                    price_unit = self.total
                print("the unit price is",price_unit)
                vendor_product_map[vendor_line].append({
                    'product': product,
                    'price_unit': price_unit,
                    'quantity': product_line.quantity,
                    'uom_id': product.uom_po_id.id,
                })

        # Create purchase orders for each vendor
        for vendor_line, products in vendor_product_map.items():
            vendor = vendor_line.vendor_id
            print("the vendor is",vendor.name)
            percentage = vendor_line.percentage_of_amount
            total_amount = vendor_line.amount


            order_lines = []
            for product_data in products:
                product = product_data['product']
                order_lines.append((0, 0, {
                    'display_type': False,
                    'name': product.name or '',
                    'product_id': product.id,
                    'price_unit': product_data['price_unit'],
                    'product_qty': product_data['quantity'],
                    'product_uom': product_data['uom_id'],
                    'taxes_id': [(6, 0, [self.tax.id])] if self.tax else [],
                }))
                print("the order is",order_lines)
            purchase_order = self.env['purchase.order'].sudo().create({
                'partner_id': vendor.id,
                'order_line': order_lines,
                'company_id': self.company_id.id,
                'is_auto_po': True,  # Adjust based on your logic
                'lease_id': self.id,
                'expense_type': self.expense_type or '',
                'exp_category': self.exp_category.id or '',
                'department_id': self.department_id.id or '',
                'bill_to': self.bill_to.id,
                'ship_to': self.ship_to.id,
            })

            # Assuming auto_invoice is a boolean field on the lease
            if self.auto_invoice:
                purchase_order.button_confirm()
                for line in purchase_order.order_line:
                    line.qty_received = line.product_qty
                purchase_order.action_create_invoice()

            # Create a record in lease.recurring.po for tracking
            po_vals = {
                    'po': purchase_order.id,
                    'date': self.start_date,
                    'to_date': last_day_of_month,
                    'status': purchase_order.state,
                    'recurring_lease_id': self.id,
                    'vendor': vendor.id,
                    'amount':  purchase_order.amount_total,
                }
            self.env['lease.recurring.po'].sudo().create(po_vals)

        self.state = 'po'
        return True

    def action_open_attachments(self):
        print("kkkkkkkk")
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'product.lease'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'product.lease', 'default_res_id': self.id}
        return res




    # @api.depends('approved_users')
    # def compute_user_approved(self):
    #     for users in self.approved_users:
    #         if users in
    @api.onchange('state')
    def _onchange_state(self):
        for rec in self:
            print(rec)
        # if self.state == 'done':


    def check_expiration(self):
        today = date.today()
        lease = self.env['product.lease'].sudo().search([('state', 'in', ['legal_approve', 'approve'])])
        for rec in lease:
            print("i am inside the lease expire check",(rec.end_date - timedelta(days=30)))
            if rec.end_date and today >= rec.end_date:
                rec.state = 'expire'
            if rec.end_date and today >= (rec.end_date - timedelta(days=30)):
                print("expiredddddd")
                if rec.mail_send_reminder != True:
                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)

                    for vendor_line in rec.vendor_lease_request_line_ids:
                        body = f"Dear User, Your Lease Request for {rec.name} is going to expire in 30 days."
                        vals = {
                            'subject': 'Lease Agreement Expiring Soon',
                            'body_html': body,
                            'email_to': vendor_line.vendor_id.email,  # Assuming vendor_id is the field for the vendor
                            'auto_delete': False,
                            'email_cc': rec.user_id.login,
                            'author_id': author.id,
                        }
                        mail_id = self.env['mail.mail'].sudo().create(vals)
                        mail_id.sudo().send()
                    rec.mail_send_reminder = True
                    rec.renew_visible = True

                    buyer_group = self.env.ref(
                        'product_purchase.group_buyers')
                    buyer_users = buyer_group.users
                    if buyer_users:

                        ########### Creating Pending Actions

                        model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': rec.name + " " + "Lease Renew Date Approaching",
                            'record': rec.id,
                            'branch': rec.bill_to.id,

                            'date': date.today(),
                        }

                        buyer_group = self.env.ref('product_purchase.group_buyers')
                        buyer_users = buyer_group.users
                        if buyer_users:
                            user_ids = [user.id for user in buyer_users]
                            pending_vals['approve_users'] = [(6, 0, user_ids)]
                            pendings = self.env['pending.actions'].create(pending_vals)

                            rec.message_post(body="Lease Agreement Expiring in 30 days and Buyer's Notified")
                    else:
                        raise UserError("No User found on Buyer group")

    def copy(self, default=None):
        print("I am in copy")
        self.ensure_one()
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code('product.lease') or 'New'
        new_lease = super(ProductLease, self).copy(default)

        new_lease.original_lease_id = self.id

        # Copy product_lease_request_line_ids
        for line in self.product_lease_request_line_ids:
            print("Copying product lease request line:", line.product)
            line.copy({'product_lease_request_id': new_lease.id})

        # Copy vendor_lease_request_line_ids if needed
        # copied_vendor_lines = self.vendor_lease_request_line_ids.copy({'vendor_lease_request_id': new_lease.id})
        vendor_lines = self.vendor_lease_request_line_ids
        print("Total vendor lines to copy:", len(vendor_lines),vendor_lines)
        for line in vendor_lines:
            print("hi")
            line.vendor_copy = True
            new_line = line.copy({'vendor_lease_request_id': new_lease.id})
            print("Copied line ID:", new_line.id)
            line.vendor_copy = False
            new_line.vendor_copy = False
        print("what is this")

        new_lease.write({
            'approve_users': [(5, 0, 0)],
            'approved_users': [(5, 0, 0)],
            'next_approve_user': [(5, 0, 0)],

        })


        return new_lease

    def action_Modification(self):
        for lease in self:
            print("the lease is",lease)
            for line in lease.vendor_lease_request_line_ids:
                if not line.percentage_of_amount:
                    line.percentage_of_amount = 0.0
            new_lease=lease.copy()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.lease',
            'view_mode': 'form',
            'res_id': new_lease.id,
            'target': 'current',
        }

    def action_renew_close(self):
        print("the self is",self.renew_visible)
        self.renew_visible = False
        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id)], limit=1)

        if pending_action:
            pending_action.status = 'closed'
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

    def action_renew(self):
        self.renew_visible = False
        print()

        # Define the values for the new lease
        new_lease_values = {
            'name': self.env['ir.sequence'].next_by_code('product.lease') or 'New',
            'start_date': self.end_date,  # Assuming end_date of the old lease is the start date of the new lease
            'state': 'draft',
            'renew_visible': False,
            'bill_to': self.bill_to.id if self.bill_to else False,
            'ship_to': self.ship_to.id if self.ship_to else False,  # Assuming there is a field for shipping address
            'product_lease_request_line_ids': [(6, 0, self.product_lease_request_line_ids.ids)],  # Assuming you have a many2many field for products
            'vendor_lease_request_line_ids': [(6, 0, self.vendor_lease_request_line_ids.ids)] , # Assuming you have a many2many field for vendors
            'department_id' : self.department_id.id,
            'exp_category' : self.exp_category.id,
            'address1' : self.address1,
            'address2' : self.address2,
            'location' : self.location,
            'city' : self.city,
            'state_name' : self.state
        }

        # Create the new lease
        new_lease = self.env['product.lease'].create(new_lease_values)

        # Create a pending action for the new lease
        model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')], limit=1)
        pending_vals = {
            'model': model.id,
            'name': f"Lease Request Created from {self.name} Renew",
            'record': new_lease.id,
            'date': fields.Date.today(),
        }
        if self.bill_to:
            pending_vals['branch'] = self.bill_to.id

        buyer_group = self.env.ref('product_purchase.group_buyers')
        buyer_users = buyer_group.users
        if buyer_users:
            user_ids = [user.id for user in buyer_users]
            pending_vals['approve_users'] = [(6, 0, user_ids)]
            self.env['pending.actions'].create(pending_vals)

        # Post a message about the renewal
        self.message_post(
            body=f"{self.env.user.name} Resubmitted the Lease Agreement to Lease Request {new_lease.name}")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.lease',
            'view_mode': 'form',
            'res_id': new_lease.id,
            'target': 'current',
        }

    @staticmethod
    def calculate_overlap_days(start_date1, end_date1, start_date2, end_date2):
        print("testttttttttttttttt")
        """Calculate the number of overlapping days between two date ranges."""
        overlap_start = max(start_date1, start_date2)
        overlap_end = min(end_date1, end_date2)

        if overlap_start <= overlap_end:
            return (overlap_end - overlap_start).days + 1
        return 0

    @staticmethod
    def calculate_covered_months(start_date, end_date):
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise TypeError("Both start_date and end_date must be datetime.date objects")

        if end_date < start_date:
            raise ValueError("end_date must be greater than or equal to start_date")

        total_months_covered = 0
        current_date = start_date

        # Find the end of the first month
        first_month_end = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        # Calculate the fraction of the first month if the start date is not at the beginning of the month
        if current_date < first_month_end:
            days_in_first_month = (first_month_end - current_date).days + 1
            total_days_in_first_month = (first_month_end - current_date.replace(day=1)).days + 1
            total_months_covered += days_in_first_month / total_days_in_first_month

        current_date = first_month_end + timedelta(days=1)

        # Iterate through the remaining months
        while current_date <= end_date:
            # Find the end of the current month
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_of_month = next_month - timedelta(days=1)

            if end_date <= end_of_month:
                # Calculate the fraction of the last month
                days_in_last_month = (end_date - current_date).days + 1
                total_days_in_last_month = (end_of_month - current_date.replace(day=1)).days + 1
                total_months_covered += days_in_last_month / total_days_in_last_month
                break

            # Full month covered
            total_months_covered += 1
            current_date = next_month

        return total_months_covered

    def generate_auto_po(self):
        current_date = date.today()

        lease_status = self.env['product.lease'].sudo().search(['|', ('state', '=', 'approve'), ('state', '=', 'legal_approve')])
        # lease_status = self.env['product.lease'].sudo().search([])
        print("heelllll")
        print("lease", lease_status)

        today = fields.Date.today()
        first_day_next_month = today.replace(day=1) + relativedelta(months=1)
        first_day_this_month = today.replace(day=1)
        last_day_previous_month = first_day_this_month - timedelta(days=1)
        days_in_previous_month = last_day_previous_month.day
        # last_day = last_day_previous_month.day
        #
        # if last_day > 30:
        #     last_day_previous_month = last_day_previous_month.replace(day=30)
        # if last_day < 30:
        #     last_day_previous_month = last_day_previous_month.replace(day=30)

        # next_month = today.replace(day=1) + timedelta(days=32)
        #
        # # Find the last day of the resulting month
        # last_day_of_month = next_month.replace(day=1) - timedelta(days=1)
        # print("the last day is", last_day_of_month)
        last_day_of_month = first_day_next_month - timedelta(days=1)
        remaining_days = (last_day_of_month - today).days

        first_day_of_previous_month = first_day_this_month - relativedelta(months=1)
        print("the last day of month", last_day_of_month)
        # holding_days = (last_day_of_month - first_day_of_previous_month).days
        po_created = False

        print("the remaining days are", remaining_days)
        for lease in lease_status:
            print("i am here")
            vendor_product_map = defaultdict(list)
            existing_pos = self.env['purchase.order'].sudo().search([('lease_id', '=', lease.id)])
            print("the test vendor map",vendor_product_map)
            if lease.is_increment:
                if current_date <= lease.inc_date:
                    for vendor_line in lease.vendor_lease_request_line_ids:
                        for product_line in lease.product_lease_request_line_ids:
                            # product = product_line.product
                            product = lease.env['product.product'].sudo().search(
                                [('product_tmpl_id', '=', product_line.product.id)], limit=1)
                            print("the product is", product)
                            price_unit = 0.0
                            po_date = None
                            to_date = None
                            holding_days =0
                            if not existing_pos:
                                rent_free_start_date = lease.rent_free_start_date
                                rent_free_end_date = lease.rent_free_end_date
                                print("the dates are", rent_free_end_date, rent_free_start_date)
                                if rent_free_start_date and rent_free_end_date:
                                    holding_days = (rent_free_end_date - rent_free_start_date).days + 1
                                    print("the holding days are",holding_days)
                                if holding_days:
                                    start_date = lease.start_date
                                    day = (last_day_previous_month - start_date).days +1
                                    print("the days are",day)
                                    if day > holding_days:
                                        po_days = day - holding_days
                                        print("the po days are",po_days)
                                        days_remaining_in_month = (last_day_previous_month - rent_free_end_date).days
                                        print("the remaing days are",days_remaining_in_month)
                                        if rent_free_end_date.month == last_day_previous_month.month:
                                            po_date = rent_free_end_date + timedelta(days=1)
                                            to_date = last_day_previous_month
                                            price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
                                            print("price units", price_units)
                                            price_unit = (price_units / days_in_previous_month) * days_remaining_in_month
                                            print("the unit price is", price_unit)
                                        else:
                                            po_date = last_day_previous_month.replace(day=1)
                                            to_date = last_day_previous_month
                                            print("test", product_line.unit_price)
                                            print("2nd test", vendor_line.percentage_of_amount)
                                            price_units = product_line.unit_price * (
                                                    vendor_line.percentage_of_amount / 100)
                                            price_unit = price_units

                                else:
                                    start_date = lease.start_date
                                    if current_date >= start_date and current_date != start_date:
                                        if start_date.month == last_day_previous_month.month:
                                            po_date = start_date
                                            to_date = last_day_previous_month
                                            days_remaining_in_month = (last_day_previous_month - start_date).days +1
                                            print("Days remaining in the start month:", days_remaining_in_month)
                                            print("last day of the prevoius month",last_day_previous_month)
                                            print("the days in the previous montg",days_in_previous_month)
                                            price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
                                            print("price units",price_units)
                                            price_unit = (price_units / days_in_previous_month) * days_remaining_in_month
                                            print("the unit price is", price_unit)
                                        else:
                                            po_date = last_day_previous_month.replace(day=1)
                                            to_date = last_day_previous_month
                                            print("test", product_line.unit_price)
                                            print("2nd test", vendor_line.percentage_of_amount)
                                            price_units = product_line.unit_price * (
                                                        vendor_line.percentage_of_amount / 100)
                                            price_unit = price_units

                            else:
                                if current_date <= lease.inc_date:
                                    po_date = last_day_previous_month.replace(day=1)
                                    to_date = last_day_previous_month
                                    print("test",product_line.unit_price)
                                    print("2nd test",vendor_line.percentage_of_amount)
                                    price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
                                    price_unit = price_units

                            if price_unit >0:
                                print("the unit price is", price_unit)
                                vendor_product_map[vendor_line].append({
                                    'product': product,
                                    'price_unit': price_unit,
                                    'quantity': product_line.quantity,
                                    'uom_id': product.uom_po_id.id,
                                })

                        # Create purchase orders for each vendor
                    for vendor_line, products in vendor_product_map.items():
                        vendor = vendor_line.vendor_id
                        print("the vendor is", vendor.name)
                        percentage = vendor_line.percentage_of_amount
                        total_amount = vendor_line.amount

                        order_lines = []
                        for product_data in products:
                            product = product_data['product']
                            order_lines.append((0, 0, {
                                'display_type': False,
                                'name': product.name or '',
                                'product_id': product.id,
                                'price_unit': product_data['price_unit'],
                                'product_qty': product_data['quantity'],
                                'taxes_id': [(6, 0, [lease.tax.id])] if lease.tax else [],
                                'product_uom': product_data['uom_id'],
                            }))
                            print("the order is", order_lines)
                        purchase_order = lease.env['purchase.order'].sudo().create({
                            'partner_id': vendor.id,
                            'order_line': order_lines,
                            'company_id': lease.company_id.id,
                            'is_auto_po': True,
                            'lease_id': lease.id,
                            'expense_type': lease.expense_type or '',
                            'exp_category': lease.exp_category.id or '',
                            'department_id': lease.department_id.id or '',
                            'bill_to': lease.bill_to.id,
                            'ship_to': lease.ship_to.id,
                            'branch_id': lease.ship_to.id,
                            'from_date' : po_date,
                            'to_date' :to_date,
                        })
                        print("the purchase order is", purchase_order)
                        self.env.cr.commit()
                        purchase_order.button_confirm()
                        po_created = True
                        # Assuming auto_invoice is a boolean field on the lease
                        if lease.auto_invoice:
                            print("the purchase order is",purchase_order)
                            purchase_order.button_confirm()
                            for line in purchase_order.order_line:
                                print("the lines are",line)
                                line.qty_received = line.product_qty
                            purchase_order.action_create_invoice()

                        # Create a record in lease.recurring.po for tracking
                        po_vals = {
                            'po': purchase_order.id,
                            'date': po_date,
                            'to_date': to_date,
                            'status': purchase_order.state,
                            'recurring_lease_id': lease.id,
                            'vendor': vendor.id,
                            'amount': purchase_order.amount_total,
                        }
                        lease.env['lease.recurring.po'].sudo().create(po_vals)
                    if po_created:
                        buyer_group = self.env.ref('product_purchase.group_buyers')
                        buyer_users = buyer_group.users
                        if buyer_users:
                            print("buyersssss", buyer_users)
                            subject = "New Lease Purchase Order Raised: %s" % lease.name
                            body = ("Dear Buyer, "
                                    "A new lease Purchase Order Request with the name %s has been raised." % (
                                        lease.name))

                            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            menu_id = self.env['ir.ui.menu'].sudo().search(
                                [('name', '=', 'Approved Lease')], limit=1) or False

                            url_params = {
                                'id': lease.id,
                                'action': self.env.ref('lease_management.action_approve_lease_view').id,
                                'model': 'product.lease',
                                'view_type': 'form',
                                'menu_id': menu_id.id if menu_id else False,
                            }

                            params = '/web?#%s' % url_encode(url_params)
                            url = base_url + params if base_url else "#"

                            print(url)
                            email_to_list = [user.email if user.email else user.login for user in buyer_users]

                            author = self.env['res.partner'].sudo().search(
                                [('name', '=', 'Administrator')], limit=1)

                            body = (
                                f"Dear Buyer, "
                                f"A new lease purchase order Request with the name <strong>{lease.name}</strong> has been raised.</strong>.<br>"
                                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                            )
                            # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                            # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                            # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                            # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                            # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                            # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"
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
                for vendor_line in lease.vendor_lease_request_line_ids:
                    for product_line in lease.product_lease_request_line_ids:
                        # product = product_line.product
                        product = lease.env['product.product'].sudo().search(
                            [('product_tmpl_id', '=', product_line.product.id)], limit=1)
                        print("the product is", product)
                        price_unit = 0.0
                        po_date = None
                        to_date = None
                        holding_days = 0
                        if not existing_pos:
                            rent_free_start_date = lease.rent_free_start_date
                            rent_free_end_date = lease.rent_free_end_date
                            print("the dates are", rent_free_end_date, rent_free_start_date)
                            if rent_free_start_date and rent_free_end_date:
                                holding_days = (rent_free_end_date - rent_free_start_date).days + 1
                                print("the holding days are", holding_days)
                            if holding_days:
                                start_date = lease.start_date
                                day = (last_day_previous_month - start_date).days + 1
                                print("the days are", day)
                                if day > holding_days:
                                    po_days = day - holding_days
                                    print("the po days are", po_days)

                                    days_remaining_in_month = (last_day_previous_month - rent_free_end_date).days
                                    print("the remaing days are", days_remaining_in_month)
                                    if rent_free_end_date.month == last_day_previous_month.month:
                                        po_date = rent_free_end_date + timedelta(days=1)
                                        to_date = last_day_previous_month
                                        price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
                                        print("price units", price_units)
                                        price_unit = (price_units / days_in_previous_month) * days_remaining_in_month
                                        print("the unit price is", price_unit)
                                    else:
                                        po_date = last_day_previous_month.replace(day=1)
                                        to_date = last_day_previous_month
                                        print("test", product_line.unit_price)
                                        print("2nd test", vendor_line.percentage_of_amount)
                                        price_units = product_line.unit_price * (
                                                vendor_line.percentage_of_amount / 100)
                                        price_unit = price_units


                            else:
                                start_date = lease.start_date
                                if current_date >= start_date and current_date != start_date:
                                    if start_date.month == last_day_previous_month.month:
                                        po_date = start_date
                                        to_date = last_day_previous_month
                                        days_remaining_in_month = (last_day_previous_month - start_date).days + 1
                                        print("Days remaining in the start month:", days_remaining_in_month)
                                        print("last day of the prevoius month", last_day_previous_month)
                                        print("the days in the previous montg", days_in_previous_month)
                                        price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
                                        print("price units", price_units)
                                        price_unit = (price_units / days_in_previous_month) * days_remaining_in_month
                                        print("the unit price is", price_unit)
                                    else:
                                        po_date = last_day_previous_month.replace(day=1)
                                        to_date = last_day_previous_month
                                        print("test", product_line.unit_price)
                                        print("2nd test", vendor_line.percentage_of_amount)
                                        price_units = product_line.unit_price * (
                                                vendor_line.percentage_of_amount / 100)
                                        price_unit = price_units

                        else:

                            if current_date <= lease.inc_date:
                                po_date = last_day_previous_month.replace(day=1)
                                to_date = last_day_previous_month
                                print("test", product_line.unit_price)
                                print("2nd test", vendor_line.percentage_of_amount)
                                price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
                                price_unit = price_units

                        if price_unit > 0:
                            print("the unit price is", price_unit)
                            vendor_product_map[vendor_line].append({
                                'product': product,
                                'price_unit': price_unit,
                                'quantity': product_line.quantity,
                                'uom_id': product.uom_po_id.id,
                            })

                    # Create purchase orders for each vendor
                for vendor_line, products in vendor_product_map.items():
                    vendor = vendor_line.vendor_id
                    print("the vendor is", vendor.name)
                    percentage = vendor_line.percentage_of_amount
                    total_amount = vendor_line.amount

                    order_lines = []
                    for product_data in products:
                        product = product_data['product']
                        order_lines.append((0, 0, {
                            'display_type': False,
                            'name': product.name or '',
                            'product_id': product.id,
                            'price_unit': product_data['price_unit'],
                            'product_qty': product_data['quantity'],
                            'taxes_id': [(6, 0, [lease.tax.id])] if lease.tax else [],
                            'product_uom': product_data['uom_id'],
                        }))
                        print("the order is", order_lines)
                    purchase_order = lease.env['purchase.order'].sudo().create({
                        'partner_id': vendor.id,
                        'order_line': order_lines,
                        'company_id': lease.company_id.id,
                        'is_auto_po': True,  # Adjust based on your logic
                        'lease_id': lease.id,
                        'expense_type': lease.expense_type or '',
                        'exp_category': lease.exp_category.id or '',
                        'department_id': lease.department_id.id or '',
                        'bill_to': lease.bill_to.id,
                        'ship_to': lease.ship_to.id,
                        'branch_id': lease.ship_to.id,
                        'from_date': po_date,
                        'to_date': to_date,
                    })
                    print("the purchase order is", purchase_order)
                    self.env.cr.commit()
                    purchase_order.button_confirm()
                    po_created = True
                    # Assuming auto_invoice is a boolean field on the lease
                    if lease.auto_invoice:
                        print("the purchase order is", purchase_order)
                        purchase_order.button_confirm()
                        for line in purchase_order.order_line:
                            print("the lines are", line)
                            line.qty_received = line.product_qty
                        purchase_order.action_create_invoice()

                    # Create a record in lease.recurring.po for tracking
                    po_vals = {
                        'po': purchase_order.id,
                        'date': po_date,
                        'to_date': to_date,
                        'status': purchase_order.state,
                        'recurring_lease_id': lease.id,
                        'vendor': vendor.id,
                        'amount': purchase_order.amount_total,
                    }
                    lease.env['lease.recurring.po'].sudo().create(po_vals)
                if po_created:
                    buyer_group = self.env.ref('product_purchase.group_buyers')
                    buyer_users = buyer_group.users
                    if buyer_users:
                        print("buyersssss", buyer_users)
                        subject = "New Lease Purchase Order Raised: %s" % lease.name
                        body = ("Dear Buyer, "
                                "A new lease Purchase Order Request with the name %s has been raised." % (
                                    lease.name))

                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        menu_id = self.env['ir.ui.menu'].sudo().search(
                            [('name', '=', 'Approved Lease')], limit=1) or False

                        url_params = {
                            'id': lease.id,
                            'action': self.env.ref('lease_management.action_approve_lease_view').id,
                            'model': 'product.lease',
                            'view_type': 'form',
                            'menu_id': menu_id.id if menu_id else False,
                        }

                        params = '/web?#%s' % url_encode(url_params)
                        url = base_url + params if base_url else "#"

                        print(url)
                        email_to_list = [user.email if user.email else user.login for user in buyer_users]

                        author = self.env['res.partner'].sudo().search(
                            [('name', '=', 'Administrator')], limit=1)

                        body = (
                            f"Dear Buyer, "
                            f"A new lease purchase order Request with the name <strong>{lease.name}</strong> has been raised.</strong>.<br>"
                            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                        )
                        # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                        # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                        # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                        # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"
                        if author:
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': ','.join(email_to_list),
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)

    @api.depends('state')
    def compute_states(self):
        if self.state == 'approve':
            self.compute_state = True
            if self.product_request_id:
                request_details = self.env['product.request'].sudo().search([('id', '=', self.product_request_id.id)], limit=1)
                if request_details:
                    pass
                    # request_details.status = 'requested'
                else:
                    pass
        else:
            self.compute_state = False


    @api.depends('approved_users')
    def compute_approved_user(self):
        if self.approved_users:
            for user in self.approved_users:
                print(user)
                if user.id in self.next_approve_user.ids:
                    self.next_approve_user -= user
                    self.user_approved = True
                else:
                    self.user_approved = False
        else:
            self.user_approved = False

    @api.depends('legal_approved_users')
    def compute_legal_approved_user(self):
        if self.legal_approved_users:
            for user in self.legal_approved_users:
                print(user)
                if user.id in self.legal_next_approve_user.ids:
                    self.legal_next_approve_user -= user
                    self.user_legal_approved = True
                else:
                    self.user_legal_approved= False
        else:
            self.user_legal_approved = False

    @api.depends('next_approve_user')
    def compute_is_an_approver(self):
        for rec in self:
            # rec.is_an_approver = self.env.user.id in rec.next_approve_user.mapped(
            #     'user_id.id') and self.env.user.id not in rec.approved_users.mapped('user_id.id')

        # for rec in self:
            rec.is_an_approver = self.env.user.id in rec.next_approve_user.mapped('id')
            print("i am just entering for the check")

    @api.depends('legal_next_approve_user')
    def compute_is_an_legal_approver(self):
        for rec in self:
            # rec.is_an_approver = self.env.user.id in rec.next_approve_user.mapped(
            #     'user_id.id') and self.env.user.id not in rec.approved_users.mapped('user_id.id')

            # for rec in self:
            rec.is_an_legal_approver = self.env.user.id in rec.legal_next_approve_user.mapped('id')
            print("i am just entering for the check")



    @api.depends('product_lease_request_line_ids')
    def compute_total_amount(self):
        total_amount = 0
        for total in self:
            for lines in total.product_lease_request_line_ids:
                total_amount += lines.amount
        # print("total_amount ", total_amount)
        self.total = total_amount

    # @api.depends('total','qty','price')
    # def compute_total_amount(self):
    #     total_amount = 0
    #     for total in self:
    #         if total.qty and total.price:
    #             total_amount += total.qty * total.price
    #     print("total_amount ", total_amount)
    #     self.total = total_amount

    def action_draft(self):
        print("draft")
        # self.state = 'draft'

    @api.model
    def create(self, vals):
        print("i am in create")
        if vals.get('name', 'New') == 'New':
            print("hai")
        return super(ProductLease, self).create(vals)


    def action_confirm_lease(self):


        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.action_confirmation_lease_wizard')
        action['context'] = {'default_lease_id': self.id,
                             'default_name': self.name,
                             'default_requested_date': self.requested_date,
                             'default_requested_by': self.user_id.id,
                             'default_product_id': self.product_id.id,
                             'default_vendor_id':self.vendor_id.id,
                             'default_company_id': self.company_id.id,
                             'default_bill_to': self.bill_to.id,
                             'default_ship_to': self.ship_to.id,
                             'default_expense_type': self.expense_type,
                             'default_exp_category': self.exp_category.id,
                             'default_total_price': self.total,
                             'default_department_id': self.department_id.id,
                             'default_start_date': self.start_date,
                             'default_end_date': self.end_date,
                             }
        return action

    def action_request(self):
        print("lease", self.vendor_lease_request_line_ids)

        for line in self.vendor_lease_request_line_ids:
            print("i am inside the for loop")
            total_amount = sum(line.amount for line in self.vendor_lease_request_line_ids)
            print("the total amount is", total_amount)
            if total_amount > line.vendor_lease_request_id.total:
                raise ValidationError("Total amount cannot exceed the total of the vendor lease request.")
            if total_amount < line.vendor_lease_request_id.total:
                raise ValidationError("Total amount cannot be less than the total of the vendor lease request.")
        print("requested")



        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

        if pending_action:
            for pend in pending_action:
                pend.status = 'closed'
        # if not employee_data.department_id:
        #     raise ValidationError("Employee data is empty")
        pr_company_data = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                ('department_id', '=', self.department_id.id),
                                                                ('expense_type', '=', self.expense_type),
                                                                ('exp_category', '=', self.exp_category.id),
                                                                ('from_amount', '<=', self.total),
                                                                ('to_amount', '>=', self.total),
                                                                ('type', '=', 'lease')],
                                                               limit=1)
        print("pr_company",self.company_id.name,self.department_id.name,self.expense_type,self.exp_category.name,self.total,pr_company_data.name)

        pr_company_data2 = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                 ('department_id', '=', self.department_id.id),
                                                                 ('expense_type', '=', self.expense_type),
                                                                 ('exp_category', '=', self.exp_category.id),
                                                                 ('from_amount', '<=', self.total),
                                                                 ('to_amount', '>=', self.total),
                                                                 ('type', '=', 'legal_workflow')],
                                                                limit=1)

        if not pr_company_data:
            raise ValidationError(
                "Sorry, The criteria provided did not match any existing Lease workflows, Please contact Administrator.")
        if not pr_company_data2:
            raise ValidationError(
                "Sorry, The criteria provided did not match any existing Legal workflows, Please contact Administrator.")
        if pr_company_data:

            for approvers in pr_company_data.pr_approve_users_id:
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
                    pass
                else:
                    raise ValidationError(
                        _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                            approvers.designation.name, approvers.department_id.name,
                            ser_branch_record.name, approvers.company_id.name))
        else:
            raise ValidationError(
                "Sorry,The criteria provided did not match any existing Lease workflows,Please contact Administrator.")

        if pr_company_data2:

            for approvers in pr_company_data2.pr_approve_users_id:
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
                    pass
                else:
                    raise ValidationError(
                        _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                            approvers.designation.name, approvers.department_id.name,
                            ser_branch_record.name, approvers.company_id.name))
        else:
            raise ValidationError(
                "Sorry,The criteria provided did not match any existing Legal workflows,Please contact Administrator.")


        if self.vendor_lease_request_line_ids:
            vendor_users = self.env['res.users'].sudo()
            for vendor_line in self.vendor_lease_request_line_ids:
                vendor = vendor_line.vendor_id
                vendor_user = self.env['res.users'].sudo().search([('partner_id', '=', vendor.id)], limit=1)
                vendor_users |= vendor_user
                print("the vendor user", vendor_users)
            if vendor_users:
                print("the login id is", vendor_users)
                for vendor_user in vendor_users:
                    new_line_vals = {
                        'user_id': vendor_user.id,
                        'approve_order': 1,
                        'department_id': False,
                        'company_id': False,
                    }
                    print("the new vals", new_line_vals)

                    self.approve_line |= self.env['lease.approve.line'].sudo().create(new_line_vals)
                    print("approval line", self.approve_line)
                    self.approve_users += vendor_user

            # else:
            #         raise ValidationError("The vendor have no user please add a user")
            for approvers in pr_company_data.pr_approve_users_id:
                print("the approvers are", approvers)
                for details in approvers:
                    line = []
                    last_approve_order = None
                    print(details.company_id.id,details.branch_id.id,details.department_id.id,details.designation.id)
                    if details.branch_id.code == "COR":
                        ser_branch = details.branch_id.id
                        ser_branch_record = details.branch_id
                    else:
                        ser_branch = self.bill_to.id
                        ser_branch_record = self.bill_to
                    corresponding_approval_flow = self.env['res.users.line'].sudo().search([
                        ('company_id', '=', details.company_id.id),
                        ('branch_id', '=', ser_branch),
                        ('department_id', '=', details.department_id.id),
                        ('designation', '=', details.designation.id)
                    ])
                    print("cores approval",corresponding_approval_flow)
                    if not corresponding_approval_flow.res_user_id:
                        raise ValidationError("No corresponding approval flow found for details: %s" % details)
                    print("corresponding approval flows:", corresponding_approval_flow.res_user_id.id)
                    self.approve_users |= corresponding_approval_flow.mapped('res_user_id')
                    print("the approval users are", self.approve_users.ids)
                    if vendor_users:
                        for vendor_user in vendor_users:
                            print("inside approve users", vendor_user.id)
                            approve_order = int(details.approve_order) + 1
                            print("the approve order is", approve_order)
                    else:
                        approve_order = details.approve_order

                    vals = {
                            'user_id': corresponding_approval_flow.res_user_id.id,
                            'company_id': corresponding_approval_flow.company_id.id,
                            # 'location': users.location.id,
                            'department_id': corresponding_approval_flow.department_id.id,
                            'designation': corresponding_approval_flow.designation.id,
                            'approve_order': approve_order,
                        }

                    line.append((0, 0, vals))
                    if last_approve_order is None or details.approve_order > last_approve_order:
                        last_approve_order = details.approve_order
                    print("last", last_approve_order)
                    self.approve_line = line

            if not vendor_users:
                first_approver = self.approve_line.filtered(lambda l: l.approve_order == 1).mapped('user_id')
                if first_approver:
                    vendor_users = first_approver
            for vendor_user in vendor_users:
                print("Creating pending action for the first approver (vendor user):", vendor_user.id)
                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                user_ids_to_pass = self.approve_users.ids if self.approve_users else []
                pending_action_vals = {
                    'model': model.id,
                    'name': self.name + " " + "Waiting For Approval",
                    'record': self.id,
                    'branch': self.bill_to.id,
                    'date': fields.Date.today(),
                    'approve_users': [(4, vendor_user.id)],
                    # Assign to the first approver (vendor user)
                }
                pending_action = self.env['pending.actions'].sudo().create(pending_action_vals)

                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity_type_id = activity_type.id if activity_type else False
                res_model_id = self.env['ir.model'].sudo().search(
                    [('model', '=', 'product.lease')]).id

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

                subject = "New Lease Request Raised: %s" % self.name
                print("Name", self.name)
                body = ("Dear User, "
                        "A New Lease Request with the name %s has been raised by" % (
                            self.name))

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Pending Actions')], limit=1) or False

                url_params = {
                    'id': self.id,
                    'action': self.env.ref('pending_actions.action_pending_actions').id,
                    'model': 'product.lease',
                    'view_type': 'form',
                    'menu_id': menu_id.id if menu_id else False,
                }

                params = '/web?#%s' % url_encode(url_params)
                url = base_url + params if base_url else "#"

                print(url)

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User,"
                    f"A new Lease Request with the name <strong>{self.name}</strong> has been raised by <strong></strong>.<br>"
                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                )
                # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"
                if author:
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': vendor_user.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)



            next_approver_user_ids = [
                next_approver.user_id.id
                for next_approver in self.approve_line
                if (
                        (vendor_user and next_approver.approve_order == 1)
                        or (not vendor_user and next_approver.approve_order == 1)
                )
            ]
            print(next_approver_user_ids, "This print")
            if next_approver_user_ids:
                self.write({'next_approve_user': [(6, 0, next_approver_user_ids)]})

                self.state = 'request'
            print("name is", self._name)

            user_name = self.env.user.name if self.env.user else ''
            message_body = f"Lease Request is Generated By the buyer. Buyer: {user_name}"
            self.message_post(body=message_body)



    def action_approve(self):
        self.write({'approved_users': [(4, self.env.user.id)]})
        self.is_an_approver = False

        approve_user = self.env['lease.approve.line'].sudo().search(
            [('approve_lease_id', '=', self.id), ('user_id', '=', self.env.user.id)])
        print(approve_user)
        for record in approve_user:
            record.write({'status': 'approve'})
        self.message_post(body=f" {approve_user.user_id.name} Approved.")

        if self.approved_users == self.approve_users:
            # self.message_post(body="The lease request for everyone has been approved")
            if self.original_lease_id:
                print("i am in org")
                original_lease = self.env['product.lease'].browse(self.original_lease_id.id)

                start_date = fields.Date.from_string(self.start_date)
                new_end_date = start_date - timedelta(days=1)
                original_lease.write({'end_date': new_end_date, 'inc_date':new_end_date})

            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

            if pending_action:
                pending_action.status = 'closed'
            activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].sudo().search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                activity.action_feedback(feedback="Activity completed")
            #############################
            self.message_post(body="The lease request for everyone has been approved.Proceeding with the legal workflow.")
            self.state = 'legal_approve'

            pr_company_data2 = self.env['pr.company'].sudo().search([('company_id', '=', self.company_id.id),
                                                                     ('department_id', '=', self.department_id.id),
                                                                     ('expense_type', '=', self.expense_type),
                                                                     ('exp_category', '=', self.exp_category.id),
                                                                     ('from_amount', '<=', self.total),
                                                                     ('to_amount', '>=', self.total),
                                                                     ('type', '=', 'legal_workflow')],
                                                                    limit=1)

            if pr_company_data2:
                print("hlw i am in legal")
                legal_lines = []
                for approvers in pr_company_data2.pr_approve_users_id:
                    print("the approvers2 are", approvers)
                    for details in approvers:
                        if details.branch_id.code == "COR":
                            ser_branch = details.branch_id.id
                            ser_branch_record = details.branch_id
                        else:
                            ser_branch = self.bill_to.id
                            ser_branch_record = self.bill_to
                        print(details.company_id.id, details.branch_id.id, details.department_id.id,
                              details.designation.id)
                        corresponding_approval_flow = self.env['res.users.line'].sudo().search([
                            ('company_id', '=', details.company_id.id),
                            ('branch_id', '=', ser_branch),
                            ('department_id', '=', details.department_id.id),
                            ('designation', '=', details.designation.id)
                        ])
                        print("cores approval2", corresponding_approval_flow)
                        print("corresponding approval flows2:", corresponding_approval_flow.res_user_id.id)
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
                        'branch': self.bill_to.id,
                        'date': fields.Date.today(),
                        'approve_users': [(4, vendor_user.id)],
                    }
                    pending_action = self.env['pending.actions'].sudo().create(pending_action_vals)
                    print("the pending action",pending_action)

                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')], limit=1)
                    activity_type_id = activity_type.id if activity_type else False
                    res_model_id = self.env['ir.model'].sudo().search(
                        [('model', '=', 'product.lease')]).id

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


                    subject = "New Lease Request Raised: %s" % self.name
                    print("Name", self.name)
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Pending Actions')], limit=1) or False

                    url_params = {
                        'id': self.id,
                        'action': self.env.ref('pending_actions.action_pending_actions').id,
                        'model': 'product.lease',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    body = (
                        f"Dear User,"
                        f"A new Lease Request with the name <strong>{self.name}</strong> has been raised by <strong></strong>.<br>"
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
                    self.write({'legal_next_approve_user': [(6, 0, legal_next_approver_user_ids)]})
                    # self.state = 'request'
                print("name is", self._name)

                # user_name = self.env.user.name if self.env.user else ''
                # message_body = "Lease request approved. Proceeding with the legal workflow."
                # self.message_post(body=message_body)


            if self.product_request_id:

                print("i am ok")
                self.product_request_id.status = 'lease'
                for line_item in self.product_request_id.product_request_line_ids:
                    if line_item.product == self.product_id:  # Assuming product_id uniquely identifies a product
                        line_item.write({
                            'quantity': self.qty,
                            'unit_price': self.price,
                            'contract_status': 'in_lease',
                            'vendors': [(6, 0, self.vendor_id.ids)],

                        })

                        break
                all_in_lease = all(line_item.contract_status == 'in_lease' for line_item in
                                   self.product_request_id.product_request_line_ids)
                if all_in_lease:
                    self.product_request_id.action_request()

            # else:
            #     if self.auto_po == True:
            #         print("the company id is", self.bill_to)
            #         if self.with_gst and not self.tax:
            #             raise UserError("Please add Tax")
            #
            #         today = fields.Date.today()
            #
            #         last_day_of_month = today.replace(day=28) + timedelta(days=4)
            #         last_day_of_month = last_day_of_month - timedelta(days=last_day_of_month.day)
            #
            #         remaining_days = (last_day_of_month - today).days
            #
            #         print("the remaining days are",remaining_days)
            #
            #         # last_day_of_month = today + relativedelta(months=1)
            #
            #         # Group product lines by vendor
            #         vendor_product_map = defaultdict(list)
            #         for vendor_line in self.vendor_lease_request_line_ids:
            #             for product_line in self.product_lease_request_line_ids:
            #                 # product = product_line.product
            #                 product = self.env['product.product'].sudo().search(
            #                     [('product_tmpl_id', '=', product_line.product.id)], limit=1)
            #                 print("the product is", product)
            #                 price_unit = 0.0
            #                 if today < self.inc_date:
            #                     price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
            #                     price_unit = price_units
            #                 else:
            #                     price_units = product_line.unit_price * (vendor_line.percentage_of_amount / 100)
            #                     price_unit = (price_units / last_day_of_month.day) * remaining_days
            #                 print("the unit price is", price_unit)
            #                 vendor_product_map[vendor_line].append({
            #                     'product': product,
            #                     'price_unit': price_unit,
            #                     'quantity': product_line.quantity,
            #                     'uom_id': product.uom_po_id.id,
            #                 })
            #
            #         # Create purchase orders for each vendor
            #         for vendor_line, products in vendor_product_map.items():
            #             vendor = vendor_line.vendor_id
            #             print("the vendor is", vendor.name)
            #             percentage = vendor_line.percentage_of_amount
            #             total_amount = vendor_line.amount
            #
            #             order_lines = []
            #             for product_data in products:
            #                 product = product_data['product']
            #                 order_lines.append((0, 0, {
            #                     'display_type': False,
            #                     'name': product.name or '',
            #                     'product_id': product.id,
            #                     'price_unit': product_data['price_unit'],
            #                     'product_qty': product_data['quantity'],
            #                     'taxes_id': [(6, 0, [self.tax.id])] if self.tax else [],
            #                     'product_uom': product_data['uom_id'],
            #                 }))
            #                 print("the order is", order_lines)
            #             purchase_order = self.env['purchase.order'].sudo().create({
            #                 'partner_id': vendor.id,
            #                 'order_line': order_lines,
            #                 'company_id': self.company_id.id,
            #                 'is_auto_po': True,  # Adjust based on your logic
            #                 'lease_id': self.id,
            #                 'expense_type': self.expense_type or '',
            #                 'exp_category': self.exp_category.id or '',
            #                 'department_id': self.department_id.id or '',
            #                 'bill_to': self.bill_to.id,
            #                 'ship_to': self.ship_to.id,
            #             })
            #
            #             # Assuming auto_invoice is a boolean field on the lease
            #             if self.auto_invoice:
            #                 purchase_order.button_confirm()
            #                 for line in purchase_order.order_line:
            #                     line.qty_received = line.product_qty
            #                 purchase_order.action_create_invoice()
            #
            #             # Create a record in lease.recurring.po for tracking
            #             po_vals = {
            #                 'po': purchase_order.id,
            #                 'date': self.start_date,
            #                 'to_date': last_day_of_month,
            #                 'status': purchase_order.state,
            #                 'recurring_lease_id': self.id,
            #                 'vendor': vendor.id,
            #                 'amount': purchase_order.amount_total,
            #             }
            #             self.env['lease.recurring.po'].sudo().create(po_vals)
            #
            #         self.state = 'po'

                # if self.auto_invoice == True:
                #     purchase_order.button_confirm()
                #     for lines in purchase_order.order_line:
                #         lines.qty_received = lines.product_qty
                #     purchase_order.action_create_invoice()


            # Change the state to the desired value when all statuses are 'approve'
            # self.write({'state': 'approved_state'})

        else:
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close", rec)
                    rec.status = 'closed'

            activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].sudo().search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                activity.action_feedback(feedback="Activity completed")

            approve_users = self.env['lease.approve.line'].sudo().search([('approve_lease_id', '=', self.id)],
                                                                      order='approve_order asc')

            user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
            print("the users are",user_ids)
            # user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]

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
                            print("the approve dict",approve_dict[order])

            print("approve_dict ", approve_dict)


            record_to_remove = self.env['res.users'].browse(self.env.user.id)
            self.next_approve_user -= record_to_remove

            if not self.next_approve_user:
                for order in order_list:
                    for order_list_users in approve_dict[order]:
                        print("view the order list",order_list_users)
                        if self.env.user.id == order_list_users['u_id']:
                            try:
                                if approve_dict[order + 1]:
                                    for users in approve_dict[order + 1]:
                                        self.write({'next_approve_user': [(4, users['u_id'])]})

                                    ####################### MAil ############################
                                    print(self.next_approve_user,
                                          "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                        [('name', '=', 'Pending Actions')], limit=1) or False

                                    url_params = {
                                        'id': self.id,
                                        'action': self.env.ref('pending_actions.action_pending_actions').id,
                                        'model': 'product.lease',
                                        'view_type': 'form',
                                        # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                        'menu_id': menu_id.id,
                                    }
                                    params = '/web?#%s' % url_encode(url_params)
                                    view_url = base_url + params if base_url else "#"

                                    print(view_url)

                                    ##################### URL for Approval #########################


                                    author = self.env['res.partner'].sudo().search(
                                        [('name', '=', 'Administrator')], limit=1) or False

                                    body = (
                                        f"Dear User,A Lease request {self.name} is waiting for Approval.<br><br>"
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

                                    for user in self.next_approve_user:
                                        print("i am just entering the pending action")
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                   limit=1)
                                        pending_vals = {
                                            'model': model.id,
                                            'name': self.name + " " + "Waiting For Approval",
                                            'record': self.id,
                                            'branch': self.bill_to.id,
                                            'date': date.today(),
                                        }
                                        if user:
                                            user_ids_to_pass = user.ids
                                            print("the user ids",user_ids_to_pass)
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            pendings = self.env['pending.actions'].sudo().create(pending_vals)
                                            print("the pending is",pendings)

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Request')], limit=1)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'product.lease')]).id
                                            for user_id in user_ids_to_pass:
                                                activity_values = {
                                                    'user_id': user.id,
                                                    'res_id': self.id,
                                                    'note': "Pending Action",
                                                    'activity_type_id': activity_type_id,
                                                    'res_model_id': res_model_id,
                                                }
                                                with self.env.cr.savepoint():
                                                    self = self.with_context(mail_activity_quick_update=True)
                                                    created_activity = self.env['mail.activity'].sudo().create(activity_values)
                                                

                                        if user.login:
                                            subject = "Lease Request Waiting For APPROVAL: %s" % self.name
                                            mail_values = {
                                                'subject': subject,
                                                'body_html': body,
                                                'email_to': user.login,
                                                'auto_delete': False,
                                                'author_id': author.id
                                            }
                                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                            print(mail_record)
                                            mail_record.send()


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
                                                self.write({'next_approve_user': [(4, users['u_id'])]})
                                                flag = 1

                                                print(self.next_approve_user,
                                                      "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Pending Actions')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref(
                                                        'pending_actions.action_pending_actions').id,
                                                    'model': 'product.lease',
                                                    'view_type': 'form',
                                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                                    'menu_id': menu_id.id,
                                                }
                                                params = '/web?#%s' % url_encode(url_params)
                                                view_url = base_url + params if base_url else "#"

                                                ##################### URL for Approval #########################

                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Pending Actions')], limit=1) or False


                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref('pending_actions.action_pending_actions').id,
                                                    'model': 'product.lease',
                                                    'view_type': 'form',
                                                    'menu_id': menu_id.id if menu_id else False,
                                                }

                                                params = '/web?#%s' % url_encode(url_params)
                                                url = base_url + params if base_url else "#"

                                                print(url)

                                                author = self.env['res.partner'].sudo().search(
                                                    [('name', '=', 'Administrator')], limit=1) or False

                                                body = (
                                                    f"Dear User,A Lease request {self.name} is waiting for Approval.<br><br>"
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

                                                for user in self.next_approve_user:
                                                    model = self.env['ir.model'].sudo().search(
                                                        [('model', '=', self._name)],
                                                        limit=1)
                                                    pending_vals = {
                                                        'model': model.id,
                                                        'name': self.name + " " + "Waiting For Approval",
                                                        'record': self.id,
                                                        'branch': self.bill_to.id,
                                                        'date': date.today(),
                                                    }
                                                    if user:
                                                        user_ids_to_pass = user.ids
                                                        pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                        pendings = self.env['pending.actions'].sudo().create(pending_vals)

                                                        activity_type = self.env['mail.activity.type'].sudo().search(
                                                            [('name', '=', 'Pending Request')], limit=1)
                                                        activity_type_id = activity_type.id if activity_type else False
                                                        res_model_id = self.env['ir.model'].sudo().search(
                                                            [('model', '=', 'product.lease')]).id
                                                        for user_id in user_ids_to_pass:
                                                            activity_values = {
                                                                'user_id': user.id,
                                                                'res_id': self.id,
                                                                'note': "Pending Action",
                                                                'activity_type_id': activity_type_id,
                                                                'res_model_id': res_model_id,
                                                            }
                                                            with self.env.cr.savepoint():
                                                                self = self.with_context(mail_activity_quick_update=True)
                                                                created_activity = self.env['mail.activity'].sudo().create(activity_values)

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






    def action_legal_approver(self):
        self.write({'legal_approved_users': [(4, self.env.user.id)]})
        self.is_an_legal_approver = False

        legal_approve_user = self.env['lease.legal.approve.line'].sudo().search(
            [('approve_lease_legal_id', '=', self.id), ('user_id', '=', self.env.user.id)])
        print(legal_approve_user)
        for record in legal_approve_user:
            record.write({'status': 'approve'})
        self.message_post(body=f" {legal_approve_user.user_id.name} Approved.")

        if self.legal_approved_users == self.legal_approve_users:
            # self.message_post(body="The lease request for everyone has been approved")

            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

            if pending_action:
                pending_action.status = 'closed'
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].sudo().search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                activity.action_feedback(feedback="Activity completed")
            #############################
            self.message_post(body="The legal teams approved the lease request")

            self.state = 'approve'

        else:
            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close", rec)
                    rec.status = 'closed'

            activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            if activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                activity.action_feedback(feedback="Activity completed")

            approve_users = self.env['lease.legal.approve.line'].sudo().search([('approve_lease_legal_id', '=', self.id)],
                                                                      order='approve_order asc')

            user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
            print("the users are",user_ids)
            # user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]

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
                            print("the approve dict",approve_dict[order])

            print("approve_dict ", approve_dict)

            record_to_remove = self.env['res.users'].browse(self.env.user.id)
            self.legal_next_approve_user -= record_to_remove

            if not self.legal_next_approve_user:
                for order in order_list:
                    for order_list_users in approve_dict[order]:
                        print("view the order list",order_list_users)
                        if self.env.user.id == order_list_users['u_id']:
                            try:
                                if approve_dict[order + 1]:
                                    for users in approve_dict[order + 1]:
                                        self.write({'legal_next_approve_user': [(4, users['u_id'])]})

                                    ####################### MAil ############################
                                    print(self.legal_next_approve_user,
                                          "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                        [('name', '=', 'Pending Actions')], limit=1) or False

                                    url_params = {
                                        'id': self.id,
                                        'action': self.env.ref('pending_actions.action_pending_actions').id,
                                        'model': 'product.lease',
                                        'view_type': 'form',
                                        # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                        'menu_id': menu_id.id,
                                    }
                                    params = '/web?#%s' % url_encode(url_params)
                                    view_url = base_url + params if base_url else "#"

                                    print(view_url)

                                    ##################### URL for Approval #########################


                                    author = self.env['res.partner'].sudo().search(
                                        [('name', '=', 'Administrator')], limit=1) or False

                                    body = (
                                        f"Dear User,A Lease request {self.name} is waiting for Approval.<br><br>"
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

                                    for user in self.legal_next_approve_user:
                                        print("i am just entering the pending action")
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                   limit=1)
                                        pending_vals = {
                                            'model': model.id,
                                            'name': self.name + " " + "Waiting For Approval",
                                            'record': self.id,
                                            'branch': self.bill_to.id,
                                            'date': date.today(),
                                        }
                                        if user:
                                            user_ids_to_pass = user.ids
                                            print("the user ids",user_ids_to_pass)
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            pendings = self.env['pending.actions'].sudo().create(pending_vals)
                                            print("the pending is",pendings)

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Request')], limit=1)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'product.lease')]).id
                                            for user_id in user_ids_to_pass:
                                                activity_values = {
                                                    'user_id': user.id,
                                                    'res_id': self.id,
                                                    'note': "Pending Action",
                                                    'activity_type_id': activity_type_id,
                                                    'res_model_id': res_model_id,
                                                }
                                                with self.env.cr.savepoint():
                                                    self = self.with_context(mail_activity_quick_update=True)
                                                    created_activity = self.env['mail.activity'].sudo().create(activity_values)

                                        if user.login:
                                            subject = "Lease Request Waiting For APPROVAL: %s" % self.name
                                            mail_values = {
                                                'subject': subject,
                                                'body_html': body,
                                                'email_to': user.login,
                                                'auto_delete': False,
                                                'author_id': author.id
                                            }
                                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                            print(mail_record)
                                            mail_record.send()


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
                                                self.write({'legal_next_approve_user': [(4, users['u_id'])]})
                                                flag = 1

                                                print(self.legal_next_approve_user,
                                                      "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Pending Actions')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref(
                                                        'pending_actions.action_pending_actions').id,
                                                    'model': 'product.request',
                                                    'view_type': 'form',
                                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                                    'menu_id': menu_id.id,
                                                }
                                                params = '/web?#%s' % url_encode(url_params)
                                                view_url = base_url + params if base_url else "#"

                                                ##################### URL for Approval #########################

                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Pending Actions')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref('pending_actions.action_pending_actions').id,
                                                    'model': 'product.lease',
                                                    'view_type': 'form',
                                                    'menu_id': menu_id.id if menu_id else False,
                                                }

                                                params = '/web?#%s' % url_encode(url_params)
                                                url = base_url + params if base_url else "#"

                                                print(url)

                                                author = self.env['res.partner'].sudo().search(
                                                    [('name', '=', 'Administrator')], limit=1) or False

                                                body = (
                                                    f"Dear User,A Lease request {self.name} is waiting for Approval.<br><br>"
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

                                                for user in self.next_approve_user:
                                                    model = self.env['ir.model'].sudo().search(
                                                        [('model', '=', self._name)],
                                                        limit=1)
                                                    pending_vals = {
                                                        'model': model.id,
                                                        'name': self.name + " " + "Waiting For Approval",
                                                        'record': self.id,
                                                        'branch': self.bill_to.id,
                                                        'date': date.today(),
                                                    }
                                                    if user:
                                                        user_ids_to_pass = user.ids
                                                        pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                        pendings = self.env['pending.actions'].sudo().create(pending_vals)

                                                        activity_type = self.env['mail.activity.type'].sudo().search(
                                                            [('name', '=', 'Pending Request')], limit=1)
                                                        activity_type_id = activity_type.id if activity_type else False
                                                        res_model_id = self.env['ir.model'].sudo().search(
                                                            [('model', '=', 'product.lease')]).id
                                                        for user_id in user_ids_to_pass:
                                                            activity_values = {
                                                                'user_id': user.id,
                                                                'res_id': self.id,
                                                                'note': "Pending Action",
                                                                'activity_type_id': activity_type_id,
                                                                'res_model_id': res_model_id,
                                                            }
                                                            with self.env.cr.savepoint():
                                                                self = self.with_context(mail_activity_quick_update=True)
                                                                created_activity = self.env['mail.activity'].sudo().create(activity_values)

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






    def action_reject(self):
        self.state = 'reject'
        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

        for rec in pending_action:
            print(rec.name)
            rec.status = 'closed'
        self.message_post(body=f"{self.env.user.name} Rejected the Lease Request.")

        activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')], limit=1)
        print("type is", self.env.user.id)
        activity = self.env['mail.activity'].sudo().search([
            ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
            ('res_id', '=', self.id), ('res_name', '=', self.name),
            ('activity_type_id', '=', activity_type.id),
        ], limit=1)
        if activity:
            for act in activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(act.id)
                act.action_feedback(feedback="Activity Declined")

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Contracts')], limit=1) or False

        url_params = {
            'id': self.id,
            'action': self.env.ref('lease_management.action_my_product_lease').id,
            'model': 'product.lease',
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
            f"The Lease Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        subject = "Lease Request Has Been Rejected: %s" % self.name

        for approvers in self.approve_line:
            if approvers.user_id.id == self.env.user.id:
                approvers.write({'status': 'cancel'})

            if approvers.status == 'approve':
                print("app",approvers.status)
                if author:
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': approvers.user_id.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
        if self.user_id:
            print("req", self.user_id)
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': self.user_id.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)

    def action_legal_reject(self):
        pass


    def action_deligate(self):
        print("deligate")
        for lines in self.approve_line:
            if lines.user_id.id == self.env.user.id:
                print("Founddd User")
                action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_deligate_user_action_lease')
                action['context'] = {'default_request_id': self.id,
                                     'default_work_flow_type': 'lease',
                                     }

                return action

    def action_deligate_legal(self):
        print("deligate")
        for lines in self.legal_approve_line:
            if lines.user_id.id == self.env.user.id:
                print("Founddd User")
                action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_deligate_user_action_lease')
                action['context'] = {'default_request_id': self.id,
                                     'default_work_flow_type': 'legal',
                                     }

                return action

    def action_delegate_admin_lease(self):
        print("self",self.id)
        approve_users = set(self.approve_users.ids)  # Fetch IDs of approve_users
        approved_users = set(self.approved_users.ids)  # Fetch IDs of approved_users

        user_ids = list(approve_users - approved_users)

        if not user_ids:
            return
        for rec in self:
            action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_admin_action')
            action['context'] = {
                'default_lease': rec.id,
                'user_ids': user_ids,
                'type_id': 'lease'
            }
            print("the action is", action)
        return action

    def action_log_message(self):
        default_user_ids = self.approve_users.ids
        print(default_user_ids, "Usersssss")
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_log_message_action1')
        action['context'] = {'default_request_id': self.id,
                             }
        print(action)
        return action

    def send_replay(self):
        print("i am in replay")
        unreplied_rfi_record = self.pr_rfi_ids.filtered(lambda r: not r.replayed and r.to_user.id == self.env.user.id)
        print("the rfi record",unreplied_rfi_record)
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_log_replay_action1')
        action['context'] = {'default_message_id': unreplied_rfi_record.id,'default_message':unreplied_rfi_record.message}
        return action

    def action_add_approver(self):
        print("i am in add approver")
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.add_approver_lease_action')
        action['context'] = {'default_lease_id': self.id,
                             'default_work_flow_type': 'lease',}
        return action

    def action_add_legal_approver(self):
        print("i am in add approver")
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.add_approver_lease_action')
        action['context'] = {'default_lease_id': self.id,
                             'default_work_flow_type': 'legal',}
        return action

    def action_remark_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.remark_lease_approve_action')
        action['context'] = {'default_lease_id': self.id,
                             'default_approve_type': 'approve',
                             'default_work_flow_type': 'lease',
                             }
        print(action)
        return action

    def action_remark_legal_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.remark_lease_approve_action')
        action['context'] = {'default_lease_id': self.id,
                             'default_approve_type': 'approve',
                             'default_work_flow_type': 'legal',
                             }
        print(action)
        return action

    def action_remark_reject(self):
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.remark_lease_approve_action')
        action['context'] = {'default_lease_id': self.id,
                             'default_approve_type': 'reject',
                             'default_work_flow_type': 'lease',
                             }
        print(action)
        return action
    def action_remark_legal_reject(self):
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.remark_lease_approve_action')
        action['context'] = {'default_lease_id': self.id,
                             'default_approve_type': 'reject',
                             'default_work_flow_type': 'legal',
                             }
        print(action)
        return action

    def action_lease_revert(self):
        return {
            'name': 'Roll back to initiator',
            'view_mode': 'form',
            'view_id': self.env.ref('lease_management.view_lease_revert_back_form').id,
            'view_type': 'form',
            'res_model': 'revert.back.lease.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_revert_from': self.env.user.id,
                'default_lease_id': self.id,
                'default_initiator': self.user_id.id,
            },
        }

    @api.onchange('bill_to')
    def _onchange_bill_to(self):
        if self.bill_to:
            self.ship_to = self.bill_to

    @api.model
    def create(self, vals):
        print("exting")
        print(self)
        # existing_lease = self.env['product.lease'].search([
        #     ('product_id', '=', vals.get('product_id')),
        #     '|',
        #     ('state', '!=', 'expire'),
        #     ('state', '!=', 'reject'),
        # ],limit=1)
        # print("the ex",existing_lease.state)
        # if existing_lease and existing_lease.state != 'reject' or existing_lease.state != 'expire':
        #     print("the existing lease",existing_lease)
        #     raise UserError("")
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('product.lease') or _('New')
        res = super(ProductLease, self).create(vals)

        # model = self.env['ir.model'].sudo().search([('model', '=', self._name)],limit=1)
        # pending_vals = {
        #     'model': model.id,
        #     'name': res.name,
        #     'record': res.id,
        #     'date': date.today(),
        # }
        # pendings = self.env['pending.actions'].sudo().create(pending_vals)

        return res

    def view_purchase_order(self):
        print("inside purchase view")
        purchase_request = self.product_request_id
        purchase_order_data = self.env['purchase.order']
        if purchase_request:
            purchase_order_data |= self.env['purchase.order'].sudo().search([
                ('pr_id', '=', purchase_request.id),
                ('partner_id', '=', self.vendor_id.id)
            ])


        purchase_order_data |= self.env['purchase.order'].sudo().search([

                ('lease_id', '=', self.id)
            ])
        print("the purchase order data",purchase_order_data)

        unique_purchase_orders = purchase_order_data.filtered(lambda po: po.id)


        if unique_purchase_orders:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Orders',
                'res_model': 'purchase.order',
                'domain': [('id', 'in', unique_purchase_orders.ids)],
                'view_mode': 'tree,form',
                'target': 'current',
            }

    def view_purchase_request(self):
        return {
            'name': 'Purchase Request',
            'view_mode': 'form',
            'res_model': 'product.request',
            'res_id': self.product_request_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # def unlink(self):
    #     for lease in self:
    #         if lease.state == 'approve':
    #             # Find and delete the associated purchase order
    #             purchase_order = self.env['purchase.order'].search([('lease_id', '=', lease.id)])
    #             if purchase_order:
    #                 raise ValidationError("This record has a purchase order. Please cancel the purchase order before deleting.")
    #
    #     # Delete the product lease
    #     return super(ProductLease, self).unlink()



    class ProductLeaseLine(models.Model):
        _name = "lease.product.line"
        _description = "Product Lease"

        product_id = fields.Many2one('product.template', string="Product", store=True, force_save=True, required=True)
        vendors = fields.Many2many('res.partner', "lease_vendors", "lease_line", "vendor", string="Vendors",
                                   required=True)
        payment_terms = fields.Many2one('account.payment.term', "Payment Terms", required=True)
        qty = fields.Float(string="Quantity", required=True)
        unit_price = fields.Float(string="Unit Price", required=True)
        sub_total = fields.Float("SubTotal", readonly=True, compute="compute_sub_total")
        expected_date = fields.Date(string="Needed Date", required=True)
        contract_status = fields.Selection(
            selection=[('new', 'New'), ('in_contract', 'In Contract')],
            string='Contract',
            default='new',
            required=True
        )

        lease_id = fields.Many2one('product.lease', string='Lease Id',
                                   invisible=True)

        @api.depends('qty', 'unit_price')
        def compute_sub_total(self):
            for rec in self:
                if rec.qty and rec.unit_price:
                    rec.sub_total = rec.qty * rec.unit_price
                else:
                    rec.sub_total = ''

    class LeaseApproveLine(models.Model):
        _name = "lease.approve.line"
        _description = "Approve Lines"
        _order = 'approve_order asc'

        approve_lease_id = fields.Many2one('product.lease', string='Lease Approve',
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

    class LeaseApprovelegalLine(models.Model):
        _name = "lease.legal.approve.line"
        _description = "Approve Legal Lines"
        _order = 'approve_order asc'

        approve_lease_legal_id = fields.Many2one('product.lease', string='Lease Approve',
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


    class LeaseReccuringPO(models.Model):
        _name = "lease.recurring.po"
        _description = "Reccuring PO"

        recurring_lease_id = fields.Many2one('product.lease', string='Lease',
                                           invisible=True)

        po = fields.Many2one("purchase.order",string="PO")
        status = fields.Char(string="State")
        date = fields.Date("From Date")
        to_date = fields.Date("To Date")
        vendor = fields.Many2one('res.partner', string="Vendor")
        amount = fields.Float(string="Amount", store=True, readonly=True)
        parent_state = fields.Selection(related="recurring_lease_id.state", string="Parent State", store=True)
        vendor_user = fields.Many2many(
            'res.users',
            string='Vendor User',
            compute='_compute_corresponding_vendor_user_po',
            store=True,
        )

        @api.depends('vendor')
        def _compute_corresponding_vendor_user_po(self):
            for record in self:
                if record.vendor:
                    vendor_users = self.env['res.users'].sudo().search(
                        [('partner_id', 'in', record.vendor.ids)])
                    record.vendor_user = vendor_users
                else:
                    record.vendor_user = False


class Purchase(models.Model):
    _inherit = 'purchase.order'

    lease_id = fields.Many2one('product.lease', string="Lease Request")
    from_date = fields.Date(string="From Date", store=True)
    to_date = fields.Date(string="To Date", store=True)

    # @api.depends('lease_id')
    # def _compute_dates(self):
    #     for order in self:
    #         if order.lease_id:
    #             # Get the corresponding lease.recurring.po records
    #             recurring_pos = self.env['lease.recurring.po'].search([('recurring_lease_id', '=', order.lease_id.id)])
    #             if recurring_pos:
    #                 # Assuming you want to take the first matching record or you can modify it as needed
    #                 order.from_date = recurring_pos[0].date
    #                 order.to_date = recurring_pos[0].to_date
    #             else:
    #                 order.from_date = False
    #                 order.to_date = False
    #         else:
    #             order.from_date = False
    #             order.to_date = False

class invoice(models.Model):
    _inherit = 'account.move'


    lease_id = fields.Many2one('product.lease', string="Lease Request", compute='_compute_lease_and_dates', store=True)
    from_date = fields.Date(string="From Date", compute='_compute_lease_and_dates', store=True)
    to_date = fields.Date(string="To Date", compute='_compute_lease_and_dates', store=True)

    @api.depends('invoice_line_ids.purchase_line_id.order_id')
    def _compute_lease_and_dates(self):
        for invoice in self:
            purchase_orders = invoice.invoice_line_ids.mapped('purchase_line_id.order_id')
            if purchase_orders:
                # Assuming you want to take the first matching purchase order or you can modify it as needed
                purchase_order = purchase_orders[0]
                invoice.lease_id = purchase_order.lease_id
                invoice.from_date = purchase_order.from_date
                invoice.to_date = purchase_order.to_date
            else:
                invoice.lease_id = False
                invoice.from_date = False
                invoice.to_date = False


class LogMessage(models.TransientModel):
    _name = "log.message"
    _description = "Log"

    request_id = fields.Many2one(
        'product.lease', string='Lease Order', readonly=True)
    message = fields.Text("Message")
    user = fields.Many2one('res.users', "Requested By", default=lambda self: self.env.user.id,readonly=True)
    to_users = fields.Many2many('res.users', 'log_message_res_users_rel_lease', 'log_message_id','res_users_id',"Requested_To", domain=lambda self: self._domain_to_users(), required=True)
    # user_from = fields.Many2many('res.users', "User_From", domain="[('groups_id', 'not in', [44])]", required=True)
    branch_id = fields.Many2many('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')
    email = fields.Char(string='Email', compute='_compute_email')
    cc_email = fields.Char(string='Email', compute='_compute_cc_email')
    user_cc = fields.Many2many('res.users', 'log_message_cc_res_users_rel_lease', 'log_message_cc_id','res_users_cc_id',"Cc", domain=lambda self: self._domain_user_cc())
    concatenated_branch_names = fields.Char(string="Branch Names", compute='_compute_branch_names')
    # pending_numbers = fields.Many2many('log.message.pending.numbers', 'log_message_pending_numbers_rel', 'log_message_id', 'pending_numbers_id', string='Pending Numbers')

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
    #
    # @api.onchange('to_users')
    # def _compute_branch_id(self):
    #     for rec in self:
    #         rec.branch_id = rec.to_users.branch_id.id
    #         rec.email = rec.to_users.login



    @api.onchange('user_ids')
    def set_domain_for_user(self):
        print(self.user_ids)
        print(type(self.user_ids))
        print(list(self.user_ids))
    def confirm(self):
        pending_number_vals = []
        for rec in  self.request_id.pr_rfi_ids:
            if not rec.replay:
                raise UserError(_("Already Request for Information Pending for Reply"))

        model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')], limit=1)

        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.request_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_action_ids)


        for pending_action in pending_action_ids:

            # pending_number_vals.append((0, 0, {'number': pending_action.id}))
            new_name = f"{self.request_id.name} waiting for Request for Information reply"
            pending_action.sudo().write({'name': new_name})

            # pending_action.status='closed'
            # self.pending_numbers = [(0, 0, {'number': pending_action.id})]
            # print("log number is",self.pending_numbers)

        for request in self.request_id:
            if self.user and self.message:
                body = (
                    f"{self.env.user.name} has logged a message in {self.request_id.name}.{self.message}"
                )
                base_url = self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Lease/Rent')], limit=1) or False

                url_params = {
                    'id': self.request_id.id,
                    'action': self.env.ref(
                    'lease_management.action_product_lease').id,
                    'model': 'product.lease',
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
                    'email_to':  ', '.join(self.to_users.mapped('login')),
                    'email_cc': self.cc_email,
                    'author_id': author.id
                }
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()

                subject = "Query was raised against Lease Request : %s" % self.request_id.name

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A Lease Request with the name <strong>{self.request_id.name} is Pending at Request For Information where you are "
                    f"a approver.<br>"

                )
                if self.request_id.state == 'request':
                    for user in self.request_id.approve_line:
                        if self.env.user.id != user.id and user.status == 'approve':
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.user_id.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    for user in self.to_users:
                        print("the user test", user.id)
                        rfi_vals = {
                            'user_id': self.env.user.id,
                            'to_user': user.id,
                            'message': self.message,
                            # 'pending_numbers': pending_number_vals
                        }
                        print("the pending vals",rfi_vals)

                        new_rfi_vals = self.env['pr.lease.rfi'].sudo().create(rfi_vals)

                        self.request_id.pr_rfi_ids |= new_rfi_vals

                        model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': "Request for Information" + " " + "on" + " " + self.request_id.name,
                            'record': self.request_id.id,
                            'branch': self.request_id.bill_to.id,

                            'date': date.today(),
                            'record_line': new_rfi_vals.id,
                            'approve_users': [(6, 0, [user.id])],
                        }
                        pendings = self.env['pending.actions'].sudo().create(pending_vals)
                        print("the new rfi vals are", new_rfi_vals.id)
                if self.request_id.state == 'legal_approve':

                    for user in self.request_id.legal_approve_line:
                        if self.env.user.id != user.id and user.status == 'approve':
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.user_id.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    for user in self.to_users:
                        print("the user test", user.id)
                        rfi_vals = {
                            'user_id': self.env.user.id,
                            'to_user': user.id,
                            'message': self.message,
                            'legal': True,
                            # 'next_pending_ids': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False
                        }

                        new_rfi_vals = self.env['pr.lease.rfi'].sudo().create(rfi_vals)

                        self.request_id.pr_rfi_ids |= new_rfi_vals

                        model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': "Request for Information" + " " + "on" + " " + self.request_id.name,
                            'record': self.request_id.id,
                            'branch': self.request_id.bill_to.id,

                            'date': date.today(),
                            'record_line': new_rfi_vals.id,
                            'approve_users': [(6, 0, [user.id])],
                        }
                        pendings = self.env['pending.actions'].sudo().create(pending_vals)
                        print("the new rfi vals are", new_rfi_vals.id)



                self.request_id.message_post(body=f"RFI (Request for Information) message from the <strong>@{self.user.name}</strong>, {self.message}")
                #
                request.state='rfi'
        pending = self.env['pending.actions'].sudo().search(
            [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id),('name', 'not like', 'waiting for Request for Information reply')], order='id desc', limit=1)
        print("if,,,,,,,,,..pending actions", pending)
        if pending:
            print("if")
            return pending.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

            return action



class PrRfiLines(models.Model):
    _name = "pr.lease.rfi"
    _description = "RFI Line"

    lease_id = fields.Many2one('product.lease', string='Product Request Id',
                            invisible=True)

    user_id = fields.Many2one('res.users', string="From")
    to_user = fields.Many2one('res.users', string="To")
    message = fields.Char("Message")
    replay = fields.Char("Replay")
    replayed = fields.Boolean("Is Replayed")
    status = fields.Selection(
        selection=[('open', 'Open'), ('close', 'Closed')],
        string='Status',
        default='open',
        required=True, tracking=True
    )
    legal = fields.Boolean("IS LE")
    is_to_user_id = fields.Boolean(default=False, compute='_get_current_user_details')
    # pending_numbers = fields.Many2many('log.message.pending.numbers', 'log_message_pending_numbers_rel',
    #                                    'log_message_id', 'pending_numbers_id', string='Pending Numbers')

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.to_user.name}"))
        return result

    # next_pending_ids = fields.Many2many(
    #     'pending.actions',
    #     string='Pending Action',
    #     relation='last_pend',
    #     column1='pr_rfi_lease_id',
    #     column2='pending_actions_id',
    #     store=True
    # )

    @api.depends('to_user')
    def _get_current_user_details(self):
        current_user_id = self.env.user.id
        for record in self:
            if record.to_user and record.to_user.id == current_user_id:
                record.is_to_user_id = True
            else:
                record.is_to_user_id = False

    def send_replay(self):
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_log_replay_action1')
        action['context'] = {'default_message_id': self.id}
        return action


class LogMessageReplay(models.TransientModel):
    _name = "message.replay"
    _description = "Log"

    message_id = fields.Many2one(
        'pr.lease.rfi', string='Reply', readonly=True)
    message = fields.Char(string="Message", readonly=True)
    replay = fields.Text("Reply", required=True)

    def confirm(self):
        print("the test vals",self.message_id.id)

        model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')], limit=1)
        print(model.id)
        print(self.message_id.id)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record_line', '=', self.message_id.id),('status', '=', 'open')],limit=1)
        print("pending action",pending_action)
        for rec in pending_action:
            if self.env.user in rec.approve_users:
                print("record to close", rec)
                rec.status = 'closed'

        for line in self.message_id:
            line.replay = self.replay
            line.replayed = True
            line.status = 'close'
        self.message_id.lease_id.message_post(
            body=f"<strong>@{self.env.user.name}</strong>,replayed: {self.replay}, to {self.message_id.user_id.name}")


        model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')], limit=1)
        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.message_id.lease_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_action_ids)
        print("last pend is", pending_action_ids)

        all_record_lines_replayed = all(line.replay for line in self.message_id.lease_id.pr_rfi_ids)
        print("all",all_record_lines_replayed)

        if all_record_lines_replayed:
            if self.message_id.legal == True:
                self.message_id.lease_id.state = 'legal_approve'
            else:
                self.message_id.lease_id.state = 'request'
            # for rfi_line in self.message_id.lease_id.pr_rfi_ids:
            #     for pending_number in rfi_line.pending_numbers:
            #         corresponding_pending_action = self.env['pending.actions'].sudo().search(
            #             [('id', '=', pending_number.number), ('status', '=', 'open')])
            #         print("the corresponding pending actions are",corresponding_pending_action)
            #         corresponding_pending_action.sudo().write({'date': fields.Datetime.now()})
            for pending_action in pending_action_ids:
                print("all are replayed")
                new_name = f"{self.message_id.lease_id.name} --Replayed for Request for Information"
                pending_action.sudo().write({'name': new_name})
                pending_action.sudo().write({'date': fields.Datetime.now()})

        pending = self.env['pending.actions'].sudo().search(
            [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id),('name', 'not like', 'waiting for Request for Information reply')], order='id desc', limit=1)
        print("if,,,,,,,,,..pending actions", pending)
        if pending:
            print("if")
            return pending.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

            return action
class Remark(models.TransientModel):
    _name = "lease.remark"
    _description = "Lease Remark"
    _inherit = ['mail.thread']

    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Char("Remark", required=True)
    lease_id = fields.Many2one('product.lease', string='Lease', readonly=True)
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('reject', 'Rejected')],
        string='State')
    work_flow_type = fields.Selection(
        selection=[('lease', 'lease'), ('legal', 'legal')],
        string='Work Flow')



    def confirm_remark(self):

        if self.lease_id and self.approve_type == 'approve' and self.work_flow_type== 'lease':
            print("i am inside the confirm")
            # self.lease_id.message_post(body=f" {self.env.user.name} Approved.")
            self.lease_id.message_post(body="Remarks " + self.replay)
            vals = {
                'lease_id': self.lease_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Lease Request",
                'approve_type': 'approve',

            }
            remarks_save = self.env['remark.lease.save'].sudo().create(vals)
            self.lease_id.action_approve()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action
        if self.lease_id and self.approve_type == 'reject' and self.work_flow_type== 'lease':
            # self.lease_id.message_post(body=f" {self.env.user.name} Rejected.")
            self.lease_id.message_post(body="Remarks " + self.replay)
            vals = {
                'lease_id': self.lease_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Lease Request",
                'approve_type': 'reject',

            }
            remarks_save = self.env['remark.lease.save'].sudo().create(vals)
            self.lease_id.action_reject()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action



        if self.lease_id and self.approve_type == 'approve' and self.work_flow_type== 'legal':
            print("i am inside the confirm")
            # self.lease_id.message_post(body=f" {self.env.user.name} Approved.")
            self.lease_id.message_post(body="Remarks " + self.replay)
            vals = {
                'lease_id': self.lease_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Lease Request",
                'approve_type': 'approve',

            }
            remarks_save = self.env['remark.lease.save'].sudo().create(vals)
            self.lease_id.action_legal_approver()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action
        if self.lease_id and self.approve_type == 'reject' and self.work_flow_type== 'legal':
            # self.lease_id.message_post(body=f" {self.env.user.name} Rejected.")
            self.lease_id.message_post(body="Remarks " + self.replay)
            vals = {
                'lease_id': self.lease_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Lease Request",
                'approve_type': 'reject',

            }
            remarks_save = self.env['remark.lease.save'].sudo().create(vals)
            self.lease_id.action_legal_reject()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action

class RemarkSave(models.Model):
    _name = "remark.lease.save"
    _description = "Remark"

    lease_id = fields.Many2one('product.lease', string='Lease', readonly=True)
    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Char("Remark", required=True)
    for_type = fields.Char("Approval Type")
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('reject', 'Rejected'),('deligate','Delegate')],
        string='State')
    work_flow_type = fields.Selection(
        selection=[('lease', 'lease'), ('legal', 'legal')],
        string='Work Flow')


class AddApprover(models.TransientModel):
    _name = 'add.approver.lease.wizard'

    _description = "Add Approver Lease workflow"

    lease_id = fields.Many2one('product.lease', string='Lease Request Id',invisible=True)
    user = fields.Many2one('res.users', string="User", required=True, domain="[('groups_id', 'not in', [44])]")

    order = fields.Integer(string="Order No", required=True)

    branch_id = fields.Many2one('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')

    email = fields.Char(string='Email')

    work_flow_type = fields.Selection(
        selection=[('lease', 'lease'), ('legal', 'legal')],
        string='Work Flow')

    @api.onchange('user')
    def _compute_branch_id(self):

        for rec in self:
            rec.branch_id = rec.user.branch_id.id

            rec.email = rec.user.login

    def add_user(self):
        print("the lease id is",self)

        if self.lease_id:

            if self.work_flow_type == 'lease':
                approve_lines = self.lease_id.approve_line
            else:
                approve_lines = self.lease_id.legal_approve_line

            if any(line.user_id == self.user for line in approve_lines):
                raise UserError(_("This user is already in the approval line."))

            if self.work_flow_type == 'lease':

                for line in self.lease_id.approve_line:

                    if line.user_id == self.env.user:
                        current_order = line.approve_order

                records = self.env['lease.approve.line'].sudo().search([('approve_lease_id', '=', self.lease_id.id)])

                highest_record = max(records, key=lambda r: r.approve_order)

                highest_approve_order = highest_record.approve_order

                if current_order < self.order and self.order <= highest_approve_order + 1:

                    self.lease_id.approve_users |= self.user

                    model = self.env['lease.approve.line'].sudo().search(
                        [('approve_lease_id', '=', self.lease_id.id), ('approve_order', '>=', self.order)])

                    for line in model:
                        line.approve_order += 1

                    vals = {

                        'approve_lease_id': self.lease_id.id,

                        'user_id': self.user.id,

                        'approve_order': self.order,

                        'status': 'draft'

                    }

                    approve_line = self.env['lease.approve.line'].sudo().create(vals)

                    self.lease_id.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")

                elif self.order > highest_approve_order + 1:

                    raise UserError(_("Order No cannot be exceeded than existing max order No "))

                else:

                    raise UserError(_("Order No cannot be less than or equal to your Order No"))

            if self.work_flow_type == 'legal':
                print(self.lease_id.id)
                print("i am here")

                for line in self.lease_id.legal_approve_line:
                    print("i am here")

                    if line.user_id == self.env.user:
                        current_order = line.approve_order

                records = self.env['lease.legal.approve.line'].sudo().search([('approve_lease_legal_id', '=', self.lease_id.id)])
                print("the record is",records)

                highest_record = max(records, key=lambda r: r.approve_order)

                highest_approve_order = highest_record.approve_order

                if current_order < self.order and self.order <= highest_approve_order + 1:
                    print("i am here")

                    self.lease_id.legal_approve_users |= self.user
                    print("self",self.lease_id.legal_approve_users)

                    model = self.env['lease.legal.approve.line'].sudo().search(
                        [('approve_lease_legal_id', '=', self.lease_id.id), ('approve_order', '>=', self.order)])
                    print("ex",model)

                    for line in model:
                        print("the line is",model)
                        line.approve_order += 1

                    vals = {

                        'approve_lease_legal_id': self.lease_id.id,

                        'user_id': self.user.id,

                        'approve_order': self.order,

                        'status': 'draft'

                    }
                    print("the vals are",vals)

                    approve_line = self.env['lease.legal.approve.line'].sudo().create(vals)
                    print("the approveline",approve_line)

                    self.lease_id.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")

                elif self.order > highest_approve_order + 1:

                    raise UserError(_("Order No cannot be exceeded than existing max order No "))

                else:

                    raise UserError(_("Order No cannot be less than or equal to your Order No"))



class RevertBack(models.Model):
    _name = 'revert.lease.back'
    _description = "Revert"

    lease_id = fields.Many2one(
        'product.lease', string='Lease order', readonly=True)
    reason = fields.Char("Message")
    revert_from = fields.Many2one(
        'res.users', string='Revert User')

class PrRfiLine(models.Model):
    _name = "pr.rfi"
    _description = "RFI Line"

class TerminateReasonLease(models.TransientModel):
    _name = "lease.terminate.wizard"
    _description = "Terminate Lease"

    reason = fields.Char(string="Reason", store=True,required=True)

    lease_id = fields.Many2one(
        'product.lease', string='Lease', readonly=True)
    cancel_date = fields.Date(string="Termination Date", default=lambda self: datetime.today().date() ,readonly=True)


    def terminate(self):
        print("dddd")
        for lease in self.lease_id:
            lease.message_post(body="Lease Terminated due to " + self.reason + " On " + str(self.cancel_date))

            lease.state = "terminate"
            # contract.active_status = "terminate"
            # contr.reason = self.reason
            # contract.cancel_date = self.cancel_date

class ProductRequestLine(models.Model):
    _name = "product.lease.request.line"
    _description = "Product Lease Request"

    product_lease_request_id = fields.Many2one('product.lease', string='Product Lease Request Id',
                                         invisible=True,required=True,ondelete='cascade')

    product = fields.Many2one('product.template', string="Product", store=True, force_save=True,
                              required=True,domain="[('categ_id.name', '=', 'Lease/Rent')]")

    quantity = fields.Float(string="Quantity", required=True)

    unit_price = fields.Float(string="Unit Price", required=True)

    uom = fields.Many2one('uom.uom', 'UOM', related='product.uom_po_id')

    amount = fields.Float(string="Amount", compute="_compute_amount", store=True, readonly=True)

    increment_amount = fields.Selection([
        ('total', 'Total'),
        ('custom', 'Custom Amount'),
    ], 'Increment Based On')

    increment_by = fields.Selection([
        ('amount', 'Amount'),
        ('percent', '%'),
    ], 'Increment By')
    inc_date = fields.Date("Date", store=True)
    inc_value = fields.Float("Monthly Value", store=True)
    inc_period_value = fields.Float("Increment Period Value", store=True,compute='compute_inc_period_increment')
    inc_amount = fields.Float("Rate")
    total_increment_value = fields.Float("Amount Monthly Incremented", compute='compute_total_increment',store=True)
    is_increment = fields.Boolean("Increment", default=True)
    amount_payable = fields.Float("Total Amount Payable ")

    @api.depends('total_increment_value')
    def compute_inc_period_increment(self):
        for record in self:
            print("checking yearly")
            print("thr fjjj",record.product_lease_request_id.increment_method)
            if record.total_increment_value and record.product_lease_request_id.increment_method:
                print("the increments are", record.product_lease_request_id.increment_method, record.total_increment_value)
                if record.product_lease_request_id.increment_method == 'year':
                    record.inc_period_value = record.total_increment_value * 12
                elif record.product_lease_request_id.increment_method == 'biennial':
                    record.inc_period_value = record.total_increment_value * 24
                    print(record.inc_period_value)
                elif record.product_lease_request_id.increment_method == 'triennial':
                    record.inc_period_value = record.total_increment_value * 36
                elif record.product_lease_request_id.increment_method == 'custom' and record.inc_date:
                    today = date.today()
                    inc_date = record.inc_date

                    # Since inc_date is always greater than today, ensure correct calculation
                    delta = relativedelta(inc_date, today)  # inc_date first since it is in the future
                    print("The delta is", delta)
                    months = delta.years * 12 + delta.months
                    print("The months are", months)
                    record.inc_period_value = record.total_increment_value * months
            else:
                if not record.total_increment_value:
                    record.total_increment_value = 0

    @api.onchange('increment_amount', 'amount', 'quantity')
    def onchange_increment_amount(self):
        print("kkk")
        if self.increment_amount == 'total':
            print("hai")
            self.inc_value = self.amount
            print("amount",self.inc_value)

    @api.depends('inc_amount', 'inc_value', 'increment_by')
    def compute_total_increment(self):
        for record in self:
            print("akk",record)
            print("the val",record.inc_value,record.inc_amount,record.increment_by)
            print("the records are", record.total_increment_value)
            if record.inc_value and record.inc_amount and record.increment_by:
                print("the increments  check are", record.inc_value, record.inc_amount, record.increment_by)
                if record.increment_by == 'amount':
                    print("i am in amount")
                    record.total_increment_value = record.inc_amount + record.inc_value
                    print("the otl", record.total_increment_value)
                elif record.increment_by == 'percent':
                    percentage = record.inc_amount / 100
                    record.total_increment_value = record.inc_value + (record.inc_value * percentage)

                else:
                    record.total_increment_value = 0
            else:
                record.total_increment_value = 0

    @api.constrains('quantity', 'unit_price')
    def _check_positive_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            if line.unit_price <= 0:
                raise ValidationError("Unit Price must be greater than zero.")


    @api.depends('unit_price', 'quantity')
    def _compute_amount(self):
        for line in self:
            line.amount = line.unit_price * line.quantity

    @api.ondelete(at_uninstall=False)
    def _unlink_purchase_line(self):
        for line in self:
            if line.product_lease_request_id.state != 'draft':
                raise UserError(_('Cannot delete a purchase request line which is in state other than DRAFT'))

    @api.constrains('product_lease_request_id', 'product')
    def _check_unique_product(self):
        for line in self:
            if line.product_lease_request_id and line.product:
                existing_lines = self.sudo().search([
                    ('id', '!=', line.id),
                    ('product_lease_request_id', '=', line.product_lease_request_id.id),
                    ('product', '=', line.product.id),
                ])
                if existing_lines:
                    raise ValidationError("The same product cannot be selected multiple times in a single request.")

    def copy(self, default=None):
        default = dict(default or {})
        return super(ProductRequestLine, self).copy(default)



class VendorRequestLine(models.Model):
    _name = "vendor.lease.request.line"
    _description = "Vendor Lease Request"

    vendor_lease_request_id = fields.Many2one('product.lease', string='Vendor Lease Request Id',
                                               invisible=True,required=True,ondelete='cascade')

    vendor_id = fields.Many2one('res.partner', string="Vendor",required=True)
    percentage_of_amount = fields.Float(string="Total Percentage(%)", compute="_inverse_amount",inverse="_compute_amount",tracking=True,required=True,store=True)
    amount = fields.Float(string="Amount", compute="_compute_amount",inverse="_inverse_amount", store=True)
    increment_amount = fields.Selection([
        ('total', 'Total'),
        ('custom', 'Custom Amount'),
    ], 'Increment Based On')

    vendor_copy = fields.Boolean(string="Copy vendor", default=False)


    @api.depends('vendor_id', 'percentage_of_amount', 'vendor_lease_request_id.total')
    def _compute_amount(self):
        for line in self:
            if line.percentage_of_amount:
                print("the total",line.vendor_lease_request_id.total)
                line.amount = line.vendor_lease_request_id.total * (line.percentage_of_amount / 100)
                print("the amount",line.amount)

    @api.depends('vendor_id', 'amount', 'vendor_lease_request_id.total')
    def _inverse_amount(self):
        for line in self:
            print("the total", line.vendor_lease_request_id.total)
            if line.amount and line.vendor_lease_request_id.total:
                line.percentage_of_amount = (line.amount / line.vendor_lease_request_id.total) * 100

    @api.constrains('percentage_of_amount')
    def _check_percentage_sum(self):
        for line in self:
            if not line.vendor_copy:
                total_percentage = 0
                total_percentage = sum(
                    line.vendor_lease_request_id.vendor_lease_request_line_ids.mapped('percentage_of_amount'))
                print("the total percentage is", total_percentage)
                if total_percentage > 100:
                    raise ValidationError("Total percentage cannot exceed 100%.")
                if total_percentage < 100:
                    raise ValidationError("Total percentage cannot less than 100%.")

    @api.constrains('amount')
    def _check_amount_total(self):
            for line in self.env['vendor.lease.request.line'].filtered(
                    lambda r: r.vendor_lease_request_id == self.vendor_lease_request_id):
                if not line.vendor_copy:
                    total_amount = 0
                    total_amount = sum(line.vendor_lease_request_id.vendor_lease_request_line_ids.mapped('amount'))
                    if total_amount > line.vendor_lease_request_id.total:
                        raise ValidationError("Total amount cannot exceed the total of the vendor lease request.")
                    if total_amount < line.vendor_lease_request_id.total:
                        raise ValidationError("Total amount cannot less than the total of the vendor lease request.")

    def copy(self, default=None):
        print("I am in copied function", self)
        default = dict(default or {})
        default.update({
            'percentage_of_amount': self.percentage_of_amount,
            'amount': self.amount,
        })
        copied_record = super(VendorRequestLine, self).copy(default)
        print("The copied function", copied_record)
        return copied_record


class Increment(models.Model):
    _name = "lease.increments"
    _description = "Lease Request Increment"

class TDS(models.Model):
    _name = "tds.master"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "TDS"
    _rec_name = "TDS"

    TDS = fields.Char(string='TDS', tracking=True,  required=True,)








