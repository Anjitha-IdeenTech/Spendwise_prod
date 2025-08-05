from odoo import api, fields, models, _

class PurchaseCancel(models.Model):
    _inherit = "purchase.order"

    def button_cancel(self):
        po = self.env['purchase.order'].sudo().search([])
        for rec in po:
            rec.bill_to = 2
            rec.ship_to = 2
            rec.state = 'cancel'