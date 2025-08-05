from datetime import datetime, date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError


class DeligateUserWizardlease(models.TransientModel):
    _name = "deligate.user.lease.wizard"
    _description = "Deligate User lease"

    deligate_user = fields.Many2one('res.users',string="User", store=True,required=True,domain=lambda self: self._domain_to_users())
    # company_id = fields.Many2one('res.users',string="User", store=True,required=True)
    # department = fields.Many2one('res.users',string="User", store=True,required=True)

    request_id = fields.Many2one(
        'product.lease', string='Product Lease', readonly=True)
    email = fields.Char(string="Email", compute='_compute_delegate_details', store=True)
    branch = fields.Many2one('res.branch',string="Branch", compute='_compute_delegate_details', store=True)
    work_flow_type = fields.Selection(
        selection=[('lease', 'lease'), ('legal', 'legal')],
        string='Work Flow')
    # phone_number = fields.Char(string="Phone Number", compute='_compute_delegate_details', store=True)


    @api.model
    def _domain_to_users(self):
        return [('id', '!=', self.env.user.id), ('groups_id', 'not in', [44])]


    @api.onchange('deligate_user')
    def _compute_delegate_details(self):
        for rec in self:
            if rec.deligate_user:
                user = rec.deligate_user
                rec.email = user.login
                rec.branch = user.branch_id.id  


    def confirm(self):

        if self.work_flow_type == 'lease':
            print("hellooo")
            print(self.deligate_user.id)
            print(self.request_id.name)
            for lines in self.request_id.approve_line:
                print(lines)
                if lines.user_id.id == self.env.user.id:
                    print(lines.user_id.id)
                    if lines.status == 'draft':
                        for lines in self.request_id.approve_line:
                            if lines.user_id.id == self.env.user.id:
                                print("inside user")
                                lines.approve_lease_id.write({
                                    'approved_users': [(4, lines.user_id.id)]
                                })
                                print(lines.approve_lease_id)
                                # record_to_remove = self.env['res.users'].browse(lines.user_id.id)
                                # lines.product_request_id.approve_users -= record_to_remove
                                # lines.product_request_id.write({
                                #     'approve_users': [(4, self.deligate_user.id)],
                                #     'next_approve_user_id': [(4, self.deligate_user.id)]
                                #
                                # })
                                lines.approve_lease_id.write({
                                    'approve_users': [(4, self.deligate_user.id)],
                                    'next_approve_user': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                })
                                print("the approve lease",lines.approve_lease_id)
                                # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                for rec in lines.approve_lease_id.approve_users:
                                    print(rec.name)

                                new_line_vals = {
                                    'user_id': self.deligate_user.id,
                                    # 'company_id': 'value2',
                                    # 'location': 'value2',
                                    # 'department_id': 'value2',
                                    # 'designation': 'value2',
                                    'approve_order': lines.approve_order,
                                }
                                self.request_id.approve_line |= self.env['lease.approve.line'].create(new_line_vals)
                                lines.approve_order = ''
                                lines.status ='deligate'
                                lines.approve_lease_id.deligated_user = self.deligate_user.id

                                ################ Pending Action
                                model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')],
                                                                           limit=1) #closing pending
                                pending_action = self.env['pending.actions'].sudo().search(
                                    [('model', '=', model.id), ('record', '=', self.request_id.id), ('status', '=', 'open')], limit=1)

                                for rec in pending_action:
                                    if self.env.user in rec.approve_users:
                                        print("record to close", rec)
                                        rec.status = 'closed'

                                activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')],
                                                                                      limit=1)
                                print("type is", self.env.user.id)
                                activity = self.env['mail.activity'].search([
                                    ('res_model_id', '=',
                                     self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
                                    ('user_id', '=', self.env.user.id),
                                    ('activity_type_id', '=', activity_type.id),
                                ], limit=1)
                                if activity:
                                    print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                                    print(activity.id)
                                    activity.action_feedback(feedback="Activity Delegated")

                                self.request_id.message_post(body=f"The lease request delegated from {self.env.user.name} to {self.deligate_user.name}")
                                # Opening Pending
                            


                                if self.deligate_user.id:
                                    print("i am inside deli")
                                    pending_vals = {
                                    'model': model.id,
                                    'name': self.request_id.name + " " + "Deligated Lease Request",
                                    'record': self.request_id.id,
                                    'date': date.today(),
                                    'branch': self.request_id.bill_to.id
                                    }
                                    
                                    activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Request')], limit=1)
                                    activity_type_id = activity_type.id if activity_type else False
                                    res_model_id = self.env['ir.model'].sudo().search(
                                    [('model', '=', 'product.lease')]).id

                                    user_ids_to_pass = self.deligate_user.id

                                    # pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                    pending_vals['approve_users'] = [(4, self.deligate_user.id)]
                                    pendings = self.env['pending.actions'].create(pending_vals)

                                    activity_values = {
                                        'user_id': self.deligate_user.id,
                                        'res_id': self.request_id.id,
                                        'note': "Pending Action",
                                        'activity_type_id': activity_type_id,
                                        'res_model_id': res_model_id,
                                    }
                                    created_activity = self.env['mail.activity'].create(activity_values)

                                # print(self.next_approve_user_id,
                                #       "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                    [('name', '=', 'Contracts')], limit=1) or False

                                url_params = {
                                    'id': self.request_id.id,
                                    'action': self.env.ref('lease_management.action_my_product_lease').id,
                                    'model': 'product.lease',
                                    'view_type': 'form',
                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                    'menu_id': menu_id.id,
                                }
                                params = '/web?#%s' % url_encode(url_params)
                                view_url = base_url + params if base_url else "#"

                                author = self.env['res.partner'].sudo().search(
                                    [('name', '=', 'Administrator')], limit=1) or False

                                body = (
                                    f"Dear User,A Lease request {self.request_id.name} is waiting for Approval.<br><br>"
                                    f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                )

                                if self.deligate_user.login:
                                    subject = "Lease Request Deligated and Waiting For APPROVAL: %s" % self.request_id.name
                                    mail_values = {
                                        'subject': subject,
                                        'body_html': body,
                                        'email_to': self.deligate_user.login,
                                        'auto_delete': False,
                                        'author_id': author.id
                                    }
                                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                    print(mail_record)
                                    mail_record.send()

                    else:
                        raise UserError("User has already deligated once")

        else:
            print("hellooo")
            print(self.deligate_user.id)
            print(self.request_id.name)
            for lines in self.request_id.legal_approve_line:
                print(lines)
                if lines.user_id.id == self.env.user.id:
                    print(lines.user_id.id)
                    if lines.status == 'draft':
                        for lines in self.request_id.legal_approve_line:
                            if lines.user_id.id == self.env.user.id:
                                print("inside user")
                                lines.approve_lease_legal_id.write({
                                    'legal_approved_users': [(4, lines.user_id.id)]
                                })
                                print(lines.approve_lease_legal_id)
                                # record_to_remove = self.env['res.users'].browse(lines.user_id.id)
                                # lines.product_request_id.approve_users -= record_to_remove
                                # lines.product_request_id.write({
                                #     'approve_users': [(4, self.deligate_user.id)],
                                #     'next_approve_user_id': [(4, self.deligate_user.id)]
                                #
                                # })
                                lines.approve_lease_legal_id.write({
                                    'legal_approve_users': [(4, self.deligate_user.id)],
                                    'legal_next_approve_user': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                })
                                print("the approve lease", lines.approve_lease_legal_id)
                                # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                for rec in lines.approve_lease_legal_id.legal_approve_users:
                                    print(rec.name)

                                new_line_vals = {
                                    'user_id': self.deligate_user.id,
                                    # 'company_id': 'value2',
                                    # 'location': 'value2',
                                    # 'department_id': 'value2',
                                    # 'designation': 'value2',
                                    'approve_order': lines.approve_order,
                                }
                                self.request_id.legal_approve_line |= self.env['lease.legal.approve.line'].create(new_line_vals)
                                lines.approve_order = ''
                                lines.status = 'deligate'
                                lines.approve_lease_legal_id.deligated_user = self.deligate_user.id

                                ################ Pending Action
                                model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')],
                                                                           limit=1)  # closing pending
                                pending_action = self.env['pending.actions'].sudo().search(
                                    [('model', '=', model.id), ('record', '=', self.request_id.id),
                                     ('status', '=', 'open')], limit=1)

                                for rec in pending_action:
                                    if self.env.user in rec.approve_users:
                                        print("record to close", rec)
                                        rec.status = 'closed'

                                activity_type = self.env['mail.activity.type'].search(
                                    [('name', '=', 'Pending Request')],
                                    limit=1)
                                print("type is", self.env.user.id)
                                activity = self.env['mail.activity'].search([
                                    ('res_model_id', '=',
                                     self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
                                    ('user_id', '=', self.env.user.id),
                                    ('activity_type_id', '=', activity_type.id),
                                ], limit=1)
                                if activity:
                                    print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                                    print(activity.id)
                                    activity.action_feedback(feedback="Activity Deligate")
                                self.request_id.message_post(
                                    body=f"The lease request delegated from {self.env.user.name} to {self.deligate_user.name}")
                                # Opening Pending
                                pending_vals = {
                                    'model': model.id,
                                    'name': self.request_id.name + " " + "Deligated Lease Request",
                                    'record': self.request_id.id,
                                    'date': date.today(),
                                    'branch': self.request_id.bill_to.id
                                }
                                activity_type = self.env['mail.activity.type'].sudo().search(
                                    [('name', '=', 'Pending Request')], limit=1)
                                activity_type_id = activity_type.id if activity_type else False
                                res_model_id = self.env['ir.model'].sudo().search(
                                    [('model', '=', 'product.lease')]).id

                                if self.deligate_user.id:
                                    print("i am inside deli")
                                    user_ids_to_pass = self.deligate_user.id
                                    # pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                    pending_vals['approve_users'] = [(4, self.deligate_user.id)]
                                    pendings = self.env['pending.actions'].create(pending_vals)

                                    activity_values = {
                                        'user_id': self.deligate_user.id,
                                        'res_id': self.request_id.id,
                                        'note': "Pending Action",
                                        'activity_type_id': activity_type_id,
                                        'res_model_id': res_model_id,
                                    }
                                    created_activity = self.env['mail.activity'].create(activity_values)

                                # print(self.next_approve_user_id,
                                #       "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                    [('name', '=', 'Contracts')], limit=1) or False

                                url_params = {
                                    'id': self.request_id.id,
                                    'action': self.env.ref('lease_management.action_my_product_lease').id,
                                    'model': 'product.lease',
                                    'view_type': 'form',
                                    # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                    'menu_id': menu_id.id,
                                }
                                params = '/web?#%s' % url_encode(url_params)
                                view_url = base_url + params if base_url else "#"

                                author = self.env['res.partner'].sudo().search(
                                    [('name', '=', 'Administrator')], limit=1) or False

                                body = (
                                    f"Dear User,A Lease request {self.request_id.name} is waiting for Approval.<br><br>"
                                    f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                                )

                                if self.deligate_user.login:
                                    subject = "Lease Request Deligated and Waiting For APPROVAL: %s" % self.request_id.name
                                    mail_values = {
                                        'subject': subject,
                                        'body_html': body,
                                        'email_to': self.deligate_user.login,
                                        'auto_delete': False,
                                        'author_id': author.id
                                    }
                                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                    print(mail_record)
                                    mail_record.send()

                    else:
                        raise UserError("User has already deligated once")
