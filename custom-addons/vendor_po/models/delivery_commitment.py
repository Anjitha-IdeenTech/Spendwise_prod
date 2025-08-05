from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DeliveryCommitment(models.TransientModel):
    _name = "delivery.commitment.date"
    _description = "Delivery Commitment"

    delivery_commit_date = fields.Datetime(string="Delivery Commitment Date", store=True,required=True)

    purchase_id = fields.Many2one(
        'purchase.order', string='Purchase Order', readonly=True)


    def confirm(self):
        print("confirmmmmmmmmmmm wizard")
        # for rec in self:
        for picking in self.purchase_id:
            for picks in picking.picking_ids:
                if picks.state == 'assigned':
                    # if picks.picking_name == 'Delivery Orders':
                    # period = stock_pick.period_week
                    print("yessss")
                    print(self.delivery_commit_date)
                    picks.delivery_commitment = self.delivery_commit_date
                    picking.delivery_commitment =True





class AdvanceShipmentDate(models.TransientModel):
    _name = "advance.shipment.date"
    _description = "Advance Shipment Date"

    advance_shipment_date = fields.Datetime(string="Advanced Shipment Date", store=True, required=True)

    purchase_id = fields.Many2one(
        'purchase.order', string='Purchase Order', readonly=True)


    def advance_confirm(self):
        print("confirmmmmmmmmmmm wizard")
        # for rec in self:
        for picking in self.purchase_id:
            for picks in picking.picking_ids:
                if picks.state == 'assigned':
                    # if picks.picking_name == 'Delivery Orders':
                    # period = stock_pick.period_week
                    print("yessss")
                    print(self.advance_shipment_date)
                    picks.asm_date =self.advance_shipment_date
                    picking.asm_date=True