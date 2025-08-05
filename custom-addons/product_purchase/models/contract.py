from datetime import datetime, date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
# import datetime
import base64
import logging
import xlrd
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo.tools.safe_eval import json

_logger = logging.getLogger(__name__)


class VendorContract(models.Model):
    _name = "contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vendor Request"
    _order = 'id desc'

    current_date = datetime.now().date()

    tender_id = fields.Many2one('tenders', string="Tender Id")
    name = fields.Char(string="Ref", readonly=True, required=True, copy=False, default='New')

    requested = fields.Many2one('res.users', string="Requested By", store=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor", store=True, force_save=True)
    user_id = fields.Many2one('res.users', string="User Id")
    # total_price = fields.Float(string="Total Price",compute='compute_total_price')
    requested_date = fields.Date(string="Requested Date", default=datetime.today().date())
    expected_date = fields.Date(string="Expected Date")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_ids = fields.Many2many('res.company', 'vendor_companies_tender_rel', 'tnd_id', 'comp_id',
                                   string="Allowed Companies")

    branch_ids = fields.Many2many('res.branch', 'vendor_branches_req_rel', 'contrct_req_id', 'branchs_id',
                                  string="Allowed Branches")

    branch_domain = fields.Char(
        compute="_compute_branch_domain",
        readonly=True,
        store=False,
    )

    # company_ids = fields.Many2many('res.partner', string="Requested To")
    product_requested_id = fields.Many2one('product.request', string="Product Requested ID")
    renew_id = fields.Many2one('product.tender.line', string="Renewal")

    vendor_request_status = fields.Selection([('draft', 'Draft'),
                                              ('accept', 'Accept'),
                                              ('reject', 'reject')], string='Contract Status of Vendor',
                                             default='draft')
    contract_status = fields.Selection([('draft', 'Draft'),
                                        ('accept', 'Quotation Sent'),
                                        ('cancel', 'Cancelled')], string='Contract Status',
                                       default='draft', tracking=True)
    tender_response_qtn_check = fields.Boolean(string="Tender qtn Comp Check", default=False)
    from_date = fields.Date(string="Contract Start Date", tracking=True, default=current_date)
    to_date = fields.Date(string="Contract End Date", tarcking=True)
    tender_response_tender_check = fields.Boolean(string="Tender Res Comp Check", default=False)

    approve_check = fields.Boolean(string="Approve Check", default=False)
    payment_terms = fields.Many2one('account.payment.term', "Payment Terms")
    lead_time = fields.Integer("Lead Time in days")

    # user_id = fields.Many2one('res.users', string="Requested User", default=lambda self: self.env.user.id)

    terms = fields.Text(string='Terms & Conditions', tracking=True)
    vendor_details = fields.Text(string='Vendor Details', tracking=True)
    compared = fields.Boolean("Compared")
    deadline = fields.Datetime(string="Deadline ")

    approve_users = fields.Many2many(
        'res.users',
        'tender_vendor_approve_users_rel',
        'request_id',
        'user_id',
        string='Approve Users',
        # default=lambda
        #     self: self.env.ref("product_purchase.group_initial_approval").users.ids
    )

    approved_users = fields.Many2many(
        'res.users',
        'tender_vendor_approved_users_rel',
        'request_id',
        'user_id',
        string='Approved Users',
    )

    next_approve_user_id = fields.Many2many('res.users', string="Next Approve User ID")

    tender_approve_line = fields.One2many('tender.approve.line',
                                          'tender_id',
                                          string='Tender Approve Line',
                                          tracking=True)

    state = fields.Selection(
        selection=[('pending', 'Pending Approval'), ('negotiation', 'Negotiation'), ('accept', 'Accepted'),
                   ('reject', 'Rejected'), ('expire', 'Expired')],
        string='Status',
        default='draft',
        required=True, tracking=True
    )

    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True,
                                    required=True)

    # exp_category = fields.Many2one('expense.category', 'Expense Category', required=True)

    # exp_category_domain = fields.Char(
    #     compute="_compute_exp_category_domain",
    #     readonly=True,
    #     store=False,
    # )

    vendor_contract_line = fields.One2many('vendor.contract.lines',
                                           'vendor_lines',
                                           string='Products Request Line',
                                           tracking=True)
    product_group = fields.Many2many('products.group', 'groups_vendor_contract_req_rel', 'contrcts_id', 'group_id',
                                     string="Product Group")

    total_price = fields.Float(string="Company Estimated Contract Value (excluding GST)", compute="compute_total_amount")
    total_vendor_amount = fields.Float(string="Your Estimated Total Contract Value (excluding GST)", compute="compute_total_vendor_amount")

    rfq_heads = fields.Many2many('tenders', 'vendor_multi_rfq_rel', 'rqst_id', 'rfq_id',
                                 string="Contracts")

    main_rfq = fields.Many2one('tenders', 'Request')
    purchase_plan = fields.Selection([
        ('monthly', 'Monthly '),
        ('one_time', 'One Time'),
        ('yearly', 'Yearly'),
    ], string="Purchase Plan")
    attachment_ids = fields.Many2many('ir.attachment', 'class_ir_attachments_contract_rel', 'class_id', 'attachment_id',
                                      'Attachments')
    main_remark = fields.Text(string="Remark")
    reference_doc =  fields.Many2many('ir.attachment', 'class_ir_attachments_client_rel', 'class_id', 'attachment_id',
                                      'Reference Doc',readonly=True)
    
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)

    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            tender = self.env['tenders'].browse(vals.get('tender_id'))
            print("tender name", tender.name)
            prefix = tender.name + '_' if tender else ''
            sequence_number = self.env['ir.sequence'].next_by_code('contract') or 'New'
            vals['name'] = prefix + sequence_number
        result = super(VendorContract, self).create(vals)
        return result

    @api.depends('vendor_contract_line')
    def compute_total_amount(self):
        if (self.purchase_plan == 'monthly'):

            total_amount = 0
            # from_date = self.from_date
            # to_date = self.to_date
            months = 1
            if self.from_date and self.to_date:
                from_date = datetime.strptime(str(self.from_date), '%Y-%m-%d')
                to_date = datetime.strptime(str(self.to_date), '%Y-%m-%d')
                months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)

            for total in self:
                for lines in total.vendor_contract_line:
                    total_amount += lines.unit_price * lines.quantity * (months)
            self.total_price = total_amount
        else:
            total_amount = 0
            for total in self:
                for lines in total.vendor_contract_line:
                    total_amount += lines.quantity * lines.unit_price

            self.total_price = total_amount
    @api.depends('vendor_contract_line')
    def compute_total_vendor_amount(self):
        if (self.purchase_plan == 'monthly'):

            total_vendor_amount = 0
            # from_date = self.from_date
            # to_date = self.to_date
            months = 1
            if self.from_date and self.to_date:
                from_date = datetime.strptime(str(self.from_date), '%Y-%m-%d')
                to_date = datetime.strptime(str(self.to_date), '%Y-%m-%d')
                months = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)

            for total in self:
                for lines in total.vendor_contract_line:
                    total_vendor_amount += lines.vendor_price * lines.quantity * (months)
            self.total_vendor_amount = total_vendor_amount
        else:
            total_vendor_amount = 0
            for total in self:
                for lines in total.vendor_contract_line:
                    total_vendor_amount += lines.quantity * lines.vendor_price

            self.total_vendor_amount = total_vendor_amount



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

    def vendor_deadline(self):
        now = datetime.today()
        record = self.env["contract"].sudo().search([('state', 'in', ('pending','negotiation'))])
        for rec in record:
            if now > rec.deadline :
                rec.state = 'expire'
                rec.message_post(body="Deadline Reached")
                if rec.tender_id:
                    rec.tender_id.message_post(body="Vendor Deadline Reached")
                    rec.tender_id.state = 'deadline_reach'

    def action_accept(self):
        print(self.user_id)
        record = self.env["vendor.contract.lines"].sudo().search([('vendor_lines', '=', self.id)])
        print("Accept Button ", record)
        if record:
            existing_product_ids = record.mapped('product_id.id')  
            contract_lines = self.env["contract.request.lines"].sudo().search(
                [('contracts_lines', '=', self.tender_id.id)])

            for rec in record:
                if not rec.product_id and rec.quantity and rec.vendor_price:
                    raise ValidationError(
                        _("A line in Vendor Contract Lines has quantity and price but no product. Please complete the product details before proceeding."))
                if rec.product_id and not rec.quantity:
                     raise ValidationError(_("Product '%s' in Vendor Contract Lines does not have a quantity specified. Please add a quantity before proceeding.") % rec.product_id.name)

            for line in contract_lines:
                if line.product_id.id not in existing_product_ids:
                    raise ValidationError(_(
                        "Product '%s' in Contract Request Lines does not exist in Vendor Contract Lines."
                    ) % line.product_id.name)
            for rec in record:

                if (rec.vendor_price == False):
                    raise ValidationError(_("Vendor Price cannot be zero"))
                
                if (rec.quantity == False):
                    raise ValidationError(_("Quantity cannot be zero"))

                existing_lines = self.env["contract.request.lines"].sudo().search([
                    ('contracts_lines', '=', self.tender_id.id), 
                    ('product_id', '=', rec.product_id.id)
                ])


                if existing_lines:
                    for existing_line in existing_lines:
                        if rec.quantity != existing_line.quantity:
                            raise ValidationError(_(
                                "You cannot modify the quantity of product '%s' in Contract Request Lines. "
                                "The current quantity is %s."
                            ) % (rec.product_id.name, existing_line.quantity))

                else:
                  
                    self.env["contract.request.lines"].create({
                        'contracts_lines': self.tender_id.id,
                        'product_id': rec.product_id.id,
                        'vendor_price': rec.vendor_price,
                        'quantity': rec.quantity,
                        'brand': rec.brand,
                        'oem': rec.oem,
                        'pack': rec.pack,
                        'uom': rec.uom.id,
                    })

            for rec in record:
                line_id = self.env["contract.request.lines"].sudo().search([('id', '=', rec.tender_line_id.id)])
                line_ids = self.env["contract.request.lines"].browse(line_id.id).write(
                    {'vendor_price': rec.vendor_price})
                self.tender_id.vendor_details = self.vendor_details
            self.env["tenders"].browse(self.tender_id.id).write({'state': 'vendor_approved'})


        self.env['contract.price.history'].create({
            'contract_id': self.tender_id.id,
            'main_rfq':self.main_rfq.id,
            'contract_request_id': self.id,
            'total_price': self.total_vendor_amount,
            'vendor_id': self.vendor_id.id,
            'date_updated': fields.Datetime.now(),
        })

        self.state = 'accept'
        self.tender_id.write({
            'attachment_ids': [(6, 0, self.attachment_ids.ids)]
        })
        subject = "Contract Request %s Accepted by: %s" % (self.tender_id.name, self.vendor_id.name)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Contracts/Agreements')], limit=1) or False

        url_params = {
            'id': self.tender_id.id,
            'action': self.env.ref('product_purchase.action_tender_status').id,
            'model': 'tenders',
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
            f"Dear {self.requested.name}, "
            f"A Contract Request by the name <strong>{self.tender_id.name} has been Approved by {self.vendor_id.name}.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.requested.email,
            'auto_delete': False,
            'author_id': author.id
        }
        mail_record = self.env['mail.mail'].sudo().create(mail_values)

    def action_reject(self):
        self.env["tenders"].browse(self.tender_id.id).write({'state': 'vendor_rejected'})
        self.state = 'reject'

        subject = "Contract Request %s Rejected by: %s" % (self.tender_id.name, self.vendor_id.name)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Purchase Requests')], limit=1) or False

        url_params = {
            'id': self.tender_id.id,
            'action': self.env.ref('product_purchase.action_product_requests').id,
            'model': 'tenders',
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
            f"Dear {self.requested.name}, "
            f"A Contract Request by the name <strong>{self.tender_id.name} has been Rejected by {self.vendor_id.name}.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.requested.email,
            'auto_delete': False,
            'author_id': author.id
        }
        mail_record = self.env['mail.mail'].sudo().create(mail_values)


class VendorContractLine(models.Model):
    _name = "vendor.contract.lines"

    vendor_lines = fields.Many2one('contract', string='Vendor Request')
    tender_line_id = fields.Many2one('contract.request.lines', string='Tender and vendor line connection')
    product_id = fields.Many2one('product.template', string='Product')
    brand = fields.Char('Brand', related='product_id.brand')
    oem = fields.Char('OEM', related='product_id.oem')
    uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_po_id')
    pack = fields.Float('Pack Size', related='product_id.pack_size')
    quantity = fields.Float(string='Quantity')
    unit_price = fields.Float(string='Unit Price')
    vendor_price = fields.Float(string="Vendor Price")
    product_group = fields.Char("Product Group")

    vendor = fields.Many2one("res.partner", "Vendor", related='vendor_lines.vendor_id')
    payment_terms = fields.Many2one('account.payment.term', "Payment Terms", related='vendor_lines.payment_terms')
    lead_time = fields.Integer("Lead Time in days", related='vendor_lines.lead_time')
    terms = fields.Text(string='Terms & Conditions', related='vendor_lines.terms')
    selected_line = fields.Boolean("Line Selected")

    status = fields.Selection([('select', 'Selected'),
                               ('reject', 'Rejected'),
                               ], string='Comparison Status',
                              tracking=True)