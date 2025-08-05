from datetime import datetime, date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError


class DeligateUserWizard(models.TransientModel):
    _name = "cr.deligate.user.wizard"
    _description = "Deligate User CR"

    deligate_user = fields.Many2one('res.users',string="User", store=True,required=True,domain=lambda self: self._domain_to_users())
    # company_id = fields.Many2one('res.users',string="User", store=True,required=True)
    # department = fields.Many2one('res.users',string="User", store=True,required=True)

    cr_id = fields.Many2one(
        'tenders', string='Contract Request', readonly=True)
    branch_id = fields.Many2one('res.branch',string="Default Branch", store=True,compute = '_compute_branch_id')
    email = fields.Char(string='Email')


    @api.model
    def _domain_to_users(self):
        return [('id', '!=', self.env.user.id), ('groups_id', 'not in', [44])]

    @api.onchange('deligate_user')
    def _compute_branch_id(self):
        for rec in self:
            rec.branch_id = rec.deligate_user.branch_id.id
            rec.email = rec.deligate_user.login



    def confirm(self):
        print("hellooo")
        print(self.deligate_user.id)
        print(self.cr_id.name)
        for lines in self.cr_id.tender_approve_line:
            if lines.user_id.id == self.env.user.id:
                if lines.status == 'draft':
                    for lines in self.cr_id.tender_approve_line:
                        if lines.user_id.id == self.env.user.id:
                            lines.tender_id.write({
                                'approved_users': [(4, lines.user_id.id)]
                            })
                            # record_to_remove = self.env['res.users'].browse(lines.user_id.id)
                            # lines.product_request_id.approve_users -= record_to_remove
                            # lines.product_request_id.write({
                            #     'approve_users': [(4, self.deligate_user.id)],
                            #     'next_approve_user_id': [(4, self.deligate_user.id)]
                            #
                            # })
                            lines.tender_id.write({
                                'approve_users': [(4, self.deligate_user.id)],
                                'next_approve_user_id': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                            })

                            # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                            for rec in lines.tender_id.approve_users:
                                print(rec.name)

                            new_line_vals = {
                                'user_id': self.deligate_user.id,
                                # 'company_id': 'value2',
                                # 'location': 'value2',
                                # 'department_id': 'value2',
                                # 'designation': 'value2',
                                'approve_order': lines.approve_order,
                            }
                            self.cr_id.tender_approve_line |= self.env['tender.approve.line'].create(new_line_vals)
                            lines.approve_order = ''
                            lines.status ='deligate'
                            lines.tender_id.deligated_user = self.deligate_user.id

                            ################ Pending Action
                            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')],
                                                                       limit=1) #closing pending
                            pending_action = self.env['pending.actions'].sudo().search(
                                [('model', '=', model.id), ('record', '=', self.cr_id.id), ('status', '=', 'open')], limit=1)

                            for rec in pending_action:
                                if self.env.user in rec.approve_users:
                                    print("record to close", rec)
                                    rec.status = 'closed'
                            activity_type = self.env['mail.activity.type'].sudo().search([('name', '=', 'Pending Request')],
                                                                                  limit=1)
                            activity = self.env['mail.activity'].sudo().search([
                                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                                ('user_id', '=', self.env.user.id), ('res_name', '=', self.cr_id.name),
                                ('activity_type_id', '=', activity_type.id),
                            ])
                            print(activity_type,activity,"actt")
                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")
                            # Opening Pending
                            pending_vals = {
                                'model': model.id,
                                'name': self.cr_id.name + " " + "Deligated Contract Request",
                                'record': self.cr_id.id,
                                'date': date.today(),
                            }
                            if self.deligate_user.id:
                                user_ids_to_pass = self.deligate_user.id
                                # pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                                if self.cr_id.branch_ids:
                                    first_branch_id = self.cr_id.branch_ids[0].id
                                    pending_vals['branch'] = first_branch_id
                                pending_vals['approve_users'] = [(4, self.deligate_user.id)]
                                pendings = self.env['pending.actions'].create(pending_vals)

                            # print(self.next_approve_user_id,
                            #       "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
                            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            menu_id = self.env['ir.ui.menu'].sudo().search(
                                [('name', '=', 'Contract Request')], limit=1) or False

                            url_params = {
                                'id': self.cr_id.id,
                                'action': self.env.ref('product_purchase.action_tender_status').id,
                                'model': 'tenders',
                                'view_type': 'form',
                                # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                'menu_id': menu_id.id,
                            }
                            params = '/web?#%s' % url_encode(url_params)
                            view_url = base_url + params if base_url else "#"

                            author = self.env['res.partner'].sudo().search(
                                [('name', '=', 'Administrator')], limit=1) or False

                            body = (
                                f"Dear User,A Contract Request {self.cr_id.name} is waiting for Approval.<br><br>"
                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                            )

                            if self.deligate_user.login:
                                subject = "Contract Request Deligated and Waiting For APPROVAL: %s" % self.cr_id.name
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
                            activity_type_id = activity_type.id if activity_type else False
                            res_model_id = self.env['ir.model'].sudo().search(
                                [('model', '=', 'tenders')]).id
                            if self.deligate_user:
                                activity_values = {
                                    'user_id': self.deligate_user.id,
                                    'res_id': self.cr_id.id,
                                    'note': "Pending Action",
                                    'summary': "Action",
                                    'activity_type_id': activity_type_id,
                                    'res_model_id': res_model_id,
                                }
                                created_activity = self.env['mail.activity'].create(activity_values)
                else:
                    raise UserError("User has already deligated once")
