from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
from datetime import datetime

from odoo.tools.safe_eval import json

#
# class ContractCompareReport(models.Model):
#     _name = "contract.compare"
#     _auto = False
#     _description = "Contract Comparing View"
#
#     product = fields.Many2one('product.template', string="Product", store=True, force_save=True)
#     unit_price = fields.Float(string="Unit Price")
#     quantity = fields.Float(string="Quantity")
#     payment_terms = fields.Many2one('account.payment.term', "Payment Terms", required=True)
#     lead_time = fields.Integer("Lead Time in days")
#     total_price = fields.Float(string="Total Price")
#     name = fields.Char(string="TRN", readonly=True, required=True, copy=False, default='New')
#     requested_to = fields.Many2one('res.partner', string="Vendor", store=True, force_save=True)
#     product_requested_id = fields.Many2one('product.request', string="Product Requested ID")




class ContractComparison(models.TransientModel):
    _name = "contract.compare.wizard"
    _description = "Contract Campare"

    purchase_request = fields.Many2one("product.request", "Purchase Request", store=True)
    product = fields.Many2one("product.template", "Products", store=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=1)
    result = fields.Text("Result")
    is_purchase_request = fields.Boolean("Based on Purchase Request")
    is_product = fields.Boolean("Based on Product")

    compare_line = fields.One2many('contract.compare.line',
                                   'compare_id',
                                   string='Product Lease Line',
                                   tracking=True)

    def action_get_contracts(self):
        for rec in self:
            if rec.is_purchase_request:
                if rec.purchase_request:
                    current_user = self.env.user
                    company_id = current_user.company_id
                    contracts = self.env['tenders'].sudo().search(
                        [('product_requested_id', '=', rec.purchase_request.id),
                         ('company_id', '=', company_id.id)]) or False
                    if contracts:
                        lines = []
                        for datas in contracts:
                            vals = (0, 0, {
                                'product': datas.product.name,
                                'unit_price': datas.unit_price,
                                'quantity': datas.quantity,
                                'payment_terms': datas.payment_terms.name,
                                'lead_time': datas.lead_time,
                                'name': datas.name,
                                'vendor': datas.requested_to.name,
                                'total_price': datas.total_price,
                            })
                            lines.append(vals)

                        return {'type': 'ir.actions.act_window',
                                'name': _('Compare'),
                                'res_model': 'contract.compare.wizard',
                                'target': 'new',
                                'view_mode': 'form',
                                'context': {'default_compare_line': lines,
                                            'default_purchase_request': self.purchase_request.id,
                                            'default_is_purchase_request': self.is_purchase_request,

                                            },
                                'nodestroy': True
                                }
                    else:
                        raise UserError("Sorry No Rate of Contract Found")
                else:
                    raise UserError("Please select the Purchase Request")

            ########## If basd on product #######
            elif rec.is_product:
                if rec.product:
                    current_user = self.env.user
                    company_id = current_user.company_id
                    contracts = self.env['tenders'].sudo().search(
                        [('product', '=', rec.product.id),
                         ('company_id', '=', company_id.id)]) or False
                    if contracts:
                        lines = []
                        for datas in contracts:
                            vals = (0, 0, {
                                'product': datas.product.name,
                                'unit_price': datas.unit_price,
                                'quantity': datas.quantity,
                                'payment_terms': datas.payment_terms.name,
                                'lead_time': datas.lead_time,
                                'name': datas.name,
                                'vendor': datas.requested_to.name,
                                'total_price': datas.total_price,
                            })
                            lines.append(vals)

                        return {'type': 'ir.actions.act_window',
                                'name': _('Compare'),
                                'res_model': 'contract.compare.wizard',
                                'target': 'new',
                                'view_mode': 'form',
                                'context': {'default_compare_line': lines,
                                            'default_product': self.product.id,
                                            'default_is_product': self.is_product,

                                            },
                                'nodestroy': True
                                }
                    else:
                        raise UserError("Sorry No Rate of Contract Found")
                else:
                    raise UserError("Please select the Product")
            else:
                raise UserError("Please select the Product or PR")
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Compare'),
                    'res_model': 'contract.compare.wizard',
                    'target': 'new',
                    'view_mode': 'form',
                    'res_id': self.id,
                    'nodestroy': True,
                }




    def action_compare(self):
        lowest_price = None
        lowest_lead_time = None
        longest_payment_terms = None
        lowest_price_name = None
        lowest_lead_time_name = None
        longest_payment_terms_name = None

        for line in self.compare_line:
            if lowest_price is None or line.unit_price < lowest_price:
                lowest_price = line.unit_price
                lowest_price_name = line.name

            if lowest_lead_time is None or line.lead_time < lowest_lead_time:
                lowest_lead_time = line.lead_time
                lowest_lead_time_name = line.name

            # if longest_payment_terms is None or len(line.payment_terms) > len(longest_payment_terms):
            #     longest_payment_terms = line.payment_terms
            #     longest_payment_terms_name = line.name

        results = ("The Contract " + lowest_price_name + " "+"has lowest price and" + " " + "Contract "+ " "+ lowest_lead_time_name +
             " " + "has lowest delivery time")
        self.result = results

        print("The Contract " + lowest_price_name + " "+"has lowest price and" + " " + "Contract "+ " "+ lowest_lead_time_name +
             " " + "has lowest delivery time")
                # message = f"The lowest price among the comparison lines is: {lowest_price}"
                # return {
                #     'type': 'ir.actions.client',
                #     'tag': 'display_notification',
                #     'params': {
                #         'title': _('Lowest Price'),
                #         'message': message,
                #         'sticky': False,
                #     },
                # }


        return {
            'type': 'ir.actions.act_window',
            'name': _('Compare'),
            'res_model': 'contract.compare.wizard',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.id,
            'nodestroy': True,
        }
        # res = self.env['ir.actions.act_window']._for_xml_id('contract_compare.action_compare_contract')
        # return res


    def action_print(self):
        return self.env.ref("contract_comparison.report_compare").report_action(self)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Compare'),
            'res_model': 'contract.compare.wizard',
            'target': 'new',
            'view_mode': 'form',
            'res_id': self.id,
            'nodestroy': True,
        }


class ContractComparison(models.TransientModel):
    _name = "contract.compare.line"
    _description = "Contract Compare"

    product = fields.Char("Product")
    unit_price = fields.Float(string="Unit Price")
    quantity = fields.Float(string="Quantity")
    payment_terms = fields.Char("Payment Terms")
    lead_time = fields.Integer("Lead Time in days")
    total_price = fields.Float(string="Total Price")
    name = fields.Char("Name")
    vendor = fields.Char(string="Vendor")
    compare_id = fields.Many2one('contract.compare.wizard', string='Contract Id',
                                 invisible=True)
