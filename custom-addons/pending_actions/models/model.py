from datetime import datetime
from datetime import date
from odoo import api, fields, models, _ , tools
from odoo.exceptions import ValidationError, MissingError, UserError
from werkzeug.urls import url_encode
import time


class PendingActions(models.Model):
    _name = "pending.actions"
    # _auto = False
    _description = "Pending Actions"
    _order = "custom_order desc, priority desc, id desc"

    date = fields.Date("Date")
    name = fields.Char("Name")
    status = fields.Selection(
        selection=[('open', 'Open'), ('closed', 'Closed')],
        string='Status',
        default='open',
        tracking=True
    )
    model = fields.Many2one("ir.model","Action Type")
    record = fields.Integer("Record ID")
    record_line = fields.Integer("Line Record")
    approve_users = fields.Many2many(
        'res.users',
        'rel_pending_approvers',
        'pending_id',
        'pending_users',
        string='Approve Users',
    )
    branch = fields.Many2one('res.branch', string="Branch")
    email_sent = fields.Boolean('Email Sent', default=False)
    exp_category = fields.Many2one('expense.category', 'Expense Category', required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    email = fields.Char(string="Email")
    Created_doc_date = fields.Date("Document Created Date")

    user = fields.Selection(
        selection=[('vendor', 'Vendor User'), ('employee', 'Employee User')],
        string='User'
    )

    custom_order = fields.Integer(compute="_compute_custom_order", store=True)
    priority = fields.Integer(string="Priority", default=10)

    @api.depends("name")
    def _compute_custom_order(self):
        for record in self:
            if record.name and "Waiting for Request for Information Reply" in record.name:
                record.custom_order = 0  # Higher priority, will be sorted to the top
            else:
                record.custom_order = 1  # Lower priority, will be sorted below

    @api.model
    def create(self, vals):
        if vals.get('name') == "Waiting for Request for Information Reply":
            vals['priority'] = 1  # Set priority to 1 for this specific name
        return super(PendingActions, self).create(vals)


    # def action_force_close(self):
    #     for rec in self:
    #         rec.status ='closed'


    def action_cancel_po(self):
        """Cancel all selected Purchase Order pending actions"""
        purchase_model = self.env.ref('purchase.model_purchase_order')  # Get the Purchase Order model
        print("the order is",purchase_model)

        for action in self:
            if action.model.id == purchase_model.id:
                print("the action",action.model.id,purchase_model.id)
                po = self.env['purchase.order'].browse(action.record).sudo()  # Use sudo() to bypass restrictions
                print("the purchase",po)

                if not po.exists():
                  
                    raise UserError(f"PO with ID {action.record} not found.")


                if po.state == 'draft':
                    po.button_cancel()
                elif po.state == 'to approve':
                    po.button_confirm()  # Confirm PO before canceling
                    po.button_cancel()
                elif po.state in ['purchase', 'done']:
                    raise UserError(f"PO {po.name} is in {po.state} state and cannot be canceled.")
                else:
                    po.button_cancel()

              

                # Mark Pending Action as Closed
                action.status = 'closed'



    def open_record(self):
        # model = self.model.model
        models = self.env['ir.model'].sudo().search([('id', '=',self.model.id)],limit=1)
        print(models)
        record = self.env[models.model].sudo().search([('id', '=', self.record)],limit=1)

        if record:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Record',
                'view_mode': 'form',
                'res_model': models.model,
                # 'domain': [('id', '=', self.record)],
                'target': 'current',
                'res_id': record.id,
            }

        else:
            raise UserError("No Document Found")

    @api.model
    def add_branches_to_approvers(self):

        approvers_user_group = self.env.ref('product_purchase.group_approvers')
        approvers_user = self.env['res.users'].search([('groups_id', 'in', approvers_user_group.id)])
        approvers_group  = self.env.ref(
            'vendor_portal.group_vendor_portal_user')
        approvers = self.env['res.users'].search([('groups_id', 'in', approvers_group.id)])

        # company_branches = self.env['res.branch'].search([])
        # allow_company = self.env['res.company'].search([('id', 'in', [2, 3, 4])])
        user_group3 = self.env.ref('account.group_account_invoice')
        user_group4 = self.env.ref('purchase.group_purchase_user')


        for approver in approvers:
            allow_company = approver.company_ids
            company_branches = self.env['res.branch'].search([('company_id', 'in',  allow_company.ids)])
           
            existing_branches = approver.branch_ids
            existing_companies = approver.company_ids

            new_branches = company_branches - existing_branches
            new_companies = allow_company - existing_companies

            if new_branches:
                approver.write({'branch_ids': [(4, branch.id) for branch in new_branches]})

            if new_companies:
                approver.write({'company_ids': [(4, company.id) for company in new_companies]})

            if user_group3 not in approver.groups_id:
                approver.write({'groups_id': [(4, user_group3.id)]})
            if user_group4 not in approver.groups_id:
                approver.write({'groups_id': [(4, user_group4.id)]})
        for approver in approvers_user:

            allow_company = approver.company_ids

            company_branches = self.env['res.branch'].search([('company_id', 'in', allow_company.ids)])

            existing_branches = approver.branch_ids
            existing_companies = approver.company_ids

            new_branches = company_branches - existing_branches
            new_companies = allow_company - existing_companies

            if new_branches:
                approver.write({'branch_ids': [(4, branch.id) for branch in new_branches]})

            if new_companies:
                approver.write({'company_ids': [(4, company.id) for company in new_companies]})

            if user_group3 not in approver.groups_id:
                approver.write({'groups_id': [(4, user_group3.id)]})

    def send_pending_actions_email(self):

        pending_actions = self.search([('status', '=', 'open')])
        if not pending_actions:
            return
        approve_users = pending_actions.mapped('approve_users')
        approve_users = list(set(approve_users))
        # last_sent_date = self.env['ir.config_parameter'].sudo().get_param('pending_actions.date')
        # last_sent_date = fields.Date.from_string(last_sent_date)
        today = datetime.now().date()
        print("the today os", today)

        batch_size = 5
        for i in range(0, len(approve_users), batch_size):
            batch_users = approve_users[i:i + batch_size]
            for user in batch_users:
                if user.email_date != today:

                    user_pending_actions = pending_actions.filtered(
                        lambda action: user in action.approve_users and action.exists()
                    )

                    subject = f"Pending Actions: {user.name}"
                    author = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')], limit=1)

                    body = (
                        f"Dear {user.name},<br><br>"
                        f"You have the following pending actions that need your attention:<br><br>"
                        f"<ul>"
                    )
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    menu_id = self.env['ir.ui.menu'].sudo().search(
                        [('name', '=', 'Pending Actions')], limit=1) or False

                    url_params = {
                        'id': user.id,
                        'action': self.env.ref('pending_actions.action_pending_actions').id,
                        'model': 'pending.actions',
                        'view_type': 'form',
                        'menu_id': menu_id.id if menu_id else False,
                    }

                    params = '/web?#%s' % url_encode(url_params)
                    url = base_url + params if base_url else "#"

                    for action in user_pending_actions:
                        action_date = action.date
                        pending_days = (datetime.now().date() - action_date).days
                        body += f"<li>{action.name} - Pending Action Date:{action.date} - Pending for {pending_days} days</li>"
                    body += (
                        f"</ul><br>"
                        f"Thank you!<br><br>"
                        f"<div style='padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; width: fit-content;'>"
                        f"<a href='{url}' style='background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                        f"font-size: 16px; padding: 10px; cursor: pointer; border-radius: 5px; display: inline-block;'>View Pending Actions</a>"
                        f"</div>"
                    )
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': user.login,
                        'auto_delete': False,

                        'author_id': author.id,
                    }
                    try:
                        mail_record = self.env['mail.mail'].sudo().create(mail_values)
                        check = mail_record.sudo().send()
                        self.env.cr.commit()

                        user.write({'email_date': today})
                        user_pending_actions.write({'email_sent': True})

                    except Exception as e:
                        print(f"Failed to send email to user {user.name}: {e}")

            print(f"Waiting for the next batch...")
            # self.env.cr.commit()
            time.sleep(15)


    def _send_pending_actions_email_initiator(self):
        

        pending_actions = self.search([('status', '=', 'open')])

        initiator_actions = {}
        today = datetime.now().date()

        for action in pending_actions:
       
            stage = ""
            initiator = None
            status = None  
            purchase = None  
            status_name = None
            approvers = [user.name for user in action.approve_users]

            if action.model.model == 'tenders':  # Contract Workflow
                contract_request = self.env['tenders'].browse(action.record)
                if contract_request.exists():
                    purchase = contract_request.product_requested_id or contract_request
                    initiator = contract_request.user_id
                    stage = "Contract Workflow"
                    status = contract_request.state

                    if status:
                        fields_info = self.env['tenders'].fields_get(allfields=['state'])
                        # print("the info",fields_info)
                        if 'state' in fields_info:
                            status_display_name = fields_info['state'].get('selection', [])
                            # print("the display",status_display_name)
                            status_name = dict(status_display_name).get(status, status).capitalize()

                        else:
                            # Handle missing 'status' gracefully
                            status_name = status


            elif action.model.model == 'product.request':  # Purchase Request Workflow
                purchase_request = self.env['product.request'].browse(action.record)
                if purchase_request.exists():
                    purchase = purchase_request
                    initiator = purchase_request.requested_by
                    stage = "Purchase request Workflow"
                    status = purchase_request.status
                    if status:
                        fields_info = self.env['product.request'].fields_get(allfields=['status'])
                        # print("the info",fields_info)
                        if 'state' in fields_info:
                            status_display_name = fields_info['status'].get('selection', [])
                            # print("the display",status_display_name)
                            status_name = dict(status_display_name).get(status, status).capitalize()

                        else:
                            # Handle missing 'status' gracefully
                            status_name = status

            elif action.model.model == 'purchase.order':  # Purchase Order Workflow (related to Purchase Request)
                purchase_order = self.env['purchase.order'].browse(action.record)
                if purchase_order.exists():
                    if purchase_order.pr_id:
                        purchase = purchase_order.pr_id
                        initiator = purchase_order.pr_id.requested_by
                        stage = "Purchase Order Workflow"
                        status = purchase_order.state

                        if status:
                            fields_info = self.env['purchase.order'].fields_get(allfields=['state'])
                            # print("the info",fields_info)
                            if 'state' in fields_info:
                                status_display_name = fields_info['state'].get('selection', [])
                                # print("the display",status_display_name)
                                status_name = dict(status_display_name).get(status, status).capitalize()

                            else:
                                # Handle missing 'status' gracefully
                                status_name = status


            elif action.model.model == 'account.move':  # Invoice Workflow
                invoice = self.env['account.move'].browse(action.record)
                if invoice.exists() and invoice.purchase_request:
                    purchase = invoice.purchase_request
                    initiator = invoice.purchase_request.requested_by
                    stage = "Invoice Workflow"
                    status = invoice.state
                    if status:
                        fields_info = self.env['account.move'].fields_get(allfields=['state'])
                        # print("the info",fields_info)
                        if 'state' in fields_info:
                            status_display_name = fields_info['state'].get('selection', [])
                            # print("the display",status_display_name)
                            status_name = dict(status_display_name).get(status, status).capitalize()

                        else:
                            # Handle missing 'status' gracefully
                            status_name = status

            # Group actions by initiator
            if initiator:
                if initiator not in initiator_actions:
                    initiator_actions[initiator] = []
                initiator_actions[initiator].append({
                    'purchase': purchase,
                    'stage': stage,
                    'status_name': status_name,
                    'approvers': ", ".join(approvers) if approvers else "N/A",
                })

      
        for initiator, actions in initiator_actions.items():
        
            email_body = f"Dear {initiator.name},<br><br>"
            email_body += "Here is the current status of your requests:<br><br>"

            for action_info in actions:
                purchase = action_info['purchase']
                stage = action_info['stage']
                status_name = action_info['status_name']
                approvers = action_info['approvers']
                email_body += (
                    f"- Your Request (ID: {purchase.name if purchase else 'N/A'}) "
                    f"is currently in the <strong>{status_name}</strong> state in {stage}.<br>"
                    f"The Approver Is: {approvers}<br><br>"
                )
            # print("the body is",email_body)
            # email_body += "Please take the necessary actions at your earliest convenience.\n\nBest regards,\nYour Team"

            subject = f"Pending Actions Report Mail To Initiator: {initiator.name}"
            author = self.env['res.partner'].sudo().search([('name', '=', 'Administrator')], limit=1)
            mail_values = {
                'subject': subject,
                'body_html': email_body,
                'email_to': initiator.login,
                'auto_delete': False,

                'author_id': author.id,
            }
            try:
                if initiator.pending_email_date != today:
                    initiator.write({'pending_email_date': today})
                    # print("mail is sended")
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                    check = mail_record.sudo().send()
                    # print("check", check)
                    self.env.cr.commit()


            except Exception as e:
                print(f"Failed to send email to user {initiator.name}: {e}")






    # @api.model_create_single
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'pending_actions')
    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW pending_actions AS (
    #             SELECT row_number() over() AS id,
    #                 req.name AS name,
    #                 req.requested_date AS date,
    #                 req.status AS status
    #             FROM
    #                 purchase_management_system AS req
    #         )
    #     """)
# class users(models.Model):
#     _inherit = 'res.users'

#     email_date = fields.Date(string='Email Sent Date',store=True)