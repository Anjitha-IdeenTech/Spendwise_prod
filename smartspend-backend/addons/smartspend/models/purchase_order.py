from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    smartspend_request_id = fields.Many2one(
        'smartspend.request', string='Purchase Request', copy=False, index='btree_not_null',
        help="SmartSpend request this order was raised from.")
    smartspend_contract_id = fields.Many2one(
        'smartspend.contract', string='Rate Contract', copy=False, index='btree_not_null',
        help="Pre-negotiated agreement the prices on this order come from.")
    smartspend_request_ref = fields.Char(
        related='smartspend_request_id.name', string='Request Reference')
    smartspend_contract_ref = fields.Char(
        related='smartspend_contract_id.name', string='Contract Reference')
    smartspend_request_count = fields.Integer(compute='_compute_smartspend_request_count')

    @api.depends('smartspend_request_id')
    def _compute_smartspend_request_count(self):
        for order in self:
            order.smartspend_request_count = 1 if order.smartspend_request_id else 0

    def action_view_smartspend_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Request'),
            'res_model': 'smartspend.request',
            'view_mode': 'form',
            'res_id': self.smartspend_request_id.id,
        }

    def action_view_smartspend_contract(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rate Contract'),
            'res_model': 'smartspend.contract',
            'view_mode': 'form',
            'res_id': self.smartspend_contract_id.id,
        }

    def button_cancel(self):
        """Take the request back out of *PO Confirmed* when nothing is left standing.

        Confirming an order moves its request to *PO Confirmed*; cancelling the
        last one has to undo that, or the request claims an order it no longer
        has — and the buyer is offered "Create Purchase Order" on a record whose
        status says one already exists. The state it returns to is the one the
        timeline recorded when the order was raised.
        """
        res = super().button_cancel()
        for request in self.smartspend_request_id:
            request = request.sudo()
            if request.purchase_order_ids.filtered(lambda order: order.state != 'cancel'):
                continue
            dropped = self.filtered(lambda order: order.smartspend_request_id == request)
            note = _("%(orders)s cancelled — this request has no order standing.",
                     orders=", ".join(dropped.mapped('name')))
            previous = request.state
            if previous == 'po_confirmed':
                # Whatever it was before the order was raised; the timeline knows.
                raised = request.history_ids.filtered(lambda h: h.state_to == 'po_confirmed')
                request.state = (raised[-1:].state_from or 'approved')
            request._log_history(
                _("Purchase Order Cancelled"), note,
                state_from=previous, state_to=request.state)
            request.message_post(body=note)
        return res

    def button_confirm(self):
        res = super().button_confirm()
        for order in self.filtered('smartspend_request_id'):
            order.smartspend_request_id._log_history(
                _("PO Confirmed: %s", order.name),
                _("Confirmed with %s", order.partner_id.name))
            if order.smartspend_request_id.state != 'po_confirmed':
                order.smartspend_request_id.state = 'po_confirmed'
        return res
