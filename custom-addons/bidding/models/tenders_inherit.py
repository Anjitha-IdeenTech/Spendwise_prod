from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date, datetime
from odoo.tools.safe_eval import json


class TendersInherit(models.Model):
    _inherit = "tenders"
    _description = 'Contract Request'

    bid_request_check = fields.Boolean(string="Bid Request check", default=False)
    bidding_id = fields.Many2one('bidding', string="Bidding ID")

    # def action_add_to_bidding(self):
    #     print("Inside Bidding")
    #     # dict_data = {
    #     #     'product_id': self.product.id,
    #     #     'quantity': self.quantity,
    #     #     'unit_price': self.unit_price,
    #     #     'total_price': self.total_price,
    #     #     'requested_date': datetime.now(),
    #     #     # 'time': self.time,
    #     #     'deadline': self.bidding_id.date,
    #     #     'status': self.status,
    #     #     'bidding_date': self.bidding_id.date,
    #     #     'request_from': self.company_id.id,
    #     #     'request_to': self.response_from.id,
    #     #     'user_id': self.user_id.id,
    #     #     'bidding_id': self.bidding_id.id,
    #     #     'response_id': self.id,
    #     #     'product_requested_id': self.product_requested_id,
    #     #     'product_request_line_id': self.product_request_line_id.id
    #     # }
    #     vals={
    #             # 'product_id': self.product.id,
    #             # 'quantity': self.quantity,
    #             # 'unit_price': self.unit_price,
    #             # 'total_price': self.total_price,
    #             'default_requested_date': datetime.now(),
    #             # 'time': self.time,
    #             # 'deadline': self.bidding_id.date,
    #             # 'status': self.status,
    #             # 'bidding_date': self.bidding_id.date,
    #             'default_request_from': self.company_id.id,
    #             # 'request_to': self.requested_to.id,
    #             'default_user_id': self.user_id.id,
    #             # 'bidding_id': self.bidding_id.id,
    #             'default_tender_id': self.id,
    #             'default_pr_id': self.product_requested_id.id,
    #             # 'product_request_line_id': self.product_request_line_id
    #         }
    #     print("return",vals)
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Add to Bidding wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'res_model': 'add.to.bidding.wizard',
    #         'context': {
    #             'default_requested_date': fields.Date.context_today(self),
    #             'default_request_from': self.company_id.id,
    #             'default_user_id': self.user_id.id,
    #             'default_tender_id': self.id,
    #             'default_pr_id': self.product_requested_id.id,
    #         }
    #     }
    def action_add_to_bidding(self):
        contract_lines = self.contracts_request_line
        print('ctr lines', contract_lines)
        product_ids = contract_lines.mapped('product_id.id')
        print('product_domain', product_ids)
        product_id_domain = json.dumps([['id', 'in', product_ids]])
        vals ={'default_requested_date': fields.Date.context_today(self),
                    'default_request_from': self.company_id.id,
                    # 'default_user_id': self.user_id.id,
                    'default_tender_id': self.id,
                    'default_pr_id': self.product_requested_id.id,
                    # 'default_product_id_domain':product_id_domain,
                             }
        print("vals",vals)
        action = self.env["ir.actions.actions"]._for_xml_id('bidding.action_add_to_bidding')
        action['context'] = {
                    'default_requested_date': fields.Date.context_today(self),
                    # 'default_request_from': self.env.user.id,
                    # 'default_user_id': self.user_id.id,
                    'default_tender_id': self.id,
                    'default_pr_id': self.product_requested_id.id,
                    # 'default_product_id_domain':product_id_domain,
                             }
        print(action)
        return action

    def get_bidding(self):
        print(self.id)
        bidding = self.env['bidding'].sudo().search(
            [('id', '=', self.bidding_id.id)])
        print(bidding)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Bid',
            'res_model': 'bidding',
            'res_id': self.bidding_id.id,
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def multi_to_bidding(self):
        for record in self:
            print("self,recod",self,record,record.main_rfq)
            if record.contracting_method == 'multi' and record.main_rfq:
                tender = self.env['tenders'].sudo().search(
                        [('main_rfq', '=', record.main_rfq.id),('state','=','vendor_approved')])

                least_price = None

                # Iterate over the tenders to find the least vendor price
                for tender_rec in tender:
                    total_price = sum(
                        tender_rec.mapped('total_vendor_price'))  # Assuming 'line_ids.price_total' stores the price
                    if least_price is None or total_price < least_price:
                        least_price = total_price
                print("the lease price is",least_price)
                vendor_ids = tender.mapped('vendor_id')  # Get vendor_ids from the tenders

                vendor_idss = tender.mapped('vendor_id').filtered(lambda v: v.id)
                print("vendor idss",vendor_ids,vendor_idss)
                if vendor_ids:
                    action = self.env["ir.actions.actions"]._for_xml_id('bidding.action_add_to_bidding')
                    action['context'] = {
                        'default_requested_date': fields.Date.context_today(self),
                        # 'default_request_from': self.env.user.id,
                        'default_request_to': [(6, 0, vendor_ids.ids)],  # Set Many2many field
                        'default_tender_id': record.id,
                        'default_pr_id': record.product_requested_id.id,
                    }
                    print(action)
                    return action


