
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class ContractNegotiationComparisonLine(models.Model):
    _name = "contract.negotiation"
    _description = "Contract Negotiation"

    contract_id = fields.Many2one('tenders', string="Contract", readonly=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    exp_category_id = fields.Many2one('expense.category', string="Expense Category", readonly=True)
    initial_price = fields.Float(string="Previous Rate", readonly=True)
    last_price = fields.Float(string="Negotiation Price", readonly=True)
    price_difference = fields.Float(string="Price Difference", readonly=True)
    product_name = fields.Char(string="Product Name", readonly=True)
