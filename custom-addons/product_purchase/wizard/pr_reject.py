from odoo import models, fields, api
from odoo.exceptions import UserError
from werkzeug.urls import url_encode


class RejectReasonWizard(models.TransientModel):
    _name = 'reject.reason.wizard'
    _description = 'Reject Reason Wizard'

    reason = fields.Text(string="Reason for Rejection", required=True)
    pr_id = fields.Many2one('product.request', 'purchase request', readonly=True)
    ctr_id = fields.Many2one('tenders', 'contract request', readonly=True)

    def confirm_rejection(self):
        if self.pr_id:
            print("the pr is",self.pr_id.id)
            pr_id = self.env['product.request'].search([('id', '=', self.pr_id.id)])
            print("pr is",pr_id)

            model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', pr_id.id), ('status', '=', 'open')])

            if pending_action:
                for pend in pending_action:
                    print(pending_action.name)
                    pend.status = 'closed'
            pr_id.status = 'declined'
            pr_id.message_post(body=f"{self.env.user.name} Rejected the Purchase Request with reason: {self.reason}.")
            contract_requests = self.env['tenders'].search([('product_requested_id', '=', pr_id.id)])
            # print("the contract request are", contract_requests)
            # for con in contract_requests:
            #     print("status is", con.state)
            restricted_states = ['approve', 'confirm', 'legal_approve']
            restricted_contracts = contract_requests.filtered(lambda c: c.state in restricted_states)

            if restricted_contracts:
                # Raise an error if any contract request is in one of the restricted states
                raise UserError(
                    "Cannot cancel the Contract request.")
            else:
                for contract in contract_requests:
                    model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                    pending_action = self.env['pending.actions'].sudo().search(
                        [('model', '=', model.id), ('record', '=', contract.id), ('status', '=', 'open')])
                    if pending_action:
                        for pend in pending_action:
                            print(pending_action.name)
                            pend.status = 'closed'
                    contract.state = 'reject'
                    contract.message_post(
                        body=f"{self.env.user.name} Rejected the Contract Request with reason: {self.reason}.")


            subject = "Purchase Request Rejected: %s" % pr_id.name

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'Purchase Request')], limit=1) or False

            url_params = {
                'id': pr_id.id,
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
                f"The Purchase Request with the name <strong>{pr_id.name}</strong> has been rejected by "
                f"<strong>{self.env.user.name}</strong> for the following reason: <br><br>"
                f"<strong>Reason:</strong> {self.reason}<br><br>"
                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
            )
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': pr_id.requested_by.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)

        if self.ctr_id:
            print("the ctr is", self.ctr_id.id)
            contract_requests = self.env['tenders'].search([('id', '=', self.ctr_id.id)])
            print("the contract is",contract_requests)
            model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', contract_requests.id), ('status', '=', 'open')])
            print("the pending action is",pending_action)

            if pending_action:
                for pend in pending_action:
                    print(pending_action.name)
                    pend.status = 'closed'
            if contract_requests.main_rfq:
                related_contracts = self.env['tenders'].search([
                    ('main_rfq', '=', contract_requests.main_rfq.id)
                ])
                print("the related contract",related_contracts)

          
                all_rejected = all(contract.state == 'reject' for contract in related_contracts)

                if not all_rejected:
                    return
                # for rfq in contract_requests.main_rfq:
                #     rfq.state = 'reject'
                #     related_contracts = self.env['tenders'].search([('main_rfq', '=', rfq.id)])
                #     for contract in related_contracts:
                #         model = self.env['ir.model'].sudo().search([('model', '=', 'tenders')], limit=1)
                #         pending_action = self.env['pending.actions'].sudo().search(
                #             [('model', '=', model.id), ('record', '=', contract.id), ('status', '=', 'open')])
                #         print("the pending action is", pending_action)
                #         if pending_action:
                #             for pend in pending_action:
                #                 print(pending_action.name)
                #                 pend.status = 'closed'
                #         print(f"Rejecting contract: {contract.id}")
                #         contract.state = 'reject'
                #         contract.message_post(
                #             body=f"{self.env.user.name} Rejected the Contract Request with reason: {self.reason}.")
                #         related_vendor_contracts = self.env['contract'].search([('tender_id', '=', contract.id)])
                #         print("the related contracts are",related_vendor_contracts)
                #         for vendor_contract in related_vendor_contracts:
                #             # vendor_contract.contract_status = 'cancel'
                #             vendor_contract.vendor_request_status = 'reject'
                #             vendor_contract.state = 'reject'
                #             vendor_contract.message_post(
                #                 body=f"{self.env.user.name} Rejected the Vendor Contract with reason: {self.reason}.")

            contract_requests.state = 'reject'
            contract_requests.message_post(body=f"{self.env.user.name} Rejected the Contract Request with reason: {self.reason}.")
            pr_id = self.env['product.request'].search([('id', '=',  contract_requests.product_requested_id.id)])
            print("pr is", pr_id)
            restricted_status = ['requested', 'accepted']
            restricted_pr = pr_id.filtered(lambda c: c.status in restricted_status)
            if restricted_pr:
                # Raise an error if any contract request is in one of the restricted states
                raise UserError(
                    "Cannot cancel the Contract request.")

            else:
                for pr in pr_id:

                    model = self.env['ir.model'].sudo().search([('model', '=', 'product.request')], limit=1)
                    pending_action = self.env['pending.actions'].sudo().search(
                        [('model', '=', model.id), ('record', '=', pr.id), ('status', '=', 'open')])

                    if pending_action:
                        for pend in pending_action:
                            print(pending_action.name)
                            pend.status = 'closed'
                    pr.status = 'declined'


                    pr.message_post(body=f"{self.env.user.name} Rejected the Purchase Request with reason: {self.reason}.")
                subject = "Contract Request Rejected: %s" % pr_id.name

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Purchase Request')], limit=1) or False

                url_params = {
                    'id': pr_id.id,
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
                    f"The Contract Request with the name <strong>{pr_id.name}</strong> has been rejected by "
                    f"<strong>{self.env.user.name}</strong> for the following reason: <br><br>"
                    f"<strong>Reason:</strong> {self.reason}<br><br>"
                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                )
                if author:
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': pr_id.requested_by.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)

