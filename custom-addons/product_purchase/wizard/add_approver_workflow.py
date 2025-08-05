from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date
from werkzeug.urls import url_encode


class AddApprover(models.TransientModel):
    _name = 'add.approver.wizard'
    _description = "Add Approver workflow"

    pr_id = fields.Many2one('product.request', string='Product Request Id',
                            invisible=True)
    cr_id = fields.Many2one('tenders', string='Contract Request Id',
                            invisible=True)
    pr_id_cr_need = fields.Many2one('product.request', string='Product Request Id',
                            invisible=True)
    po_id = fields.Many2one('purchase.order', string='Purchase Order Id',
                            invisible=True)

    user = fields.Many2one('res.users',string= "User", required= True,domain="[('groups_id', 'not in', [44])]")
    order = fields.Integer(string="Order No",required = True)
    branch_id = fields.Many2one('res.branch', string="Default Branch", store=True, compute='_compute_branch_id')
    email = fields.Char(string='Email')
    admin_add = fields.Boolean(string="Is Admin")
    @api.onchange('user')
    def _compute_branch_id(self):
        for rec in self:
            rec.branch_id = rec.user.branch_id.id
            rec.email = rec.user.login

    def add_user(self):
        if self.pr_id:
            if not self.admin_add:
                for line in self.pr_id.pr_approve_line:
                    if line.user_id == self.env.user :
                        current_order = line.approve_order
            else:
                approve_dict={}
                for line in self.pr_id.pr_approve_line:
                    approve_dict[line.approve_order] = line.status
                sorted_approve_dict = {k: v for k, v in sorted(approve_dict.items(), key=lambda item: item[1])}
                first_draft_approve_order = None
                print("sorted",sorted_approve_dict,approve_dict)
                for approve_order , status in sorted_approve_dict.items():
                    if status == 'draft':
                        print("working",approve_order)
                        first_draft_approve_order = approve_order
                        break  # Exit loop as soon as the first draft is found
                if first_draft_approve_order is None:
                    raise ValidationError("No Pending status found in the Approve Users.")
                # for line in self.pr_id.pr_approve_line:
                #     if line.approve_order == first_draft_approve_order:
                #         user_id = line.user_id
                current_order = first_draft_approve_order
            print("current",current_order)
            records = self.env['pr.approve.line'].sudo().search([('product_request_id', '=', self.pr_id.id)])
            highest_record = max(records, key=lambda r: r.approve_order)
            highest_approve_order = highest_record.approve_order
            if current_order < self.order and self.order <= highest_approve_order+1:
                if self.user in self.pr_id.approve_users:
                    raise UserError(_("This user is already in the approval list."))
                self.pr_id.approve_users |= self.user

                model = self.env['pr.approve.line'].sudo().search([('product_request_id', '=', self.pr_id.id),('approve_order','>=',self.order)])
                for line in model:
                    line.approve_order += 1
                vals = {
                    'product_request_id': self.pr_id.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['pr.approve.line'].sudo().create(vals)
                self.pr_id.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")
            elif self.order == current_order:
                if self.user in self.pr_id.approve_users:
                    raise UserError(_("This user is already in the approval list."))
                self.pr_id.approve_users |= self.user
                model = self.env['pr.approve.line'].sudo().search(
                    [('product_request_id', '=', self.pr_id.id), ('approve_order', '>=', self.order),('status','in',('draft','deligate'))])
                self.pr_id.write({'next_approve_user_id': [(6, 0, [self.user.id])]})

                for line in model:
                    print("users",line.user_id.name)
                    line.approve_order += 1
                vals = {
                    'product_request_id': self.pr_id.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['pr.approve.line'].sudo().create(vals)
                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                    ('res_name', '=', self.pr_id.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback=f"User Added at {self.order} position")
                model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.pr_id.id), ('status', '=', 'open')])
                if pending_action:
                    for pending in pending_action:
                        pending.status = 'closed'


                pending_vals = {
                    'model': model.id,
                    'name': self.pr_id.name + " " + "Purchase Request Waiting For Approval",
                    'record': self.pr_id.id,
                    'branch': self.pr_id.bill_to.id,
                    'date': date.today(),
                }
                print("user", self.user, "next", self.pr_id.next_approve_user_id)
                if self.user:
                    print("workkkkkkkkkkk")
                    user_ids_to_pass = self.user.ids
                    pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                    pendings = self.env['pending.actions'].create(pending_vals)
                    print("Pendinggg", pendings)
                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')],
                        limit=1)
                    activity_type_id = activity_type.id if activity_type else False
                    res_model_id = self.env['ir.model'].sudo().search(
                        [('model', '=', 'product.request')]).id
                    for user_id in user_ids_to_pass:
                        activity_values = {
                            'user_id': user_id,
                            'res_id': self.pr_id.id,
                            'note': "Pending Action",
                            'summary': "Action",
                            'activity_type_id': activity_type_id,
                            'res_model_id': res_model_id,
                        }
                        created_activity = self.env['mail.activity'].create(activity_values)
                    subject = "Purchase Request Waiting For APPROVAL: %s" % self.pr_id.name

                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Purchase Request')], limit=1) or False

                    url_params = {
                        'id': self.pr_id.id,
                        'action': self.env.ref('product_purchase.action_product_requests').id,
                        'model': 'product.request',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    print(url)

                    author = self.env['res.partner'].sudo().search(
                        [('name', '=', 'Administrator')], limit=1)

                    body = (
                        f"Dear User, "
                        f"A new Purchase Request with the name <strong>{self.pr_id.name} is waiting for Approval.<br>"
                        f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                        f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                    )


                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': self.user.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                self.pr_id.message_post(body=f" {self.env.user.name} Added User {self.user.name} at position {self.order}.")
            elif self.order > highest_approve_order+1 :
                raise UserError(_("Order No cannot be exceeded than existing max order No "))
            else:
                raise UserError(_("Order No cannot be less than to your Order No"))

        if self.cr_id:
            if not self.admin_add:
                for line in self.cr_id.tender_approve_line:
                    if line.user_id == self.env.user :
                        current_order = line.approve_order
            else:
                approve_dict={}
                for line in self.cr_id.tender_approve_line:
                    approve_dict[line.approve_order] = line.status
                sorted_approve_dict = {k: v for k, v in sorted(approve_dict.items(), key=lambda item: item[1])}
                first_draft_approve_order = None
                print("sorted",sorted_approve_dict,approve_dict)
                for approve_order , status in sorted_approve_dict.items():
                    if status == 'draft':
                        print("working",approve_order)
                        first_draft_approve_order = approve_order
                        break  # Exit loop as soon as the first draft is found
                if first_draft_approve_order is None:
                    raise ValidationError("No Pending status found in the Approve Users.")
                # for line in self.pr_id.pr_approve_line:
                #     if line.approve_order == first_draft_approve_order:
                #         user_id = line.user_id
                current_order = first_draft_approve_order

            records = self.env['tender.approve.line'].sudo().search([('tender_id', '=', self.cr_id.id)])
            highest_record = max(records, key=lambda r: r.approve_order)
            highest_approve_order = highest_record.approve_order
            if current_order < self.order and self.order <= highest_approve_order + 1:
                if self.user in self.cr_id.approve_users:
                    raise UserError(_("This user is already in the approval list."))
                self.cr_id.approve_users |= self.user

                model = self.env['tender.approve.line'].sudo().search(
                    [('tender_id', '=', self.cr_id.id), ('approve_order', '>=', self.order)])
                for line in model:
                    line.approve_order += 1
                vals = {
                    'tender_id': self.cr_id.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['tender.approve.line'].sudo().create(vals)
                self.cr_id.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")
            elif self.order == current_order:
                if self.user in self.cr_id.approve_users:
                    raise UserError(_("This user is already in the approval list."))
                self.cr_id.approve_users |= self.user
                model = self.env['tender.approve.line'].sudo().search(
                    [('tender_id', '=', self.cr_id.id), ('approve_order', '>=', self.order),('status','in',('draft','deligate'))])
                self.cr_id.write({'next_approve_user_id': [(6, 0, [self.user.id])]})

                for line in model:
                    print("users",line.user_id.name)
                    line.approve_order += 1
                vals = {
                    'tender_id': self.cr_id.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['tender.approve.line'].sudo().create(vals)
                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'tenders')]).id),
                    ('res_name', '=', self.cr_id.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback=f"User Added at {self.order} position")
                model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.cr_id.id), ('status', '=', 'open')])
                if pending_action:
                    for pending in pending_action:
                        pending.status = 'closed'


                pending_vals = {
                    'model': model.id,
                    'name': self.cr_id.name + " " + "Contract Request Waiting For Approval",
                    'record': self.cr_id.id,
                    'branch': self.cr_id.branch_ids[0].id,
                    'date': date.today(),
                }
                print("user", self.user, "next", self.cr_id.next_approve_user_id)
                if self.user:
                    print("workkkkkkkkkkk")
                    user_ids_to_pass = self.user.ids
                    pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                    pendings = self.env['pending.actions'].create(pending_vals)
                    print("Pendinggg", pendings)
                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')],
                        limit=1)
                    activity_type_id = activity_type.id if activity_type else False
                    res_model_id = self.env['ir.model'].sudo().search(
                        [('model', '=', 'tenders')]).id
                    for user_id in user_ids_to_pass:
                        activity_values = {
                            'user_id': user_id,
                            'res_id': self.cr_id.id,
                            'note': "Pending Action",
                            'summary': "Action",
                            'activity_type_id': activity_type_id,
                            'res_model_id': res_model_id,
                        }
                        created_activity = self.env['mail.activity'].create(activity_values)

                self.cr_id.message_post(body=f" {self.env.user.name} Added User {self.user.name} at position {self.order}.")
            elif self.order > highest_approve_order+1 :
                raise UserError(_("Order No cannot be exceeded than existing max order No "))

            else:
                raise UserError(_("Order cannot be less than to your Order No"))

        if self.pr_id_cr_need:
            if not self.admin_add:
                for line in self.pr_id_cr_need.cr_need_approve_line:
                    if line.user_id == self.env.user :
                        current_order = line.approve_order
            else:
                approve_dict={}
                for line in self.pr_id_cr_need.cr_need_approve_line:
                    approve_dict[line.approve_order] = line.status
                sorted_approve_dict = {k: v for k, v in sorted(approve_dict.items(), key=lambda item: item[1])}
                first_draft_approve_order = None
                print("sorted",sorted_approve_dict,approve_dict)
                for approve_order , status in sorted_approve_dict.items():
                    if status == 'draft':
                        print("working",approve_order)
                        first_draft_approve_order = approve_order
                        break  # Exit loop as soon as the first draft is found
                if first_draft_approve_order is None:
                    raise ValidationError("No Pending status found in the Approve Users.")
                # for line in self.pr_id.pr_approve_line:
                #     if line.approve_order == first_draft_approve_order:
                #         user_id = line.user_id
                current_order = first_draft_approve_order

            records = self.env['cr.need.approve.line'].sudo().search([('product_request_id', '=', self.pr_id_cr_need.id)])
            highest_record = max(records, key=lambda r: r.approve_order)
            highest_approve_order = highest_record.approve_order
            if current_order < self.order and self.order <= highest_approve_order+1:
                if self.user in self.pr_id_cr_need.approve_users_cr:
                    raise UserError(_("This user is already in the approval list."))
                self.pr_id_cr_need.approve_users_cr |= self.user

                model = self.env['cr.need.approve.line'].sudo().search([('product_request_id', '=', self.pr_id_cr_need.id),('approve_order','>=',self.order)])
                for line in model:
                    line.approve_order += 1
                vals = {
                    'product_request_id': self.pr_id_cr_need.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['cr.need.approve.line'].sudo().create(vals)
                self.pr_id_cr_need.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")
            elif self.order == current_order:
                if self.user in self.pr_id_cr_need.approve_users_cr:
                    raise UserError(_("This user is already in the approval list."))
                self.pr_id_cr_need.approve_users_cr |= self.user
                model = self.env['cr.need.approve.line'].sudo().search(
                    [('product_request_id', '=', self.pr_id_cr_need.id), ('approve_order', '>=', self.order),('status','in',('draft','deligate'))])
                self.pr_id_cr_need.write({'next_approve_user_id_cr': [(6, 0, [self.user.id])]})

                for line in model:
                    print("users",line.user_id.name)
                    line.approve_order += 1
                vals = {
                    'product_request_id': self.pr_id_cr_need.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['cr.need.approve.line'].sudo().create(vals)
                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Request')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'product.request')]).id),
                    ('res_name', '=', self.pr_id_cr_need.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback=f"User Added at {self.order} position")
                model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.pr_id_cr_need.id), ('status', '=', 'open')])
                if pending_action:
                    for pending in pending_action:
                        pending.status = 'closed'


                pending_vals = {
                    'model': model.id,
                    'name': self.pr_id_cr_need.name + " " + "Purchase Request Waiting For Approval",
                    'record': self.pr_id_cr_need.id,
                    'branch': self.pr_id_cr_need.bill_to.id,
                    'date': date.today(),
                }
                print("user", self.user, "next", self.pr_id_cr_need.next_approve_user_id_cr)
                if self.user:
                    print("workkkkkkkkkkk")
                    user_ids_to_pass = self.user.ids
                    pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                    pendings = self.env['pending.actions'].create(pending_vals)
                    print("Pendinggg", pendings)
                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')],
                        limit=1)
                    activity_type_id = activity_type.id if activity_type else False
                    res_model_id = self.env['ir.model'].sudo().search(
                        [('model', '=', 'product.request')]).id
                    for user_id in user_ids_to_pass:
                        activity_values = {
                            'user_id': user_id,
                            'res_id': self.pr_id_cr_need.id,
                            'note': "Pending Action",
                            'summary': "Action",
                            'activity_type_id': activity_type_id,
                            'res_model_id': res_model_id,
                        }
                        created_activity = self.env['mail.activity'].create(activity_values)
                self.pr_id_cr_need.message_post(body=f" {self.env.user.name} Added User {self.user.name} at position {self.order}.")
            elif self.order > highest_approve_order+1 :
                raise UserError(_("Order No cannot be exceeded than existing max order No "))
            else:
                raise UserError(_("Order No cannot be less than to your Order No"))

        if self.po_id:
            if not self.admin_add:
                for line in self.po_id.approvers_line_ids:
                    if line.user_id == self.env.user :
                        current_order = line.approve_order
            else:
                approve_dict={}
                for line in self.po_id.approvers_line_ids:
                    approve_dict[line.approve_order] = line.status
                sorted_approve_dict = {k: v for k, v in sorted(approve_dict.items(), key=lambda item: item[1])}
                first_draft_approve_order = None
                print("sorted",sorted_approve_dict,approve_dict)
                for approve_order , status in sorted_approve_dict.items():
                    if status == 'draft':
                        print("working",approve_order)
                        first_draft_approve_order = approve_order
                        break  # Exit loop as soon as the first draft is found
                if first_draft_approve_order is None:
                    raise ValidationError("No Pending status found in the Approve Users.")
                # for line in self.pr_id.pr_approve_line:
                #     if line.approve_order == first_draft_approve_order:
                #         user_id = line.user_id
                current_order = first_draft_approve_order

            records = self.env['po.approve.line'].sudo().search([('po_approve_id', '=', self.po_id.id)])
            highest_record = max(records, key=lambda r: r.approve_order)
            highest_approve_order = highest_record.approve_order
            if current_order < self.order and self.order <= highest_approve_order+1:
                if self.user in self.po_id.approve_users:
                    raise UserError(_("This user is already in the approval list."))
                self.po_id.approve_users |= self.user

                model = self.env['po.approve.line'].sudo().search([('po_approve_id', '=', self.po_id.id),('approve_order','>=',self.order),('status','in',('draft','deligate'))])
                for line in model:
                    line.approve_order += 1
                vals = {
                    'po_approve_id': self.po_id.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['po.approve.line'].sudo().create(vals)
                self.po_id.message_post(body=f" {self.env.user.name} Added User {self.user.name}.")
            elif self.order == current_order:
                if self.user in self.po_id.approve_users:
                    raise UserError(_("This user is already in the approval list."))
                self.po_id.approve_users |= self.user
                model = self.env['po.approve.line'].sudo().search(
                    [('po_approve_id', '=', self.po_id.id), ('approve_order', '>=', self.order)])
                self.po_id.write({'next_approve_user': [(6, 0, [self.user.id])]})

                for line in model:
                    print("users",line.user_id.name)
                    line.approve_order += 1
                vals = {
                    'po_approve_id': self.po_id.id,
                    'user_id': self.user.id,
                    'approve_order': self.order,
                    'status': 'draft'
                }
                approve_line = self.env['po.approve.line'].sudo().create(vals)
                activity_type = self.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Pending Action')], limit=1)
                activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
                    ('res_name', '=', self.po_id.name),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if activity:
                    for rec in activity:
                        rec.action_feedback(feedback=f"User Added at {self.order} position")
                model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.po_id.id), ('status', '=', 'open')])
                if pending_action:
                    for pending in pending_action:
                        pending.status = 'closed'


                pending_vals = {
                    'model': model.id,
                    'name': self.po_id.name + " " + "Purchase Request Waiting For Approval",
                    'record': self.po_id.id,
                    'branch': self.po_id.bill_to.id,
                    'date': date.today(),
                }
                print("user", self.user, "next", self.po_id.next_approve_user)
                if self.user:
                    print("workkkkkkkkkkk")
                    user_ids_to_pass = self.user.ids
                    pending_vals['approve_users'] = [(6, 0, user_ids_to_pass)]
                    pendings = self.env['pending.actions'].create(pending_vals)
                    print("Pendinggg", pendings)
                    activity_type = self.env['mail.activity.type'].sudo().search(
                        [('name', '=', 'Pending Request')],
                        limit=1)
                    activity_type_id = activity_type.id if activity_type else False
                    res_model_id = self.env['ir.model'].sudo().search(
                        [('model', '=', 'purchase.order')]).id
                    for user_id in user_ids_to_pass:
                        activity_values = {
                            'user_id': user_id,
                            'res_id': self.po_id.id,
                            'note': "Pending Action",
                            'summary': "Action",
                            'activity_type_id': activity_type_id,
                            'res_model_id': res_model_id,
                        }
                        created_activity = self.env['mail.activity'].create(activity_values)
                self.po_id.message_post(body=f" {self.env.user.name} Added User {self.user.name} at position {self.order}.")
            elif self.order > highest_approve_order+1 :
                raise UserError(_("Order No cannot be exceeded than existing max order No "))
            else:
                raise UserError(_("Order No cannot be less than or equal to your Order No"))