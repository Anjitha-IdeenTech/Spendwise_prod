from datetime import datetime, timedelta, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError


class VendorPriceHistory(models.TransientModel):
    _name = "vendor.history.wizard"
    _description = "Price History"

    product = fields.Many2one('product.template', string="Product", store=True, force_save=True,
                              required=True)
    related_branch = fields.Many2one('res.branch', string="Branch ")
    name = fields.Char("Name")
    least_price_br = fields.Float(string="Least Price in branch")
    least_price_other = fields.Float(string="Least Price in All")
    avg_price = fields.Float(string="Average Price of product")

    contract_line_ids = fields.One2many('contract.history.line',
                                               'contract_product_history',
                                               string='Contract History',
                                               tracking=True)

    contract_request_line_ids = fields.One2many('contract.request.line',
                                        'contract_request_history',
                                        string='Contract Request History',
                                        tracking=True)

    purchase_line_ids = fields.One2many('purchase.line',
                                                'purchase_history',
                                                string='Purchase History',
                                                tracking=True)

    @api.onchange('product')
    def onchange_in_product(self):
        print("HELLLLLLLLLLLLLLLLLLLLLLLLLLOOOOOOOOOOOOOOOOOOOO")
        products_line2 = self.env['product.contracts.line'].sudo().search([
            ('product_id', '=', self.product.id)], order='unit_price asc')
        if products_line2:
            products_line_ids = products_line2.mapped('products_line').ids
            # print("line ids",products_line_ids)

            total = 0
            for contract_line2 in products_line2:
                total += 1
                self.avg_price += contract_line2.unit_price
            if total>0 and self.avg_price>0:
                self.avg_price = self.avg_price/total

            least_price_line = products_line2[0]
            self.least_price_other = least_price_line.unit_price
        else:
            self.least_price_other = 0

        if products_line2:
            product_contract2 = self.env['product.tender.line'].sudo().search(
                [
                    ('id', 'in', products_line_ids),  # Keep this condition for specific lines
                    ('branch_ids', 'in', self.related_branch.ids),  # Use related_branch.ids directly
                    ('status', 'in', ('active', 'renew', 'expire'))
                ],
                order='id desc'
            )
            if product_contract2:
                # If product_contract2 contains multiple records, select the first one
                product_contract_line_ids = product_contract2.mapped('product_product_line.id')
                products_line3 = self.env['product.contracts.line'].sudo().search([
                    ('id', 'in', product_contract_line_ids)], order='unit_price asc', limit=1)
                if products_line3:
                    self.least_price_br = products_line3.unit_price
                else:
                    self.least_price_br = 0
            else:
                self.least_price_br = 0
        else:
            self.least_price_br = 0

        products_line = self.env['product.contracts.line'].sudo().search([
            ('product_id', '=', self.product.id)], order='id desc')

        for contract_line in products_line:
            product_contract = self.env['product.tender.line'].sudo().search(
                [('id', '=', contract_line.products_line.id), ('start_date', '<=', date.today()),
                 ('end_date', '>=', date.today()), ('status', 'in', ('active', 'renew'))], order='id desc')
            for contract in product_contract:
                if contract:
                    contract_line_values = []
                    for items in contract:
                        if items.vendor and items.name:
                            contract_line_values.append({
                                'vendor': items.vendor.id,
                                'contract_name': items.name,
                                'contract': items.id,
                                'payment_terms': items.payment_terms.id,
                                'unit_price': contract_line.unit_price,
                                'status': items.status,
                            })

                    self.contract_line_ids = [(0, 0, line_vals) for line_vals in contract_line_values]

        contract_requests = self.env['contract.request.lines'].sudo().search([
            ('product_id', '=', self.product.id)], order='id desc')
        if contract_requests:
            contract_requests_line_values = []

            for contract_rq in contract_requests:
                if contract_rq:
                    contract_requests_line_values.append({
                        'vendor': contract_rq.contracts_lines.vendor_id.id,
                        'contract_name': contract_rq.contracts_lines.id,
                        # 'contract': contract.id,
                        'payment_terms': contract_rq.contracts_lines.payment_terms.id,
                        'unit_price': contract_rq.unit_price,
                        'status': contract_rq.contracts_lines.state,
                    })

            self.contract_request_line_ids = [(0, 0, line_vals) for line_vals in contract_requests_line_values]

        purchases = self.env['purchase.order.line'].sudo().search([
            ('product_id', '=', self.product.id)], order='id desc')
        if purchases:
            purchase_line_values = []

            for purchase in purchases:
                if purchase.order_id:
                    purchase_line_values.append({
                        'vendor': purchase.order_id.partner_id.id,
                        'purchase_order': purchase.order_id.id,
                        # 'contract': contract.id,
                        'payment_terms': purchase.order_id.payment_term_id.id,
                        'unit_price': purchase.price_unit,
                        'status': purchase.order_id.state,
                    })

            self.purchase_line_ids = [(0, 0, line_vals) for line_vals in purchase_line_values]
class ContractHistoryLine(models.TransientModel):
    _name = "contract.history.line"
    _description = "Contract History"

    contract_product_history = fields.Many2one('vendor.history.wizard', string="History", store=True, force_save=True)
    contract_name = fields.Char("Name")
    vendor = fields.Many2one('res.partner',"Vendor")
    contract = fields.Many2one('product.tender.line',"Contract")
    payment_terms = fields.Many2one('account.payment.term',"Payment Terms")
    unit_price = fields.Float(string="Unit Price", required=True)
    status = fields.Char("Status")


class ContractRequestLine(models.TransientModel):
    _name = "contract.request.line"
    _description = "Contract Request History"

    contract_request_history = fields.Many2one('vendor.history.wizard', string="History", store=True, force_save=True)
    contract_name = fields.Many2one('tenders', "Contract Requests")
    vendor = fields.Many2one('res.partner', "Vendor")
    payment_terms = fields.Many2one('account.payment.term', "Payment Terms")
    unit_price = fields.Float(string="Unit Price", required=True)
    status = fields.Char("Status")


class ContractRequestLine(models.TransientModel):
    _name = "purchase.line"
    _description = "Purchase History"

    purchase_history = fields.Many2one('vendor.history.wizard', string="History", store=True, force_save=True)
    purchase_order = fields.Many2one('purchase.order', "Purchase Order")
    vendor = fields.Many2one('res.partner', "Vendor")
    payment_terms = fields.Many2one('account.payment.term', "Payment Terms")
    unit_price = fields.Float(string="Unit Price", required=True)
    status = fields.Char("Status")