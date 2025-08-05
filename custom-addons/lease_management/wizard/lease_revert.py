

from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError, MissingError, UserError
from werkzeug.urls import url_encode

class RevertBAckWizard(models.TransientModel):
    _name = 'revert.back.lease.wizard'
    _description = "Revert Back"

    lease_id = fields.Many2one(
        'product.lease', string='Purchase Order', readonly=True)
    reason = fields.Char("Message")
    revert_from = fields.Many2one(
        'res.users', string='Revert User')
    initiator = fields.Many2one(
        'res.users', string='Initiator User')



    def action_confirm(self):
        if self.reason:
            rec = self.env['revert.lease.back'].create({
                'lease_id': self.lease_id.id,
                'reason': self.reason,
                'revert_from': self.revert_from.id,
            })
            print("Revert",rec)
            self.lease_id.state = 'revert'
            self.lease_id.write({
                'approved_users': [(5, 0, 0)],
                'approve_users': [(5, 0, 0)],
                'next_approve_user': [(5, 0, 0)],

            })

            self.lease_id.approve_line = [(5, 0, 0)]
            model = self.env['ir.model'].sudo().search([('model', '=','product.lease')], limit=1)
            print("Model",model)
            pending_actions = self.env['pending.actions'].sudo().search([
                ('model', '=',  model.id),  # Assuming the model field in PendingAction stores the model name
                ('record', '=', self.lease_id.id),  # Assuming the record field in PendingAction stores the record ID
                ('status', '=', 'open')  # Assuming the status field indicates the pending status
            ])
            print("Pending action",pending_actions)
            # Update the status of the found pending actions to "close"
            pending_actions.unlink()
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Request')], limit=1)
            print("type is", self.env.user.id)
            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.lease')]).id),
                ('res_name', '=', self.lease_id.name),
                ('activity_type_id', '=', activity_type.id),
            ])
            for act in activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print(activity.id)

                act.action_feedback(feedback="Request Reverted to Initiator")
            if self.lease_id.product_request_id.budget_details:
                self.self.lease_id.product_request_id.budget_details.amount_used -= self.lease_id.total_price

            subject = "Lease Request Reverted Back : %s" % self.lease_id.name

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'Purchase Request')], limit=1) or False
            print("Menu ",menu_id)
            url_params = {
                'id': self.lease_id.id,
                'action': self.env.ref('lease_management.action_product_lease').id,
                'model': 'product.lease',
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
                f"A  Lease Request has Reverted back with the name <strong>{self.lease_id.name} .<br>"
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

        else:
            raise ValidationError(_("Reason Cannot be empty"))