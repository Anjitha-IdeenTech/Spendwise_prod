from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from datetime import date
import json
from datetime import timedelta

class ProductInherit(models.Model):
    _inherit = "product.template"

    product_tender_line_id = fields.One2many('product.tender.line',
                                             'product_template_id',
                                             string='Product Tender Line',
                                             tracking=True)

    brand = fields.Char("Brand")
    oem = fields.Char("OEM")
    pack_size = fields.Float("Pack Size")

    contracts_count = fields.Char("Count",compute="compute_contracts_count")

    @api.constrains('name')
    def _check_unique_product_name(self):
        for record in self:
            if self.env['product.template'].search_count([('name', '=', record.name)]) > 1:
                raise ValidationError("Product with the same name already exists!")

    def compute_contracts_count(self):
        for rec in self:
            contracts_count = self.env['product.tender.line'].search_count([('product_product_line.product_id', '=', self.id),
                       ('status', '=', 'active'),('company_ids','in',self.env.company.id)])
            rec.contracts_count = contracts_count



    def view_contracts(self):
        print("helloooo")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rate Contracts',
            'view_mode': 'tree,form',
            'res_model': 'product.tender.line',
            'domain': [('product_product_line.product_id', '=', self.id),
                       ('status', '=', 'active'),('company_ids','in',self.env.company.id)],
            'target': 'current'
        }


class ProductTenderLine(models.Model):
    _name = "product.tender.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rate Contracts"

    name = fields.Char(string="Contract No", readonly=True, required=True, copy=False, default='New')
    purchase_tender_type = fields.Char(string='Tender Type')
    vendor = fields.Many2one('res.partner', string='Vendor',required=True)
    purchase_representative = fields.Many2one('res.users', string='Purchase Representative')
    quantity = fields.Float(string='Quantity')
    unit_price = fields.Float(string='Unit Price')
    total = fields.Float(string='Total')
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        invisible=True
    )
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user, invisible=True)
    product_template_id = fields.Many2one('product.template', string='Product Template Id',
                                          invisible=True)
    tender_deadline = fields.Date(string="Deadline")

    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    active_status = fields.Selection([('active', 'Active'),
                                      ('cancel', 'Cancel'),
                                      ('expire','Expired')], string='Active')
    min_qty = fields.Float(string='Minimum Quantity', tracking=True)
    delivery_terms = fields.Text(string='Delivery Terms', tracking=True)
    recuring = fields.Boolean(string="Recurring Payment",default=False)

    status = fields.Selection(
        selection=[('active', 'Active'), ('expire', 'Expired'), ('resubmit', 'Resubmited'),
                   ('renew', 'Renewed'),('terminate', 'Terminated')
                   ],
        string='State',
        default='active',
        required=True
    )

    to_approve_users = fields.Many2many(
        'res.users',
        'rel_tender_apprvers',
        'tender_id',
        'approvrs',
        string='Approve Users',
    )
    approved_users = fields.Many2many(
        'res.users',
        'approved_tender_relation',
        'tender_apprved',
        'tender_user_id',
        string='Approved Users',
    )

    next_approve_user = fields.Many2many(
        'res.users',
        'next_aprved_tender',
        'next_tender',
        'tender_users_id',
        string='Next Approver', )

    is_an_approver = fields.Boolean("Approver", compute='compute_is_approver')

    approve_contract_line_ids = fields.One2many('product.tender.approve.line',
                                                'contract_approve_ids',
                                                string='Tender Approve Line',
                                                tracking=True)
    mail_send =fields.Boolean("Mail Send")
    mail_send_reminder = fields.Boolean("Mail Send Reminder")
    payment_terms = fields.Many2one('account.payment.term', "Payment Terms", required=True)
    lead_time = fields.Integer("Lead Time in days")
    company_ids = fields.Many2many('res.company', 'companies_contract_rel', 'contct_id', 'company_id',
                                   string="Allowed Companies",required=True)

    branch_ids = fields.Many2many('res.branch', 'branches_contract_rel', 'contrct_id', 'branch_id',
                                   string="Allowed Branches",required=True)

    branch_domain = fields.Char(
        compute="_compute_branch_domain",
        readonly=True,
        store=False,
    )

    request_no = fields.Many2one('tenders', string='Contract Request No')

    product_group = fields.Many2many('products.group', 'groups_contract_rel', 'contrcts_id', 'group_id',
                                   string="Product Group")


    product_product_line = fields.One2many('product.contracts.line',
                                                'products_line',
                                                string='Products Contracts Line',
                                                tracking=True)
    product_quantity_line = fields.One2many('quantity.terms',
                                           'quantity_line',
                                           string='Products Value terms',
                                           tracking=True)
    reason = fields.Char(string="Termination Reason", store=True)
    cancel_date = fields.Date(string="Termination Date")
    exp_category = fields.Many2one('expense.category', 'Expense Category')
    exp_category_domain = fields.Char(
        compute="_compute_exp_category_domain",
        readonly=True,
        store=False,
    )
    renew_visible = fields.Boolean("Renew Visible",default=False)
    purchase_plan = fields.Selection([
        ('monthly', 'Monthly '),
        ('one_time', 'One Time'),
        ('yearly', 'Yearly'),
    ], string="Purchase Plan")

    attachment_vendor_ids = fields.Many2many('ir.attachment', 'class_ir_attachments_rate_rel', 'class_id',
                                             'attachment_id',
                                             'Attachments')

    purchase_head = fields.Many2one('res.users', string='Purchase Head')
    is_purchase_head = fields.Boolean(string='Is Purchase Head', compute='_compute_purchase_head')
    assigned = fields.Boolean(string='Assign', default=False)
    assigned_to = fields.Many2many(
        'res.users',
        'assigned_user_tend_rel',
        'tender_id',
        'user_id',
        string='Buyer'
    )

    vendor_addresss = fields.Html(string="Vendor Address", store=True)
    vendor_change_name = fields.Text(string="Vendor Name", store=True)

    @api.onchange('vendor')
    def _onchange_partner_id(self):
        """Fetch and update the full vendor's address when the vendor changes."""
        for record in self:
            if record.vendor:
                # Construct the full address
                record.vendor_change_name = record.vendor.name or ""
                address_lines = "<br/>".join(filter(None, [
                    f"(Partner Code: {record.vendor.ref or ''})",
                    f"GST No: {record.vendor.vat or ''}",
                    f"{record.vendor.street or ''}, {record.vendor.street2 or ''}",
                    f"{record.vendor.city or ''}, {record.vendor.state_id.name or ''}, {record.vendor.country_id.name or ''}"
                    f"Pin: {record.vendor.zip or ''}".strip(", "),
                    f"Phone: {record.vendor.phone or ''}",
                    f"Email: {record.vendor.email or ''}"
                ]))
                record.vendor_addresss = address_lines
            else:
                record.vendor_address = False

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
        action['context'] = {'default_current_tr': self.id
                             }
        print(action)
        return action


    @api.constrains('start_date')
    def _check_start_date(self):
        for record in self:
            if record.start_date and record.start_date < fields.Date.today():
                # raise ValidationError("Start date cannot be set in the past.")
                print("Start date cannot be set in the past")

    @api.constrains('end_date')
    def _check_end_date(self):
        for record in self:
            if record.end_date and record.end_date < fields.Date.today():
                raise ValidationError("End date cannot be set in the past.")


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
                rec.product_product_line = lines
            else:
                rec.product_product_line = [(5, 0, 0)]

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

    @api.onchange('company_ids')
    def onchange_company_ids(self):
        selected_company_ids = self.company_ids.ids
        allowed_branch_ids = []
        if self.branch_ids:

            for branch in self.branch_ids:
                if branch.company_id.id in selected_company_ids:
                    allowed_branch_ids.append(branch.id)

            self.branch_ids = [(6, 0, allowed_branch_ids)]
            print(allowed_branch_ids)

        # for rec in self
            # removed_companies = rec._origin.company_ids - rec.company_ids
            # print(removed_companies)
            # if removed_companies:
            #     removed_company_ids = removed_companies.ids
            #     rec.branch_ids -= rec.branch_ids.filtered(lambda branch: branch.company_id.id in removed_company_ids)

    def action_open_contract_request(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract Requests',
            'view_mode': 'tree,form',
            'res_model': 'tenders',
            'domain': [('id', '=', self.request_no.id),
                      ],
            'target': 'current'
        }

    def action_open_purchase_request(self):
        records1 = self.env['purchase.order'].sudo().search([('partner_id', '=', self.vendor.id),

                                                             ('create_date', '>=', self.start_date),
                                                             ('create_date', '<=', self.end_date)])
        print("records1 ", records1)
        product_request_ids = records1.mapped('pr_id')
        records2 = self.env['product.request'].sudo().search(
            [('id', 'in', product_request_ids.ids), ('requested_date', '>=', self.start_date),
             ('requested_date', '<=', self.end_date), ])
        matching_purchase_order_ids = []
        for purchase_request in records2:
            # Check each order line of the current purchase order
            print(purchase_request)
            for line in purchase_request.product_request_line_ids:
                # If the product ID of the order line is in the product IDs of self
                print(line)
                if line.product.name in self.product_product_line.mapped('product_id.name'):
                    # Add the purchase order ID to the list
                    matching_purchase_order_ids.append(purchase_request.id)
                    # Break the loop to avoid adding the same purchase order multiple times
                    break
        print("matching_purchase_order_ids", matching_purchase_order_ids)
        # Search for the purchase orders with the matching IDs
        purchase_requests = self.env['product.request'].browse(matching_purchase_order_ids)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Requests(Approved)',
            'view_mode': 'tree,form',
            'res_model': 'product.request',
            'domain': [('id', 'in', matching_purchase_order_ids),
                       ],
            'target': 'current'
        }

    def action_open_purchase_order(self):
        # records1 = self.env['purchase.order'].sudo().search([('partner_id', '=', self.vendor.id),
        #                                                      ('state', 'in', ['purchase', 'done']),
        #                                                      ('create_date', '>=', self.start_date),
        #                                                      ('create_date', '<=', self.end_date)])
        # print("records1 ", records1)
        # product_request_ids = records1.mapped('pr_id')
        # records2 = self.env['product.request'].sudo().search(
        #     [('id', 'in', product_request_ids.ids), ('requested_date', '>=', self.start_date),
        #      ('requested_date', '<=', self.end_date), ])

        # purchase_ordersss = self.env['purchase.order'].search([
        #     ('pr_id', 'in', records2.ids),])
        # matching_purchase_order_ids = []
        # print(purchase_ordersss)
        # for purchase_order in purchase_ordersss:
        #     # Check each order line of the current purchase order
        #     print(purchase_order)
        #     for order_line in purchase_order.order_line:
        #         # If the product ID of the order line is in the product IDs of self
        #         print(order_line)
        #         if order_line.product_id.name in self.product_product_line.mapped('product_id.name'):
        #             # Add the purchase order ID to the list
        #             matching_purchase_order_ids.append(order_line.id)
        #             # Break the loop to avoid adding the same purchase order multiple times

        # print("matching_purchase_order_ids", matching_purchase_order_ids)
        # # Search for the purchase orders with the matching IDs
        # purchase_orders = self.env['purchase.order'].browse(matching_purchase_order_ids)
        records1 = self.env['purchase.order'].sudo().search([('partner_id', '=', self.vendor.id),
                                                             ('state', 'in', ['purchase', 'done']),('ct_number','in',self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order.line',
            'views': [(self.env.ref('lease_management.view_purchase_order_line_custom_tree').id, 'tree')],
            'domain': [('order_id', 'in', records1.ids),
                       ],
            'target': 'current'
        }


    def button_terminate(self):
        print("kkkk")
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.termination_action')
        action['context'] = {'default_contract_id': self.id}
        # self.status="terminate"
        return action

    @api.depends('next_approve_user')
    def compute_is_approver(self):
        for rec in self:
            rec.is_an_approver = self.env.user.id in rec.next_approve_user.mapped('id')

    def button_approve(self):
        print("Helloooo")
        self.write({'approved_users': [(4, self.env.user.id)]})
        self.write({'next_approve_user': [(3, self.env.user.id)]})
        approver = self.env['product.tender.approve.line'].sudo().search(
            [('contract_approve_ids', '=', self.id), ('user_id', '=', self.env.user.id)])
        for record in approver:
            record.write({'status': 'approve'})

        # self.is_an_approver = False
        approve_users = self.env['product.tender.approve.line'].sudo().search(
            [('contract_approve_ids', '=', self.id)], order='approve_order asc')

        user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
        # user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
        current_order = None
        next_user = None

        for user in user_ids:
            if self.env.user.id == user['u_id']:
                current_order = user['order']

        if current_order is not None:
            for user in user_ids:
                if user['order'] == current_order + 1:
                    next_user = user

        if next_user:
            next_user_id = next_user['u_id']
            next_order = next_user['order']
            self.write({'next_approve_user': [(4, next_user_id)]})

            print("Next User ID:", next_user_id)
            print("Next Order:", next_order)
        else:
            all_approved = all(approver.status == 'approve' for approver in approve_users)

            if all_approved:
                self.status = 'renew'
                model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id)], limit=1)

                if pending_action:
                    pending_action.status = 'closed'
                print("approved")
                tender_lines = []
                for line in self.product_product_line:

                    tender_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'unit_price': line.unit_price,
                        'product_group': line.product_group,
                    }))
                tender_record = self.env['product.tender.line'].create({
                    'vendor': self.vendor.id,
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'lead_time': self.lead_time,
                    'payment_terms': self.payment_terms.id,
                    'user_id': self.user_id.id,
                    'company_ids': [(4, company_id) for company_id in self.company_ids.ids],
                    'branch_ids': [(4, branch_id) for branch_id in self.branch_ids.ids],
                    # 'request_no': self.id,
                    'delivery_terms': self.delivery_terms,
                    'status': 'renew',
                    'product_product_line': tender_lines
                })

                # tender_vals = {
                #     'product': self.product_template_id.id,
                #     'requested_to': self.vendor.id,
                #     'unit_price': self.unit_price,
                #     'quantity': self.quantity,
                #     'user_id': self.user_id.id,
                #     'renew_id': self.id,
                #     'requested_date': date.today(),
                # }

                # contract_vals = {
                #     'product': self.product_template_id.id,
                #     'requested_to': self.vendor.id,
                #     'unit_price': self.unit_price,
                #     'quantity': self.quantity,
                #     'user': self.user_id.id,
                #     'user_id': self.vendor.user_id.id,
                #     'from_date': date.today(),
                #     'renew_id': self.id,
                #     'renewal': True
                # }
                # print(self.user_id.name)
                # print(self.vendor.id)
                # tender_request = self.env['tenders'].sudo().create(tender_vals)
                # model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                # pending_vals = {
                #     'model': model.id,
                #     'name': tender_request.name,
                #     'record': tender_request.id,
                #     'date': date.today(),

                # }

                # # if approve_user_ids:
                # #     user_ids_to_pass = [user['user_id'] for user in approve_user_ids]
                # #     pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                # pendings = self.env['pending.actions'].create(pending_vals)
                # contract_record = self.env['contract'].sudo().create(contract_vals)
                # self.message_post(body="Contract generated for vendor, wait for vendor approval")

                # print(tender_request.id)
                # print(tender_request.name)


            else:
                print("not approved")

            # self.state = 'approve'
            print("Current user is the last approver or not found.")

    def contract_expire(self):
        print("hellooooooo")
        today = date.today()
        tender_line = self.env['product.tender.line'].sudo().search([('status', '=', 'active')])
        print(tender_line)
        for rec in tender_line:
            if rec.purchase_plan != 'one_time':
                print(rec,"montly plan")
                print(rec.end_date)
                print((rec.end_date - timedelta(days=30)))
                if rec.exp_category.name in ['Non-Maruti Insurance (Non-MI)', 'Maruti Insurance (MI)']:
                    notify_days = 10
                else:
                    notify_days = 30

                notify_date = rec.end_date - timedelta(days=notify_days) if rec.end_date else None
                if rec.end_date and today >= notify_date:
                    print("expiredddddd")
                    if rec.mail_send_reminder != True:
                        author = self.env['res.partner'].sudo().search(
                            [('name', '=', 'Administrator')], limit=1)
                        
                        body = (
                                f"Dear User,Your contract for {rec.product_template_id.name} going to be expired in 30 days")
                        vals = {

                            'subject': 'Product Contract going to be expired',
                            'body_html': body,
                            # 'email_to': ','.join(mail_to),
                            'email_to': rec.vendor.email ,
                            'auto_delete': False,
                            'email_cc': rec.user_id.login,
                            # 'email_from': ,
                            'author_id': author.id
                            
                        }
                        # print(vals)
                        mail_id = self.env['mail.mail'].sudo().create(vals)
                        
                        mail_id.sudo().send()
                        rec.mail_send_reminder = True
                        rec.renew_visible = True

                        if rec.exp_category.name in ['Non-Maruti Insurance (Non-MI)', 'Maruti Insurance (MI)']:
                            users_line = self.env['res.users.line'].sudo().search(
                            [
                                ('department_id.name', '=', 'SCM'),
                                ('designation', '=', 'Fleet Manager')], limit=1)
                        else:
                            users_line = self.env['res.users.line'].sudo().search(
                                [
                                    ('department_id.name', '=', 'SCM'),
                                    ('designation', '=', 'Purchase Head')], limit=1)
                        print("Purchase head", users_line, users_line.res_user_id.name)
                        # tender_line.purchase_head = users_line.res_user_id.id
                        if users_line and users_line.res_user_id:
                            existing_user = rec.purchase_head
                            if existing_user != users_line.res_user_id.id:  # Only update if different
                                rec.purchase_head = users_line.res_user_id.id
                        if users_line and users_line.res_user_id.id:


                            ########### Creating Pending Actions

                            model = self.env['ir.model'].sudo().search([('model', '=', 'product.tender.line')], limit=1)
                            pending_vals = {
                                'model': model.id,
                                'name': rec.name + " " + "Contract Renew Date Approaching",
                                'record': rec.id,

                                'exp_category': rec.exp_category.id,

                                'date': date.today(),
                            }

                            user_ids = [user.id for user in users_line.res_user_id]
                            pending_vals['approve_users'] = [(6, 0, user_ids)]
                            pendings = self.env['pending.actions'].create(pending_vals)

                            rec.message_post(
                                body="Contract Expiring in {} days and Buyer's Notified".format(notify_days))
                        else:
                            raise UserError("No User found on Buyer group")
                if rec.end_date and today >= rec.end_date :
                    rec.status = 'expire'
                    # rec.active_status = 'expire'
                    if rec.mail_send != True:

                        body = (
                                f"Dear User,Your contract for {rec.product_template_id.name} has been expired")
                        vals = {
                            'subject': 'Product Contract Expired',
                            'body_html': body,
                            # 'email_to': ','.join(mail_to),
                            'email_to': rec.vendor.email ,
                            'auto_delete': False,
                            'email_cc': rec.user_id.login
                            # 'email_from': ,
                        }
                        # print(vals)
                        mail_id = self.env['mail.mail'].sudo().create(vals)
                        mail_id.sudo().send()
                        rec.mail_send = True

            elif rec.end_date and today >= rec.end_date :
                print("single")
                rec.status = 'expire'
    def action_tender_close(self):
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


    def action_tender_resubmission(self):
        print("re submit")
        
        vals = {
            'vendor_id': self.vendor.id,
            'exp_category' : self.request_no.exp_category.id,
            'expense_type' : self.request_no.expense_type,
            'payment_terms' :self.payment_terms.id,
            'company_ids': [(6, 0, self.company_ids.ids)],  # Correct format for many2many field
            'branch_ids': [(6, 0, self.branch_ids.ids)],
            'purchase_plan': self.purchase_plan,

        }
        print("vals",vals)
        ctr = self.env['tenders'].create(vals)
        print('ctr',ctr)
        for rec in self.product_product_line:
            vals = {
                'product_id': rec.product_id.id,
                'unit_price': rec.unit_price,
                'contracts_lines':ctr.id,
            }
            line = self.env['contract.request.lines'].create(vals)

        ctr.message_post(body=f"{self.env.user.name} Resubmitted the Contract {self.name}")
        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

        if pending_action:
            for rec in pending_action:
                rec.status = 'closed'

        model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
        pending_vals = {
            'model': model.id,
            'name': ctr.name + " " + "Contract Request Created from " + self.name + " Renew",
            'record': ctr.id,

            'date': date.today(),
        }
        if self.branch_ids:
            first_branch_id = self.branch_ids[0].id
            pending_vals['branch'] = first_branch_id

        buyer_group = self.env.ref('product_purchase.group_buyers')
        buyer_users = buyer_group.users
        if buyer_users:
            user_ids = [user.id for user in buyer_users]
            pending_vals['approve_users'] = [(6, 0, user_ids)]
            pendings = self.env['pending.actions'].create(pending_vals)
        print("pending",pendings)
        self.message_post(body=f"{self.env.user.name} Resubmitted the Contract to Contract Request {ctr.name}")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract Request',
            'view_mode': 'form',
            'res_model': 'tenders',
            'res_id':ctr.id,
            'target': 'current'
        }

        # self.message_post(body="Wait for Approvals")
        # pr_company_data = self.env['pr.company'].sudo().search([('company_id', 'in', self.company_ids.ids),
        #                                                         ('type', '=', 'renewal')],
        #                                                        limit=1)

        # print(pr_company_data)
        # counter = 0
        # if pr_company_data:
        #     line = []
        #     for approvers in pr_company_data.pr_approve_users_id:
        #         users_line = self.env['res.users.line'].sudo().search(
        #             [('company_id', '=', approvers.company_id.id), ('branch_id', '=', approvers.branch_id.id),
        #              ('department_id', '=', approvers.department_id.id),
        #              ('designation', '=', approvers.designation.id)])  # searching user in users line
        #         print(users_line, "PR USERSSSSSSSSSSSSS")
        #         if users_line:
        #             self.write({'to_approve_users': [(4, users_line.res_user_id.id)]})
        #             vals = {
        #                 'user_id': users_line.res_user_id.id,
        #                 'company_id': approvers.company_id.id,
        #                 'branch_id': approvers.branch_id.id,
        #                 'department_id': approvers.department_id.id,
        #                 'designation': approvers.designation.id,
        #                 'approve_order': approvers.approve_order,

        #             }
        #             print(vals)
        #             line.append({'user_id': users_line.res_user_id.id,
        #                          'approve_order': approvers.approve_order})

        #             self.approve_contract_line_ids |= self.env['product.tender.approve.line'].create(vals)
        #             self.env.cr.commit()
        #             model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        #             pending_vals = {
        #                 'model': model.id,
        #                 'name': self.name,
        #                 'record': self.id,
        #                 'date': date.today(),
        #             }
        #             if self.to_approve_users:
        #                 user_ids_to_pass = [(6, 0, self.to_approve_users.ids)]
        #                 pending_vals['approve_users'] = user_ids_to_pass

        #             pendings = self.env['pending.actions'].create(pending_vals)

        #             next_approver_user_ids = [next_approver.user_id.id for next_approver in self.approve_contract_line_ids if
        #                                       next_approver.approve_order == 1]
        #             print(next_approver_user_ids)
        #             if all(item is not False for item in next_approver_user_ids):
        #                 self.write({'next_approve_user': [(6, 0, next_approver_user_ids)]})
        #                 self.status = 'resubmit'
        #         else:
        #             raise ValidationError("Sorry no,user found on these criteria,Please contact Administrator.")
        # else:
        #     raise ValidationError(
        #         "Sorry,The criteria provided did not match any existing workflows,Please contact Administrator.")



    # @api.constrains('vendor', 'unit_price', 'product_template_id')
    # def _check_unique_vendor(self):
    #     for rec in self:
    #         if rec.vendor and rec.product_template_id:
    #             same_tendor = self.env['product.tender.line'].search(
    #                 [('vendor', '=', rec.vendor.id),
    #                  ('product_template_id', '=', rec.product_template_id.id)
    #                     , ('id', '!=', rec.id),
    #                  ('status','=','active')])
    #             if same_tendor:
    #                 raise ValidationError(_("Tender already exist for this vendor for this product"))

    @api.constrains('unit_price', 'product_template_id')
    def _check_unit_price(self):
        for rec in self:
            if rec.unit_price:
                same_tenders = self.env['product.tender.line'].sudo().search([
                    ('product_template_id', '=', rec.product_template_id.id),
                    ('unit_price', '<', rec.unit_price),('status','=','active')
                ])
                if same_tenders:
                    raise ValidationError(_("A tender already exists for this product with a lower price."))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.tender.line') or 'New'

        result = super(ProductTenderLine, self).create(vals)

        return result

    @api.onchange('quantity')
    def onchange_in_quantity(self):
        print("Inside quantity on change")
        if self.quantity:
            self.total = self.quantity * self.unit_price

    @api.onchange('unit_price')
    def onchange_in_unit_price(self):
        # print(self.request_check)
        print("Inside unit_price on change")
        if self.unit_price:
            self.total = self.quantity * self.unit_price


    def generate_po(self):
    # print("HAIIIIIIIIIIIIIIII")
        current_date = datetime.now().date()
        print(current_date)
        contracts = self.env['product.tender.line'].sudo().search([('recuring', '=', True),('status','=','active'),
                                                            ('start_date', '<=', current_date),
                                                            ('end_date', '>=', current_date)
                                                            ])
        order_line = []
        for contract in contracts:
            print(contract)
            products = self.env['product.product'].sudo().search([('product_tmpl_id', '=', contract.product_template_id.id)],limit=1)
            # print(products)
            for product in products:
                # print(product)
                order_line = [(0, 0, {
                    'display_type': False,
                    'name': contract.product_template_id.name,
                    'product_id': product.id,
                    'price_unit': contract.unit_price,
                    'product_qty': contract.quantity,
                    'product_uom': contract.product_template_id.uom_po_id.id,
                })]
                # print(order_line)
                purchase_order = self.env['purchase.order'].create({
                    'partner_id': contract.vendor.id,
                    'order_line': order_line,
                    'company_id': contract.company_id.id,
                    'is_readonly': True,
                    'location': contract.company_id.id,
                    'bill_to':  contract.company_id.id,
                    'ship_to':  contract.company_id.id,
                    'is_auto_po': True,
                })
                self.env.cr.commit()



class ContractsApprovalsLines(models.Model):
    _name = "product.tender.approve.line"
    _description = "Approver Tender Lines"

    contract_approve_ids = fields.Many2one('product.tender.line', string='Tender Approve',
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




class TerminateReason(models.TransientModel):
    _name = "contract.terminate.wizard"
    _description = "Terminate Contract"

    reason = fields.Char(string="Reason", store=True,required=True)

    contract_id = fields.Many2one(
        'product.tender.line', string='Purchase Order', readonly=True)
    cancel_date = fields.Date(string="Termination conducted date", default=lambda self: datetime.today().date() ,readonly=True)
    termination_date = fields.Date(string="Termination date")


    def terminate(self):
        print("dddd")
        for contract in self.contract_id:
            contract.message_post(
                body=(
                        "Contract Terminated due to "
                        + self.reason
                        + " on "
                        + str(self.cancel_date)
                        + ". Termination date: "
                        + str(self.termination_date)
                )
            )
            if contract.request_no:
                contract.request_no.message_post(
                    body=(
                            "Contract Terminated due to "
                            + self.reason
                            + " on "
                            + str(self.cancel_date)
                            + ". Termination date: "
                            + str(self.termination_date)
                    )
                )


                contract.request_no.state = "terminate"
                contract.request_no.termination_date = self.termination_date

            contract.status = "terminate"
            # contract.active_status = "terminate"
            contract.reason = self.reason
            contract.cancel_date = self.cancel_date






class ContractsProductsLines(models.Model):
    _name = "product.contracts.line"
    _description = "Products Contract Lines"

    products_line = fields.Many2one('product.tender.line', string='Products Line',
                                       invisible=True)
    product_group = fields.Char("Product Group")

    product_id = fields.Many2one('product.template', string='Product',required=True)
    uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_po_id')
    unit_price = fields.Float("Price")


class ContractsQuantityTerms(models.Model):
    _name = "quantity.terms"
    _description = "Value Terms"

    quantity_line = fields.Many2one('product.tender.line', string='Value Line',
                                       invisible=True)
    from_date = fields.Date(string='From Date', tracking=True)
    to_date = fields.Date(string='To Date', tracking=True)
    total_value = fields.Float("Total Value")


    @api.constrains('from_date')
    def _check_from_date(self):
        for record in self:
            if record.from_date and record.from_date < record.quantity_line.start_date:
                raise ValidationError("From date cannot be earlier than the start date.")

    @api.constrains('to_date')
    def _check_to_date(self):
        for record in self:
            if record.to_date and record.to_date > record.quantity_line.end_date:
                raise ValidationError("To date cannot be later than the end date.")



