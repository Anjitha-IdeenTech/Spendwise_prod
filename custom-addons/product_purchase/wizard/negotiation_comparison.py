from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
import logging

_logger = logging.getLogger(__name__)



class PurchaseRequestStatusWizard(models.TransientModel):
    _name = 'contract.request.nego.wizard'
    _description = 'Contract Request'


    comparison_details = fields.Boolean(string="Negotiation Comparison Details", default=False)

    def action_confirm(self):
        if not self.comparison_details:
            raise UserError("Please Select The Comparison Details")
        tenders = self.env['tenders'].search([('negotiation_true', '=', True)])
        lines = []
        for tender in tenders:
            existing_record = self.env['contract.negotiation'].search([('contract_id', '=', tender.id)])
            for ex in existing_record:
                ex.unlink()

            if tender.price_history_ids:
                initial_price = tender.price_history_ids[0].total_price
                last_price = tender.price_history_ids[-1].total_price
                price_difference = initial_price - last_price
                product_names = [
                    line.product_id.name for line in tender.contracts_request_line if
                    line.product_id and line.product_id.name
                ]
                unique_product_names = ", ".join(set(product_names))
                self.env['contract.negotiation'].create({
                    'contract_id': tender.id,
                    'vendor_id': tender.vendor_id.id,
                    'department_id': tender.department_id.id,
                    'exp_category_id': tender.exp_category.id,
                    'initial_price': initial_price,
                    'last_price': last_price,
                    'price_difference': price_difference,
                    'product_name': unique_product_names,
                })



        return {
            'type': 'ir.actions.act_window',
            'name': 'Negotiation Comparison Details',
            'view_mode': 'tree,form',
            'res_model': 'contract.negotiation',
            'target': 'current',
        }
