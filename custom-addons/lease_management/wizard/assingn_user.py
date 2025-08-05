from odoo import models, fields, api
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import datetime, date
from werkzeug.urls import url_encode

class AssignBuyer(models.TransientModel):
    _name = 'assign.user'
    _description = "Assign Buyer"

    current_po = fields.Many2one('purchase.order', string='Current PO')

    user_id = fields.Many2many(
        'res.users',
        string='User',
    )



    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        current_po_id = self.env.context.get('active_id')  
        if current_po_id:
            current_po = self.env['purchase.order'].browse(current_po_id)
            if current_po.exists() and current_po.bill_to:
                product_ids = current_po.order_line.mapped('product_id').ids
                existing_po_lines = self.env['purchase.order.line'].sudo().search([
                    ('order_id.bill_to', '=', current_po.bill_to.id),
                    ('order_id.ct_number', 'in', current_po.ct_number.ids),
                    ('product_id', 'in', product_ids),
                ])
                print("existing po",existing_po_lines)

                assigned_po = existing_po_lines.filtered(lambda po: po.order_id.assigned_to)
                print("the assign is",assigned_po)

                if assigned_po:

                    user_ids = assigned_po[0].order_id.assigned_to.ids
                    print("Assigning user from existing PO:", assigned_po[0].order_id.assigned_to.name)
                    defaults['user_id'] = [(6, 0, user_ids)]
                else:

                    location_head = self.env['res.users.line'].sudo().search([
                        ('branch_id', '=', current_po.bill_to.id),
                        ('designation', '=', 'Location Head')
                    ], limit=1)

                    if location_head and location_head.res_user_id:
                        print("Assigning user from Location Head:", location_head.res_user_id.name)
                        defaults['user_id'] = [(6, 0, [location_head.res_user_id.id])]

        return defaults

    def action_confirm(self):
        if self.user_id:
            if self.current_po:
                model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.current_po.id), ('status', '=', 'open')])
                self.current_po.assigned = True
                self.current_po.assigned_to = self.user_id
                if pending_action:
                    for rec in pending_action:
                        print(rec.name)
                        rec.status = 'closed'
                pending_vals = {
                    'model': model.id,
                    'name': self.current_po.name + " " + "Purchase Order Assigned to you",

                    'record': self.current_po.id,
                    'branch': self.current_po.bill_to.id,
                    'department_id': self.current_po.department_id.id,
                    'exp_category': self.current_po.exp_category.id,
                    'Created_doc_date': self.current_po.date,
                    'date': date.today(),

                }

                if self.current_po.bill_to:
                    pending_vals['branch'] = self.current_po.bill_to.id
                pending_vals['approve_users'] = [(6, 0, [self.user_id.id])]
                self.sudo().current_po.message_post(body="Purchase Head assigned Purchase Order to " + self.user_id.name)
                pendings = self.env['pending.actions'].sudo().create(pending_vals)

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
                approval_url = base_url + params if base_url else "#"



                # body = f"Dear User,A Purchase Order {self.name} has been initiated."
                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1) or False

                body = (
                    f"Dear User,A Purchase Order {self.current_po.name} has been assigned to you. Waiting for your confirmation.<br><br>"
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

                if self.current_po.assigned_to.email:
                    mail_values = {
                        'subject': 'PO Waiting for acknowledgment',
                        'body_html': body,
                        'email_to': self.current_po.assigned_to.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)

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
