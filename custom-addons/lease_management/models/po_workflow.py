from datetime import datetime
from datetime import date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo.exceptions import Warning


class PurchaseApprovals(models.Model):
    _inherit = "purchase.order"



    approvers_line_ids = fields.One2many('po.approve.line',
                                         'po_approve_id',
                                         string='Purchase Approve Line',
                                         tracking=True)
    is_confirmed = fields.Boolean("Is Confirmed")
    is_auto_po = fields.Boolean("Automated PO")
    is_an_approver = fields.Boolean("Approver",compute='compute_is_an_approver')

    po_rfi_ids = fields.One2many('po.rfi.line',
                                 'po_id',
                                 string='Purchase Order Line',
                                 tracking=True)
    po_remark_ids = fields.One2many('remark.po.save',
                                 'po_id',
                                 string='Purchase Order REmark',
                                 tracking=True)

    approve_users = fields.Many2many(
        'res.users',
        'rel_po_apprvers',
        'po_id',
        'po_user',
        string='Approve Users',
    )
    approved_users = fields.Many2many(
        'res.users',
        'approved_po_relation',
        'po_apprved',
        'po_user_id',
        string='Approved Users',
    )

    next_approve_user = fields.Many2many(
        'res.users',
        'next_aprved_po',
        'next_po',
        'po_users_id',
        string='Next Approver', )

    state = fields.Selection([
        ('draft', 'Draft/Approvals'),
        ('sent', 'Sent'),
        ('rfi','Request For Information'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('paid', 'PAID')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    in_budget = fields.Boolean("In Budget",compute="_compute_inbudget",readonly=False,default=True,store=True,force_save=True)
    user_approve_check = fields.Boolean(string="User Approve check", compute="_compute_total", default=False)
    deligated_user = fields.Many2one(
        'res.users', string='User Deligated', tracking=True, compute="_compute_user_id")
    user_init_check = fields.Boolean(string="User Initiator check", compute="_compute_init", default=False)
    product_bundle = fields.Html(string='Product Bundle',readonly=True,)

    ct_number = fields.Many2many(
        'product.tender.line',
        'purchase_tenders_rel',
        'purchase_id',
        'tender_id',
        string='Contract Request'
    )
    email_sent = fields.Boolean(string="Email Sent", default=False)

    utr_no = fields.Char(string='UTR Number')

    vendor_addresss = fields.Html(string="Vendor Address", store=True)
    vendor_change_name = fields.Text(string="Vendor Name", store=True)

    purchase_head = fields.Many2one('res.users', string='Purchase Head')
    is_purchase_head = fields.Boolean(string='Is Purchase Head', compute='_compute_purchase_head')
    assigned = fields.Boolean(string='Assign', default=False)
    assigned_to = fields.Many2many(
        'res.users',
        'assigned_user_purchase_rel',
        'tender_id',
        'user_id',
        string='Buyer'
    )
    closed = fields.Boolean(string="Closed", default=False)




    def action_close(self):
        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

        if pending_action:
            print(pending_action.name)
            pending_action.status = 'closed'

        self.message_post(body=f"{self.env.user.name} has closed the Purchase Order")

        activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Purchase Order')], limit=1)
        print("type is", self.env.user.id)

        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
        ])

        print("the activity is", activity)

        for act in activity:
            print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
            print("the activity is", act.id)
            act.action_feedback(feedback="Activity Declined")

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search([('name', '=', 'purchase')], limit=1)

        url_params = {
            'id': self.id,
            'action': self.env.ref('vendor_po.action_view_vendors_po').id,
            'model': 'purchase.order',
            'view_type': 'form',
            'menu_id': menu_id.id if menu_id else False,
        }

        params = '/web?#%s' % url_encode(url_params)
        url = base_url + params if base_url else "#"

        print(url)

        author = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')], limit=1)

        body = (
            f"Dear User, "
            f"The Purchase Order Request with the name <strong>{self.name}</strong> has been closed by <strong>{self.env.user.name}</strong>.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        subject = f"Purchase Order Request Has Been Closed: {self.name}"

        if self.pr_id.requested_by.email:
            mail_values = {
                'subject': 'Purchase Order Closed',
                'body_html': body,
                'email_to': self.pr_id.requested_by.email,
                'email_cc': 'cor.orders@popularv.com, %s' % self.partner_id.email if self.partner_id.email else 'cor.orders@popularv.com',
                'auto_delete': False,
                'author_id': author.id,
            }
            mail_record = self.env['mail.mail'].sudo().create(mail_values)
            mail_record.sudo().send()

        self.closed = True




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

    def assign_user(self):
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.view_assign_user_action')
        action['context'] = {'default_current_po': self.id
                             }
        print(action)
        return action

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Fetch and update the full vendor's address when the vendor changes."""
        for record in self:
            if record.partner_id:
                # Construct the full address
                record.vendor_change_name = record.partner_id.name or ""
                address_lines = "<br/>".join(filter(None, [
                    f"(Partner Code: {record.partner_id.ref or ''})",
                    f"GST No: {record.partner_id.vat or ''}",
                    f"{record.partner_id.street or ''}, {record.partner_id.street2 or ''}",
                    f"{record.partner_id.city or ''}, {record.partner_id.state_id.name or ''}, {record.partner_id.country_id.name or ''}" 
                    f"Pin: {record.partner_id.zip or ''}".strip(", "),
                    f"Phone: {record.partner_id.phone or ''}",
                    f"Email: {record.partner_id.email or ''}"
                ]))
                record.vendor_addresss = address_lines
            else:
                record.vendor_addresss = False


    def status_change(self):
        print("hi")
        self.state = 'purchase'

    @api.depends("user_init_check")
    def _compute_init(self):
        print('Inside user_init_check')
        for rec in self:
            if self.env.user == rec.contact:
                rec.user_init_check = True
            else:
                rec.user_init_check = False

    def po_close(self):
        model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])
        print("pending po",pending_action)
        if pending_action:
            for pending in pending_action:
                pending.status = 'closed'
        pending = self.env['pending.actions'].sudo().search(
            [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
        if pending:
            return pending.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
            return action
    def action_log_message_po(self):
        default_user_ids = self.approve_users.ids
        print(default_user_ids, "Usersssss")
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_log_message_po_action')
        action['context'] = {'default_purchase_id': self.id,
                             }
        print(action)
        return action
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
    def action_add_approver_admin(self):

        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')

        action['context'] = {'default_po_id': self.id,
                             'default_admin_add': True
                             }

        print(action)
        return action

    def action_add_approver(self):

        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.add_approver_action')

        action['context'] = {'default_po_id': self.id, }

        print(action)

        return action

    def action_deligate_po(self):
        print("deligate")
        for lines in self.approvers_line_ids:
            if lines.user_id.id == self.env.user.id:
                print("Founddd User")
                action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_po_deligate_user_action')
                action['context'] = {'default_po_id': self.id}
                return action

    
    def action_delegate_admin(self):
        print("i am in delegate")

        # user_ids = [user.id for user in self.next_approve_user_id]
        approve_users = set(self.approve_users.ids)
        approved_users = set(self.approved_users.ids)

        user_ids = list(approve_users - approved_users)
        print("the user id",user_ids)

        if not user_ids:
            return
        action = self.env["ir.actions.actions"]._for_xml_id('product_purchase.update_deligate_user_admin_action')
        action['context'] = {
            'default_po_id': self.id,
            'user_ids': user_ids,
            'type_id' : 'po'
        }
        return action

    def action_remark_approver(self):
        print("inside checking approval")
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.remark_po_approve_action')
        action['context'] = {'default_po_id': self.id,
                             'default_approve_type': 'approve',
                             }
        print(action)
        return action

    def action_remark_reject(self):
        self.ensure_one()
        if self.exp_category and self.exp_category.reject_not_possible:
            raise ValidationError(
                "Rejection is not possible for this Purchase Order as the linked expense category does not allow rejection."
            )
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.remark_po_approve_action')
        action['context'] = {'default_po_id': self.id,
                             'default_approve_type': 'cancel',
                             }
        print(action)
        return action

    def action_send_mail_vendor(self):
        self.email_sent = True
        return {
            'name': 'Send Mail to Vendor',
            'type': 'ir.actions.act_window',
            'res_model': 'send.mail.vendor.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',  # Open in a new modal
            'context': {
                'default_vendor_id': self.partner_id.id,  # Pass vendor id
                'default_purchase_order_id':self.id,
                'default_email_template_id': self.env.ref('lease_management.email_template_id').id,  # Replace with your template
            }
        }

    @api.depends('pr_budget_id', 'amount_total')
    def _compute_inbudget(self):
        for rec in self:
            if rec.pr_budget_id and rec.amount_total:
                if rec.pr_budget_id.amount_available < 0:
                    rec.in_budget = False
            else:
                rec.in_budget = True

    @api.depends('next_approve_user')
    def compute_is_an_approver(self):
        for rec in self:
            rec.is_an_approver = self.env.user.id in rec.next_approve_user.mapped('id')

    def action_purchase_list(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract Requests',
            'view_mode': 'tree,form',
            'res_model': 'product.request',
            'domain': [('id', '=', self.pr_id.id)],

            'target': 'current'
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

    def button_confirm(self):

        print("helllooo worldddd")
        print(self.is_confirmed)
        print(self.is_auto_po)

        if self.is_auto_po == False:
            if self.is_confirmed != True:

                # if self.pr_budget_id:
                #     self.pr_budget_id.amount_used += self.amount_total
                #     self._compute_inbudget()
                pr_company_data = None
                # if self.amount_untaxed > 10500:
                #     if self.exp_category.name not in ['Paint & Consumables',
                #                                       'Lubricant'] or self.amount_untaxed >= 10500:
                if self.l10n_in_gst_treatment == 'unregistered':
                    print("GST treatment is 'Unregistered Business'")
                    for line in self.order_line:
                        # Clear all taxes for the product line
                        line.write({
                            'taxes_id': [(5, 0, 0)]  # This will remove all taxes from the order line
                        })
                if self.exp_category.name not in ['Paint & Consumables', 'Lubricant','Tyre/Battery Purchase Agreement']:
                    pr_company_data = self.env['pr.company'].sudo().search([
                        ('company_id', '=', self.company_id.id),
                        # ('company_id', '=', self.env.company.id),
                        # ('branch_id','=',self.branch_id.id),
                        # ('department_id', '=',self.department_id.id),
                        ('expense_type', '=',self.expense_type),
                        #('exp_category', '=',self.exp_category.id),
                        ('from_amount', '<=', self.amount_total),
                        ('to_amount', '>=', self.amount_total),
                        ('type','=','purchase')],
                        limit=1)
                    print(pr_company_data.name)
                if pr_company_data:
                    vendor_user = self.env['res.users'].sudo().search([('partner_id', '=', self.partner_id.id)], limit=1)
                    if vendor_user:
                        print("the login id is", vendor_user)

                        new_line_vals = {
                            'user_id': vendor_user.id,
                            'approve_order': 1,
                            'department_id': False,
                            'company_id': False,
                        }
                        print("the new vals", new_line_vals)

                        self.approvers_line_ids |= self.env['po.approve.line'].create(new_line_vals)
                        print("approval line", self.approvers_line_ids)
                        self.approve_users += vendor_user

                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
                        pending_vals = {
                            'model': model.id,
                            'name': self.name,
                            'record': self.id,
                            'branch': self.ship_to.id,
                            'date': date.today(),
                            'department_id': self.department_id.id,
                            'exp_category': self.exp_category.id,
                            'Created_doc_date': self.date,
                            'approve_users': [(4, vendor_user.id)],
                            'user': 'vendor',
                        }
                        pendings = self.env['pending.actions'].create(pending_vals)
                        print("the pending",pendings)
                        
                        approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                        pendings.write({'email': approve_users_emails})

                        activity_type = self.env['mail.activity.type'].sudo().search(
                            [('name', '=', 'Pending Purchase Order')],
                            limit=1)
                        activity_type_id = activity_type.id if activity_type else False
                        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id

                        activity_values = {
                                'user_id': vendor_user.id,
                                'res_id': self.id,
                                'note': "Pending Action",
                                'activity_type_id': activity_type_id,
                                'res_model_id': res_model_id,
                            }
                        with self.env.cr.savepoint():
                            self = self.with_context(mail_activity_quick_update=True)
                            created_activity = self.env['mail.activity'].create(activity_values)

                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        menu_id = self.env['ir.ui.menu'].sudo().search(
                            [('name', '=', 'Purchase')], limit=1) or False

                        url_params = {
                            'id': self.id,
                            'action': self.env.ref('vendor_po.action_view_vendors_po').id,
                            'model': 'purchase.order',
                            'view_type': 'form',
                            'menu_id': menu_id.id if menu_id else False,
                            'function': 'action_approval',
                        }

                        params = '/web?#%s' % url_encode(url_params)
                        approval_url = base_url + params if base_url else "#"

                        print("appppppppppppppppppppppppppppprovalllllllllllllll", approval_url)

                        # body = f"Dear User,A Purchase Order {self.name} has been initiated."
                        author = self.env['res.partner'].sudo().search(
                            [('name', '=', 'Administrator')], limit=1) or False

                        body = (
                            f"Dear Vendor,A Purchase Order {self.name} has been raised and waiting for your acknowledgement.<br><br>"
                            f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                            # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                            # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                            # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                            # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                            # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"

                        )

                        if self.partner_id.email:
                            mail_values = {
                                'subject': 'PO Waiting for acknowledgment',
                                'body_html': body,
                                'email_to': self.partner_id.login,
                                'auto_delete': False,
                                'author_id': author.id
                            }
                            mail_record = self.env['mail.mail'].sudo().create(mail_values)


                    self.message_post(body="Wait for PO Approval")
                    for approvers in pr_company_data.pr_approve_users_id:
                        print("the approvers are", approvers)
                        for details in approvers:
                            line = []
                            last_approve_order = None
                            corresponding_approval_flow = self.env['res.users.line'].sudo().search([
                                ('company_id', '=', details.company_id.id),
                                ('branch_id', '=', details.branch_id.id),
                                ('department_id', '=', details.department_id.id),
                                ('designation', '=', details.designation.id)
                            ])
                            print("cores appro", corresponding_approval_flow)
                            if not corresponding_approval_flow.res_user_id:
                                raise ValidationError("No corresponding approval flow found for details: %s" % details)
                            print("corresponding approval flows:", corresponding_approval_flow.res_user_id.id)
                            self.approve_users |= corresponding_approval_flow.mapped('res_user_id')
                            print("the approval users are", self.approve_users.ids)
                            if vendor_user:
                                print("inside approve users", vendor_user.id)
                                approve_order = int(details.approve_order) + 1
                                print("the approve order is", approve_order)
                            else:
                                print("the users of order", details.approve_order)
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
                            print("the line is", line)
                            if last_approve_order is None or details.approve_order > last_approve_order:
                                last_approve_order = details.approve_order
                            print("last", last_approve_order)
                            self.approvers_line_ids = line
                            print("last approve line", self.approvers_line_ids)
                            print("the approve users ids are", self.approve_users.ids)



                    next_approver_user_ids = [
                        next_approver.user_id.id
                        for next_approver in self.approvers_line_ids
                        if (
                                (vendor_user and next_approver.approve_order == 1)
                                or (not vendor_user and next_approver.approve_order == 1)  ) ]

                    if not vendor_user:
                        subject = "New Purchase Order Request Raised: %s" % self.name
                        print("Name", self.name)
                        body = ("Dear User, "
                                "A new Purchase Order Request with the name %s has been raised against an Purchase Request by" % (
                                    self.name))

                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        menu_id = self.env['ir.ui.menu'].sudo().search(
                            [('name', '=', 'Purchase')], limit=1) or False

                        url_params = {
                            'id': self.id,
                            'action': self.env.ref('pending_actions.action_pending_actions').id,
                            'model': 'purchase.order',
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
                            f"A new Purchase Order Request with the name <strong>{self.name}</strong> has been raised against Invoice Request by <strong></strong>.<br>"
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

                        for user_id in next_approver_user_ids:
                            print("i am just entering the pending action")
                            print("the user is", user_id)
                            model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                       limit=1)
                            pending_vals = {
                                'model': model.id,
                                'name': self.name + " " + "Purchase Order Request Waiting For Approval",
                                'record': self.id,
                                'branch': self.ship_to.id,
                                'department_id': self.department_id.id,
                                'exp_category': self.exp_category.id,
                                'Created_doc_date': self.date,
                                'date': date.today(),
                            }
                            print("the pending vals", pending_vals)
                            if user_id:
                                print("the user is there")
                                user_ids_to_pass = [user_id]
                                print("the user ids", user_ids_to_pass)
                                pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                pendings = self.env['pending.actions'].create(pending_vals)
                                print("the pending is", pendings)
                                approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                pendings.write({'email': approve_users_emails})

                                activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Purchase Order')], limit=1)
                                print("the activity type", activity_type)
                                activity_type_id = activity_type.id if activity_type else False
                                res_model_id = self.env['ir.model'].sudo().search(
                                    [('model', '=', 'purchase.order')]).id

                                activity_values = {
                                    'user_id': user_id,
                                    'res_id': self.id,
                                    'note': "Pending Action",
                                    'activity_type_id': activity_type_id,
                                    'res_model_id': res_model_id,
                                }
                                with self.env.cr.savepoint():
                                    self = self.with_context(mail_activity_quick_update=True)
                                    created_activity = self.env['mail.activity'].create(activity_values)
                                print("the created activity", created_activity)
                                user = self.env['res.users'].sudo().search([('id', '=', self.user_id.id)], limit=1)
                                print("the user is check create", user)

                            if user:
                                subject = "Purchase Order Request Waiting For APPROVAL: %s" % self.name
                                mail_values = {
                                    'subject': subject,
                                    'body_html': body,
                                    'email_to': user.login,
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                # mail_record.send()

                    print(next_approver_user_ids, "This print")
                    if all(item is not False for item in next_approver_user_ids):
                        self.write({'next_approve_user': [(6, 0, next_approver_user_ids)]})
                        self.is_confirmed = True
                    else:
                        res = super(PurchaseApprovals, self).button_confirm()
                        return res

                    print("name is", self._name)

                    user_name = self.env.user.name if self.env.user else ''
                    # message_body = f"Lease Request is Generated By the buyer. Buyer: {user_name}"
                    # self.message_post(body=message_body)

                else:
                    res = super(PurchaseApprovals, self).button_confirm()
                    return res
            else:
                res = super(PurchaseApprovals, self).button_confirm()
                return res
        else:
            if self.pr_budget_id:
                self.pr_budget_id.amount_used -= self.amount_untaxed
            res = super(PurchaseApprovals, self).button_confirm()
            return res

    def action_approval(self):

        self.message_post(body=self.env.user.name + " " + "Approved The Purchase Order")
        print("approvee")
        print("Hellooo users")
        print(self.env.user.id)
        self.write({'approved_users': [(4, self.env.user.id)]})
        self.is_an_approver = False
        self.write({'next_approve_user': [(3, self.env.user.id)]})
        approver = self.env['po.approve.line'].sudo().search(
            [('po_approve_id', '=', self.id), ('user_id', '=', self.env.user.id)])
        for record in approver:
            record.write({'status': 'approve'})
        if self.approved_users == self.approve_users:

            self.is_confirmed = True
            # self.state = 'approved'
            # print("the state is", self.state)

            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

            if pending_action:
                pending_action.status = 'closed'

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Purchase Order')],
                                                                  limit=1)
            print("the activity type is", activity_type)
            print("type is", self.env.user.id)
            print("the self id is", self.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ])
            if activity:
                for rec in activity:
                    print(activity.id)
                    activity.action_feedback(feedback="Activity completed")
            self.message_post(body="The Purchase Order has been approved by everyone")

            if self.pr_id:
                model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                           limit=1)
                pending_vals = {
                    'model': model.id,
                    'name': self.name + " " + "Recieve Products of PO",
                    'record': self.id,
                    'branch': self.ship_to.id,
                    'department_id': self.department_id.id,
                    'exp_category': self.exp_category.id,
                    'Created_doc_date': self.date,
                    'date': date.today(),
                }
                print("the pending vals", pending_vals)
                if self.pr_id.requested_by:
                    print("the user is there")
                    user_ids_to_pass = self.pr_id.requested_by.id
                    print("the user ids", user_ids_to_pass)
                    pending_vals['approve_users'] = [(4,user_ids_to_pass)]
                    pendings = self.env['pending.actions'].create(pending_vals)
                    print("the pending is", pendings)
                    approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                    pendings.write({'email': approve_users_emails})
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Purchase')], limit=1) or False

                    url_params = {
                        'id': self.id,
                        'action': self.env.ref('vendor_po.action_view_vendors_po').id,
                        'model': 'purchase.order',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                        'function': 'action_approval',
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    approval_url = base_url + params if base_url else "#"

                    print("appppppppppppppppppppppppppppprovalllllllllllllll", approval_url)

                    # body = f"Dear User,A Purchase Order {self.name} has been initiated."
                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1) or False

                    body = (
                        f"A Purchase Order {self.name} has been Approve and waiting for Recieving Product.<br><br>"
                        f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                        # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                        # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                        # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                        # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                        # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"

                    )

                    if self.pr_id.requested_by.email:
                        mail_values = {
                            'subject': 'PO Waiting for Product acknowledgment',
                            'body_html': body,
                            'email_to': self.pr_id.requested_by.email,
                            'email_cc': ['cor.orders@popularv.com', self.partner_id.login],
                            'auto_delete': False,
                            'author_id': author.id
                        }
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)

            self.button_confirm()

        else:

            model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

            for rec in pending_action:
                if self.env.user in rec.approve_users:

                    rec.status = 'closed'

            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Purchase Order')], limit=1)

            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
                ('user_id', '=', self.env.user.id), ('res_name', '=', self.name),
                ('activity_type_id', '=', activity_type.id),
            ])

            if activity:
                for rec in activity:

                    rec.action_feedback(feedback="Activity completed")

            approve_users = self.env['po.approve.line'].sudo().search(
                [('po_approve_id', '=', self.id)], order='approve_order asc')


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

                                    subject = "New Purchase Order Request Raised: %s" % self.name
                                    print("Name", self.name)
                                    body = ("Dear User, "
                                            "A new Purchase Order Request with the name %s has been raised against an Purchase Request by" % (
                                                self.name))

                                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    menu_id = self.env['ir.ui.menu'].sudo().search(
                                        [('name', '=', 'Purchase')], limit=1) or False

                                    url_params = {
                                        'id': self.id,
                                        'action': self.env.ref('vendor_po.action_view_vendors_po').id,
                                        'model': 'purchase.order',
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
                                        f"A new Purchase Order Request with the name <strong>{self.name}</strong> has been raised. <strong></strong>.<br>"
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
                                        print("the user is", user)
                                        model = self.env['ir.model'].sudo().search([('model', '=', self._name)],
                                                                                   limit=1)
                                        pending_vals = {
                                            'model': model.id,
                                            'name': self.name + " " + "Purchase Order Request Waiting For Approval",
                                            'record': self.id,
                                            'branch': self.ship_to.id,
                                            'department_id': self.department_id.id,
                                            'exp_category': self.exp_category.id,
                                            'Created_doc_date': self.date,
                                            'date': date.today(),
                                        }
                                        print("the pending vals", pending_vals)
                                        if user:
                                            print("the user is there")
                                            user_ids_to_pass = user.ids
                                            print("the user ids", user_ids_to_pass)
                                            pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                            pendings = self.env['pending.actions'].create(pending_vals)
                                            print("the pending is", pendings)
                                            approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                                            pendings.write({'email': approve_users_emails})

                                            activity_type = self.env['mail.activity.type'].sudo().search(
                                                [('name', '=', 'Pending Purchase Order')], limit=1)
                                            print("the activity type", activity_type)
                                            activity_type_id = activity_type.id if activity_type else False
                                            res_model_id = self.env['ir.model'].sudo().search(
                                                [('model', '=', 'purchase.order')]).id
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
                                                with self.env.cr.savepoint():
                                                    self = self.with_context(mail_activity_quick_update=True)
                                                    created_activity = self.env['mail.activity'].create(activity_values)
                                                print("the created activity", created_activity)

                                        if user.login:
                                            subject = "Purchase Order Request Waiting For APPROVAL: %s" % self.name
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
                                                        'branch': self.ship_to.id,
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

                                                print(self.next_approve_user_id)
                                    except:
                                        print("pass")
                                        pass
                                    if flag:
                                        break



    def action_rejected(self):
        print("helloo rejected")
        self.state = 'cancel'

        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

        for rec in pending_action:
            print(rec.name)
            rec.status = 'closed'
        self.message_post(body=f"{self.env.user.name} Rejected the Purchase Order Request.")

        activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Purchase Order')], limit=1)
        print("type is", self.env.user.id)
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
        ])
        print("the activity is", activity)
        if activity:
            for act in activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(act.id)
                act.action_feedback(feedback="Activity Declined")
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'purchase')], limit=1) or False

        url_params = {
            'id': self.id,
            'action': self.env.ref('vendor_po.action_view_vendors_po').id,
            'model': 'purchase.order',
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
            f"The Purchase Order Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        subject = "Purchase Order Request Has Been Rejected: %s" % self.name


        purchase_request = self.env['product.request'].search([('id', '=', self.pr_id.id)], limit=1)
        lease_request = self.env['product.lease'].search([('id', '=', self.lease_id.id)], limit=1)

        pur_id = None
        lease_initiator = None
        if purchase_request:
            pur_id = purchase_request.requested_by.id
            print("pr id is", pur_id)
            purchase_request.status = 'declined'
            purchase_request.message_post(
                body=f"{self.env.user.name} Rejected the Purchase Order Request So the purchase Request is Rejected.")
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': purchase_request.requested_by.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)

        if lease_request:
            print("lease request is there",lease_request)
            lease_initiator = lease_request.user_id.id
            lease_request.state='reject'
            lease_request.message_post(body=f"{self.env.user.name} Rejected the Purchase Order Request So the Lease Order is Rejected.")
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': lease_request.user_id.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)



        for approvers in self.approvers_line_ids:
            if approvers.user_id.id == self.env.user.id:
                approvers.write({'status': 'cancel'})

            if approvers.status == 'approve':
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

        self.write({
            'state': 'cancel',
            'is_confirmed': False,
            'approvers_line_ids': [(5, 0, 0)],
            'approve_users': [(5, 0, 0)],
            'approved_users': [(5, 0, 0)],
            'next_approve_user': [(5, 0, 0)],
        })

    def button_cancel(self):
        res = super(PurchaseApprovals, self).button_cancel()
        print("helloo rejected")
        self.state = 'cancel'

        model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')], limit=1)

        if pending_action:
            print(pending_action.name)
            pending_action.status = 'closed'
        self.message_post(body=f"{self.env.user.name} Rejected the Purchase Order Request.")

        activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Purchase Order')], limit=1)
        print("type is", self.env.user.id)

        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
        ])

        print("the activity is", activity)

        for act in activity:
            print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
            print("the activity is", act.id)
            act.action_feedback(feedback="Activity Declined")
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'purchase')], limit=1) or False

        url_params = {
            'id': self.id,
            'action': self.env.ref('vendor_po.action_view_vendors_po').id,
            'model': 'purchase.order',
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
            f"The Purchase Order Request with the name <strong>{self.name}</strong> has been rejected by <strong>{self.env.user.name}</strong>.<br>"
            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
            f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
            f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
        )
        subject = "Purchase Order Request Has Been Rejected: %s" % self.name

        purchase_request = self.env['product.request'].search([('id', '=', self.pr_id.id)], limit=1)
        lease_request = self.env['product.lease'].search([('id', '=', self.lease_id.id)], limit=1)

        pur_id = None
        lease_initiator = None
        if purchase_request:
            pur_id = purchase_request.requested_by.id
            print("pr id is", pur_id)

        if lease_request:
            print("lease request is there", lease_request)
            lease_initiator = lease_request.user_id.id
            lease_request.state = 'reject'
            lease_request.message_post(
                body=f"{self.env.user.name} Rejected the Purchase Order Request So the Lease Order is Rejected.")

        if pur_id:
            print("req", self.user_id)
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': purchase_request.requested_by.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)
        if lease_initiator:
            print("req", self.user_id)
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': lease_request.user_id.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)

        for approvers in self.approvers_line_ids:
            if approvers.user_id.id == self.env.user.id:
                approvers.write({'status': 'cancel'})

            if approvers.status == 'approve':
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

        self.write({
            'state': 'cancel',
            'is_confirmed': False,
            'approvers_line_ids': [(5, 0, 0)],
            'approve_users': [(5, 0, 0)],
            'approved_users': [(5, 0, 0)],
            'next_approve_user': [(5, 0, 0)],
        })

        return res


class PoApproveLines(models.Model):
    _name = "po.approve.line"
    _description = "PO Approvers Lines"

    po_approve_id = fields.Many2one('purchase.order', string='PO Approve',
                                    invisible=True)

    user_id = fields.Many2one('res.users', string="User")
    company_id = fields.Many2one('res.company', string="Company")
    branch_id = fields.Many2one('res.branch', string="Branch")
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

class LogMessage(models.TransientModel):
    _name = "log.message.wizard.po"
    _description = "Log"

    purchase_id = fields.Many2one(
        'purchase.order', string='Purchase Order', readonly=True)
    message = fields.Text("Message")
    user = fields.Many2one('res.users', "Requested By", default=lambda self: self.env.user.id)
    # user_ids = fields.Many2many('res.users', "To")
    to_users = fields.Many2one('res.users', "Requested To",domain="[('groups_id', 'not in', [44])]", required=True)
    branch_id = fields.Many2one('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')
    email = fields.Char(string='Email')

    @api.onchange('to_users')
    def _compute_branch_id(self):
        for rec in self:
            rec.branch_id = rec.to_users.branch_id.id
            rec.email = rec.to_users.login
    @api.onchange('user_ids')
    def set_domain_for_user(self):
        print(self.user_ids)
        print(type(self.user_ids))
        print(list(self.user_ids))



    def confirm(self):
        print("helloo")
        for rec in  self.purchase_id.po_rfi_ids:
            if not rec.replay:
                raise UserError(_("Already Request for Information Pending for Reply"))

        print("helloo")
        model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)

        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.purchase_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_action_ids)

        for pending_action in pending_action_ids:
            # pending_action.status = 'closed'
            new_name = f"{self.purchase_id.name} waiting for RFI reply"
            pending_action.sudo().write({'name': new_name})
        for request in self.purchase_id:
            if self.user and self.message:
                body = (
                    f"{self.env.user.name} has logged a message in {self.purchase_id.name}.{self.message}"
                )
                vals = {
                    'subject': f"Logged a message in {self.purchase_id.name}",
                    'body_html': body,
                    'email_to': self.to_users.login,
                }
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()

                self.purchase_id.message_post(body=f"<strong>@{self.user.name}</strong>, {self.message}")

                rfi_vals = {
                    'user_id': self.env.user.id,
                    'to_user': self.to_users.id,
                    'message': self.message,
                    # 'user_id':self.env.user.id,
                    'next_pending_ids': [(6, 0, pending_action_ids.ids)] if pending_action_ids else False
                }

                new_rfi_vals = self.env['po.rfi.line'].create(rfi_vals)
                self.purchase_id.po_rfi_ids |= new_rfi_vals

                model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                pending_vals = {
                    'model': model.id,
                    'name': "Request For Information" + " " + "on" + " " + self.purchase_id.name,
                    'record': self.purchase_id.id,
                    'branch': self.purchase_id.ship_to.id,
                    'date': date.today(),
                    'record_line': new_rfi_vals.id,
                    'department_id': self.purchase_id.department_id.id,
                    'exp_category': self.purchase_id.exp_category.id,
                    'Created_doc_date': self.purchase_id.date,
                    'approve_users': [(6, 0, self.to_users.ids)],
                }
                pendings = self.env['pending.actions'].create(pending_vals)
                approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                pendings.write({'email': approve_users_emails})
                request.state = 'rfi'
        pending_ids = self.env['pending.actions'].sudo().search(
            [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
        if pending_ids:
            return pending_ids.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
            return action

class PrRfiLine(models.Model):
    _name = "po.rfi.line"
    _description = "RFI Line"

    po_id = fields.Many2one('purchase.order', string='Purchase Order Id',
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
        relation='last_pend_po',
        column1='po_rfi_lease_id',
        column2='pending_actions_id',
        store=True
    )

    @api.depends('to_user')
    def _get_current_user_details(self):
        current_user_id = self.env.user.id
        for record in self:
            if record.to_user and record.to_user.id == current_user_id:
                record.is_to_user_id = True
            else:
                record.is_to_user_id = False

    def send_replay(self):
        action = self.env["ir.actions.actions"]._for_xml_id('lease_management.update_log_replay_po_action')
        action['context'] = {'default_message_id': self.id}
        return action


class LogMessageReplay(models.TransientModel):
    _name = "message.replay.wizard.po"
    _description = "Log"

    message_id = fields.Many2one(
        'po.rfi.line', string='Reply', readonly=True)
    replay = fields.Text("Message", required=True)

    def confirm(self):
        print("jjjgygsd")
        # for pending_action in self.message_id.next_pending_ids:
        #     # Create a copy of the pending action record
        #     print("Reply next pending",pending_action)
        #     new_action = pending_action.copy()
        #     print("new action",new_action)
        #     new_action.sudo().write({
        #         'date':date.today(),
        #         'status': 'open',
        #         'name': "Replay for RFI" + " " + "for" + " " + self.message_id.po_id.name,
        #     })
        model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
        pending_action_ids = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record', '=', self.message_id.po_id.id), ('status', '=', 'open')])
        print("the pending actions are", pending_action_ids)

        for pending_action in pending_action_ids:
            # pending_action.status = 'closed'
            new_name = f"{self.message_id.po_id.name} --Replied for RFI "
            pending_action.sudo().write({'name': new_name})

        for line in self.message_id:
            line.replay = self.replay
            line.replayed = True
            line.status = 'close'
        self.message_id.po_id.message_post(
            body=f"<strong>@{self.env.user.name}</strong>,Replied: {self.replay}, to {self.message_id.user_id.name}")

        model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
        print(model.id)
        print(self.message_id.id)
        pending_action = self.env['pending.actions'].sudo().search(
            [('model', '=', model.id), ('record_line', '=', self.message_id.id)], limit=1)

        print(pending_action)
        if pending_action:
            pending_action.status = 'closed'
        all_record_lines_replayed = all(line.replay for line in self.message_id.po_id.po_rfi_ids)

        if all_record_lines_replayed:
            # If all record lines have their 'replay' column filled, change the status to 'requested'
            self.message_id.po_id.state = 'draft'
        pending = self.env['pending.actions'].sudo().search(
            [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
        if pending:
            return pending.open_record()
        else:
            action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
            return action





class RemarkPO(models.TransientModel):
    _name = "po.remark"
    _description = "PO Remark"
    _inherit = ['mail.thread']

    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Char("Remark", required=True)
    po_id = fields.Many2one('purchase.order', string='PO', readonly=True)
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('cancel', 'Rejected')],
        string='State')



    def confirm_remark(self):

        if self.po_id and self.approve_type == 'approve':
            print("i am inside the confirm")
            # self.lease_id.message_post(body=f" {self.env.user.name} Approved.")
            self.po_id.message_post(body="Remarks " + self.replay)
            vals = {
                'po_id': self.po_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "PO Request",
                'approve_type': 'approve',

            }
            remarks_save = self.env['remark.po.save'].create(vals)
            self.po_id.action_approval()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action
        if self.po_id and self.approve_type == 'cancel':
            # self.lease_id.message_post(body=f" {self.env.user.name} Rejected.")
            self.po_id.message_post(body="Remarks " + self.replay)
            vals = {
                'po_id': self.po_id.id,
                'from_user': self.env.user.id,
                'replay': self.replay,
                'for_type': "PO Request",
                'approve_type': 'cancel',

            }
            remarks_save = self.env['remark.po.save'].create(vals)
            self.po_id.action_rejected()
            pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
            if pending:
                return pending.open_record()
            else:
                action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                return action

class RemarkSave(models.Model):
    _name = "remark.po.save"
    _description = "Remark"

    po_id = fields.Many2one('purchase.order', string='Purchase', readonly=True)
    from_user = fields.Many2one('res.users', string="Approval by")
    replay = fields.Char("Remark", required=True)
    for_type = fields.Char("Approval Type")
    approve_type = fields.Selection(
        selection=[('approve', 'Approved'), ('cancel', 'Rejected'),('deligate','Delegate')],
        string='State')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    price_unit = fields.Float(readonly=True)

    @api.onchange('product_qty')
    def _onchange_quantity(self):
        if self.product_id:
            current_price = self.price_unit
            super(PurchaseOrderLine, self)._onchange_quantity()
            self.price_unit = current_price


