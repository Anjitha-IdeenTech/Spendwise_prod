from datetime import datetime, date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError


class DeligateUserWizard(models.TransientModel):
    _name = "deligate.user.invoice.wizard"
    _description = "Deligate User Ivoice"

    deligate_user = fields.Many2one('res.users',string="User", store=True,required=True,domain=lambda self: self._domain_to_users())
    # company_id = fields.Many2one('res.users',string="User", store=True,required=True)
    # department = fields.Many2one('res.users',string="User", store=True,required=True)

    invoice_id = fields.Many2one(
        'account.move', string='Invoice Request', readonly=True)
    branch_id = fields.Many2one('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')
    email = fields.Char(string='Email')

    @api.onchange('deligate_user')
    def _compute_branch_id(self):
        for rec in self:
            rec.branch_id = rec.deligate_user.branch_id.id
            rec.email = rec.deligate_user.login

    @api.model
    def _domain_to_users(self):
        return [('id', '!=', self.env.user.id), ('groups_id', 'not in', [44])]



    def confirm(self):
        print("hellooo")
        print(self.deligate_user.id)
        print(self.invoice_id.name)
        if self.invoice_id.state == 'accounting':
            for lines in self.invoice_id.invoice_approve_line:
                print("the lines are",lines)
                print("inside invoice")
                if lines.user_id.id == self.env.user.id:
                    print("user matched")
                    if lines.status == 'draft':
                        print(lines.status)
                        for lines in self.invoice_id.invoice_approve_line:
                            print(lines)
                            if lines.user_id.id == self.env.user.id:
                                print("user checkk")
                                lines.invoice_id.write({
                                    'approved_users': [(4, lines.user_id.id)]
                                })
                                # record_to_remove = self.env['res.users'].browse(lines.user_id.id)
                                # lines.product_request_id.approve_users -= record_to_remove
                                # lines.product_request_id.write({
                                #     'approve_users': [(4, self.deligate_user.id)],
                                #     'next_approve_user_id': [(4, self.deligate_user.id)]
                                #
                                # })
                                lines.invoice_id.write({
                                    'approve_users': [(4, self.deligate_user.id)],
                                    'next_approve_user': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                })

                                # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                for rec in lines.invoice_id.approve_users:
                                    print(rec.name)

                                new_line_vals = {
                                    'user_id': self.deligate_user.id,
                                    # 'company_id': 'value2',
                                    # 'location': 'value2',
                                    # 'department_id': 'value2',
                                    # 'designation': 'value2',
                                    'approve_order': lines.approve_order,
                                }
                                print("new",new_line_vals)
                                self.invoice_id.invoice_approve_line |= self.env['invoice.approve.line'].create(new_line_vals)
                                lines.approve_order = ''
                                lines.status ='deligate'
                                lines.invoice_id.deligated_user = self.deligate_user.id
                                print(self.invoice_id.invoice_approve_line)

                                ################ Pending Action
                                model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')],
                                                                           limit=1) #closing pending
                                print("model",model)
                                pending_action = self.env['pending.actions'].sudo().search(
                                    [('model', '=', model.id), ('record', '=', self.invoice_id.id), ('status', '=', 'open')], limit=1)
                                print("pend",pending_action)

                                if pending_action:
                                    for rec in pending_action:
                                        if self.env.user in rec.approve_users:
                                            print("record to close", rec)
                                            rec.status = 'closed'
                                activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Request')],
                                    limit=1)
                                activity = self.env['mail.activity'].sudo().search([
                                    ('res_model_id', '=',
                                     self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                                    ('user_id', '=', self.env.user.id), ('res_id', '=', self.invoice_id.id),
                                    ('activity_type_id', '=', activity_type.id),
                                ], limit=1)
                                if activity:
                                    activity.action_feedback(feedback="Activity Delegated")
                                # Opening Pending
                                pending_vals = {
                                    'model': model.id,
                                    'name': self.invoice_id.name + " " + "Deligated Invoice Request",
                                    'record': self.invoice_id.id,
                                    'branch':self.invoice_id.branch_id.id,
                                    'date': date.today(),
                                }
                                if self.deligate_user.id:
                                    user_ids_to_pass = self.deligate_user.id
                                    # pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                    pending_vals['approve_users'] = [(4, self.deligate_user.id)]
                                    pendings = self.env['pending.actions'].create(pending_vals)

                                # print(self.next_approve_user_id,
                                #       "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                    [('name', '=', 'Accounting')], limit=1) or False

                                url_params = {
                                    'id': self.invoice_id.id,
                                    'action': self.env.ref('account.action_move_in_invoice_type').id,
                                    'model': 'account.move',
                                    'view_type': 'form',
                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                    'menu_id': menu_id.id,
                                }
                                params = '/web?#%s' % url_encode(url_params)
                                view_url = base_url + params if base_url else "#"

                                author = self.env['res.partner'].sudo().search(
                                    [('name', '=', 'Administrator')], limit=1) or False

                                body = (
                                    f"Dear User,A Invoice Request {self.invoice_id.name} is waiting for Approval.<br><br>"
                                    f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                )

                                if self.deligate_user.login:
                                    subject = "Invoice Request Deligated and Waiting For APPROVAL: %s" % self.invoice_id.name
                                    mail_values = {
                                        'subject': subject,
                                        'body_html': body,
                                        'email_to': self.deligate_user.login,
                                        'auto_delete': False,
                                        'author_id': author.id
                                    }
                                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Request')], limit=1)
                                print("the activity type", activity_type)
                                activity_type_id = activity_type.id if activity_type else False
                                res_model_id = self.env['ir.model'].sudo().search(
                                    [('model', '=', 'account.move')]).id
                                if self.deligate_user:
                                    activity_values = {
                                        'user_id': self.deligate_user.id,
                                        'res_id': self.invoice_id.id,
                                        'note': "Pending Action",
                                        'activity_type_id': activity_type_id,
                                        'res_model_id': res_model_id,
                                    }
                                    created_activity = self.env['mail.activity'].create(activity_values)
                                    print("the created activity", created_activity)
                    else:
                        raise UserError("User has already deligated once")

        if self.invoice_id.state == 'finance':
            for lines in self.invoice_id.invoice_payment_approve_line:
                print("the lines are", lines)
                print("inside invoice")
                if lines.user_id.id == self.env.user.id:
                    print("user matched")
                    if lines.status == 'draft':
                        print(lines.status)
                        for lines in self.invoice_id.invoice_payment_approve_line:
                            print(lines)
                            if lines.user_id.id == self.env.user.id:
                                print("user checkk")
                                lines.invoice_id.write({
                                    'payment_approved_users': [(4, lines.user_id.id)]
                                })
                                # record_to_remove = self.env['res.users'].browse(lines.user_id.id)
                                # lines.product_request_id.approve_users -= record_to_remove
                                # lines.product_request_id.write({
                                #     'approve_users': [(4, self.deligate_user.id)],
                                #     'next_approve_user_id': [(4, self.deligate_user.id)]
                                #
                                # })
                                lines.invoice_id.write({
                                    'payment_approve_users': [(4, self.deligate_user.id)],
                                    'payment_next_approve_user': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                })

                                # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                for rec in lines.invoice_id.payment_approve_users:
                                    print(rec.name)

                                new_line_vals = {
                                    'user_id': self.deligate_user.id,
                                    # 'company_id': 'value2',
                                    # 'location': 'value2',
                                    # 'department_id': 'value2',
                                    # 'designation': 'value2',
                                    'approve_order': lines.approve_order,
                                }
                                print("new", new_line_vals)
                                self.invoice_id.invoice_payment_approve_line |= self.env['invoice.payment.approve.line'].create(
                                    new_line_vals)
                                lines.approve_order = ''
                                lines.status = 'deligate'
                                lines.invoice_id.deligated_user = self.deligate_user.id
                                print(self.invoice_id.invoice_payment_approve_line)

                                ################ Pending Action
                                model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')],
                                                                           limit=1)  # closing pending
                                print("model", model)
                                pending_action = self.env['pending.actions'].sudo().search(
                                    [('model', '=', model.id), ('record', '=', self.invoice_id.id),
                                     ('status', '=', 'open')], limit=1)
                                print("pend", pending_action)

                                if pending_action:
                                    for rec in pending_action:
                                        if self.env.user in rec.approve_users:
                                            print("record to close", rec)
                                            rec.status = 'closed'
                                activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Request')],
                                    limit=1)
                                activity = self.env['mail.activity'].sudo().search([
                                    ('res_model_id', '=',
                                     self.env['ir.model'].sudo().search([('model', '=', 'account.move')]).id),
                                    ('user_id', '=', self.env.user.id), ('res_id', '=', self.invoice_id.id),
                                    ('activity_type_id', '=', activity_type.id),
                                ], limit=1)
                                if activity:
                                    activity.action_feedback(feedback="Activity Delegated")
                                # Opening Pending
                                pending_vals = {
                                    'model': model.id,
                                    'name': self.invoice_id.name + " " + "Deligated Invoice Request",
                                    'record': self.invoice_id.id,
                                    'branch': self.invoice_id.branch_id.id,
                                    'date': date.today(),
                                }
                                if self.deligate_user.id:
                                    user_ids_to_pass = self.deligate_user.id
                                    # pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                    pending_vals['approve_users'] = [(4, self.deligate_user.id)]
                                    pendings = self.env['pending.actions'].create(pending_vals)

                                # print(self.next_approve_user_id,
                                #       "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                    [('name', '=', 'Accounting')], limit=1) or False

                                url_params = {
                                    'id': self.invoice_id.id,
                                    'action': self.env.ref('account.action_move_in_invoice_type').id,
                                    'model': 'account.move',
                                    'view_type': 'form',
                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                    'menu_id': menu_id.id,
                                }
                                params = '/web?#%s' % url_encode(url_params)
                                view_url = base_url + params if base_url else "#"

                                author = self.env['res.partner'].sudo().search(
                                    [('name', '=', 'Administrator')], limit=1) or False

                                body = (
                                    f"Dear User,A Invoice Request {self.invoice_id.name} is waiting for Approval.<br><br>"
                                    f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                )

                                if self.deligate_user.login:
                                    subject = "Invoice Request Deligated and Waiting For APPROVAL: %s" % self.invoice_id.name
                                    mail_values = {
                                        'subject': subject,
                                        'body_html': body,
                                        'email_to': self.deligate_user.login,
                                        'auto_delete': False,
                                        'author_id': author.id
                                    }
                                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Request')], limit=1)
                                print("the activity type", activity_type)
                                activity_type_id = activity_type.id if activity_type else False
                                res_model_id = self.env['ir.model'].sudo().search(
                                    [('model', '=', 'account.move')]).id
                                if self.deligate_user:
                                    activity_values = {
                                        'user_id': self.deligate_user.id,
                                        'res_id': self.invoice_id.id,
                                        'note': "Pending Action",
                                        'activity_type_id': activity_type_id,
                                        'res_model_id': res_model_id,
                                    }
                                    created_activity = self.env['mail.activity'].create(activity_values)
                                    print("the created activity", created_activity)
                    else:
                        raise UserError("User has already deligated once")