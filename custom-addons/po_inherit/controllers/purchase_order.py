from odoo import http
from odoo.exceptions import ValidationError, UserError
from odoo.http import request, _logger
from datetime import datetime
from odoo import api, models, fields, _


class PurchaseOrder(http.Controller):

    @http.route('/web/session/authenticate', type='json', auth="public")
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()

    @http.route('/data/create_sale_purchase', type='json', auth="public")
    def create_rm_purchase(self, **rec):
        request.session.authenticate(rec['db'], rec['login'], rec['password'])
        print(rec)
        po_numbers = []
        for row in rec["data"]:
            invoice_date = row["master"]["date_approve"]
            date = datetime.strptime(invoice_date, '%d/%m/%Y')

            vendor_gst = row["master"]["partner_id"]["gst_no"]
            if vendor_gst:
                vendor = vendor_gst and request.env['res.partner'].sudo().search([('vat', '=', vendor_gst)],
                                                                                 limit=1) or False
                if not vendor:
                    vendor_details = {
                        'name': row["master"]["partner_id"]["name"],
                        'company_type': "company",
                        'currency_id': 20,
                        'street': row["master"]["partner_id"]["address"],
                        # 'l10n_in_gst_treatment': "regular",
                        'street2': " ",
                        'city': " ",
                        'zip': " ",
                        'phone': row["master"]["partner_id"]["phone"],
                        'email': row["master"]["partner_id"]["email"],
                        'vat': row["master"]["partner_id"]["gst_no"],
                        # 'parent_id': 1
                    }
                    print("one")
                    vendor = request.env['res.partner'].sudo().create(vendor_details)
                    request.env.cr.commit()
            else:
                raise ValueError("GST number is missing")

            order_line = []
            for product_line in row["child"]:
                product_item = product_line["name"]
                if product_item:
                    product = product_item and request.env['product.product'].sudo().search(
                        [('name', '=', product_item)], limit=1) or False
                    uom_ids = request.env['uom.uom'].sudo().search([])
                    unit_id = request.env.ref('uom.product_uom_unit') and request.env.ref(
                        'uom.product_uom_unit').id or False
                    for record in uom_ids:
                        if record.name == "kg":
                            unit_id = record.id
                    if not product:
                        product_details = {
                            'name': product_line["name"],
                            # 'default_code': row.ITEM_NUM,
                            'list_price': product_line["price_unit"],
                            # 'l10n_in_hsn_code': row.HSN_CODE,
                            'uom_id': unit_id,
                            'uom_po_id': unit_id,
                            'detailed_type': 'product',
                            'categ_id': 1,
                            'standard_price': product_line["price_unit"],

                        }

                        product = request.env['product.template'].sudo().create(product_details)
                        request.env.cr.commit()
                        print("product template")
                if product:
                    order_line.append((0, 0, {
                        'display_type': False,
                        # 'sequence': 10,
                        'product_id': product.id,
                        'name': product.name or '',
                        # 'date_planned': row.TRANSACTION_DATE or False,
                        'account_analytic_id': False,
                        'product_qty': product_line["product_qty"] or 0,
                        'qty_received_manual': 0,
                        # 'discount': discount or 0,
                        # 'product_uom': product.uom_id.id or request.env.ref(
                        #     'uom.product_uom_unit') and request.env.ref('uom.product_uom_unit').id or False,
                        'price_unit': product_line["price_unit"] or 0,
                        # 'taxes_id': tax_variant and [(6, 0, [tax_variant.id])] or [],
                    }))
        if vendor:
            purchase_order_1 = request.env['purchase.order'].create({
                'partner_id': vendor.id,
                # 'partner_ref': row.SALES_ORDER_NUMBER or '',
                # 'origin': row.INVOICE_NUM or '',
                # 'date_order':row["master"]["date_order"] or False,
                # 'date_planned':row["master"]["date_approve"] or False,
                # 'partner_id': self.env.ref('base.main_partner').id,
                # 'name': row.INVOICE_NUM or '',
                'order_line': order_line,
            })
            request.env.cr.commit()

            # if purchase_order_1:
            #     purchase_order_1.button_confirm()
            #     purchase_order_1.date_approve = date
            #     purchase_order_1.action_view_picking()
            #     if purchase_order_1.picking_ids:
            #         for picking in purchase_order_1.picking_ids:
            #             picking.button_validate()
            #             pick_to_backorder = request.env['stock.immediate.transfer']
            #             stock_immediate = pick_to_backorder.create(
            #                 {'pick_ids': [(6, 0, purchase_order_1.picking_ids.ids)]})
            #             request.env.cr.commit()
            #             stock_immediate.process()
            #     po_numbers.append({
            #         'poNumber': purchase_order_1.name,
            #         'orderID': row["master"]["orderID"]
            #                     })
            #     return {'purchase_order': purchase_order_1.name}
            return {'purchase_order': purchase_order_1.name}
