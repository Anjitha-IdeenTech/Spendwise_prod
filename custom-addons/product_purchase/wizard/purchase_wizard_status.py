from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
import logging

_logger = logging.getLogger(__name__)



class PurchaseRequestStatusWizard(models.TransientModel):
    _name = 'purchase.request.status.wizard'
    _description = 'Purchase Request'


    show_all = fields.Boolean(string="Show All Purchase Requests", default=False)
    show_pending_request = fields.Boolean(string="Show pending Purchase Requests", default=False)
    show_withoutasn_pending_request = fields.Boolean(string="Show pending Purchase Requests With Out ASN and auto PO", default=False)
    show_my_pending_request = fields.Boolean(string="Show My Pending Purchase Requests", default=False)

    allowed_company_ids = fields.Many2many(
        'res.company',
        string="Select Companies",
        default=lambda self: self.env.user.company_ids,
        required=True,
    )

    @api.constrains('allowed_company_ids')
    def _check_company_selection(self):
        for wizard in self:
            if not wizard.allowed_company_ids:
                raise ValidationError(_("Please select at least one company."))

    @api.constrains( 'show_all', 'show_pending_request', 'show_withoutasn_pending_request', 'show_my_pending_request')
    def _check_company_selection(self):
        for wizard in self:
            if not (
                    wizard.show_all or wizard.show_pending_request or wizard.show_withoutasn_pending_request or wizard.show_my_pending_request):
                raise ValidationError(
                    _("Please select at least one of the following: 'Show All', 'Show Pending', 'Show Without ASN', or 'Show My Pending Request'."))

    def _get_allowed_company_ids(self):
        return self.allowed_company_ids.ids

    def action_confirm(self):
        company_ids = self._get_allowed_company_ids()
        if self.show_all:
            
            requests = self.env['product.request'].search([('status', '!=', 'declined'), ('company_id', 'in', company_ids)])

            for req in requests:
                # Search for existing records
                existing_record = self.env['purchase.request.status.result'].search([
                    ('purchase_request_id', '=', req.id)
                ])  # Limit to 1 for performance
                for ex in existing_record:
                    ex.unlink()

                # Gather related records
                contracts = self.env['tenders'].search([('product_requested_id', '=', req.id), ('company_id', 'in', company_ids)])
                purchase_orders = self.env['purchase.order'].search([('pr_id', '=', req.id), ('company_id', 'in', company_ids)])
                invoices = self.env['account.move'].search([('purchase_request', '=', req.id), ('company_id', 'in', company_ids)])

                self.env['purchase.request.status.result'].create({
                    'purchase_request_id': req.id,
                    'contract_ids': [(6, 0, contracts.ids)],  # Link multiple contracts
                    'purchase_order_ids': [(6, 0, purchase_orders.ids)],  # Link multiple POs
                    'invoice_ids': [(6, 0, invoices.ids)],  # Link multiple invoices
                })


            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchase Request Status Results'),
                'res_model': 'purchase.request.status.result',
                'view_mode': 'tree,form',
            }
        if self.show_pending_request:
            processed_requests = set()
            purchase_request = False
            contracts = self.env['tenders']  # Initialize as empty recordset
            purchase_orders = self.env['purchase.order']  # Initialize as empty recordset
            invoices = self.env['account.move']
            all_records = self.env['purchase.request.status.result'].search([])

            # Unlink (delete) all the records
            all_records.unlink()

            # pending_actions = self.env['pending.actions'].sudo().search([('status', '=', 'open')])

            allowed_company_ids = self.env.user.company_ids.ids
            allowed_branch_ids = self.env.user.branch_ids.ids if hasattr(self.env.user, 'branch_ids') else []

            pending_actions_domain = [('status', '=', 'open')]
            if allowed_branch_ids:
                pending_actions_domain.append(('branch', 'in', allowed_branch_ids))
            pending_actions = self.env['pending.actions'].sudo().search(pending_actions_domain)

            for action in pending_actions:
                if action.model.model == 'tenders':
                    contract_request = self.env['tenders'].browse(action.record)
                    if contract_request.exists():
                        purchase = contract_request.product_requested_id
                        existing_record = self.env['purchase.request.status.result'].search([
                            ('purchase_request_id', '=', purchase.id)
                        ])
                        for ex in existing_record:
                            ex.unlink()
                        if purchase and purchase.company_id.id in company_ids:
                            contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_request = purchase.id

                elif action.model.model == 'product.request':
                    purchase = self.env['product.request'].browse(action.record)
                    if purchase.exists():
                        existing_record = self.env['purchase.request.status.result'].search([
                            ('purchase_request_id', '=', purchase.id)
                        ])
                        for ex in existing_record:
                            ex.unlink()
                        if purchase and purchase.company_id.id in company_ids:
                            contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_request= purchase.id

                elif action.model.model == 'purchase.order':
                    purchase_order = self.env['purchase.order'].browse(action.record)
                    if purchase_order.exists() and purchase_order.pr_id:
                        purchase = purchase_order.pr_id
                        if purchase:
                            existing_record = self.env['purchase.request.status.result'].search([
                                ('purchase_request_id', '=', purchase.id)
                            ])
                            for ex in existing_record:
                                ex.unlink()
                            if purchase and purchase.company_id.id in company_ids:
                                contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_request = purchase.id  # Add the purchase request ID

                elif action.model.model == 'account.move':  # Invoice Workflow
                    invoice = self.env['account.move'].browse(action.record)
                    if invoice.exists() and invoice.purchase_request:
                        purchase = invoice.purchase_request
                        if purchase:
                            existing_record = self.env['purchase.request.status.result'].search([
                                ('purchase_request_id', '=', purchase.id)
                            ])
                            for ex in existing_record:
                                ex.unlink()
                            if purchase and purchase.company_id.id in company_ids:
                                contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_request = purchase.id

                if purchase_request and purchase_request not in processed_requests:
                    processed_requests.add(purchase_request)
                    self.env['purchase.request.status.result'].create({
                        'purchase_request_id': purchase_request,
                        'contract_ids': [(6, 0, contracts.ids)],   # Link multiple contracts
                        'purchase_order_ids': [(6, 0, purchase_orders.ids)],  # Link multiple POs
                        'invoice_ids': [(6, 0, invoices.ids)],
                    })

            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchase Request Status Results'),
                'res_model': 'purchase.request.status.result',
                'view_mode': 'tree,form',

            }

        if self.show_withoutasn_pending_request:
            processed_requests = set()
            purchase_request = False
            contracts = self.env['tenders']  # Initialize as empty recordset
            purchase_orders = self.env['purchase.order']  # Initialize as empty recordset
            invoices = self.env['account.move']
            all_records = self.env['purchase.request.status.result'].search([])

            # Unlink (delete) all the records
            all_records.unlink()

            # pending_actions = self.env['pending.actions'].sudo().search([
            #     ('status', '=', 'open'),'&',
            #     ('name', 'not ilike', 'Recieve Products of PO'),
            #     ('name', 'not ilike', 'Assign The User To The Purchase Order')
            # ])

            allowed_company_ids = self.env.user.company_ids.ids
            allowed_branch_ids = self.env.user.branch_ids.ids if hasattr(self.env.user, 'branch_ids') else []

            pending_actions_domain = [('status', '=', 'open'),'&',
                ('name', 'not ilike', 'Recieve Products of PO'),
                ('name', 'not ilike', 'Assign The User To The Purchase Order')]
            if allowed_branch_ids:
                pending_actions_domain.append(('branch', 'in', allowed_branch_ids))
            pending_actions = self.env['pending.actions'].sudo().search(pending_actions_domain)
            # pending_actionss = self.env['pending.actions'].sudo().search([
            #     ('status', '=', 'open'),
            #     ('name', 'not ilike', 'Receive Products of PO')
            # ])
            # print("the testing pending actions are",pending_actionss)

            for action in pending_actions:
                if action.model.model == 'tenders':
                    contract_request = self.env['tenders'].browse(action.record)
                    if contract_request.exists():
                        purchase = contract_request.product_requested_id
                        existing_record = self.env['purchase.request.status.result'].search([
                            ('purchase_request_id', '=', purchase.id)
                        ])
                        for ex in existing_record:
                            ex.unlink()
                        if purchase and purchase.company_id.id in company_ids:
                            contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_request = purchase.id

                elif action.model.model == 'product.request':
                    purchase = self.env['product.request'].browse(action.record)
                    if purchase.exists():
                        existing_record = self.env['purchase.request.status.result'].search([
                            ('purchase_request_id', '=', purchase.id)
                        ])
                        for ex in existing_record:
                            ex.unlink()
                        if purchase and purchase.company_id.id in company_ids:
                            contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                            invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                            purchase_request = purchase.id

                elif action.model.model == 'purchase.order':
                    purchase_order = self.env['purchase.order'].browse(action.record)
                    if purchase_order.exists() and purchase_order.pr_id:
                        purchase = purchase_order.pr_id
                        if purchase:
                            existing_record = self.env['purchase.request.status.result'].search([
                                ('purchase_request_id', '=', purchase.id)
                            ])
                            for ex in existing_record:
                                ex.unlink()
                            if purchase and purchase.company_id.id in company_ids:
                                contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_request = purchase.id  # Add the purchase request ID

                elif action.model.model == 'account.move':  # Invoice Workflow
                    invoice = self.env['account.move'].browse(action.record)
                    if invoice.exists() and invoice.purchase_request:
                        purchase = invoice.purchase_request
                        if purchase:
                            existing_record = self.env['purchase.request.status.result'].search([
                                ('purchase_request_id', '=', purchase.id)
                            ])
                            for ex in existing_record:
                                ex.unlink()
                            if purchase and purchase.company_id.id in company_ids:
                                contracts = self.env['tenders'].search([('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_orders = self.env['purchase.order'].search([('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)])

                                invoices = self.env['account.move'].search([('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)])

                                purchase_request = purchase.id

                if purchase_request and purchase_request not in processed_requests:
                    processed_requests.add(purchase_request)

                    self.env['purchase.request.status.result'].create({
                        'purchase_request_id': purchase_request,
                        'contract_ids': [(6, 0, contracts.ids)],  # Link multiple contracts
                        'purchase_order_ids': [(6, 0, purchase_orders.ids)],  # Link multiple POs
                        'invoice_ids': [(6, 0, invoices.ids)],
                    })

            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchase Request Status Results'),
                'res_model': 'purchase.request.status.result',
                'view_mode': 'tree,form',

            }

        if self.show_my_pending_request:
            processed_requests = set()
            purchase_request = False
            contracts = self.env['tenders']
            purchase_orders = self.env['purchase.order']
            invoices = self.env['account.move']
            all_records = self.env['purchase.request.status.result'].search([])

            all_records.unlink()


            allowed_company_ids = self.env.user.company_ids.ids
            allowed_branch_ids = self.env.user.branch_ids.ids if hasattr(self.env.user, 'branch_ids') else []

            pending_actions_domain = [('status', '=', 'open')]
            if allowed_branch_ids:
                pending_actions_domain.append(('branch', 'in', allowed_branch_ids))
            _logger.debug(f"Pending actions domain: {pending_actions_domain}")
            pending_actions = self.env['pending.actions'].search(pending_actions_domain)
            print("pending actions",pending_actions)
            for action in pending_actions:
                if action.model.model == 'tenders':
                    contract_request = self.env['tenders'].browse(action.record)
                    if contract_request.exists() and contract_request.user_id == self.env.user and contract_request.company_id.id in company_ids:
                        purchase = contract_request.product_requested_id
                        if purchase:
                            existing_record = self.env['purchase.request.status.result'].search([
                                ('purchase_request_id', '=', purchase.id)
                            ])
                            for ex in existing_record:
                                ex.unlink()
                            contracts = self.env['tenders'].search([
                                ('product_requested_id', '=', purchase.id), ('company_id', 'in', company_ids)
                            ])
                            purchase_orders = self.env['purchase.order'].search([
                                ('pr_id', '=', purchase.id), ('company_id', 'in', company_ids)
                            ])
                            invoices = self.env['account.move'].search([
                                ('purchase_request', '=', purchase.id), ('company_id', 'in', company_ids)
                            ])
                            purchase_request = purchase.id

                elif action.model.model == 'product.request':
                    purchase = self.env['product.request'].browse(action.record)
                    if purchase.exists() and purchase.requested_by == self.env.user and purchase.company_id.id in company_ids:
                        existing_record = self.env['purchase.request.status.result'].search([
                            ('purchase_request_id', '=', purchase.id)
                        ])
                        for ex in existing_record:
                            ex.unlink()
                        contracts = self.env['tenders'].search([
                            ('product_requested_id', '=', purchase.id),
                            ('company_id', 'in', company_ids)
                        ])
                        purchase_orders = self.env['purchase.order'].search([
                            ('pr_id', '=', purchase.id),
                            ('company_id', 'in', company_ids)
                        ])
                        invoices = self.env['account.move'].search([
                            ('purchase_request', '=', purchase.id),
                            ('company_id', 'in', company_ids)
                        ])
                        purchase_request = purchase.id

                elif action.model.model == 'purchase.order':
                    purchase_order = self.env['purchase.order'].browse(action.record)
                    if purchase_order.exists() and purchase_order.user_id == self.env.user and purchase_order.pr_id and purchase_order.company_id.id in company_ids:
                        purchase = purchase_order.pr_id
                        if purchase:
                            existing_record = self.env['purchase.request.status.result'].search([
                                ('purchase_request_id', '=', purchase.id)
                            ])
                            for ex in existing_record:
                                ex.unlink()
                            contracts = self.env['tenders'].search([
                                ('product_requested_id', '=', purchase.id),
                                ('company_id', 'in', company_ids)
                            ])
                            purchase_orders = self.env['purchase.order'].search([
                                ('pr_id', '=', purchase.id),
                                ('company_id', 'in', company_ids)
                            ])
                            invoices = self.env['account.move'].search([
                                ('purchase_request', '=', purchase.id),
                                ('company_id', 'in', company_ids)
                            ])
                            purchase_request = purchase.id

                elif action.model.model == 'account.move':  # Invoice Workflow
                    invoice = self.env['account.move'].browse(action.record)
                    if invoice.exists() and invoice.purchase_request and invoice.purchase_request.requested_by == self.env.user and invoice.company_id.id in company_ids:
                        purchase = invoice.purchase_request
                        if purchase:
                            existing_record = self.env['purchase.request.status.result'].search([
                                ('purchase_request_id', '=', purchase.id)
                            ])
                            for ex in existing_record:
                                ex.unlink()
                            contracts = self.env['tenders'].search([
                                ('product_requested_id', '=', purchase.id),
                                ('company_id', 'in', company_ids)
                            ])
                            purchase_orders = self.env['purchase.order'].search([
                                ('pr_id', '=', purchase.id),
                                ('company_id', 'in', company_ids)
                            ])
                            invoices = self.env['account.move'].search([
                                ('purchase_request', '=', purchase.id),
                                ('company_id', 'in', company_ids)
                            ])
                            purchase_request = purchase.id

                if purchase_request and purchase_request not in processed_requests:
                    processed_requests.add(purchase_request)
                    self.env['purchase.request.status.result'].create({
                        'purchase_request_id': purchase_request,
                        'contract_ids': [(6, 0, contracts.ids)],  # Link multiple contracts
                        'purchase_order_ids': [(6, 0, purchase_orders.ids)],  # Link multiple POs
                        'invoice_ids': [(6, 0, invoices.ids)],
                    })

            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchase Request Status Results'),
                'res_model': 'purchase.request.status.result',
                'view_mode': 'tree,form',
}

