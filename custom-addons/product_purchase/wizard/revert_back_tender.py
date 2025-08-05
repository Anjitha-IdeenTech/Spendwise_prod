

from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError, MissingError, UserError
from werkzeug.urls import url_encode
from datetime import date

class RevertBAckWizard(models.TransientModel):
    _name = 'revert.back.tender.wizard'
    _description = "Revert Back"

    tender_id = fields.Many2one(
        'tenders', string='tender', readonly=True)
    reason = fields.Text("Message")
    revert_from = fields.Many2one(
        'res.users', string='Revert User')
    initiator = fields.Many2one(
        'res.users', string='Initiator User')

    all_multi_is_revert = fields.Boolean(
        string="All Multi RFQ Is Revert",
        help="Revert all tenders associated with the main RFQ if checked. Otherwise, revert only this tender.")
    contracting_method = fields.Char(
        string="Contracting Method",
        compute="_compute_contracting_method",
        store=False)

    @api.depends('tender_id')
    def _compute_contracting_method(self):
        for record in self:
            # Assign contracting method only if tender_id exists
            record.contracting_method = record.tender_id.contracting_method if record.tender_id else ''



    def action_confirm(self):
        if self.tender_id.contracting_method == 'nego':
            if self.reason:
                rec = self.env['revert.contract.back'].create({
                    'tender_id': self.tender_id.id,
                    'reason': self.reason,
                    'revert_from': self.revert_from.id,
                })
                print("Revert",rec)
                self.tender_id.state = 'draft'
                self.tender_id.write({
                    'approved_users': [(5, 0, 0)],
                    'approve_users': [(5, 0, 0)],
                    'next_approve_user_id': [(5, 0, 0)],

                })

                self.tender_id.tender_approve_line = [(5, 0, 0)]
                model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.tender_id.id), ('status', '=', 'open')])

                print("pending",pending_action)

                if pending_action:
                    for rec in pending_action:
                        print(rec.name)
                        rec.sudo().status = 'closed'

                activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')], limit=1)

                activity = self.env['mail.activity'].sudo().search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                    ('res_name', '=', self.tender_id.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                print("activity",activity)
                if activity:
                    for act in activity:
                        act.action_feedback(feedback="Activity Declined")

                # if self.tender_id.budget_details:
                #     self.tender_id.budget_details.amount_used -= self.tender_id.total_price
                self.tender_id.sudo().message_post(body=f" {self.env.user.name} Reverted back to Buyer's.")
                # buyer_group = self.env.ref(
                #     'product_purchase.group_buyers').sudo()
                # buyer_users = buyer_group.users
                if self.tender_id.assigned_to:
                    user_ids = [self.tender_id.assigned_to.id]
                else:
                    buyer_group = self.env.ref('product_purchase.group_buyers').sudo()
                    buyer_users = buyer_group.users
                    user_ids = [user.id for user in buyer_users]
                if user_ids:

                    model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                    pending_vals = {
                        'model': model.id,
                        'name': self.tender_id.name + " " + "Contract Request Reverted",
                        'record': self.tender_id.id,
                        'branch': self.tender_id.branch_ids.ids[0] if self.tender_id.branch_ids else None,
                        'date': date.today(),
                    }

                    # user_ids = [user.id for user in buyer_users]
                    pending_vals['approve_users'] = [(6, 0, user_ids)]
                    pendings = self.env['pending.actions'].sudo().create(pending_vals)


                    subject = "Contract Request Reverted Back : %s" % self.tender_id.name
                    print("subject",subject)

                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Contracts')], limit=1) or False
                    print("Menu ",menu_id)
                    url_params = {
                        'id': self.tender_id.id,
                        'action': self.env.ref('product_purchase.action_tender_status').id,
                        'model': 'tenders',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    print("URL",url)

                    email_to_list = [
                        user.email or user.login
                        for user in self.env['res.users'].sudo().browse(user_ids)
                        if user.email or user.login
                    ]

                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)

                    body = (
                        f"Dear User, "
                        f"A Contract has Reverted back with the name <strong>{self.tender_id.name} .<br>"
                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                    )
                    if self.initiator:

                        mail_values = {
                            'subject': subject,
                            'body_html': body,
                            'email_to': ','.join(email_to_list),
                            'auto_delete': False,
                            'author_id': author.id
                        }
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)


                pending = self.env['pending.actions'].sudo().search(
                [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
                print("return",pending)
                if pending:
                    print("if ",pending)
                    return pending.open_record()
                else:
                    print("else")
                    action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                    return action

            else:
                raise ValidationError(_("Reason Cannot be empty"))

        if self.tender_id.contracting_method == 'multi':
            if self.all_multi_is_revert:
                if self.tender_id.main_rfq.id:
                    branchs = self.env['tenders'].sudo().search([
                        ('main_rfq', '=', self.tender_id.main_rfq.id),
                    ])
                    print("the branch is",branchs)
                    if self.reason:
                        for branch in branchs:
                            rec = self.env['revert.contract.back'].create({
                                'tender_id': branch.id,
                                'reason': self.reason,
                                'revert_from': self.revert_from.id,
                            })
                            branch.state = 'rfq'
                            branch.write({
                                'approved_users': [(5, 0, 0)],
                                'approve_users': [(5, 0, 0)],
                                'next_approve_user_id': [(5, 0, 0)],

                            })
                            branch.tender_approve_line = [(5, 0, 0)]
                            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                            pending_action = self.env['pending.actions'].sudo().search(
                                [('model', '=', model.id), ('record', '=', branch.id), ('status', '=', 'open')])

                            print("pending", pending_action)

                            if pending_action:
                                for rec in pending_action:
                                    print(rec.name)
                                    rec.sudo().status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')],
                                                                                         limit=1)

                            activity = self.env['mail.activity'].sudo().search([
                                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                                ('res_name', '=', branch.name),
                                ('activity_type_id', '=', activity_type.id),
                            ])
                            print("activity", activity)
                            if activity:
                                for act in activity:
                                    act.action_feedback(feedback="Activity Declined")
                            branch.sudo().message_post(body=f" {self.env.user.name} Reverted back to Buyer's.")

                        if self.tender_id.assigned_to:
                            user_ids = [self.tender_id.assigned_to.id]
                        else:
                            buyer_group = self.env.ref('product_purchase.group_buyers').sudo()
                            buyer_users = buyer_group.users
                            user_ids = [user.id for user in buyer_users]
                        if user_ids:
                            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                            branch_names = ', '.join(branch.name for branch in branchs)
                            pending_vals = {
                                'model': model.id,
                                'name': f"{self.tender_id.name} Contract Request Reverted And The Multi RFQ's Are {branch_names}",
                                'record': self.tender_id.id,
                                'branch': self.tender_id.branch_ids.ids[0] if self.tender_id.branch_ids else None,
                                'date': date.today(),
                            }

                            # user_ids = [user.id for user in buyer_users]
                            pending_vals['approve_users'] = [(6, 0, user_ids)]
                            pendings = self.env['pending.actions'].sudo().create(pending_vals)

                            subject = "Contract Request Reverted Back : %s" % self.tender_id.name
                            print("subject", subject)

                            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            menu_id = self.env['ir.ui.menu'].sudo().search(
                                [('name', '=', 'Contracts')], limit=1) or False
                            print("Menu ", menu_id)
                            url_params = {
                                'id': self.tender_id.id,
                                'action': self.env.ref('product_purchase.action_tender_status').id,
                                'model': 'tenders',
                                'view_type': 'form',
                                'menu_id': menu_id.id if menu_id else False,
                            }

                            params = '/web?#%s' % url_encode(url_params)
                            url = base_url + params if base_url else "#"

                            print("URL", url)

                            email_to_list = [
                                user.email or user.login
                                for user in self.env['res.users'].sudo().browse(user_ids)
                                if user.email or user.login
                            ]

                            author = self.env['res.partner'].sudo().search(
                                [('name', '=', 'Administrator')], limit=1)

                            body = (
                                f"Dear User, "
                                f"A Contract has Reverted back with the name <strong>{self.tender_id.name} .<br>"
                                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                            )
                            if self.initiator:
                                mail_values = {
                                    'subject': subject,
                                    'body_html': body,
                                    'email_to': ','.join(email_to_list),
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)

            else:
                if self.reason:
                    con = self.env['contract'].sudo().search([
                        ('main_rfq', '=', self.tender_id.main_rfq.id),
                    ])
                    print("the con is",con)
                    for tender in con:
                        tender.compute_total_vendor_amount()
                        if tender.total_vendor_amount:
                            print("2nd test",tender.total_vendor_amount)
                            tender.state = 'accept'
                            tender_obj = tender.tender_id
                            print("th etender is",tender_obj)
                            if tender_obj:
                                tender_obj.state = 'vendor_approved'
                            for line in tender_obj.contracts_request_line:
                                print("Quantity in tender contract line:", line.quantity, line.product_id.name)

                                # Compare the quantity from contract_request_line with the tender_id contract_request_line
                                for tender_line in tender.vendor_contract_line:
                                    if tender_line.product_id == line.product_id:
                                        print("Comparing Quantity: Tender Line Quantity:", tender_line.quantity)

                                        # Check if quantities are different (or any other condition you need)
                                        if tender_line.quantity != line.quantity:
                                            # Update the quantity in the contract request line
                                            line.quantity = tender_line.quantity
                                            print("Quantity updated to:", tender_line.quantity)

                    rec = self.env['revert.contract.back'].create({

                        'tender_id': self.tender_id.id,

                        'reason': self.reason,

                        'revert_from': self.revert_from.id,

                    })

                    self.tender_id.state = 'rfq'

                    self.tender_id.write({

                        'approved_users': [(5, 0, 0)],

                        'approve_users': [(5, 0, 0)],

                        'next_approve_user_id': [(5, 0, 0)],

                    })

                    self.tender_id.tender_approve_line = [(5, 0, 0)]

                    model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)

                    pending_action = self.env['pending.actions'].sudo().search(

                        [('model', '=', model.id), ('record', '=', self.tender_id.id), ('status', '=', 'open')]

                    )

                    if pending_action:

                        for rec in pending_action:
                            rec.sudo().status = 'closed'

                    activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')],
                                                                                 limit=1)

                    activity = self.env['mail.activity'].sudo().search([

                        ('res_model_id', '=', model.id),

                        ('res_name', '=', self.tender_id.name),

                        ('activity_type_id', '=', activity_type.id),

                    ])

                    if activity:

                        for act in activity:
                            act.action_feedback(feedback="Activity Declined")

                    self.tender_id.sudo().message_post(body=f" {self.env.user.name} Reverted back to Buyer's.")

                    # Notify Buyers

                    # buyer_group = self.env.ref('product_purchase.group_buyers').sudo()

                    # buyer_users = buyer_group.users

                    if self.tender_id.assigned_to:
                        user_ids = [self.tender_id.assigned_to.id]
                    else:
                        buyer_group = self.env.ref('product_purchase.group_buyers').sudo()
                        buyer_users = buyer_group.users
                        user_ids = [user.id for user in buyer_users]

                    if user_ids:

                        branch_name = self.tender_id.branch_ids[0].name if self.tender_id.branch_ids else None

                        pending_vals = {

                            'model': model.id,

                            'name': f"{self.tender_id.name} Contract Request Reverted",

                            'record': self.tender_id.id,

                            'branch': self.tender_id.branch_ids.ids[0] if branch_name else None,

                            'date': date.today(),

                            'approve_users': [(6, 0, user_ids)],

                        }

                        self.env['pending.actions'].sudo().create(pending_vals)

                        # Send Notification Email

                        subject = f"Contract Request Reverted Back: {self.tender_id.name}"

                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

                        menu_id = self.env['ir.ui.menu'].sudo().search([('name', '=', 'Contracts')], limit=1) or False

                        url_params = {

                            'id': self.tender_id.id,

                            'action': self.env.ref('product_purchase.action_tender_status').id,

                            'model': 'tenders',

                            'view_type': 'form',

                            'menu_id': menu_id.id if menu_id else False,

                        }

                        url = f"{base_url}/web?#%s" % url_encode(url_params) if base_url else "#"

                        email_to_list = [
                            user.email or user.login
                            for user in self.env['res.users'].sudo().browse(user_ids)
                            if user.email or user.login
                        ]

                        author = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')], limit=1)

                        body = (

                            f"Dear User,<br>"

                            f"A contract has been reverted with the name <strong>{self.tender_id.name}</strong>.<br>"

                            f"<a href='{url}' style='display: inline-block; padding: 10px 20px; background-color: #008CBA; "

                            f"color: white; text-align: center; text-decoration: none; font-size: 16px; margin: 4px 2px; "

                            f"cursor: pointer; border-radius: 5px;'>View Request</a><br>"

                        )

                        if self.initiator:
                            mail_values = {

                                'subject': subject,

                                'body_html': body,

                                'email_to': ','.join(email_to_list),

                                'auto_delete': False,

                                'author_id': author.id,

                            }

                            self.env['mail.mail'].sudo().create(mail_values)

