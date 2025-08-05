from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
import logging

_logger = logging.getLogger(__name__)

class PurchaseRequestStatusResult(models.Model):
    _name = 'purchase.request.status.result'
    _description = 'Purchase Status'
    _order = 'purchase_request_id Asc'
    _rec_name = 'purchase_request_id'

    purchase_request_id = fields.Many2one('product.request', string="Purchase Request")
    contract_ids = fields.Many2many('tenders', string="Contracts")
    purchase_order_ids = fields.Many2many('purchase.order', string="Purchase Orders")
    invoice_ids = fields.Many2many('account.move', string="Invoices")

    expense_category_id = fields.Many2one('expense.category', string="Expense Category",
                                          related="purchase_request_id.exp_category", store=True)
    department_id = fields.Many2one('hr.department', string="Department", related="purchase_request_id.department_id",
                                    store=True)
    branch_id = fields.Many2one('res.branch', string="Branch", related="purchase_request_id.bill_to",
                                    store=True)
    is_completed = fields.Char(string="Completion Status", compute='_compute_is_completed', store=True)

    purchase_request_status = fields.Char(string="Purchase Request Status", compute='_compute_status_fields', store=True)
    contract_status = fields.Char(string="Contract Status", compute='_compute_status_fields', store=True)
    purchase_order_status = fields.Char(string="Purchase Order Status", compute='_compute_status_fields', store=True)
    invoice_status = fields.Char(string="Invoice Status", compute='_compute_status_fields', store=True)

    approver_purchase_id = fields.Many2one('res.users', string="Purchase Request Approver", compute='_compute_status_fields', store=True)
    approver_contract_id = fields.Many2one('res.users', string="Contract Request Approver", compute='_compute_status_fields', store=True)
    approver_po_id = fields.Many2one('res.users', string="Purchase Order Approver", compute='_compute_status_fields', store=True)
    approver_invoice_id = fields.Many2one('res.users', string="Invoice Approver", compute='_compute_status_fields', store=True)


    approve_users_pr_emails = fields.Char(string='Purchase Approver Email')
    approve_users_cr_emails = fields.Char(string='Contract Approver Email')
    approve_users_po_emails = fields.Char(string='PO Approver Email')
    approve_users_invoice_emails = fields.Char(string='Invoice Approver Email')

    has_pending_purchase_action = fields.Boolean(string="Has Pending Purchase Action", compute='_compute_pending_action')
    has_pending_contract_action = fields.Boolean(string="Has Pending Contract Action", compute='_compute_pending_action')
    has_pending_po_action = fields.Boolean(string="Has Pending PO Action", compute='_compute_pending_action')
    has_pending_invoice_action = fields.Boolean(string="Has Pending Invoice Action", compute='_compute_pending_action')


    initiator_id = fields.Many2one('res.users', string="Purchase Initiator", compute='_compute_initiator_fields',
                                   store=True)
    initiator_email = fields.Char(string="Initiator Email", compute='_compute_initiator_fields', store=True)

    @api.depends('purchase_request_id')
    def _compute_initiator_fields(self):
        """Compute the initiator's name and email from the purchase request."""
        for record in self:
            if record.purchase_request_id and record.purchase_request_id.requested_by:
                record.initiator_id = record.purchase_request_id.requested_by.id
                record.initiator_email = record.purchase_request_id.requested_by.login
            else:
                record.initiator_id = False
                record.initiator_email = 'N/A'

    @api.depends('purchase_request_id', 'contract_ids', 'purchase_order_ids', 'invoice_ids')
    def _compute_pending_action(self):
        """Compute whether there are pending actions for each approver."""
        for record in self:
            record.has_pending_purchase_action = bool(self.env['pending.actions'].sudo().search([
                ('record', '=', record.purchase_request_id.id),
                ('status', '=', 'open')
            ], limit=1))
            record.has_pending_contract_action = bool(self.env['pending.actions'].sudo().search([
                ('record', 'in', record.contract_ids.ids),
                ('status', '=', 'open')
            ], limit=1))
            record.has_pending_po_action = bool(self.env['pending.actions'].sudo().search([
                ('record', 'in', record.purchase_order_ids.ids),
                ('status', '=', 'open')
            ], limit=1))
            record.has_pending_invoice_action = bool(self.env['pending.actions'].sudo().search([
                ('record', 'in', record.invoice_ids.ids),
                ('status', '=', 'open')
            ], limit=1))

    @api.depends('purchase_request_id', 'contract_ids', 'purchase_order_ids', 'invoice_ids')
    def _compute_status_fields(self):
        for record in self:
            purchase_status_display = self._get_selection_display_name('product.request', 'status')
            contract_status_display = self._get_selection_display_name('tenders', 'state')
            purchase_order_status_display = self._get_selection_display_name('purchase.order', 'state')
            invoice_status_display = self._get_selection_display_name('account.move', 'state')

            # Compute statuses as lists
            # record.purchase_request_status = f"{record.purchase_request_id.name} - {record.purchase_request_id.status}" if record.purchase_request_id else 'N/A'
            record.purchase_request_status  = ', '.join(
                [f"{purchase_status_display .get(purchase_request_id.status, purchase_request_id.status).capitalize()}"
                 for purchase_request_id in record.purchase_request_id]
            ) or 'N/A'

            record.contract_status = ', '.join(
                [f"{contract_status_display.get(contract.state, contract.state)}"
                 for contract in record.contract_ids]
            ) or 'N/A'

            # Compute purchase order statuses
            record.purchase_order_status = ', '.join(
                [f"{purchase_order_status_display.get(po.state, po.state)}"
                 for po in record.purchase_order_ids]
            ) or 'N/A'

            # Compute invoice statuses
            record.invoice_status = ', '.join(
                [f"{invoice_status_display.get(invoice.state, invoice.state).capitalize()}"
                 for invoice in record.invoice_ids]
            ) or 'N/A'

            if record.purchase_request_id and record.purchase_request_id.status in ['requested', 'on_check','rfi']:
                pending_action = self.env['pending.actions'].sudo().search([
                    ('record', '=', record.purchase_request_id.id),
                    ('status', '=', 'open')
                ], limit=1)
                print("Pending Action:", pending_action)
                if pending_action:
                    if pending_action.approve_users:
                        record.approver_purchase_id = pending_action.approve_users[0].id
                        record.approve_users_pr_emails = ', '.join(pending_action.approve_users.mapped('login'))

                else:
                    record.approver_purchase_id= False

            if record.contract_ids and any(contract.state in ['confirm', 'rfi'] for contract in record.contract_ids):
                pending_action = self.env['pending.actions'].sudo().search([
                    ('record', 'in', record.contract_ids.ids),
                    ('status', '=', 'open')
                ], limit=1)
                print("Pending Action:", pending_action)
                if pending_action:
                    if pending_action.approve_users:
                        record.approver_contract_id = pending_action.approve_users[0].id
                        record.approve_users_cr_emails = ', '.join(pending_action.approve_users.mapped('login'))
                else:
                    record.approver_contract_id = False
            if record.purchase_order_ids and any(po.state in ['draft', 'rfi','sent','purchase'] for po in record.purchase_order_ids):
                pending_action = self.env['pending.actions'].sudo().search([
                    ('record', 'in', record.purchase_order_ids.ids),
                    ('status', '=', 'open')
                ], limit=1)
                print("Pending Action:", pending_action)
                if pending_action:
                    if pending_action.approve_users:
                        record.approver_po_id = pending_action.approve_users[0].id
                        record.approve_users_po_emails = ', '.join(pending_action.approve_users.mapped('login'))
                else:
                    record.approver_po_id = False
            if record.invoice_ids and any(invoice.state in ['accounting', 'finance'] for invoice in record.invoice_ids):
                pending_action = self.env['pending.actions'].sudo().search([
                    ('record', 'in', record.invoice_ids.ids),
                    ('status', '=', 'open')
                ], limit=1)
                print("Pending Action:", pending_action)
                if pending_action:
                    if pending_action.approve_users:
                        record.approver_invoice_id = pending_action.approve_users[0].id
                        record.approve_users_invoice_emails = ', '.join(pending_action.approve_users.mapped('login'))
                else:
                    record.approver_invoice_id = False

    def _get_selection_display_name(self, model_name, field_name):
        """Fetch the display names for a selection field."""
        field_info = self.env[model_name].fields_get(allfields=[field_name])
        if field_name in field_info:
            selection = field_info[field_name].get('selection', [])
            return dict(selection)
        return {}

    @api.depends('purchase_order_ids')
    def _compute_is_completed(self):
        """Determine if the purchase request is fully completed."""
        for record in self:
            # Ensure there are purchase orders and that all are in 'paid' state
            if record.purchase_order_ids:
                purchase_orders_completed = all(po.state == 'paid' for po in record.purchase_order_ids)
            else:
                purchase_orders_completed = False

            # Set is_completed to True only if all purchase orders are completed (paid)
            if purchase_orders_completed:
                record.is_completed = "Fully Completed"

    def _get_approver_for_record(self, record):
        """Generic method to get approver user for any record."""
        model_name = record._name
        # model = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)

        # if not model:
        #     _logger.error(f"Model {model_name} not found.")
        #     return False

        # pending_action = self.env['pending.actions'].sudo().search([
        #     ('record', '=', record.id),
        #     # ('model', '=', model.id),
        #     ('status', '=', 'open')
        # ], limit=1)
        #
        # if not pending_action:
        #     _logger.warning(f"No pending actions found for record {record.name}.")
        #     return False
        #
        # return pending_action.approve_users or False


