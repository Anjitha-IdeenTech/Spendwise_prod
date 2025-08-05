from odoo import models, fields, api
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import datetime, date

class AssignBuyer(models.TransientModel):
    _name = 'assign.buyer'
    _description = "Assign Buyer"

    current_cr = fields.Many2one('tenders', string='Current CR')
    current_tr = fields.Many2one('product.tender.line', string='Current TR')
    buyer_id = fields.Many2many(
        'res.users',
        string='Buyer',
        domain="[('groups_id', 'in', [72])]"
    )

    def action_confirm(self):
        if self.buyer_id:
            if self.current_cr:
                model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.current_cr.id), ('status', '=', 'open')])
                self.current_cr.assigned = True
                self.current_cr.assigned_to = self.buyer_id
                if pending_action:
                    for rec in pending_action:
                        print(rec.name)
                        rec.status = 'closed'
                pending_vals = {
                    'model': model.id,
                    'name': self.current_cr.name + " " + "Contract Request Assigned to you",

                    'record': self.current_cr.id,
                    'department_id': self.current_cr.department_id.id,
                    'exp_category': self.current_cr.exp_category.id,
                    'date': date.today(),

                }

                if self.current_cr.branch_ids:
                    first_branch_id = self.current_cr.branch_ids[0].id
                    pending_vals['branch'] = first_branch_id
                pending_vals['approve_users'] = [(6, 0, [self.buyer_id.id])]
                self.sudo().current_cr.message_post(body="Purchase Head assigned Pending Contract Request to " + self.buyer_id.name)
                pendings = self.env['pending.actions'].sudo().create(pending_vals)
                approve_users_emails = ', '.join(pendings.approve_users.mapped('login'))

                pendings.write({'email': approve_users_emails})

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
            
            if self.current_tr:
                model = self.env['ir.model'].sudo().search([('model', '=', 'product.tender.line')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.current_tr.id), ('status', '=', 'open')])
                if pending_action:
                    for rec in pending_action:
                        print(rec.name)
                        rec.status = 'closed'

                self.current_tr.assigned = True
                self.current_tr.assigned_to = self.buyer_id

                pending_vals = {
                    'model': model.id,
                    'name': self.current_tr.name + " " + "Contract Renew Date Approaching Assigned to you",

                    'record': self.current_tr.id,
                    'date': date.today(),

                }

                if self.current_tr.branch_ids:
                    first_branch_id = self.current_tr.branch_ids[0].id
                    pending_vals['branch'] = first_branch_id
                pending_vals['approve_users'] = [(6, 0, [self.buyer_id.id])]
                self.sudo().current_tr.message_post(
                    body="Purchase Head assigned Contract Renew Date Approaching Assigned to you " + self.buyer_id.name)
                pendings = self.env['pending.actions'].sudo().create(pending_vals)

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



