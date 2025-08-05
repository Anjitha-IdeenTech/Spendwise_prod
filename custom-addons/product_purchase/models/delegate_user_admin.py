from datetime import datetime, date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError


class DeligateUserWizard(models.TransientModel):
    _name = "deligate.user.admin.wizard"
    _description = "Deligate User Admin"
    # _inherit = ['product.lease']

    deligate_user = fields.Many2one('res.users', string="Delegate User", store=True, required=True,domain="[('groups_id', 'not in', [44])]")
    # company_id = fields.Many2one('res.users',string="User", store=True,required=True)
    # department = fields.Many2one('res.users',string="User", store=True,required=True)

    user_ids = fields.Many2one('res.users', string='Approve Users', required=True,
                               domain=lambda self: self._get_user_domain())

    request_id = fields.Many2one('product.request', string='Product Request', readonly=True)
    lease_id = fields.Many2one('product.lease', string='Lease Request', readonly=True)
    lease = fields.Integer(string="Lease")
    request_contract_id = fields.Many2one('tenders', string='Contract Request', readonly=True)
    po_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    type_id = fields.Selection(selection=[('pr', 'pr'), ('cr', 'cr'), ('tn', 'tn'), ('po', 'po'), ('lease', 'lease'),('inva','inva'),('invf','invf')],
                               string='Type')

    remark = fields.Text(string='Remark')

    @api.depends('lease')
    def _compute_lease(self):
        for record in self:
            if record.lease:
                lease_num = self.env['product.lease'].search([('id', '=', record.lease)], limit=1)
                record.lease_id = lease_num
                print("the record lease",record.lease_id)
            else:
                record.lease_id = False

    @api.model
    def _default_user_ids(self):
        return self.env.context.get('user_ids', [])

    @api.model
    def _get_user_domain(self):
        return [('id', 'in', self.env.context.get('user_ids', []))]

    @api.model
    def default_get(self, fields):
        res = super(DeligateUserWizard, self).default_get(fields)
        if 'type_id' in self.env.context:
            res['type_id'] = self.env.context.get('type_id')
        if 'lease_id' in self.env.context:
            res['lease_id'] = self.env.context.get('lease_id')
        return res

    def confirm(self):
        print("type",self.lease)
        if self.type_id == 'pr':
            print(self.request_id)
            if self.user_ids.id in self.request_id.next_approve_user_id.ids:
                for lines in self.request_id.pr_approve_line:
                    if lines.user_id.id == self.user_ids.id:

                        if lines.status == 'draft':
                            for lines in self.request_id.pr_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.product_request_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.product_request_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],
                                        'next_approve_user_id': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                    })

                                    # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                    for rec in lines.product_request_id.approve_users:
                                        print(rec.name)

                                    new_line_vals = {
                                        'user_id': self.deligate_user.id,
                                        # 'company_id': 'value2',
                                        # 'location': 'value2',
                                        # 'department_id': 'value2',
                                        # 'designation': 'value2',
                                        'approve_order': lines.approve_order,
                                    }
                                    self.request_id.pr_approve_line |= self.env['pr.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.request_id.message_post(body=message)
                            self.request_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'pr_id': self.request_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.save'].create(vals)

                            model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')],

                                                                       limit=1)  # closing pending

                            pending_action = self.env['pending.actions'].sudo().search(

                                [('model', '=', model.id), ('record', '=', self.request_id.id),
                                 ('status', '=', 'open')])

                            for rec in pending_action:
                                if self.user_ids in rec.approve_users:
                                    rec.status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Request')],

                                limit=1)

                            activity = self.env['mail.activity'].sudo().search(
                                [('res_model_id', '=', self.env['ir.model'].sudo().search(
                                    [('model', '=', 'product.request')]).id),

                                 ('user_id', '=', self.user_ids.id),
                                 ('res_name', '=', self.request_id.name),

                                 ('activity_type_id', '=', activity_type.id),

                                 ], limit=1)

                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")

                            # Opening Pending

                            pending_vals = {

                                'model': model.id,

                                'name': self.request_id.name + " " + "Delegated Purchase Request",

                                'record': self.request_id.id,

                                'branch': self.request_id.bill_to.id,

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

                                'id': self.request_id.id,

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

                                f"Dear User,A Purchase request {self.request_id.name} is waiting for Approval.<br><br>"

                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "

                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "

                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            )

                            if self.deligate_user.login:
                                subject = "Purchase Request Delegated and Waiting For APPROVAL: %s" % self.request_id.name

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

                                [('model', '=', 'product.request')]).id

                            if self.deligate_user:
                                activity_values = {

                                    'user_id': self.deligate_user.id,

                                    'res_id': self.request_id.id,

                                    'note': "Pending Action",

                                    'summary': "Action",

                                    'activity_type_id': activity_type_id,

                                    'res_model_id': res_model_id,

                                }

                                created_activity = self.env['mail.activity'].create(activity_values)

                        else:
                            raise UserError("User has already delegated once")
            else:
                for lines in self.request_id.pr_approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.request_id.pr_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.product_request_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.product_request_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],

                                    })

                                    # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                    for rec in lines.product_request_id.approve_users:
                                        print(rec.name)

                                    new_line_vals = {
                                        'user_id': self.deligate_user.id,
                                        # 'company_id': 'value2',
                                        # 'location': 'value2',
                                        # 'department_id': 'value2',
                                        # 'designation': 'value2',
                                        'approve_order': lines.approve_order,
                                    }
                                    self.request_id.pr_approve_line |= self.env['pr.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.request_id.message_post(body=message)
                            self.request_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'pr_id': self.request_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.save'].create(vals)
                        else:
                            raise UserError("User has already delegated once")

        if self.type_id == 'cr':
            if self.user_ids.id in self.request_id.next_approve_user_id_cr.ids:
                for lines in self.request_id.cr_need_approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.request_id.cr_need_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.product_request_id.write({
                                        'approved_users_cr': [(4, lines.user_id.id)]
                                    })
                                    lines.product_request_id.write({
                                        'approve_users_cr': [(4, self.deligate_user.id)],
                                        'next_approve_user_id_cr': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                    })

                                    # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                    for rec in lines.product_request_id.approve_users_cr:
                                        print(rec.name)

                                    new_line_vals = {
                                        'user_id': self.deligate_user.id,
                                        # 'company_id': 'value2',
                                        # 'location': 'value2',
                                        # 'department_id': 'value2',
                                        # 'designation': 'value2',
                                        'approve_order': lines.approve_order,
                                    }
                                    self.request_id.cr_need_approve_line |= self.env['cr.need.approve.line'].create(
                                        new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.request_id.message_post(body=message)
                            self.request_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'pr_id': self.request_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.save'].create(vals)

                            model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')],

                                                                       limit=1)  # closing pending

                            pending_action = self.env['pending.actions'].sudo().search(

                                [('model', '=', model.id), ('record', '=', self.request_id.id),
                                 ('status', '=', 'open')])

                            for rec in pending_action:
                                if self.user_ids in rec.approve_users:
                                    print("record to close", rec)
                                    rec.status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Request')],

                                limit=1)

                            activity = self.env['mail.activity'].sudo().search(
                                [('res_model_id', '=', self.env['ir.model'].sudo().search(
                                    [('model', '=', 'product.request')]).id),

                                 ('user_id', '=', self.user_ids.id),
                                 ('res_name', '=', self.request_id.name),

                                 ('activity_type_id', '=', activity_type.id),

                                 ], limit=1)

                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")

                            # Opening Pending

                            pending_vals = {

                                'model': model.id,

                                'name': self.request_id.name + " " + "Delegated Purchase Request",

                                'record': self.request_id.id,

                                'branch': self.request_id.bill_to.id,

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

                                'id': self.request_id.id,

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

                                f"Dear User,A Purchase request {self.request_id.name} is waiting for Approval.<br><br>"

                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "

                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "

                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            )

                            if self.deligate_user.login:
                                subject = "Purchase Request Delegated and Waiting For APPROVAL: %s" % self.request_id.name

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

                                [('model', '=', 'product.request')]).id

                            if self.deligate_user:
                                activity_values = {

                                    'user_id': self.deligate_user.id,

                                    'res_id': self.request_id.id,

                                    'note': "Pending Action",

                                    'summary': "Action",

                                    'activity_type_id': activity_type_id,

                                    'res_model_id': res_model_id,

                                }

                                created_activity = self.env['mail.activity'].create(activity_values)

                        else:
                            raise UserError("User has already delegated once")
            else:
                for lines in self.request_id.cr_need_approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.request_id.cr_need_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.product_request_id.write({
                                        'approved_users_cr': [(4, lines.user_id.id)]
                                    })
                                    lines.product_request_id.write({
                                        'approve_users_cr': [(4, self.deligate_user.id)],

                                    })

                                    # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                    for rec in lines.product_request_id.approve_users_cr:
                                        print(rec.name)

                                    new_line_vals = {
                                        'user_id': self.deligate_user.id,
                                        # 'company_id': 'value2',
                                        # 'location': 'value2',
                                        # 'department_id': 'value2',
                                        # 'designation': 'value2',
                                        'approve_order': lines.approve_order,
                                    }
                                    self.request_id.cr_need_approve_line |= self.env['cr.need.approve.line'].create(
                                        new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.request_id.message_post(body=message)
                            self.request_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'pr_id': self.request_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.save'].create(vals)
                        else:
                            raise UserError("User has already delegated once")
        if self.type_id == 'tn':
            if self.user_ids.id in self.request_contract_id.next_approve_user_id.ids:
                for lines in self.request_contract_id.tender_approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.request_contract_id.tender_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.tender_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
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
                                    self.request_contract_id.tender_approve_line |= self.env[
                                        'tender.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.tender_id.deligated_user = self.deligate_user.id

                            
                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.request_contract_id.message_post(body=message)
                            self.request_contract_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'cr_id': self.request_contract_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.save.cr'].create(vals)

                            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')],

                                                                       limit=1)  # closing pending

                            pending_action = self.env['pending.actions'].sudo().search(

                                [('model', '=', model.id), ('record', '=', self.request_contract_id.id),
                                 ('status', '=', 'open')])

                            for rec in pending_action:
                                if self.user_ids in rec.approve_users:
                                    rec.status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Request')],

                                limit=1)

                            activity = self.env['mail.activity'].sudo().search(
                                [('res_model_id', '=', self.env['ir.model'].sudo().search(
                                    [('model', '=', 'tenders')]).id),

                                 ('user_id', '=', self.user_ids.id),
                                 ('res_name', '=', self.request_contract_id.name),

                                 ('activity_type_id', '=', activity_type.id),

                                 ], limit=1)

                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")

                            # Opening Pending

                            pending_vals = {

                                'model': model.id,

                                'name': self.request_contract_id.name + " " + "Delegated Contract Request",

                                'record': self.request_contract_id.id,

                                'branch': self.request_contract_id.branch_ids[
                                    0].id if self.request_contract_id.branch_ids else False,

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

                                [('name', '=', 'Contract Request')], limit=1) or False

                            url_params = {

                                'id': self.request_contract_id.id,

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

                                f"Dear User,A Contract request {self.request_contract_id.name} is waiting for Approval.<br><br>"

                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "

                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "

                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            )

                            if self.deligate_user.login:
                                subject = "Contract Request Delegated and Waiting For APPROVAL: %s" % self.request_contract_id.name

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

                                    'res_id': self.request_contract_id.id,

                                    'note': "Pending Action",

                                    'summary': "Action",

                                    'activity_type_id': activity_type_id,

                                    'res_model_id': res_model_id,

                                }

                                created_activity = self.env['mail.activity'].create(activity_values)

                        else:
                            raise UserError("User has already delegated once")
            else:
                for lines in self.request_contract_id.tender_approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.request_contract_id.tender_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.tender_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.tender_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],

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
                                    self.request_contract_id.tender_approve_line |= self.env[
                                        'tender.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.tender_id.deligated_user = self.deligate_user.id

                            
                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.request_contract_id.message_post(body=message)
                            self.request_contract_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'cr_id': self.request_contract_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.save.cr'].sudo().create(vals)
                        else:
                            raise UserError("User has already delegated once")

        if self.type_id == 'po':
            if self.user_ids.id in self.po_id.next_approve_user.ids:
                for lines in self.po_id.approvers_line_ids:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.po_id.approvers_line_ids:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.po_approve_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.po_approve_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],
                                        'next_approve_user': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                    })

                                    # lines.product_request_id.next_approve_user_id = self.deligate_user.id
                                    for rec in lines.po_approve_id.approve_users:
                                        print("last", rec.name)

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
                                    lines.status = 'deligate'
                                    # lines.po_approve_id.deligated_user = self.deligate_user.id

                            
                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.po_id.message_post(body=message)
                            self.po_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'po_id': self.po_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.po.save'].sudo().create(vals)

                            model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')],

                                                                       limit=1)  # closing pending

                            pending_action = self.env['pending.actions'].sudo().search(

                                [('model', '=', model.id), ('record', '=', self.po_id.id),
                                 ('status', '=', 'open')])

                            for rec in pending_action:
                                if self.user_ids in rec.approve_users:
                                    print("record to close", rec)
                                    rec.status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Purchase Order')],

                                limit=1)

                            activity = self.env['mail.activity'].sudo().search(
                                [('res_model_id', '=', self.env['ir.model'].sudo().search(
                                    [('model', '=', 'purchase.order')]).id),

                                 ('user_id', '=', self.user_ids.id),
                                 ('res_name', '=', self.po_id.name),

                                 ('activity_type_id', '=', activity_type.id),

                                 ], limit=1)

                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")

                            # Opening Pending

                            pending_vals = {

                                'model': model.id,

                                'name': self.po_id.name + " " + "Deligated Purchase Request",

                                'record': self.po_id.id,

                                'branch': self.po_id.bill_to.id,

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

                                [('name', '=', 'Pending Actions')], limit=1) or False

                            url_params = {

                                'id': self.po_id.id,

                                'action': self.env.ref('pending_actions.action_pending_actions').id,

                                'model': 'purchase.order',

                                'view_type': 'form',

                                # 'menu_id': self.env.ref('product_purchase.product_purchase').id,

                                'menu_id': menu_id.id,

                            }

                            params = '/web?#%s' % url_encode(url_params)

                            view_url = base_url + params if base_url else "#"

                            author = self.env['res.partner'].sudo().search(

                                [('name', '=', 'Administrator')], limit=1) or False

                            body = (

                                f"Dear User,A PurchaseOrder {self.po_id.name} is waiting for Approval.<br><br>"

                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "

                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "

                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            )

                            if self.deligate_user.login:
                                subject = "Purchase order Delegated and Waiting For APPROVAL: %s" % self.request_id.name

                                mail_values = {

                                    'subject': subject,

                                    'body_html': body,

                                    'email_to': self.deligate_user.login,

                                    'auto_delete': False,

                                    'author_id': author.id

                                }

                                mail_record = self.env['mail.mail'].sudo().create(mail_values)

                            activity_type = self.env['mail.activity.type'].sudo().search(

                                [('name', '=', 'Pending Purchase Order')], limit=1)

                            activity_type_id = activity_type.id if activity_type else False

                            res_model_id = self.env['ir.model'].sudo().search(

                                [('model', '=', 'purchase.order')]).id

                            if self.deligate_user:
                                activity_values = {

                                    'user_id': self.deligate_user.id,

                                    'res_id': self.po_id.id,

                                    'note': "Pending Action",

                                    'summary': "Action",

                                    'activity_type_id': activity_type_id,

                                    'res_model_id': res_model_id,

                                }

                                created_activity = self.env['mail.activity'].create(activity_values)

                        else:
                            raise UserError("User has already delegated once")
            else:
                for lines in self.po_id.approvers_line_ids:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.po_id.approvers_line_ids:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.po_approve_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.po_approve_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],

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
                                    lines.status = 'deligate'
                                    # lines.po_approve_id.deligated_user = self.deligate_user.id

                            
                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.po_id.message_post(body=message)
                            self.po_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'po_id': self.po_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.po.save'].create(vals)
                        else:
                            raise UserError("User has already delegated once")

        if self.type_id == 'lease':
            for record in self:
                if record.lease:
                    lease_num = self.env['product.lease'].search([('id', '=', record.lease)], limit=1)
                    lease_id = lease_num
                    print("the record lease", lease_id)
                else:
                    lease_id = False
            print("lease",lease_id)
            if self.user_ids.id in lease_id.next_approve_user.ids:
                print("test",lease_id.next_approve_user.ids)
                for lines in lease_id.approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            print("in draft")
                            for lines in lease_id.approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.approve_lease_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.approve_lease_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],
                                        'next_approve_user': [(4, self.deligate_user.id), (3, lines.user_id.id)]
                                    })

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
                                    lease_id.approve_line |= self.env['lease.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.approve_lease_id.deligated_user = self.deligate_user.id

                            
                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            lease_id.message_post(body=message)
                            lease_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'lease_id': lease_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            print("get vals",vals)
                            remarks_save = self.env['remark.lease.save'].create(vals)

                            model = self.env['ir.model'].sudo().search([('model', '=', 'product.lease')],

                                                                       limit=1)  # closing pending

                            pending_action = self.env['pending.actions'].sudo().search(

                                [('model', '=', model.id), ('record', '=', lease_id.id),
                                 ('status', '=', 'open')])

                            for rec in pending_action:
                                if self.user_ids in rec.approve_users:
                                    rec.status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Request')],

                                limit=1)

                            activity = self.env['mail.activity'].sudo().search(
                                [('res_model_id', '=', self.env['ir.model'].sudo().search(
                                    [('model', '=', 'product.lease')]).id),

                                 ('user_id', '=', self.user_ids.id),
                                 ('res_name', '=', lease_id.name),

                                 ('activity_type_id', '=', activity_type.id),

                                 ], limit=1)

                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")

                            # Opening Pending

                            pending_vals = {

                                'model': model.id,

                                'name': lease_id.name + " " + "Delegated Lease Request",

                                'record': lease_id.id,

                                'branch': lease_id.bill_to.id,

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

                                [('name', '=', 'Lease/Rent')], limit=1) or False

                            url_params = {

                                'id': lease_id.id,

                                'action': self.env.ref('lease_management.action_product_lease').id,

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

                                f"Dear User,A Lease request {lease_id.name} is waiting for Approval.<br><br>"

                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "

                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "

                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            )

                            if self.deligate_user.login:
                                subject = "Lease Request Delegated and Waiting For APPROVAL: %s" % self.request_id.name

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

                                [('model', '=', 'product.lease')]).id

                            if self.deligate_user:
                                activity_values = {

                                    'user_id': self.deligate_user.id,

                                    'res_id': lease_id.id,

                                    'note': "Pending Action",

                                    'summary': "Action",

                                    'activity_type_id': activity_type_id,

                                    'res_model_id': res_model_id,

                                }

                                created_activity = self.env['mail.activity'].create(activity_values)

                        else:
                            raise UserError("User has already delegated once")
            else:
                for lines in lease_id.approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in lease_id.approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.approve_lease_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.approve_lease_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],

                                    })

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
                                    lease_id.approve_line |= self.env['lease.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.approve_lease_id.deligated_user = self.deligate_user.id

                            
                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.lease_id.message_post(body=message)
                            self.lease_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'lease_id': lease_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.lease.save'].create(vals)
                        else:
                            raise UserError("User has already delegated once")


        if self.type_id == 'inva':
            print(self.invoice_id)
            if self.user_ids.id in self.invoice_id.next_approve_user.ids:
                for lines in self.invoice_id.invoice_approve_line:
                    if lines.user_id.id == self.user_ids.id:

                        if lines.status == 'draft':
                            for lines in self.invoice_id.invoice_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.invoice_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
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
                                    self.invoice_id.invoice_approve_line |= self.env['invoice.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.invoice_id.message_post(body=message)
                            self.invoice_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'invoice_id': self.invoice_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.invoice.save'].create(vals)

                            model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')],

                                                                       limit=1)  # closing pending

                            pending_action = self.env['pending.actions'].sudo().search(

                                [('model', '=', model.id), ('record', '=', self.invoice_id.id),
                                 ('status', '=', 'open')])

                            for rec in pending_action:
                                if self.user_ids in rec.approve_users:
                                    rec.status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Request')],

                                limit=1)

                            activity = self.env['mail.activity'].sudo().search(
                                [('res_model_id', '=', self.env['ir.model'].sudo().search(
                                    [('model', '=', 'account.move')]).id),
                                 ('res_id', '=', self.invoice_id.id),

                                 ('user_id', '=', self.user_ids.id),
                                 # ('res_name', '=', self.invoice_id.name),

                                 ('activity_type_id', '=', activity_type.id),

                                 ], limit=1)

                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")

                            # Opening Pending

                            pending_vals = {

                                'model': model.id,

                                'name': self.invoice_id.name + " " +self.invoice_id.po_number.name+" " + "Delegated Invoice Request-Accounting",

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

                                'id': self.request_id.id,

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

                                f"Dear User,A Invoice request {self.invoice_id.name} is waiting for Approval.<br><br>"

                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "

                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "

                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            )

                            if self.deligate_user.login:
                                subject = "Invoice Request Delegated and Waiting For APPROVAL: %s" % self.invoice_id.name

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

                                [('model', '=', 'account.move')]).id

                            if self.deligate_user:
                                activity_values = {

                                    'user_id': self.deligate_user.id,

                                    'res_id': self.invoice_id.id,

                                    'note': "Pending Action",

                                    'summary': "Action",

                                    'activity_type_id': activity_type_id,

                                    'res_model_id': res_model_id,

                                }

                                created_activity = self.env['mail.activity'].create(activity_values)

                        else:
                            raise UserError("User has already delegated once")

            else:
                for lines in self.invoice_id.invoice_approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.invoice_id.invoice_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.invoice_id.write({
                                        'approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.invoice_id.write({
                                        'approve_users': [(4, self.deligate_user.id)],

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
                                    self.invoice_id.invoice_approve_line |= self.env['invoice.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.invoice_id.message_post(body=message)
                            self.invoice_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'invoice_id': self.invoice_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.invoice.save'].create(vals)
                        else:
                            raise UserError("User has already delegated once")

        if self.type_id == 'invf':
            print(self.invoice_id)
            if self.user_ids.id in self.invoice_id.payment_next_approve_user.ids:
                for lines in self.invoice_id.invoice_payment_approve_line:
                    if lines.user_id.id == self.user_ids.id:

                        if lines.status == 'draft':
                            for lines in self.invoice_id.invoice_payment_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.invoice_id.write({
                                        'payment_approved_users': [(4, lines.user_id.id)]
                                    })
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
                                    self.invoice_id.invoice_payment_approve_line |= self.env['invoice.payment.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.invoice_id.message_post(body=message)
                            self.invoice_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'invoice_id': self.invoice_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.invoice.save'].create(vals)

                            model = self.env['ir.model'].sudo().search([('model', '=', 'account.move')],

                                                                       limit=1)  # closing pending

                            pending_action = self.env['pending.actions'].sudo().search(

                                [('model', '=', model.id), ('record', '=', self.invoice_id.id),
                                 ('status', '=', 'open')])

                            for rec in pending_action:
                                if self.user_ids in rec.approve_users:
                                    rec.status = 'closed'

                            activity_type = self.env['mail.activity.type'].sudo().search(
                                [('name', '=', 'Pending Request')],

                                limit=1)

                            activity = self.env['mail.activity'].sudo().search(
                                [('res_model_id', '=', self.env['ir.model'].sudo().search(
                                    [('model', '=', 'account.move')]).id),
                                 ('res_id', '=', self.invoice_id.id),

                                 ('user_id', '=', self.user_ids.id),
                                 # ('res_name', '=', self.invoice_id.name),

                                 ('activity_type_id', '=', activity_type.id),

                                 ], limit=1)

                            if activity:
                                activity.action_feedback(feedback="Activity Delegated")

                            # Opening Pending

                            pending_vals = {

                                'model': model.id,

                                'name': self.invoice_id.name + " " +self.invoice_id.po_number.name+" " + "Delegated Invoice Request-Payment",

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

                                'id': self.request_id.id,

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

                                f"Dear User,A Invoice request {self.invoice_id.name} is waiting for Approval.<br><br>"

                                f"<a href='{view_url}' style='display: inline-block; padding: 10px 20px; "

                                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "

                                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                            )

                            if self.deligate_user.login:
                                subject = "Invoice Request Delegated and Waiting For APPROVAL: %s" % self.invoice_id.name

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

                                [('model', '=', 'account.move')]).id

                            if self.deligate_user:
                                activity_values = {

                                    'user_id': self.deligate_user.id,

                                    'res_id': self.invoice_id.id,

                                    'note': "Pending Action",

                                    'summary': "Action",

                                    'activity_type_id': activity_type_id,

                                    'res_model_id': res_model_id,

                                }

                                created_activity = self.env['mail.activity'].create(activity_values)

                        else:
                            raise UserError("User has already delegated once")

            else:
                for lines in self.invoice_id.invoice_payment_approve_line:
                    if lines.user_id.id == self.user_ids.id:
                        if lines.status == 'draft':
                            for lines in self.invoice_id.invoice_payment_approve_line:
                                if lines.user_id.id == self.user_ids.id:
                                    lines.invoice_id.write({
                                        'payment_approved_users': [(4, lines.user_id.id)]
                                    })
                                    lines.invoice_id.write({
                                        'payment_approve_users': [(4, self.deligate_user.id)],

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
                                    self.invoice_id.invoice_payment_approve_line |= self.env['invoice.payment.approve.line'].create(new_line_vals)
                                    lines.approve_order = ''
                                    lines.status = 'deligate'
                                    # lines.product_request_id.deligated_user = self.deligate_user.id

                            message = _("%s Delegated the User %s to %s.") % (self.env.user.name, self.user_ids.name, self.deligate_user.name)
                            self.invoice_id.message_post(body=message)
                            self.invoice_id.message_post(body="Remarks:" + " " + self.remark)
                            vals = {
                                'invoice_id': self.invoice_id.id,
                                'from_user': self.env.user.id,
                                'replay': self.remark,
                                'for_type': "Admin Delegation",
                                'approve_type': 'deligate',

                            }
                            remarks_save = self.env['remark.invoice.save'].create(vals)
                        else:
                            raise UserError("User has already delegated once")
