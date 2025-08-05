

from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError, MissingError, UserError
from werkzeug.urls import url_encode

class RevertBAckWizard(models.TransientModel):
    _name = 'revert.back.wizard'
    _description = "Revert Back"

    pr_id = fields.Many2one(
        'product.request', string='Purchase Request', readonly=True)
    cr_id = fields.Many2one(
        'product.request', string='Purchase Request', readonly=True)
    reason = fields.Text("Message")
    revert_from = fields.Many2one(
        'res.users', string='Revert User')
    initiator = fields.Many2one(
        'res.users', string='Initiator User')



    def action_confirm(self):
        if self.reason:
            if self.pr_id:
                rec = self.env['revert.back'].create({
                    'pr_id': self.pr_id.id,
                    'reason': self.reason,
                    'revert_from': self.revert_from.id,
                })
                print("Revert",rec)
                self.pr_id.status = 'revert'
                self.pr_id.write({
                    'approved_users': [(5, 0, 0)],
                    'approve_users': [(5, 0, 0)],
                    'next_approve_user_id': [(5, 0, 0)],

                })

                self.pr_id.pr_approve_line = [(5, 0, 0)]
                model = self.env['ir.model'].sudo().search([('model', '=','product.request')], limit=1)
                print("Model",model)
                pending_actions = self.env['pending.actions'].sudo().search([
                    ('model', '=',  model.id),  # Assuming the model field in PendingAction stores the model name
                    ('record', '=', self.pr_id.id),  # Assuming the record field in PendingAction stores the record ID
                    ('status', '=', 'open')  # Assuming the status field indicates the pending status
                ])
                print("Pending action",pending_actions)
                # Update the status of the found pending actions to "close"
                if pending_actions:
                    pending_actions.status = 'closed'
                if self.pr_id.budget_details:
                    self.pr_id.sudo().budget_details.amount_used -= self.pr_id.total_price
                self.pr_id.message_post(body=f" {self.env.user.name} Reverted back to Initiator.")
                subject = "Purchase Request Reverted Back : %s" % self.pr_id.name

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Purchase Request')], limit=1) or False
                print("Menu ",menu_id)
                url_params = {
                    'id': self.pr_id.id,
                    'action': self.env.ref('product_purchase.action_product_requests').id,
                    'model': 'product.request',
                    'view_type': 'form',
                    'menu_id': menu_id.id if menu_id else False,
                }

                params = '/web?#%s' % url_encode(url_params)
                url = base_url + params if base_url else "#"

                print("URL",url)

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A  Purchase Request has Reverted back with the name <strong>{self.pr_id.name} .<br>"
                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                )
                if self.initiator:

                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': self.initiator.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    # return {
                    #     'type': 'ir.actions.act_window',
                    #     'view_type': 'tree',
                    #     'view_id': self.env.ref('pending_actions.view_dynamic_view').id,
                    #     'view_mode': 'tree',
                    #     'res_model': 'pending.actions',
                    #     'target': 'current',  # Keeps the action in the current window
                    # }
                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                    ('res_name', '=', self.pr_id.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback="Purchase Request Reverted Back")
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
            
            if self.cr_id:
                rec = self.env['revert.back'].create({
                    'pr_id': self.cr_id.id,
                    'reason': self.reason,
                    'revert_from': self.revert_from.id,
                })

                print("Revert", rec)
                self.cr_id.status = 'revert'

                self.cr_id.write({
                    'approved_users_cr': [(5, 0, 0)],
                    'approve_users_cr': [(5, 0, 0)],
                    'next_approve_user_id_cr': [(5, 0, 0)],

                })

                self.cr_id.cr_need_approve_line = [(5, 0, 0)]
                model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
                print("Model", model)
                pending_actions = self.env['pending.actions'].sudo().search([
                    ('model', '=', model.id),  # Assuming the model field in PendingAction stores the model name
                    ('record', '=', self.cr_id.id),  # Assuming the record field in PendingAction stores the record ID
                    ('status', '=', 'open')  # Assuming the status field indicates the pending status
                ])
                print("Pending action", pending_actions)
                # Update the status of the found pending actions to "close"
                if pending_actions:
                    for pend in pending_actions:
                        pend.status = 'closed'
                if self.cr_id.budget_details:
                    self.cr_id.sudo().budget_details.amount_used -= self.cr_id.total_price
                self.cr_id.message_post(body=f" {self.env.user.name} Reverted back to Initiator.")
                subject = "Purchase Request Reverted Back : %s" % self.cr_id.name

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Purchase Request')], limit=1) or False
                print("Menu ", menu_id)
                url_params = {
                    'id': self.cr_id.id,
                    'action': self.env.ref('product_purchase.action_product_requests').id,
                    'model': 'product.request',
                    'view_type': 'form',
                    'menu_id': menu_id.id if menu_id else False,
                }

                params = '/web?#%s' % url_encode(url_params)
                url = base_url + params if base_url else "#"

                print("URL", url)

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A  Purchase Request has Reverted back with the name <strong>{self.pr_id.name} .<br>"
                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                )
                if self.initiator:
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': self.initiator.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    # return {
                    #     'type': 'ir.actions.act_window',
                    #     'view_type': 'tree',
                    #     'view_id': self.env.ref('pending_actions.view_dynamic_view').id,
                    #     'view_mode': 'tree',
                    #     'res_model': 'pending.actions',
                    #     'target': 'current',  # Keeps the action in the current window
                    # }
                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                    ('res_name', '=', self.cr_id.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback="Purchase Request Reverted Back")
                pending = self.env['pending.actions'].sudo().search(
                    [('status', '=', 'open'), ('approve_users', 'in', self.env.user.id)], order='id desc', limit=1)
                print("return", pending)
                if pending:
                    print("if ", pending)
                    return pending.open_record()
                else:
                    print("else")
                    action = self.env["ir.actions.act_window"]._for_xml_id('pending_actions.action_pending_actions')
                    return action



        else:
            raise ValidationError(_("Reason Cannot be empty"))

