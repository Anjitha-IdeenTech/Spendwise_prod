from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
import logging
import re

# _logger = logging.getLogger(__name__)


class AutoGSTIGSTCustom(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'product_qty')
    def _onchange_product_id(self):
        if self.product_id:
            purchase_tax = False
            self.taxes_id = False
            supplier_state = self.order_id.partner_id.state_id
            if not supplier_state:
                raise UserError(_("Update State in Supplier Address"))
            ship_to_state = self.order_id.ship_to.state_id
            if not supplier_state:
                raise UserError(_("Update State in Shipping Address"))
            product_supplier_tax = self.product_id.supplier_taxes_id[0].name
            if not product_supplier_tax:
                raise UserError(_("Update Supplier Tax in Product Master"))
            match = re.search(r'\d+', product_supplier_tax)
            if match:
                extracted_supplier_tax = int(match.group())
                # _logger.info(extracted_supplier_tax)
                if extracted_supplier_tax:
                    if supplier_state == ship_to_state:
                        purchase_tax = self.env['account.tax'].sudo().search(
                            [('company_id', '=', self.company_id.id), ('amount', '=', str(extracted_supplier_tax)),
                             ('type_tax_use', '=', "purchase"),
                             ('name', '=', "GST " + str(int(float(extracted_supplier_tax))) + "%")], limit=1)
                    else:
                        purchase_tax = self.env['account.tax'].sudo().search(
                            [('company_id', '=', self.company_id.id), ('amount', '=', str(extracted_supplier_tax)),
                             ('type_tax_use', '=', "purchase"),
                             ('name', '=', "IGST " + str(int(float(extracted_supplier_tax))) + "%")], limit=1)
            else:
                tax_amount = self.product_id.supplier_taxes_id.amount
                if tax_amount == 0:
                    purchase_tax = self.env['account.tax'].sudo().search(
                        [('company_id', '=', self.company_id.id),
                         ('type_tax_use', '=', "purchase"),
                         ('name', '=', "GST " + str(int(float(extracted_supplier_tax))) + "%")], limit=1)
            # _logger.info(purchase_tax.id)
            tax = purchase_tax and [(6, 0, [purchase_tax.id])] or [] or False
            self.taxes_id = tax




class MailMailInherited(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def send_mail(self):
        outgoing_mails = self.env['mail.mail'].sudo().search([('state', '=', 'outgoing')])
        if outgoing_mails:
            for mail in outgoing_mails:
                mail.send()


