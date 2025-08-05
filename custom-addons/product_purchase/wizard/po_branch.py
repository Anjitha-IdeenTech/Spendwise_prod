from datetime import datetime
from datetime import date

from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo.exceptions import Warning

import base64



class BranchSelectionWizard(models.TransientModel):
    _name = 'po.branch.selection.wizard'
    _description = 'Po Branch Selection Wizard'

    branch_ids = fields.Many2many(
        'res.branch', string='Branches',
        help="Select the branches for which the purchase orders should be generated."
    )
    tender_id = fields.Many2one('tenders',string='Tender')

    def action_confirm_selection(self):
        current_date = datetime.now().date()
        print("The current date is", current_date)
        print("The tender is", self.tender_id)
        print("The payment", self.tender_id.recuring_payment, self.tender_id.purchase_plan, self.tender_id.state)

        if self.tender_id.recuring_payment and self.tender_id.state == 'approve':
            print("Enter the 1st if")
            if self.tender_id.from_date <= current_date <= self.tender_id.to_date:
                rate_con = self.env['product.tender.line'].sudo().search([
                    ('request_no', '=', self.tender_id.id),
                ])
                print("The rate con is", rate_con)

                if self.branch_ids:
                    for company in self.tender_id.company_ids:
                        for branch in self.branch_ids:
                            # print("The branch is", branch)
                            order_lines = []  # Collect all order lines here for a single PO

                            for line in self.tender_id.contracts_request_line:
                                # print("The line", line.product_id.name)

                                existing_pos = self.env['purchase.order.line'].sudo().search([
                                    ('order_id.ct_number', 'in', rate_con.ids),
                                    ('product_id.product_tmpl_id', '=', line.product_id.id),
                                    ('order_id.bill_to', '=', branch.id),
                                ])
                                # print("the existing po are",existing_pos)
                                # total_existing_taxed = sum(
                                #     pos.order_id.amount_total for pos in existing_pos
                                # )
                                # print("Total existing taxed amount for product", line.product_id.name, "is",
                                #       total_existing_taxed)
                                # print("the untaxed amount is",  total_existing_taxed)
                                # print("the contract total amount is", self.tender_id.total_price)
                                # if  total_existing_taxed >= self.tender_id.total_price:
                                #     print(
                                #         f"Skipping branch {branch.name} as quantities match.")
                                #     continue
                                if line.vendor_price > 0:
                                    price = line.vendor_price
                                else:
                                    price = line.unit_price

                                order_lines.append((0, 0, {
                                    'product_id': self.env['product.product'].search(
                                        [('product_tmpl_id', '=', line.product_id.id)], limit=1).id,
                                    'product_qty': line.quantity,
                                    'price_unit': price,
                                }))

                            total_existing_taxed = sum(
                                pos.order_id.amount_total for pos in existing_pos
                            )
                            # print("Total existing taxed amount for product", line.product_id.name, "is",
                            #       total_existing_taxed)
                            # print("the untaxed amount is", total_existing_taxed)
                            # print("the contract total amount is", self.tender_id.total_price)
                            # if total_existing_taxed >= self.tender_id.total_vendor_price:
                            #     # print(
                            #     #     f"Skipping branch {branch.name} as quantities match.")
                            #     continue

                            # Create the PO if there are any valid order lines
                            if order_lines:
                                po_vals = {
                                    'partner_id': self.tender_id.vendor_id.id,
                                    'date_order': current_date,
                                    'ct_number': rate_con.ids,
                                    'bill_to': branch.id,
                                    'ship_to': branch.id,
                                    'company_id': company.id,
                                    'is_auto_po': True,
                                    'exp_category': self.tender_id.exp_category.id,
                                    'order_line': order_lines,
                                    'expense_type': self.tender_id.expense_type,
                                    'department_id' : self.tender_id.department_id.id,
                                }
                                new_po = self.env['purchase.order'].sudo().create(po_vals)
                                # print("New Purchase Order Created:", new_po.name)

                                # Assign the Purchase Head
                                users_line = self.env['res.users.line'].sudo().search([
                                    ('department_id.name', '=', 'SCM'),
                                    ('designation', '=', 'Purchase Head')
                                ], limit=1)
                                print("Purchase head:", users_line, users_line.res_user_id.name)

                                new_po.purchase_head = users_line.res_user_id.id

                                # Create a Pending Action
                                if users_line and users_line.res_user_id.id:
                                    model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')],
                                                                               limit=1)
                                    pending_vals = {
                                        'model': model.id,
                                        'name': f"{rate_con.name} Assign The User To The Purchase Order",
                                        'record': new_po.id,
                                        'date': date.today(),
                                        'branch': new_po.bill_to.id,
                                        'department_id': new_po.department_id.id,
                                        'exp_category': new_po.exp_category.id,
                                        'Created_doc_date': new_po.date,
                                        'approve_users': [(6, 0, [users_line.res_user_id.id])]
                                    }
                                    self.env['pending.actions'].create(pending_vals)
                                self.tender_id.message_post(body=f"{self.env.user.name} Generate A Purchase Order.")
                            else:
                                raise ValidationError(
                                    "Already Full Quantity Purchase Order Is Generated"
                                )
