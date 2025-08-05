from datetime import datetime, date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError


class DeligateUserWizard(models.TransientModel):
    _name = "po.deligate.user.wizard"
    _description = "Deligate User"

    deligate_user = fields.Many2one('res.users',string="User", store=True,required=True,domain=lambda self: self._domain_to_users())
    # company_id = fields.Many2one('res.users',string="User", store=True,required=True)
    # department = fields.Many2one('res.users',string="User", store=True,required=True)

    email = fields.Char(string="Email", compute='_compute_delegate_details', store=True)
    branch_id = fields.Many2one('res.branch',string="Branch", compute='_compute_delegate_details', store=True)

    po_id = fields.Many2one(
        'purchase.order', string='Product Request', readonly=True)

    @api.onchange('deligate_user')
    def _compute_delegate_details(self):
        for rec in self:
            if rec.deligate_user:
                user = rec.deligate_user
                rec.email = user.login
                rec.branch_id = user.branch_id.id
                print("the branch is",rec.branch_id)

    
    @api.model
    def _domain_to_users(self):
        return [('id', '!=', self.env.user.id), ('groups_id', 'not in', [44])]



    def confirm(self):
        print("hellooo")
        print(self.deligate_user.id)
        print(self.po_id.name)
        for lines in self.po_id.approvers_line_ids:
            if lines.user_id.id == self.env.user.id:
                if lines.status == 'draft':
                    for lines in self.po_id.approvers_line_ids:
                        if lines.user_id.id == self.env.user.id:
                            lines.po_approve_id.write({
                                'approved_users': [(4, lines.user_id.id)]
                            })
                            # record_to_remove = self.env['res.users'].browse(lines.user_id.id)
                            # lines.product_request_id.approve_users -= record_to_remove
                            # lines.product_request_id.write({
                            #     'approve_users': [(4, self.deligate_user.id)],
                            #     'next_approve_user_id': [(4, self.deligate_user.id)]
                            #
                            # })
                            lines.po_approve_id.write({
                                'approve_users': [(4, self.deligate_user.id)],
                                'next_approve_user': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                            })

                            # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                            for rec in lines.po_approve_id.approve_users:
                                print(rec.name)

                            new_line_vals = {
                                'user_id': self.deligate_user.id,
                                # 'company_id': 'value2',
                                # 'location': 'value2',
                                # 'department_id': 'value2',
                                # 'designation': 'value2',
                                'approve_order': lines.approve_order,
                            }
                            self.po_id.approvers_line_ids |= self.env['po.approve.line'].create(new_line_vals)
                            lines.approve_order = ''
                            lines.status ='deligate'
                            lines.po_approve_id.deligated_user = self.deligate_user.id

                            ################ Pending Action
                            model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')],
                                                                       limit=1) #closing pending
                            pending_action = self.env['pending.actions'].sudo().search(
                                [('model', '=', model.id), ('record', '=', self.po_id.id), ('status', '=', 'open')], limit=1)

                            if pending_action:
                                pending_action.status = 'closed'
                            # Opening Pending
                            pending_vals = {
                                'model': model.id,
                                'name': self.po_id.name + " " + "Deligated Purchase Request",
                                'record': self.po_id.id,
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
                                [('name', '=', 'Purchase Request')], limit=1) or False

                            url_params = {
                                'id': self.po_id.id,
                                'action': self.env.ref('product_purchase.action_product_requests').id,
                                'model': 'product.request',
                                'view_type': 'form',
                                # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
                                'menu_id': menu_id.id,
                            }
                            params = '/web?#%s' % url_encode(url_params)
                            view_url = base_url + params if base_url else "#"

                            author = self.env['res.partner'].sudo().search(
                                [('name', '=', 'Administrator')], limit=1) or False

                            body = (
                                f"Dear User,A Purchase Order {self.po_id.name} is waiting for Approval.<br><br>"
                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "
                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"
                            )

                            if self.deligate_user.login:
                                subject = "Purchase Order - Deligated and Waiting For APPROVAL: %s" % self.po_id.name
                                mail_values = {
                                    'subject': subject,
                                    'body_html': body,
                                    'email_to': self.deligate_user.login,
                                    'auto_delete': False,
                                    'author_id': author.id
                                }
                                mail_record = self.env['mail.mail'].sudo().create(mail_values)
                else:
                    raise UserError("User has already deligated once")
