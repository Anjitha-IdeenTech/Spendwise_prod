from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date

from werkzeug.urls import url_encode

from collections import defaultdict


from operator import attrgetter


class InvoiceInherit(models.Model):
    _inherit = "account.move"
    _description = 'Invoice Request'


    company_user_id = fields.Many2one('res.users', string="User ID")



    invoice_approve_line = fields.One2many('invoice.approve.line',

                                      'invoice_id',

                                      string='Invoice Approve Line',

                                      tracking=True)

    invoice_payment_approve_line = fields.One2many('invoice.payment.approve.line',

                                           'invoice_id',

                                           string='Invoice Payment Approve Line',

                                           tracking=True)

    is_confirmed = fields.Boolean("Is Confirmed")

    is_auto_po = fields.Boolean("Automated PO")

    is_an_approver = fields.Boolean("Approver", compute='compute_is_an_approver')

    is_an_payment_approver = fields.Boolean("Payment Approver", compute='compute_is_an_payment_approver')

    deligated_user = fields.Many2one(
        'res.users', string='User Deligated', tracking=True, compute="_compute_user_id")




    approve_users = fields.Many2many(

        'res.users',

        'rel_invoice_apprvers',

        'po_id',

        'po_user',

        string='Approve Users',

    )

    approved_users = fields.Many2many(

        'res.users',

        'approved_invoice_relation',

        'po_apprved',

        'po_user_id',

        string='Approved Users',

    )



    next_approve_user = fields.Many2many(

        'res.users',

        'next_aprved_invoice',

        'next_po',

        'po_users_id',

        string='Next Approver', )


    payment_approve_users = fields.Many2many(

        'res.users',

        'payment_rel_invoice_apprvers',

        'po_id',

        'po_user',

        string='Approve Users',

    )

    payment_approved_users = fields.Many2many(

        'res.users',

        'payment_approved_invoice_relation',

        'po_apprved',

        'po_user_id',

        string='Approved Users',

    )



    payment_next_approve_user = fields.Many2many(

        'res.users',

        'payment_next_aprved_invoice',

        'next_po',

        'po_users_id',

        string='Next Approver', )





    user_approve_check = fields.Boolean(string="User Approve check", compute="_compute_total", default=False)


    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('requested','Requested'),
        ('approved', 'Approved'),
        ('reject','Reject'),
        ('rfi','Request for Information'),
        ('accounting','Accounting'),
        ('finance','Finance'),
        ('posted', 'PAID'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True, default='draft')

    invoice_rfi_ids = fields.One2many('pr.invoice.rfi',
                                 'invoice_id',
                                 string='Invoice Request Line',
                                 tracking=True)

    remarks_ids = fields.One2many('remark.invoice.save',
                                 'invoice_id',
                                 string='Remark Line',
                                 tracking=True)
                                
    is_to_user = fields.Boolean(compute='_compute_is_to_user', string='Is To User')

    user_id = fields.Many2one('res.users', 'Requested By', default=lambda self: self.env.user, readonly=True)

    voucher_code = fields.Char(string='Voucher Code')
    accounting_person = fields.Many2one('res.users', string='Accounting Person', tracking=True, domain="[('groups_id', 'not in', [44])]")
    utr_no = fields.Char(string='UTR Number')
    payment_date = fields.Date(string="Payment Date",default=fields.Date.today())
    payment_amount = fields.Float(string="Payment Amount", compute='_compute_payment_amount', store=True)
    TDS = fields.Integer(string="TDS Amount")
    reduced_amount = fields.Integer(string="Total Deductions", compute='_compute_reduced_amount',currency_field='currency_id')
    po_number = fields.Many2one('purchase.order', 'Purchase Order')
    purchase_request = fields.Many2one('product.request', 'Purchase Request')

    ct_number = fields.Many2many(
        'product.tender.line',
        'purchase_tenders_rel_invoice',
        'purchase_id',
        'tender_id',
        string='Contract Request'
    )

    purchase_request_approvals = fields.One2many(
        'pr.approve.line',
        compute='_compute_purchase_request_approvals',
        string='Purchase Request Approvals',
        store=False
    )
    contract_request_approvals = fields.One2many(
        'tender.approve.line',
        compute='_compute_contract_request_approvals',
        string='Contract Request Approvals',
        store=False
    )

    other_deductions = fields.Integer(string="Additional deductions",store=True)

    vendor_addresss = fields.Html(string="Vendor Address", store=True)
    vendor_change_name = fields.Text(string="Vendor Name", store=True)

    type_input = fields.Char(string="Attachment Name", compute='_compute_type_input', store=True)

    additional_charges = fields.Float(string="Additional Charges",store=True)

    @api.depends('message_attachment_count')
    def _compute_type_input(self):
        """Compute the attachment name if an invoice is uploaded."""
        for record in self:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', record.id)
            ])
            print("the attachment is",attachments)
            if attachments:
                record.type_input = attachments[-1].name  # Get the latest attachment name
            

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Fetch and update the vendor's name and address fields when the vendor changes."""
        for record in self:
            if record.partner_id:
                # Set the vendor name in vendor_change_name
                record.vendor_change_name = record.partner_id.name or ""

                # Construct the address by joining available fields with a comma
                address = "<br/>".join(filter(None, [
                    f"{record.partner_id.street or ''}, {record.partner_id.street2 or ''},{record.partner_id.city or ''}",
                    record.partner_id.state_id.name,
                    record.partner_id.country_id.name,
                    f"Pin: {record.partner_id.zip}" if record.partner_id.zip else None
                ]))

                # Set the address in vendor_address
                record.vendor_addresss = address
            else:
                # Clear both fields if partner_id is empty
                record.vendor_change_name = False
                record.vendor_addresss = False


    @api.depends('ct_number')
    def _compute_contract_request_approvals(self):
        for record in self:
            # Collect the approval lines from the related contracts (tender lines)
            approval_lines = self.env['tender.approve.line'].search([
                ('tender_id', 'in', record.ct_number.mapped('request_no.id'))
            ])
            record.contract_request_approvals = approval_lines

    @api.depends('purchase_request')
    def _compute_purchase_request_approvals(self):
        for invoice in self:
            if invoice.purchase_request:
                # Get the related purchase request approval lines
                invoice.purchase_request_approvals = invoice.purchase_request.pr_approve_line
            else:
                invoice.purchase_request_approvals = False

    @api.depends('invoice_rfi_ids')
    def _compute_is_to_user(self):
        current_user_id = self.env.user.id
        for record in self:
            record.is_to_user = any(
                not rfi.replayed and rfi.to_user.id == current_user_id for rfi in record.invoice_rfi_ids)
            print("the user is", record.is_to_user)

    @api.onchange('TDS','other_deductions')
    def _compute_reduced_amount(self):
        self.reduced_amount = (self.TDS or 0) + (self.other_deductions or 0)

    def status_change(self):
        print("hi")
        self.state= 'accounting'
        # model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        # pending_action = self.env['pending.actions'].sudo().search(
        #     [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

        # if pending_action:
        #     pending_action.status = 'closed'

        # activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')],
        #                                                       limit=1)
        # print("the activity type is", activity_type)
        # print("type is", self.env.user.id)
        # print("the self id is", self.id)
        # activity = self.env['mail.activity'].search([
        #     ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
        #     ('user_id', '=', self.env.user.id), ('res_id', '=', self.id),
        #     ('activity_type_id', '=', activity_type.id),
        # ], limit=1)
        # if activity:
        #     for act in activity:
        #         print(activity.id)
        #         act.action_feedback(feedback="Activity completed")
        # self.message_post(body="The Payment Users Have Approved")
        # self.message_post(body="The Invoice request for everyone has been approved")

        # self.action_post()

        # purchase_orders = self.env['purchase.order'].search([('invoice_ids', '=', self.id)], limit=1)
        # utr_number = self.utr_no
        # if utr_number:
        #     if purchase_orders.utr_no:
        #         # Check if the utr_no already contains this number
        #         if utr_number not in purchase_orders.utr_no.split(','):
        #             purchase_orders.utr_no += ',' + utr_number  # Append the new UTR number with a comma
        #     else:
        #         purchase_orders.utr_no = utr_number
        # stock_picking_ids = self.env['stock.picking'].sudo().search([
        #     ('origin', '=', purchase_orders.name), ('state', '=', 'assigned')])
        # if not stock_picking_ids:
        #     purchase_orders.state = 'paid'


    @api.depends('TDS', 'other_deductions', 'amount_untaxed', 'amount_tax')
    def _compute_payment_amount(self):
        for record in self:
            if record.TDS + record.other_deductions > record.amount_untaxed + record.amount_tax:
                raise ValidationError("TDS and other deductions cannot exceed the total amount.")

            record.payment_amount = (record.amount_untaxed + record.amount_tax) - record.TDS - record.other_deductions
            record.amount_residual = record.payment_amount
            record.amount_total = record.payment_amount
           

    @api.model
    def create(self, vals):
        record = super(InvoiceInherit, self).create(vals)
        record._update_amounts()
        return record

    def write(self, vals):
        print("the vals", vals)

        if any(key in vals for key in ['TDS', 'other_deductions']):
            for record in self:

                if record.amount_total is None:
                    record.amount_total = record.amount_untaxed + record.amount_tax

                if 'TDS' in vals and vals['TDS'] > record.amount_total:
                    raise ValidationError("TDS amount cannot exceed the total amount.")
                if 'other_deductions' in vals and vals['other_deductions'] > record.amount_total:
                    raise ValidationError("Additional amount cannot exceed the total amount.")


        res = super(InvoiceInherit, self).write(vals)

        if any(key in vals for key in ['TDS', 'other_deductions']):
            self._update_amounts()

        return res

    def _update_amounts(self):
        print("here")
        for record in self:

            record.amount_residual = (record.amount_untaxed + record.amount_tax) - record.TDS - record.other_deductions
            record.amount_total = record.amount_residual


    @api.depends('next_approve_user')
    def compute_is_an_approver(self):

        for rec in self:
            if self.state == 'accounting':
                rec.is_an_approver = self.env.user.id in rec.next_approve_user.mapped('id')
                print(rec.next_approve_user)
            else:
                rec.is_an_approver = False

    @api.depends('payment_next_approve_user')
    def compute_is_an_payment_approver(self):
        for rec in self:
            print("the tset", self.payment_next_approve_user)
            rec.is_an_payment_approver = self.env.user.id in rec.payment_next_approve_user.mapped('id')



    def action_post(self):
        print("Inside create invoice action_post")
        print("vendor : ", self.partner_id)
        partner = self.env['res.partner'].sudo().search(
            [('id', '=', self.partner_id.id),], limit=1)
        if partner and partner.user_id.id:
            self.company_user_id = partner.user_id.id
        return super().action_post()

    def _compute_user_id(self):
        for rec in self:
            rec.deligated_user = self.env.user.id

    @api.depends("user_approve_check")
    def _compute_total(self):
        print('Inside user_approve_check')
        for rec in self:
            if self.env.user in rec.next_approve_user:
                rec.user_approve_check = True
            else:
                rec.user_approve_check = False

    def view_purchase_request(self):
        if self.purchase_request:
            return {
                'name': 'Purchase Request',
                'view_mode': 'form',
                'res_model': 'product.request',
                'res_id': self.purchase_request.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def view_purchase_order(self):
        if self.po_number:
            return {
                'name': 'Purchase Order',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'res_id': self.po_number.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
    def action_contract_list(self):
        print("the number", self.ct_number.ids)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract Requests',
            'view_mode': 'tree,form',
            'res_model': 'product.tender.line',
            'domain': [('id', 'in', self.ct_number.ids)],

            'target': 'current'
        }

    def create(self, vals):
        print("the vals are",vals)
        print("I am inside the invoice")
        res = super(InvoiceInherit, self).create(vals)
        print(res)
        res.write({'invoice_date': date.today()})
        if not vals:
            return res
        try:
            if 'payment_date' in vals[0]:
                print("paymrnt date")
                return res
        except:
            pass
        purchase_order = self.env['purchase.order'].search([('invoice_ids', '=', res.id)],limit=1)
        print("the purchase",purchase_order.l10n_in_gst_treatment)
        res.write({'l10n_in_gst_treatment': purchase_order.l10n_in_gst_treatment})
        res.write({'branch_id':purchase_order.bill_to})
        res.write({'po_number': purchase_order.id})
        if purchase_order.pr_id:
            res.write({'purchase_request': purchase_order.pr_id.id})
        
        if purchase_order.ct_number:
            ct_number_ids = purchase_order.ct_number.ids  # Get the IDs of the ct_number Many2many field
            res.write({'ct_number': [(6, 0, ct_number_ids)]}) 

        branch = None
        if res.branch_id:
            if res.branch_id.code == "COR":
                branch = res.branch_id
            else:
                company = res.branch_id.company_id
                if company.name == "Popular Vehicles & Services Ltd - KL":
                    branch = self.env['res.branch'].search([('name', '=', 'KL Location Level')], limit=1)
                if company.name == "Popular Vehicles & Services Ltd - TN":
                    branch = self.env['res.branch'].search([('name', '=', 'TN Location Level')], limit=1)
                if company.name == "Popular Vehicles & Services Ltd - KA":
                    branch = self.env['res.branch'].search([('name', '=', 'KA Location Level')], limit=1)


      
        pr_company_data = self.env['pr.company'].sudo().search([
            ('company_id', '=', res.company_id.id),
            ('branch_id', '=', branch.id),
            ('exp_category', '=', purchase_order.exp_category.id),
            ('from_amount', '<=', res.amount_total),
            ('to_amount', '>=', res.amount_total),
            ('type', '=', 'accounting')],
            limit=1)
        if not pr_company_data:
            pr_company_data = self.env['pr.company'].sudo().search([
                ('company_id', '=', res.company_id.id),
                ('branch_id', '=', branch.id),
                ('exp_category', '=', 'NILL'),
                ('type', '=', 'accounting')],
                limit=1)
            print("company1", pr_company_data.name)

        pr_company_data2 = self.env['pr.company'].sudo().search([
            ('company_id', '=', res.company_id.id),
            ('branch_id', '=', branch.id),
            ('exp_category', '=', purchase_order.exp_category.id),
            ('from_amount', '<=', res.amount_total),
            ('to_amount', '>=', res.amount_total),
            ('type', '=', 'payment')],
            limit=1)
        if not pr_company_data2:
            pr_company_data2 = self.env['pr.company'].sudo().search([
                ('company_id', '=', res.company_id.id),
                ('branch_id', '=', branch.id),
                ('exp_category', '=', 'NILL'),
                ('type', '=', 'payment')],
                limit=1)
            print("company2", pr_company_data2.name)

        if pr_company_data and pr_company_data2:
            user_groups = defaultdict(list)
            vendor_users = self.env['res.users'].sudo()
            if res.lease_id.with_gst:
                print("testing lease")
                if res.partner_id:
                    # vendor_users = self.env['res.users'].sudo()

                    vendor = res.partner_id
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

                            res.invoice_approve_line |= self.env['invoice.approve.line'].sudo().create(new_line_vals)
                            print("approval line", res.invoice_approve_line)
                            # self.approve_users += vendor_user
                            res.write({'approve_users': [(4, vendor_users.id)]})
                            user_groups[1].append(vendor_users)
            for approvers in pr_company_data.pr_approve_users_id:
                line = []
                for users in approvers:
                    if users.branch_id.code == "COR":
                        ser_branch = users.branch_id.id
                        ser_branch_record = users.branch_id
                    else:
                        ser_branch = res.branch_id.id
                        ser_branch_record = res.branch_id
                    print("approvers")
                    users_line = self.env['res.users.line'].sudo().search(
                        [('company_id', '=', users.company_id.id),
                         ('branch_id', '=', ser_branch),
                         ('department_id', '=', users.department_id.id),
                         ('designation', '=', users.designation.id),('res_user_id', '!=', False)],limit=1)
                    print("approve user",users_line.res_user_id.id)
                    if users_line and users_line.res_user_id:
                            res.write({'approve_users': [(4, users_line.res_user_id.id)]})
                    else:
                            raise ValidationError(
                                    _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                        approvers.designation.name, approvers.department_id.name,
                                        ser_branch_record.name, approvers.company_id.name))
                    # res.write({'approve_users': [(4, users_line.res_user_id.id)]})
                    approve_order = int(users.approve_order) + 1 if vendor_users else users.approve_order
                    print("the line approve order", approve_order)
                    print("the user id is", users_line.res_user_id.id)
                    vals = {
                        'user_id': users_line.res_user_id.id,
                        'company_id': users.company_id.id,
                        'branch_id': ser_branch,
                        'department_id': users.department_id.id,
                        'designation': users.designation.id,
                        'approve_order': approve_order,
                    }
                    line.append((0, 0, vals))
                    res.invoice_approve_line = line
                    user_groups[approve_order].append(users)  # Group users by their approval order
                    print("the user group", user_groups)

            # Get the lowest approval order
            lowest_approve_order = min(user_groups.keys()) if user_groups else None
            print("the lowest approval", lowest_approve_order)

            # Create pending actions only for the lowest order users
            if lowest_approve_order is not None:
                next_approver_users = user_groups[lowest_approve_order]
                print("the next is", next_approver_users)
                if vendor_users:

                    res.write({'next_approve_user': [(4, vendor_users.id)]})
                    res.is_confirmed = True

                    # Create pending actions
                    model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                    pending_vals = {
                        'model': model.id,
                        'name': str(res.po_number.name) + " " +res.name + " " + "Invoice Request Waiting For Approval-Accounting",
                        'record': res.id,
                        'branch': res.branch_id.id,
                        'date': date.today(),
                        'approve_users': [(4, vendor_users.id)]
                    }
                    pendings = self.env['pending.actions'].create(pending_vals)
                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')],
                        limit=1)
                    activity_type_id = activity_type.id if activity_type else False
                    res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id

                    activity_values = {
                        'user_id': vendor_users.id,
                        'res_id': res.id,
                        'note': "Pending Action",
                        'activity_type_id': activity_type_id,
                        'res_model_id': res_model_id,
                    }
                    print("the activity is", activity_values)

                    with self.env.cr.savepoint():
                        self = self.with_context(mail_activity_quick_update=True)
                        created_activity = self.env['mail.activity'].sudo().create(activity_values)

                    if next_approver_users:
                        print("buyersssss", next_approver_users)
                        subject = "New invoice Request Raised: %s" % res.name
                        print("Name", res.name)

                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        menu_id = self.env['ir.ui.menu'].sudo().search(
                            [('name', '=', 'Accounting')], limit=1) or False

                        url_params = {
                            'id': res.id,
                            'action': self.env.ref('account.action_move_in_invoice_type').id,
                            'model': 'account.move',
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
                            f"A new Invoice Request with the name <strong>{self.name}</strong> has been raised against Purchase Request by <strong></strong>.<br>"
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
                                'email_to': vendor_users.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)
                else:
                    for user in next_approver_users:
                        if user.branch_id.code == "COR":
                            ser_branch = user.branch_id.id
                            ser_branch_record = user.branch_id
                        else:
                            ser_branch = res.branch_id.id
                            ser_branch_record = res.branch_id
                        users_line = self.env['res.users.line'].sudo().search(
                            [('company_id', '=', user.company_id.id),
                            ('branch_id', '=', ser_branch),
                            ('department_id', '=', user.department_id.id),
                            ('designation', '=', user.designation.id),('res_user_id', '!=', False)],limit=1)
                        print("the next", user)
                        res.write({'next_approve_user': [(4, users_line.res_user_id.id)]})
                        res.is_confirmed = True

                        # Create pending actions
                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': str(res.po_number.name) + " " +res.name + " " + "Invoice Request Waiting For Approval-Accounting",
                            'record': res.id,
                            'branch': res.branch_id.id,
                            'date': date.today(),
                            'approve_users': [(4, users_line.res_user_id.id)]
                        }
                        pendings = self.env['pending.actions'].create(pending_vals)
                        activity_type = self.env['mail.activity.type'].sudo().search(
                            [('name', '=', 'Pending Request')],
                            limit=1)
                        activity_type_id = activity_type.id if activity_type else False
                        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id

                        activity_values = {
                            'user_id': users_line.res_user_id.id,
                            'res_id': res.id,
                            'note': "Pending Action",
                            'activity_type_id': activity_type_id,
                            'res_model_id': res_model_id,
                        }
                        print("the activity is", activity_values)

                        created_activity = self.env['mail.activity'].sudo().create(activity_values)
                        print("the activity is", created_activity)

                        if next_approver_users:
                            print("buyersssss", next_approver_users)
                            subject = "New invoice Request Raised: %s" % res.name
                            print("Name", res.name)

                            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            menu_id = self.env['ir.ui.menu'].sudo().search(
                                [('name', '=', 'Accounting')], limit=1) or False

                            url_params = {
                                'id': res.id,
                                'action': self.env.ref('account.action_move_in_invoice_type').id,
                                'model': 'account.move',
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
                                f"A new Invoice Request with the name <strong>{self.name}</strong> has been raised against Purchase Request by <strong></strong>.<br>"
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
                                    'email_to': users_line.res_user_id.login,
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)
            res.state = 'accounting'
            res._onchange_partner_id()
        else:
            raise ValidationError(
                "Sorry,The criteria provided did not match any existing Invoice workflows,Please contact Administrator.")

        return res

    def action_approval(self):
        self.message_post(body=self.env.user.name + " " + "Approved The Invoice Request")
        print("approvee")
        print("Hellooo users")
        print(self.env.user.id)
        self.write({'approved_users': [(4, self.env.user.id)]})
        self.is_an_approver = False
        self.write({'next_approve_user': [(3, self.env.user.id)]})
        approver = self.env['invoice.approve.line'].sudo().search(
            [('invoice_id', '=', self.id), ('user_id', '=', self.env.user.id)])
        for record in approver:
            record.write({'status': 'accept'})
        if self.approved_users == self.approve_users:
            if self.state == 'accounting':
                self.state = 'finance'

                # self.state = 'approved'
                print("the state is", self.state)

                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

                if pending_action:
                    for pend in pending_action:
                        pend.status = 'closed'

                activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')],
                                                                      limit=1)
                print("the activity type is", activity_type)
                print("type is", self.env.user.id)
                print("the self id is", self.id)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                    ('user_id', '=', self.env.user.id), ('res_id', '=', self.id),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for act in activity:
                        print(activity.id)
                        act.action_feedback(feedback="Activity completed")
                self.message_post(body="The Accounting users Have Approved")
                purchase_order = self.env['purchase.order'].search([('invoice_ids', '=', self.id)], limit=1)

                branch = None
                if self.branch_id:
                    if self.branch_id.code == "COR":
                        branch = self.branch_id
                    else:
                        company = self.branch_id.company_id
                        if company.name == "Popular Vehicles & Services Ltd - KL":
                            branch = self.env['res.branch'].search([('name', '=', 'KL Location Level')], limit=1)
                        if company.name == "Popular Vehicles & Services Ltd - TN":
                            branch = self.env['res.branch'].search([('name', '=', 'TN Location Level')], limit=1)
                        if company.name == "Popular Vehicles & Services Ltd - KA":
                            branch = self.env['res.branch'].search([('name', '=', 'KA Location Level')], limit=1)

                pr_company_data = self.env['pr.company'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', branch.id),
                ('exp_category', '=', purchase_order.exp_category.id),
                ('from_amount', '<=', self.amount_total),
                ('to_amount', '>=', self.amount_total),
                ('type', '=', 'payment')],
                limit=1)
                if not pr_company_data:
                    pr_company_data = self.env['pr.company'].sudo().search([
                        ('company_id', '=', self.company_id.id),
                        ('branch_id', '=', branch.id),
                        ('exp_category', '=', 'NILL'),
                        ('type', '=', 'payment')],
                        limit=1)
                print("company2", pr_company_data.name)

                if pr_company_data:
                    user_groups = defaultdict(list)
                    for approvers in pr_company_data.pr_approve_users_id:
                        line = []
                        for users in approvers:
                            if users.branch_id.code == "COR":
                                ser_branch = users.branch_id.id
                                ser_branch_record = users.branch_id
                            else:
                                ser_branch = self.branch_id.id
                                ser_branch_record = self.branch_id
                            users_line = self.env['res.users.line'].sudo().search(
                                [('company_id', '=', users.company_id.id),
                                 ('branch_id', '=', ser_branch),
                                 ('department_id', '=', users.department_id.id),
                                 ('designation', '=', users.designation.id),('res_user_id', '!=', False)], limit=1)
                            if users_line and users_line.res_user_id:
                                self.write({'payment_approve_users': [(4, users_line.res_user_id.id)]})
                            else:
                                raise ValidationError(
                                    _("No User at %s (Designation)-- in %s Department of --%s Branch, %s FOR APPROVAL") % (
                                        approvers.designation.name, approvers.department_id.name,
                                        ser_branch_record.name, approvers.company_id.name))
                            # self.write({'payment_approve_users': [(4, users_line.res_user_id.id)]})
                            approve_order = users.approve_order
                            print("the line approve order", approve_order)
                            print("the user id is", users_line.res_user_id.id)
                            vals = {
                                'user_id': users_line.res_user_id.id,
                                'company_id': users.company_id.id,
                                'branch_id': ser_branch,
                                'department_id': users.department_id.id,
                                'designation': users.designation.id,
                                'approve_order': approve_order,
                            }
                            line.append((0, 0, vals))
                            self.invoice_payment_approve_line = line
                            user_groups[approve_order].append(users)  # Group users by their approval order
                            print("the user group", user_groups)

                    # Get the lowest approval order
                    lowest_approve_order = min(user_groups.keys()) if user_groups else None
                    print("the lowest approval", lowest_approve_order)

                    # Create pending actions only for the lowest order users
                    if lowest_approve_order is not None:
                        payment_next_approver_users = user_groups[lowest_approve_order]
                        print("the next is", payment_next_approver_users)
                        for user in payment_next_approver_users:
                            if user.branch_id.code == "COR":
                                ser_branch = user.branch_id.id
                                ser_branch_record = user.branch_id
                            else:
                                ser_branch = self.branch_id.id
                                ser_branch_record = self.branch_id
                            users_line = self.env['res.users.line'].sudo().search(
                                [('company_id', '=', user.company_id.id),
                                 ('branch_id', '=', ser_branch),
                                 ('department_id', '=', user.department_id.id),
                                 ('designation', '=', user.designation.id),('res_user_id', '!=', False)],limit=1)
                            print("the next", user)
                            self.write({'payment_next_approve_user': [(4, users_line.res_user_id.id)]})
                            self.is_confirmed = True

                            # Create pending actions
                            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                            pending_vals = {
                                'model': model.id,
                                'name': str(self.po_number.name) + " " +self.name + " " + "Invoice Request Waiting For Approval-Payment",
                                'record': self.id,
                                'branch': self.branch_id.id,
                                'date': date.today(),
                                'approve_users': [(4, users_line.res_user_id.id)]
                            }
                            pendings = self.env['pending.actions'].create(pending_vals)
                            print("the next pending",pendings)
                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Request')],
                                limit=1)
                            activity_type_id = activity_type.id if activity_type else False
                            res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id

                            activity_values = {
                                'user_id': users_line.res_user_id.id,
                                'res_id': self.id,
                                'note': "Pending Action",
                                'activity_type_id': activity_type_id,
                                'res_model_id': res_model_id,
                            }
                            print("the activity is", activity_values)

                            created_activity = self.env['mail.activity'].sudo().create(activity_values)
                            print("the activity is", created_activity)

                            if payment_next_approver_users:
                                print("buyersssss", payment_next_approver_users)
                                subject = "New invoice Request Raised: %s" % self.name
                                print("Name", self.name)

                                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                    [('name', '=', 'Accounting')], limit=1) or False

                                url_params = {
                                    'id': self.id,
                                    'action': self.env.ref('account.action_move_in_invoice_type').id,
                                    'model': 'account.move',
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
                                    f"A new Invoice Request with the name <strong>{self.name}</strong> has been raised against Purchase Request by <strong></strong>.<br>"
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
                                        'email_to': users_line.res_user_id.login,
                                        'auto_delete': False,
                                        'author_id': author.id
                                    }
                                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    # self.state = 'accounting_approved'
                else:
                    raise ValidationError(
                        "Sorry,The criteria provided did not match any existing invoice workflows,Please contact Administrator.")


        else:

            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
            print("the pending", pending_action)
            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close", rec)
                    rec.status = 'closed'

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            print("the activity type is", activity_type.id)
            print("the self id is", self.id)
            print("the res is",self.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                ('user_id', '=', self.env.user.id),('res_id', '=' , self.id),
                ('activity_type_id', '=', activity_type.id),
            ])
            print("activity name is",self.name)
            print("the activity is",activity)
            if activity:
                print("the activity is", activity)
                activity.action_feedback(feedback="Activity completed")

            approve_users = self.env['invoice.approve.line'].sudo().search(
                [('invoice_id', '=', self.id)], order='approve_order asc')
            print("the approve users", approve_users)

            user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
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
                            print("the approve dict", approve_dict[order])

            print("approve_dict ", approve_dict)

            record_to_remove = self.env['res.users'].browse(self.env.user.id)
            self.next_approve_user -= record_to_remove
            print("the next approve", self.next_approve_user)

            if not self.next_approve_user:
                print("no next approver")
                for order in order_list:
                    for order_list_users in approve_dict[order]:
                        print("view the order list", order_list_users)
                        if self.env.user.id == order_list_users['u_id']:
                            print("i am ok with correct")
                            try:
                                print("iam in try")
                                if approve_dict[order + 1]:
                                    print("i am in approve dict")
                                    for users in approve_dict[order + 1]:
                                        self.write({'next_approve_user': [(4, users['u_id'])]})

                                    ####################### MAil ############################
                                    print(self.next_approve_user,
                                          "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                    # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    # menu_id = self.env['ir.ui.menu'].sudo().search(
                                    #     [('name', '=', 'Contracts')], limit=1) or False
                                    #
                                    # url_params = {
                                    #     'id': self.id,
                                    #     'action': self.env.ref('lease_management.action_my_product_lease').id,
                                    #     'model': 'product.lease',
                                    #     'view_type': 'form',
                                    #     # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                    #     'menu_id': menu_id.id,
                                    # }
                                    # params = '/web?#%s' % url_encode(url_params)
                                    # view_url = base_url + params if base_url else "#"

                                    ##################### URL for Approval #########################

                                    subject = "New invoice Request Raised: %s" % self.name
                                    print("Name", self.name)
                                    body = ("Dear User, "
                                            "A new Invoice Request with the name %s has been raised against an Purchase Request by" % (
                                                self.name))

                                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                        [('name', '=', 'Accounting')], limit=1) or False

                                    url_params = {
                                        'id': self.id,
                                        'action': self.env.ref('account.action_move_in_invoice_type').id,
                                        'model': 'account.move',
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
                                        f"A new Invoice Request with the name <strong>{self.name}</strong> has been raised against Invoice Request by <strong></strong>.<br>"
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



                                    for user in self.next_approve_user:
                                        print("i am just entering the pending action")
                                        print("the user is",user)
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                   limit=1)
                                        pending_vals = {
                                            'model': model.id,
                                            'name': str(self.po_number.name) + " " +self.name + " " + "Invoice Request Waiting For Approval-Payment",
                                            'record': self.id,
                                            'branch': self.branch_id.id,
                                            'date': date.today(),
                                        }
                                        print("the pending vals",pending_vals)
                                        if user:
                                            print("the user is there")
                                            user_ids_to_pass = user.ids
                                            print("the user ids", user_ids_to_pass)
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            pendings = self.env['pending.actions'].create(pending_vals)
                                            print("the pending is", pendings)

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Request')], limit=1)
                                            print("the activity type",activity_type)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'account.move')]).id
                                            for user_id in user_ids_to_pass:
                                                print("the user_id is",user_id)
                                                print("the ews_id is", self.id)

                                                activity_values = {
                                                    'user_id': user_id,
                                                    'res_id': self.id,
                                                    'note': "Pending Action",
                                                    'activity_type_id': activity_type_id,
                                                    'res_model_id': res_model_id,
                                                }
                                                created_activity = self.env['mail.activity'].create(activity_values)
                                                print("the created activity",created_activity)

                                        if user.login:
                                            subject = "Invoice Request Waiting For APPROVAL: %s (PO: %s)" % (self.name, self.po_number.name)
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
                                                self.write({'next_approve_user': [(4, users['u_id'])]})
                                                flag = 1

                                                print(self.next_approve_user,
                                                      "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Purchase Request')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref(
                                                        'account.action_move_in_invoice_type').id,
                                                    'model': 'account.move',
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

                                                for user in self.next_approve_user:
                                                    model = self.env['ir.model'].sudo().search(
                                                        [('model', '=', self._name)],
                                                        limit=1)
                                                    pending_vals = {
                                                        'model': model.id,
                                                        'name': self.name + " " + "Waiting For Invoice Approval",
                                                        'record': self.id,
                                                        'branch': self.branch_id.id,
                                                        'date': date.today(),
                                                    }
                                                    if user:
                                                        user_ids_to_pass = user.ids
                                                        pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                                        pendings = self.env['pending.actions'].create(pending_vals)

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
                                                                'activity_type_id': activity_type_id,
                                                                'res_model_id': res_model_id,
                                                            }
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
        # else:
        #     all_approved = all(approver.status == 'accept' for approver in approve_users)
        #     print("its all approved",all_approved)
        #     if all_approved:
        #         self.is_confirmed = True
        #         self.state = 'approved'
        #         print("the state is", self.state)
        #
        #         model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        #         pending_action = self.env['pending.actions'].sudo().search(
        #             [('model', '=', model.id), ('record', '=', self.id)], limit=1)
        #
        #         if pending_action:
        #             pending_action.status = 'closed'
        #
        #         activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Purchase Order')],
        #                                                               limit=1)
        #         print("type is", self.env.user.id)
        #         activity = self.env['mail.activity'].search([
        #             ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
        #             ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
        #             ('activity_type_id', '=', activity_type.id),
        #         ], limit=1)
        #         if activity:
        #             print(activity.id)
        #             activity.action_feedback(feedback="Activity completed")
        #         self.action_post()

    def action_payment_approver(self):
        # if not all([self.utr_no, self.payment_date, self.payment_amount, self.TDS]):
        #     raise UserError("UTR Number, Payment Date, Payment Amount, and TDS Amount must be set before approving.")

        self.message_post(body=self.env.user.name + " " + "Approved The Invoice Request")
        print("approvee")
        print("Hellooo users")
        print(self.env.user.id)
        self.write({'payment_approved_users': [(4, self.env.user.id)]})
        self.is_an_payment_approver = False
        self.write({'payment_next_approve_user': [(3, self.env.user.id)]})
        approver = self.env['invoice.payment.approve.line'].sudo().search(
            [('invoice_id', '=', self.id), ('user_id', '=', self.env.user.id)])
        # payment_approve_users = self.env['invoice.payment.approve.line'].sudo().search(
        #     [('invoice_id', '=', self.id)], order='approve_order asc')
        # print("the pyment approve users", payment_approve_users)
        print("the payment approve user",self.payment_approve_users)
        print("the payment approved user", self.payment_approved_users)
        for record in approver:
            record.write({'status': 'accept'})
        if self.payment_approved_users == self.payment_approve_users:
                self.state = 'finance'
                self.is_confirmed = True
                # self.state = 'approved'
                print("the state is", self.state)

                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

                if pending_action:
                    pending_action.status = 'closed'

                activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')],
                                                                      limit=1)
                print("the activity type is", activity_type)
                print("type is", self.env.user.id)
                print("the self id is", self.id)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                    ('user_id', '=', self.env.user.id), ('res_id', '=', self.id),
                    ('activity_type_id', '=', activity_type.id),
                ], limit=1)
                if activity:
                    for act in activity:
                        print(activity.id)
                        act.action_feedback(feedback="Activity completed")
                self.message_post(body="The Payment Users Have Approved")
                self.message_post(body="The Invoice request for everyone has been approved")

                self.action_post()

                purchase_orders = self.env['purchase.order'].search([('invoice_ids', '=', self.id)], limit=1)
                utr_number = self.utr_no
                if utr_number:
                    if purchase_orders.utr_no:
                        if utr_number not in purchase_orders.utr_no.split(','):
                            purchase_orders.utr_no += ',' + utr_number  
                    else:
                        purchase_orders.utr_no = utr_number
                stock_picking_ids = self.env['stock.picking'].sudo().search([
                    ('origin', '=', purchase_orders.name), ('state', '=', 'assigned')])
                if not stock_picking_ids:
                    purchase_orders.state = 'paid'

        else:

            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
            print("the pending", pending_action)
            for rec in pending_action:
                if self.env.user in rec.approve_users:
                    print("record to close", rec)
                    rec.status = 'closed'

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            print("the activity type is", activity_type.id)
            print("the self id is", self.id)
            print("the res is", self.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                ('user_id', '=', self.env.user.id), ('res_id', '=', self.id),
                ('activity_type_id', '=', activity_type.id),
            ], limit=1)
            print("activity name is", self.name)
            print("the activity is", activity)
            if activity:
                print("the activity is", activity)
                activity.action_feedback(feedback="Activity completed")

            payment_approve_users = self.env['invoice.payment.approve.line'].sudo().search(
                [('invoice_id', '=', self.id)], order='approve_order asc')
            print("the approve users", payment_approve_users)

            user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in payment_approve_users]
            order_list = list(set([order_id.approve_order for order_id in payment_approve_users]))
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
                            print("the approve dict", approve_dict[order])

            print("approve_dict ", approve_dict)

            record_to_remove = self.env['res.users'].browse(self.env.user.id)
            self.payment_next_approve_user -= record_to_remove
            print("the next approve", self.payment_next_approve_user)

            if not self.payment_next_approve_user:
                print("no next approver")
                for order in order_list:
                    for order_list_users in approve_dict[order]:
                        print("view the order list", order_list_users)
                        if self.env.user.id == order_list_users['u_id']:
                            print("i am ok with correct")
                            try:
                                print("iam in try")
                                if approve_dict[order + 1]:
                                    print("i am in approve dict")
                                    for users in approve_dict[order + 1]:
                                        self.write({'payment_next_approve_user': [(4, users['u_id'])]})

                                    ####################### MAil ############################
                                    print(self.payment_next_approve_user,
                                          "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                    # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    # menu_id = self.env['ir.ui.menu'].sudo().search(
                                    #     [('name', '=', 'Contracts')], limit=1) or False
                                    #
                                    # url_params = {
                                    #     'id': self.id,
                                    #     'action': self.env.ref('lease_management.action_my_product_lease').id,
                                    #     'model': 'product.lease',
                                    #     'view_type': 'form',
                                    #     # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                    #     'menu_id': menu_id.id,
                                    # }
                                    # params = '/web?#%s' % url_encode(url_params)
                                    # view_url = base_url + params if base_url else "#"

                                    ##################### URL for Approval #########################

                                    subject = "New invoice Request Raised: %s" % self.name
                                    print("Name", self.name)
                                    body = ("Dear User, "
                                            "A new Invoice Request with the name %s has been raised against an Purchase Request by" % (
                                                self.name))

                                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                        [('name', '=', 'Accounting')], limit=1) or False

                                    url_params = {
                                        'id': self.id,
                                        'action': self.env.ref('account.action_move_in_invoice_type').id,
                                        'model': 'account.move',
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
                                        f"A new Invoice Request with the name <strong>{self.name}</strong> has been raised against Invoice Request by <strong></strong>.<br>"
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

                                    for user in self.payment_next_approve_user:
                                        print("i am just entering the pending action")
                                        print("the user is", user)
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                   limit=1)
                                        pending_vals = {
                                            'model': model.id,
                                            'name': str(self.po_number.name) + " " +self.name + " " + "Invoice Request Waiting For Approval-Payment",
                                            'record': self.id,
                                            'branch': self.branch_id.id,
                                            'date': date.today(),
                                        }
                                        print("the pending vals", pending_vals)
                                        if user:
                                            print("the user is there")
                                            user_ids_to_pass = user.ids
                                            print("the user ids", user_ids_to_pass)
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            print("the test pending vals",pending_vals)
                                            pendings = self.env['pending.actions'].create(pending_vals)
                                            print("the pending is", pendings)

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Request')], limit=1)
                                            print("the activity type", activity_type)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'account.move')]).id
                                            for user_id in user_ids_to_pass:
                                                print("the user_id is", user_id)
                                                print("the ews_id is", self.id)

                                                activity_values = {
                                                    'user_id': user_id,
                                                    'res_id': self.id,
                                                    'note': "Pending Action",
                                                    'activity_type_id': activity_type_id,
                                                    'res_model_id': res_model_id,
                                                }
                                                created_activity = self.env['mail.activity'].create(activity_values)
                                                print("the created activity", created_activity)

                                        if user.login:
                                            subject = "Invoice Request Waiting For APPROVAL: %s (PO: %s)" % (self.name, self.po_number.name)
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
                                                self.write({'payment_next_approve_user': [(4, users['u_id'])]})
                                                flag = 1

                                                print(self.payment_next_approve_user,
                                                      "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                                base_url = self.env['ir.config_parameter'].sudo().get_param(
                                                    'web.base.url')
                                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                                    [('name', '=', 'Purchase Request')], limit=1) or False

                                                url_params = {
                                                    'id': self.id,
                                                    'action': self.env.ref(
                                                        'account.action_move_in_invoice_type').id,
                                                    'model': 'account.move',
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

                                                for user in self.payment_next_approve_user:
                                                    model = self.env['ir.model'].sudo().search(
                                                        [('model', '=', self._name)],
                                                        limit=1)
                                                    pending_vals = {
                                                        'model': model.id,
                                                        'name': self.name + " " + "Waiting For Invoice Approval",
                                                        'record': self.id,
                                                        'branch': self.branch_id.id,
                                                        'date': date.today(),
                                                    }
                                                    if user:
                                                        user_ids_to_pass = user.ids
                                                        pending_vals['payment_approve_users'] = [(6, 0, user_ids_to_pass)]
                                                        pendings = self.env['pending.actions'].create(pending_vals)

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
                                                                'activity_type_id': activity_type_id,
                                                                'res_model_id': res_model_id,
                                                            }
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

                                                print(self.payment_next_approve_user_id)
                                    except:
                                        print("pass")
                                        pass
                                    if flag:
                                        break
    def action_rejected(self):
        print("helloo rejected")
        # self.state = 'reject'

        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

        for rec in pending_action:
            print(rec.name)
            rec.status = 'closed'
        self.message_post(body=f"{self.env.user.name} Rejected the Invoice Request.")

        activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
        print("type is", self.env.user.id)
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
        ])
        print("the activity is",activity)
        if activity:
            for act in activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(act.id)
                act.action_feedback(feedback="Activity Declined")
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Accounting')], limit=1) or False

        url_params = {
            'id': self.id,
            'action': self.env.ref('account.action_move_in_invoice_type').id,
            'model': 'account.move',
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
            f"The invoice Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        subject = "Invoice Request Has Been Rejected: %s" % self.name

        purchase_order = self.env['purchase.order'].search([('invoice_ids', '=', self.id)], limit=1)
        print("the purchase order",purchase_order)
        purchase_request = self.env['product.request'].search([('id', '=',  purchase_order.pr_id.id)], limit=1)
        lease_request = self.env['product.lease'].search([('id', '=',  purchase_order.lease_id.id)], limit=1)
        if purchase_order:
            pur_id = purchase_order.pr_id
            print("pr id is",pur_id)
        if pur_id:
            pr_initiator = pur_id.requested_by.id

        if self.state =='accounting':

            for approvers in self.invoice_approve_line:
                if approvers.user_id.id == self.env.user.id:
                    approvers.write({'status': 'cancel'})

                if approvers.status == 'accept':
                    print("app", approvers.status)

                    mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': approvers.user_id.login,
                            'auto_delete': False,
                            'author_id': author.id
                        }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
        if self.state == 'finance':
            for approver in self.invoice_payment_approve_line:
                if approver.user_id.id == self.env.user.id:
                    approver.write({'status': 'cancel'})

                if approver.status == 'accept':
                    print("app", approver.status)

                    mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': approver.user_id.login,
                            'auto_delete': False,
                            'author_id': author.id
                        }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)

        if purchase_order:
            print("req", self.user_id)
            purchase_order.state = 'cancel'
            purchase_order.message_post(
                body=f"{self.env.user.name} Rejected the Invoice Request So the Purchase Order is Rejected.")

        if lease_request:
            print("req", self.user_id)
            lease_request.state = 'reject'
            lease_request.message_post(
                body=f"{self.env.user.name} Rejected the Invoice Request So the Lease Order is Rejected.")
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to':  lease_request.user_id.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)
        if purchase_request:
            pur_id = purchase_request.requested_by.id
            purchase_request.status = 'declined'
            purchase_request.message_post(
                body=f"{self.env.user.name} Rejected the Invoice Request So the Purchase Request is Rejected.")
            print("pr id is", pur_id)
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': purchase_request.requested_by.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)

        self.state ='reject'


    def action_deligate(self):
        print("deligate")
        if self.state == 'accounting':
            for lines in self.invoice_approve_line:
                if lines.user_id.id == self.env.user.id:
                    print("Founddd User")
                    action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_invoice_action')
                    action['context'] = {'default_invoice_id': self.id}

                    return action
        if self.state == 'finance':
            for lines in self.invoice_payment_approve_line:
                if lines.user_id.id == self.env.user.id:
                    print("Founddd User")
                    action = self.env["ir.actions.actions"]._for_xml_id(
                        'product_purchase.update_deligate_user_invoice_action')
                    action['context'] = {'default_invoice_id': self.id}

                    return action

    def action_delegate_admin(self):

        approve_users = set(self.approve_users.ids)  # Fetch IDs of approve_users
        approved_users = set(self.approved_users.ids)  # Fetch IDs of approved_users

        user_ids = list(approve_users - approved_users)

        if not user_ids:
            return

        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_admin_action')
        action['context'] = {
            'default_invoice_id': self.id,
            'user_ids': user_ids,
            'type_id': 'inva'
        }

        return action

    def action_delegate_admin_fin(self):

        approve_users = set(self.payment_approve_users.ids)  # Fetch IDs of approve_users
        approved_users = set(self.payment_approved_users.ids)  # Fetch IDs of approved_users

        user_ids = list(approve_users - approved_users)

        if not user_ids:
            return

        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_admin_action')
        action['context'] = {
            'default_invoice_id': self.id,
            'user_ids': user_ids,
            'type_id': 'invf'
        }

        return action

    def action_log_message(self):
        default_user_ids = self.approve_users.ids
        print(default_user_ids, "Usersssss")
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_invoice_message_action1')
        action['context'] = {'default_request_id': self.id,
                             }
        print(action)
        return action

    def send_replay(self):
        unreplied_rfi_record = self.invoice_rfi_ids.filtered(
            lambda r: not r.replayed and r.to_user.id == self.env.user.id)
        print("the rfi record", unreplied_rfi_record)
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_invoice_replay_action1')
        action['context'] = {'default_message_id': unreplied_rfi_record.id,
                             'default_message': unreplied_rfi_record.message}
        return action



    def action_add_approver(self):
        print("i am in add approver")
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_invoice_action')
        action['context'] = {'default_invoice_id': self.id}
        return action
    def action_add_approver_admin(self):
        user_ids = [user.id for user in self.next_approve_user]
        if not user_ids:
            return
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_invoice_action')
        action['context'] = {'default_invoice_id': self.id,
                             'default_admin_add': True

                             }
        print(action)
        return action
    def action_add_approver_admin_finance(self):
        user_ids = [user.id for user in self.payment_next_approve_user]
        if not user_ids:
            return
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_invoice_action')
        action['context'] = {'default_invoice_id': self.id,
                             'default_admin_add': True

                             }
        print(action)
        return action

    def action_remark_approver(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_invoice_approve_action')
        action['context'] = {'default_invoice_id': self.id,
                             'default_approve_type': 'approve',
                             }
        print(action)
        return action

    def action_remark_reject(self):
        self.ensure_one()
        purchase_order = self.env['purchase.order'].search([('invoice_ids', '=', self.id)], limit=1)
        if purchase_order.exp_category and purchase_order.exp_category.reject_not_possible:
            raise ValidationError(
                "Rejection is not possible for this Invoice as the linked expense category does not allow rejection."
            )
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.remark_invoice_approve_action')
        action['context'] = {'default_invoice_id': self.id,
                             'default_approve_type': 'reject',
                             }
        print(action)
        return action


class InvoiceApproveLine(models.Model):
    _name = "invoice.approve.line"
    _description = "Approve Line"
    _order = 'approve_order asc'

    invoice_id = fields.Many2one('account.move', string='Invoice id',
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

class InvoiceApproveLine(models.Model):
    _name = "invoice.payment.approve.line"
    _description = "Payment Approve Line"
    _order = 'approve_order asc'

    invoice_id = fields.Many2one('account.move', string='Invoice id',
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



class LogMessage(models.TransientModel):
    _name = "log.invoice.message"
    _description = "Log Invoice"

    request_id = fields.Many2one(
        'account.move', string='Invoice', readonly=True)
    message = fields.Text("Message")
    user = fields.Many2one('res.users', "Requested By", default=lambda self: self.env.user.id)
    # user_ids = fields.Many2many('res.users', "To")
    to_users = fields.Many2many('res.users', 'log_message_invoice_users_rel', 'log_message_id', 'res_users_id',
                                "Requested_To", domain=lambda self: self._domain_to_users(), required=True)
    # user_from = fields.Many2many('res.users', "User_From", domain="[('groups_id', 'not in', [44])]", required=True)
    branch_id = fields.Many2many('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')
    email = fields.Char(string='Email', compute='_compute_email')
    cc_email = fields.Char(string='Email', compute='_compute_cc_email')
    user_cc = fields.Many2many('res.users', 'log_message_cc_invoice_users_rel', 'log_message_cc_id', 'res_users_cc_id',
                               "Cc", domain=lambda self: self._domain_user_cc())
    concatenated_branch_names = fields.Char(string="Branch Names", compute='_compute_branch_names')

    # pending_update = fields.Many2many('pending_actions', 'log_message_pending_action_rel', 'pending_id','users_id',"Pending")
    # pending_num = fields.Integer(string="Pending")

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
        print("request id is",self.request_id)

        model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)

        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.request_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_action_ids)


        for pending_action in pending_action_ids:
            # pending_action.status='closed'
            new_name = f"{self.request_id.name} waiting for Request for Information reply"
            pending_action.sudo().write({'name': new_name})

        for request in self.request_id:
            if self.user and self.message:
                body = (
                    f"{self.env.user.name} has logged a message in {self.request_id.name}.{self.message}"
                )
                base_url = self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Accounting')], limit=1) or False

                url_params = {
                    'id': self.request_id.id,
                    'action': self.env.ref(
                        'account.action_move_in_invoice_type').id,
                    'model': 'account.move',
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
                    'subject': f"Logged a message in {self.request_id.name}",
                    'body_html': body,
                    'email_to':  ', '.join(self.to_users.mapped('login')),
                    'email_cc': self.cc_email,
                    'author_id': author.id
                }
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()

                subject = "Query was raised against Invoice Request : %s" % self.request_id.name

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A Invoice Request with the name <strong>{self.request_id.name} is Pending at Request For Information where you are "
                    f"a approver.<br>"

                )
                if self.request_id.state == 'accounting':
                    for user in self.request_id.invoice_approve_line:
                        if self.env.user.id != user.id and user.status == 'accept':
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.user_id.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)

                    self.request_id.message_post(body=f"<strong>@{self.user.name}</strong>, {self.message}")
                    for user in self.to_users:
                        rfi_vals = {
                            'user_id': self.env.user.id,
                            'to_user': user.id,
                            'message': self.message,
                            'next_pending_ids': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False,
                            'accounting': True,
                        }

                        new_rfi_vals = self.env['pr.invoice.rfi'].create(rfi_vals)

                        self.request_id.invoice_rfi_ids |= new_rfi_vals
                        print("the new",new_rfi_vals.next_pending_ids.ids)

                        model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': "RFI" + " " + "on" + " " + "the" + " " + "invoice" + " " + self.request_id.name,
                            'record': self.request_id.id,

                            'date': date.today(),
                            'record_line': new_rfi_vals.id,
                            'approve_users': [(6, 0, [user.id])],
                        }
                        pendings = self.env['pending.actions'].create(pending_vals)

                if self.request_id.state == 'finance':
                    for user in self.request_id.invoice_payment_approve_line:
                        if self.env.user.id != user.id and user.status == 'accept':
                            mail_values = {
                                'subject': subject,
                                'body_html': body,
                                'email_to': user.user_id.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)

                    self.request_id.message_post(body=f"<strong>@{self.user.name}</strong>, {self.message}")
                    for user in self.to_users:
                        rfi_vals = {
                            'user_id': self.env.user.id,
                            'to_user': user.id,
                            'message': self.message,
                            'next_pending_ids': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False
                        }

                        new_rfi_vals = self.env['pr.invoice.rfi'].create(rfi_vals)

                        self.request_id.invoice_rfi_ids |= new_rfi_vals
                        print("the new", new_rfi_vals.next_pending_ids.ids)
                        model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': "Request For Information" + " " + "on" + " " + "the" + " " + "invoice" + " " + self.request_id.name,
                            'record': self.request_id.id,

                            'date': date.today(),
                            'record_line': new_rfi_vals.id,
                            'approve_users': [(6, 0, [user.id])],
                        }
                        pendings = self.env['pending.actions'].create(pending_vals)


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
    _name = "pr.invoice.rfi"
    _description = "RFI Line nvoice"

    invoice_id = fields.Many2one('account.move', string='Invoice Request Id',
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
    is_to_user_id = fields.Boolean(default=False, compute='_get_current_user_details')

    accounting = fields.Boolean("IS LE")

    next_pending_ids = fields.Many2many(
        comodel_name='pending.actions',
        string='Pending Action',
        relation='last_invoice_pend',
        column1='pr_invoice_rfi_invoice_id',
        column2='pending_actions_id',
        store=True
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.to_user.name}"))
        return result

    @api.depends('to_user')
    def _get_current_user_details(self):
        current_user_id = self.env.user.id
        for record in self:
            if record.to_user and record.to_user.id == current_user_id:
                record.is_to_user_id = True
            else:
                record.is_to_user_id = False

    def send_replay(self):
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_log_invoice_replay_action1')
        action['context'] = {'default_message_id': self.id}
        return action


class LogMessageReplay(models.TransientModel):
    _name = "message.invoice.replay"
    _description = "Log"

    message_id = fields.Many2one(
        'pr.invoice.rfi', string='Replay', readonly=True)
    message = fields.Char(string="Message", readonly=True)
    replay = fields.Char("Message", required=True)

    def confirm(self):
        print(" i am here")

        model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)
        pending_ids = self.env['pending.actions'].sudo().search([('model', '=', model.id),('record_line', '=', self.message_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_ids)

        for rec in pending_ids:
            if self.env.user in rec.approve_users:
                print("record to close", rec)
                rec.status = 'closed'

        for line in self.message_id:
            line.replay = self.replay
            line.replayed = True
            line.status = 'close'
        self.message_id.invoice_id.message_post(
            body=f"<strong>@{self.env.user.name}</strong>,Replied: {self.replay}, to {self.message_id.user_id.name}")

        model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)
        print(model.id)
        print(self.message_id.id)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.message_id.invoice_id.id), ('status', '=', 'open')])



        all_record_lines_replayed = all(line.replay for line in self.message_id.invoice_id.invoice_rfi_ids)

        if all_record_lines_replayed:
            if self.message_id.accounting == True:
                self.message_id.invoice_id.state = 'accounting'
            else:
                self.message_id.invoice_id.state = 'finance'
            for pending_action in pending_action:
                print("all are replayed")
                new_name = f"{self.message_id.invoice_id.name} --Replied for Request for Information"
                pending_action.sudo().write({'name': new_name})
                pending_action.sudo().write({'date': fields.Datetime.now()})
            # If all record lines have their 'replay' column filled, change the status to 'requested'
        pending = self.env['pending.actions'].sudo().search(
            [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id),('name', 'not like', 'waiting for Request for Information reply')], order='id desc', limit=1)
        print("if,,,,,,,,,..pending actions", pending)
        if pending:
            print("if")
            return pending.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')

            return action




class AddApprover(models.TransientModel):
    _name = 'add.approver.invoice.wizard'

    _description = "Add Approver Invoice workflow"

    invoice_id = fields.Many2one('account.move', string='Invoice Request Id',

                            invisible=True)
    user = fields.Many2one('res.users', string="User", required=True, domain="[('groups_id', 'not in', [44])]")

    order = fields.Integer(string="Order No", required=True)

    branch_id = fields.Many2one('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')

    email = fields.Char(string='Email')
    admin_add = fields.Boolean(string="Is Admin")

    @api.onchange('user')
    def _compute_branch_id(self):

        for rec in self:
            rec.branch_id = rec.user.branch_id.id

            rec.email = rec.user.login

    def add_user(self):
        print("the invoice id is",self.invoice_id)

        if self.invoice_id:
            if self.invoice_id.state == 'accounting':

                if not self.admin_add:
                    for line in self.invoice_id.invoice_approve_line:
                        print("i am inside the invoice",self.invoice_id.invoice_approve_line)

                        if line.user_id == self.env.user:
                            current_order = line.approve_order
                else:
                    approve_dict = {}
                    for line in self.invoice_id.invoice_approve_line:
                        approve_dict[line.approve_order] = line.status
                    sorted_approve_dict = {k: v for k, v in sorted(approve_dict.items(), key=lambda item: item[1])}
                    first_draft_approve_order = None
                    print("sorted", sorted_approve_dict, approve_dict)
                    for approve_order, status in sorted_approve_dict.items():
                        if status == 'draft':
                            print("working", approve_order)
                            first_draft_approve_order = approve_order
                            break  # Exit loop as soon as the first draft is found
                    if first_draft_approve_order is None:
                        raise ValidationError("No Pending status found in the Approve Users.")
                    # for line in self.pr_id.pr_approve_line:
                    #     if line.approve_order == first_draft_approve_order:
                    #         user_id = line.user_id
                    current_order = first_draft_approve_order

                records = self.env['invoice.approve.line'].sudo().search([('invoice_id', '=', self.invoice_id.id)])

                highest_record = max(records, key=lambda r: r.approve_order)

                highest_approve_order = highest_record.approve_order

                if current_order < self.order and self.order <= highest_approve_order + 1:

                    self.invoice_id.approve_users |= self.user

                    model = self.env['invoice.approve.line'].sudo().search(
                        [('invoice_id', '=', self.invoice_id.id), ('approve_order', '>=', self.order)])

                    for line in model:
                        line.approve_order += 1

                    vals = {

                        'invoice_id': self.invoice_id.id,

                        'user_id': self.user.id,

                        'approve_order': self.order,

                        'status': 'draft'

                    }

                    approve_line = self.env['invoice.approve.line'].sudo().create(vals)

                    self.invoice_id.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")

                elif self.order == current_order:
                    self.invoice_id.approve_users |= self.user
                    model = self.env['invoice.approve.line'].sudo().search(
                        [('invoice_id', '=', self.invoice_id.id), ('approve_order', '>=', self.order),
                         ('status', 'in', ('draft', 'deligate'))])
                    self.invoice_id.write({'next_approve_user': [(6, 0, [self.user.id])]})

                    for line in model:
                        print("users", line.user_id.name)
                        line.approve_order += 1
                    vals = {
                        'invoice_id': self.invoice_id.id,
                        'user_id': self.user.id,
                        'approve_order': self.order,
                        'status': 'draft'
                    }
                    approve_line = self.env['invoice.approve.line'].sudo().create(vals)
                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')], limit=1)
                    activity = self.env['mail.activity'].search([
                        ('res_model_id', '=',
                         self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                        ('res_id', '=', self.invoice_id.id),
                        ('activity_type_id', '=', activity_type.id),
                    ])
                    if activity:
                        for rec in activity:
                            rec.action_feedback(feedback=f"User Added at {self.order} position")
                    model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)
                    pending_action = self.env['pending.actions'].sudo().search(
                        [('model', '=', model.id), ('record', '=', self.invoice_id.id), ('status', '=', 'open')])
                    if pending_action:
                        for pending in pending_action:
                            pending.status = 'closed'

                    pending_vals = {
                        'model': model.id,
                        'name': str(self.invoice_id.po_number.name) + " " +self.invoice_id.name + " " + "Invoice Request Waiting For Approval-Accounting",
                        'record': self.invoice_id.id,
                        'branch': self.invoice_id.branch_id.id,
                        'date': date.today(),
                    }
                    print("user", self.user, "next", self.invoice_id.next_approve_user)
                    if self.user:
                        print("workkkkkkkkkkk")
                        user_ids_to_pass = self.user.ids
                        pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                        pendings = self.env['pending.actions'].create(pending_vals)
                        print("Pendinggg", pendings)
                        activity_type = self.env['mail.activity.type'].sudo().search(
                            [('name', '=', 'Pending Request')],
                            limit=1)
                        activity_type_id = activity_type.id if activity_type else False
                        res_model_id = self.env['ir.model'].sudo().search(
                            [('model', '=', 'account.move')]).id
                        for user_id in user_ids_to_pass:
                            activity_values = {
                                'user_id': user_id,
                                'res_id': self.invoice_id.id,
                                'note': "Pending Action",
                                'summary': "Action",
                                'activity_type_id': activity_type_id,
                                'res_model_id': res_model_id,
                            }
                            created_activity = self.env['mail.activity'].create(activity_values)
                            subject = "New invoice Request Raised: %s" % self.invoice_id.name
                            print("Name", self.invoice_id.name)

                            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            menu_id = self.env['ir.ui.menu'].sudo().search(
                                [('name', '=', 'Accounting')], limit=1) or False

                            url_params = {
                                'id': self.invoice_id.id,
                                'action': self.env.ref('account.action_move_in_invoice_type').id,
                                'model': 'account.move',
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
                                f"A new Invoice Request with the name <strong>{self.invoice_id.name}</strong> has been raised against Purchase Request by <strong></strong>.<br>"
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
                                    'email_to': self.user.login,
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    self.invoice_id.message_post(
                        body=f" {self.env.user.name} Added User {self.user.name} at position {self.order}.")

                elif self.order > highest_approve_order + 1:

                    raise UserError(_("Order No cannot be exceeded than existing max order No "))

                else:

                    raise UserError(_("Order No cannot be less than or equal to your Order No"))

            if self.invoice_id.state == 'finance':

                if not self.admin_add:

                    for line in self.invoice_id.invoice_payment_approve_line:
                        print("i am inside the invoice", self.invoice_id.invoice_payment_approve_line)

                        if line.user_id == self.env.user:
                            current_order = line.approve_order
                else:
                    approve_dict = {}
                    for line in self.invoice_id.invoice_payment_approve_line:
                        approve_dict[line.approve_order] = line.status
                    sorted_approve_dict = {k: v for k, v in sorted(approve_dict.items(), key=lambda item: item[1])}
                    first_draft_approve_order = None
                    print("sorted", sorted_approve_dict, approve_dict)
                    for approve_order, status in sorted_approve_dict.items():
                        if status == 'draft':
                            print("working", approve_order)
                            first_draft_approve_order = approve_order
                            break  # Exit loop as soon as the first draft is found
                    if first_draft_approve_order is None:
                        raise ValidationError("No Pending status found in the Approve Users.")
                    # for line in self.pr_id.pr_approve_line:
                    #     if line.approve_order == first_draft_approve_order:
                    #         user_id = line.user_id
                    current_order = first_draft_approve_order

                records = self.env['invoice.payment.approve.line'].sudo().search([('invoice_id', '=', self.invoice_id.id)])

                highest_record = max(records, key=lambda r: r.approve_order)

                highest_approve_order = highest_record.approve_order

                if current_order < self.order and self.order <= highest_approve_order + 1:

                    self.invoice_id.payment_approve_users |= self.user

                    model = self.env['invoice.payment.approve.line'].sudo().search(
                        [('invoice_id', '=', self.invoice_id.id), ('approve_order', '>=', self.order)])

                    for line in model:
                        line.approve_order += 1

                    vals = {

                        'invoice_id': self.invoice_id.id,

                        'user_id': self.user.id,

                        'approve_order': self.order,

                        'status': 'draft'

                    }

                    approve_line = self.env['invoice.payment.approve.line'].sudo().create(vals)

                    self.invoice_id.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")
                
                elif self.order == current_order:
                    self.invoice_id.approve_users |= self.user
                    model = self.env['invoice.payment.approve.line'].sudo().search(
                        [('invoice_id', '=', self.invoice_id.id), ('approve_order', '>=', self.order),
                         ('status', 'in', ('draft', 'deligate'))])
                    self.invoice_id.write({'payment_next_approve_user': [(6, 0, [self.user.id])]})

                    for line in model:
                        print("users", line.user_id.name)
                        line.approve_order += 1
                    vals = {
                        'invoice_id': self.invoice_id.id,
                        'user_id': self.user.id,
                        'approve_order': self.order,
                        'status': 'draft'
                    }
                    approve_line = self.env['invoice.payment.approve.line'].sudo().create(vals)
                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')], limit=1)
                    activity = self.env['mail.activity'].search([
                        ('res_model_id', '=',
                         self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                        ('res_id', '=', self.invoice_id.id),
                        ('activity_type_id', '=', activity_type.id),
                    ])
                    if activity:
                        for rec in activity:
                            rec.action_feedback(feedback=f"User Added at {self.order} position")
                    model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')], limit=1)
                    pending_action = self.env['pending.actions'].sudo().search(
                        [('model', '=', model.id), ('record', '=', self.invoice_id.id), ('status', '=', 'open')])
                    if pending_action:
                        for pending in pending_action:
                            pending.status = 'closed'

                    pending_vals = {
                        'model': model.id,
                        'name': str(
                            self.invoice_id.po_number.name) + " " + self.invoice_id.name + " " + "Invoice Request Waiting For Approval-Finance",
                        'record': self.invoice_id.id,
                        'branch': self.invoice_id.branch_id.id,
                        'date': date.today(),
                    }
                    print("user", self.user, "next", self.invoice_id.payment_next_approve_user )
                    if self.user:
                        print("workkkkkkkkkkk")
                        user_ids_to_pass = self.user.ids
                        pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                        pendings = self.env['pending.actions'].create(pending_vals)
                        print("Pendinggg", pendings)
                        activity_type = self.env['mail.activity.type'].sudo().search(
                            [('name', '=', 'Pending Request')],
                            limit=1)
                        activity_type_id = activity_type.id if activity_type else False
                        res_model_id = self.env['ir.model'].sudo().search(
                            [('model', '=', 'account.move')]).id
                        for user_id in user_ids_to_pass:
                            activity_values = {
                                'user_id': user_id,
                                'res_id': self.invoice_id.id,
                                'note': "Pending Action",
                                'summary': "Action",
                                'activity_type_id': activity_type_id,
                                'res_model_id': res_model_id,
                            }
                            created_activity = self.env['mail.activity'].create(activity_values)
                            subject = "New invoice Request Raised: %s" % self.invoice_id.name
                            print("Name", self.invoice_id.name)

                            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            menu_id = self.env['ir.ui.menu'].sudo().search(
                                [('name', '=', 'Accounting')], limit=1) or False

                            url_params = {
                                'id': self.invoice_id.id,
                                'action': self.env.ref('account.action_move_in_invoice_type').id,
                                'model': 'account.move',
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
                                f"A new Invoice Request with the name <strong>{self.invoice_id.name}</strong> has been raised against Purchase Request by <strong></strong>.<br>"
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
                                    'email_to': self.user.login,
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    self.invoice_id.message_post(
                        body=f" {self.env.user.name} Added User {self.user.name} at position {self.order}.")


                elif self.order > highest_approve_order + 1:

                    raise UserError(_("Order No cannot be exceeded than existing max order No "))

                else:

                    raise UserError(_("Order No cannot be less than or equal to your Order No"))


class Remark(models.TransientModel):
    _name = "invoice.remark"
    _description = "Invoice Remark"
    _inherit = ['mail.thread']

    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Char("Remark", required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('reject', 'Rejected')],
        string='State')

    def confirm_remark(self):

        if self.invoice_id and self.approve_type == 'approve':
            if self.invoice_id.state == 'accounting':
                print("i am inside the confirm")
                # self.invoice_id.message_post(body=f" {self.env.user.name} Approved.")
                self.invoice_id.message_post(body="Remarks " + self.replay)
                vals = {
                    'invoice_id': self.invoice_id.id,
                    'from_user': self.env.user.id,
                    'replay': self.replay,
                    'for_type': "InvoiceRequest",
                    'approve_type': 'approve',

                }
                remarks_save = self.env['remark.invoice.save'].create(vals)

                self.invoice_id.action_approval()

                pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
                if pending:
                    return pending.open_record()
                else:
                    action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                    return action

            if self.invoice_id.state == 'finance':
                print("i am inside the confirm")
                # self.invoice_id.message_post(body=f" {self.env.user.name} Approved.")
                self.invoice_id.message_post(body="Remarks " + self.replay)
                vals = {
                    'invoice_id': self.invoice_id.id,
                    'from_user': self.env.user.id,
                    'replay': self.replay,
                    'for_type': "InvoiceRequest",
                    'approve_type': 'approve',

                }
                remarks_save = self.env['remark.invoice.save'].create(vals)

                self.invoice_id.action_payment_approver()

                pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
                if pending:
                    return pending.open_record()
                else:
                    action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                    return action

        if self.invoice_id and self.approve_type == 'reject':
            # self.invoice_id.message_post(body=f" {self.env.user.name} Rejected.")
            self.invoice_id.message_post(body="Remarks " + self.replay)
            vals = {
                'invoice_id': self.invoice_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "Invoice Request",
                'approve_type': 'reject',

            }
            remarks_save = self.env['remark.invoice.save'].create(vals)
            self.invoice_id.action_rejected()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action

class RemarkSave(models.Model):
    _name = "remark.invoice.save"
    _description = "Remark"

    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Char("Remark", required=True)
    for_type = fields.Char("Approval Type")
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('reject', 'Rejected'), ('deligate', 'Delegate')],
        string='State')


