from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, MissingError, UserError


class StockDeliveryDate(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        print("inside the validate function")
        print("the orgin is",self.origin)
        if self.origin:
            purchase_order = self.env['purchase.order'].search([('name', '=', self.origin)], limit=1)
            if purchase_order:
                # Call the action_create_invoice method if it exists
                if hasattr(purchase_order, 'action_create_invoice'):
                    print(purchase_order)
                    # print("line qty",purchase_order.order_line.qty_received)
                    self.env.cr.commit()
                    for line in purchase_order.order_line:
                        for move in self.move_ids_without_package:
                            if move.product_id == line.product_id:
                                line.qty_received += move.quantity_done
                    inv_action = purchase_order.action_create_invoice()
                    print("invoice",inv_action)

                    if inv_action.get('res_model') == 'account.move':
                        # Get the ID of the created invoice
                        invoice_id = inv_action.get('res_id')
                        print("Created invoice ID:", invoice_id)

                        # Now you can use invoice_id to do further processing if needed
                        invoice_record = self.env['account.move'].browse(invoice_id)

                        if self.asn_created and invoice_record:
                            invoice_record.write({
                                'invoice_upload': self.asn_created.invoice_upload,
                                'attachment_upload': self.asn_created.attachment_upload
                            })
                        elif not self.asn_created and self.invoice:
                            invoice_record.write({
                                'invoice_upload': self.invoice,
                                'attachment_upload': self.attachment_upload
                            })
                        else:
                            raise UserError(_("No Invoice found"))
                    self.env.cr.commit()
                    self.asn_created.state='delivered'
                else:
                    print(f"Purchase Order {self.origin} does not have an action_create_invoice method.")
            else:
                print(f"Purchase Order {self.origin} not found.")
        else:
            print("No origin found in the stock picking.")
        return super(StockDeliveryDate, self).button_validate()


class Purchase(models.Model):
    _inherit = 'purchase.order'

    def action_view_invoice(self, invoices=False):
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
            print("the result is", result)
            tree_view_id = self.env.ref('account.view_move_tree').id
            form_view_id = self.env.ref('account.view_move_form').id
            result['views'] = [(tree_view_id, 'tree'), (form_view_id, 'form')]

        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result