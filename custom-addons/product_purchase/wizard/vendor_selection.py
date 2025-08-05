# product_category_wizard.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError, MissingError, UserError
import json
import re

class ProductCategoryWizard(models.TransientModel):
    _name = 'product.category.wizard'
    _description = "Vendor Selection Based On Product Category"

    current_cr = fields.Many2one('tenders', string='Current CR')
    category_id = fields.Many2one('product.category', string='Product Category')
    vendor_ids = fields.Many2many('res.partner', string='Vendors',compute='compute_vendor_selection')
  

    @api.onchange('category_id')
    def compute_vendor_selection(self):
        if self.category_id:
            vendors = self.env['res.partner'].search([('product_category', 'in', self.category_id.ids)])
            self.write({'vendor_ids': [(6, 0, vendors.ids)]})
        else:
            self.vendor_ids = False

    def action_search_vendors(self):
        if self.category_id:
            vendors = self.env['res.partner'].search([('product_category', 'in', self.category_id.ids)])
            self.write({'vendor_ids': [(6, 0, vendors.ids)]})
        else:
            self.vendor_ids = False

    def action_confirm(self):
        if self.vendor_ids:
            if self.current_cr.main_rfq.id:
                tender_ids = self.env['tenders'].search([('main_rfq', '=', self.current_cr.main_rfq.id)])
                print("existing",tender_ids ,"CR",self.current_cr,"Mainrfq",self.current_cr.main_rfq.id)
                for tender in tender_ids:
                    if tender.vendor_id.id in self.vendor_ids.ids:
                        raise ValidationError("Vendor already exists in Current Contract requests!")
            # Select the first vendor
            first_vendor = self.vendor_ids[0]
            # Assign the first vendor to current_cr.vendor field
            if not self.current_cr.main_rfq:
                self.current_cr.main_rfq = self.current_cr.id
                name = self.current_cr.main_rfq.name
                self.current_cr.name = f"{name}-A"
            self.current_cr.vendor_id = first_vendor
            print("first",first_vendor)
            self.current_cr.state = 'rfq'
            self.current_cr.vendor_selection = True
            # Create new contract requests for the remaining vendors
            for vendor in self.vendor_ids[1:]:

                base_name = self.current_cr.main_rfq.name.split('-')[0]
                related_contracts = self.env['tenders'].search([('name', 'like', base_name)])
                print("the contracts are", related_contracts)
                max_seq = 0

                for contract in related_contracts:
                    match = re.search(rf"{base_name}-([A-Z])$", contract.name)
                    if match:
                        seq_letter = match.group(1)
                        seq_number = ord(seq_letter) - ord('A')
                        if seq_number > max_seq:
                            max_seq = seq_number
                # base_name = self.current_cr.main_rfq.name
                self.current_cr.name_array = []

                self.current_cr.name_sequence = max_seq + 1
                new_name = f"{base_name}-{chr(65 + self.current_cr.name_sequence)}"
                if isinstance(self.current_cr.name_array, list):
                    self.current_cr.name_array.append(new_name)
                    self.current_cr.name_array = json.dumps(self.current_cr.name_array)
                else:
                    print("Name array is not a list. It is of type:", type(self.current_cr.name_array))

                print("remaining vendors",vendor)
                existing_rfq_heads = self.current_cr.rfq_heads.ids

                new_rfq_heads = existing_rfq_heads + [self.current_cr.id]

                contract_request_vals = {
                    'name':new_name,
                    'main_remark':self.current_cr.main_remark,
                    'contracting_method': 'multi',
                    'reference_doc': [(6, 0, self.current_cr.reference_doc.ids)],
                    'vendor_id': vendor.id,
                    'from_date': self.current_cr.from_date,
                    'to_date': self.current_cr.to_date,
                    'expense_type': self.current_cr.expense_type,
                    'lead_time': self.current_cr.lead_time,
                    'payment_terms': self.current_cr.payment_terms.id,
                    'deadline': self.current_cr.deadline,
                    'purchase_plan': self.current_cr.purchase_plan,
                    'requested_date': self.current_cr.requested_date,
                    'exp_category' : self.current_cr.exp_category.id,
                    'user_id': self.current_cr.user_id.id,
                    'company_ids': [(6, 0, self.current_cr.company_ids.ids)],
                    'branch_ids': [(6, 0, self.current_cr.branch_ids.ids)],
                    'terms': self.current_cr.terms,
                    'rfq_heads': [(6, 0, new_rfq_heads)],
                    'main_rfq': self.current_cr.main_rfq.id,
                    'state': 'rfq',
                    'product_requested_id': self.current_cr.product_requested_id.id,
                    'vendor_selection': True,
                }
                contract_request = self.env['tenders'].sudo().create(contract_request_vals)
                contract_request.sudo().contracting_method = 'multi'

                contract_request_lines_vals = []
                for line in self.current_cr.contracts_request_line:
                    line_vals = {
                        'contracts_lines': contract_request.id,
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'unit_price': line.unit_price,
                        'product_group': line.product_group,
                    }
                    contract_request_lines_vals.append(line_vals)
                self.env['contract.request.lines'].create(contract_request_lines_vals)

