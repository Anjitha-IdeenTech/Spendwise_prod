from odoo import models, fields, api



class VendorCategory(models.Model):
    _inherit = 'res.partner'

    category = fields.Char("Category")

class ContractPO(models.Model):
    _name = 'contract.po'
    _description = 'Contract and Purchase Order'

    contract_id = fields.Many2one('product.tender.line', string="Contract",ondelete='cascade')
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order",ondelete='cascade')
    branch_id = fields.Many2one('res.branch', string="Branch",ondelete='cascade')
    contract_po_line_ids = fields.One2many('contract.po.line', 'contract_po_id', string="Contract PO Lines",ondelete='cascade')

class ContractPOLine(models.Model):
    _name = 'contract.po.line'
    _description = 'Contract PO Line'

    active = fields.Boolean(default=True)
    contract_po_id = fields.Many2one('contract.po', string="Contract PO", ondelete='cascade')
    contract_id = fields.Many2one('product.tender.line', string="Contract", ondelete='cascade')
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order", ondelete='cascade')
    branch_id = fields.Many2one('res.branch', string="Branch",ondelete='cascade')
    pr_id = fields.Many2one('product.request', string='Purchase Request', ondelete='cascade')
    vendor_id = fields.Many2one('res.partner', string='Vendor',ondelete='cascade')

class Branches(models.Model):
    _inherit = 'res.branch'

    def action_show_contracts(self):
        contract_po_data = []
        print("The self id is", self.id)

        # Step 1: Search for active contracts related to this branch
        active_contracts = self.env['product.tender.line'].search([
            ('branch_ids', 'in', self.id),
            ('status', '=', 'active')
        ])
        print("Active contracts:", active_contracts)

        # Step 2: Find related product requests (PRs) for these active contracts (Only active PRs)
        product_request_lines = self.env['product.request.line'].search([
            ('contract', 'in', active_contracts.ids),
            ('product_request_id.bill_to', '=', self.id),
            ('product_request_id.active', '=', True),  # Only active PRs
        ])
        print("The product request lines are:", product_request_lines)

        # Step 3: Find purchase requests for the identified product request lines
        purchase_requests = self.env['product.request'].search([
            ('product_request_line_ids', 'in', product_request_lines.ids),
            ('bill_to', '=', self.id),
            ('status', '=', 'accepted')
        ])
        print("The purchase requests are:", purchase_requests)

        # Step 4: Find purchase orders related to the identified product request lines
        purchase_orders = self.env['purchase.order'].search([
            ('pr_id', 'in', purchase_requests.ids),
            ('branch_id', '=', self.id),  # Ensure PO is related to the branch
        ])
        print("The purchase orders are:", purchase_orders)

        # Step 5: Prepare the contract_po_data list with the required fields
        contract_po_data = []
        unique_combinations = set()

        for contract in active_contracts:
            # Get the PR lines associated with this contract and ensure they are active
            corresponding_pr_lines = product_request_lines.filtered(lambda line: line.contract.id == contract.id)

            # Get the PO associated with the PR lines
            for pr_line in corresponding_pr_lines:
                # Find corresponding purchase orders
                corresponding_pos = purchase_orders.filtered(lambda po: po.pr_id.id == pr_line.product_request_id.id)
                po_id = corresponding_pos and corresponding_pos[0].id or None

                # Create a unique key (contract_id, po_id, pr_id)
                combination_key = (contract.id, po_id, pr_line.product_request_id.id)

                # Check if this combination is already processed
                if combination_key not in unique_combinations:
                    unique_combinations.add(combination_key)  # Mark this combination as processed
                    contract_po_data.append({
                        'contract_id': contract.id,
                        'purchase_order_id': po_id,
                        'pr_id': pr_line.product_request_id.id,
                        'branch_id': self.id,
                        'vendor_id': contract.vendor.id,
                    })
                    print("Added Contract PO data:", contract_po_data)
                else:
                    print(
                        f"Skipped duplicate for Contract: {contract.id}, PO: {po_id}, PR: {pr_line.product_request_id.id}")

        # Archive or delete existing contract.po.line records before creating new ones
        existing_records = self.env['contract.po.line'].search([('branch_id', '=', self.id)])
        existing_records.unlink()

        # Step 6: Create new records based on the filtered data
        if contract_po_data:
            display_records = self.env['contract.po.line'].create(contract_po_data)
            print("Created contract.po.line records:", display_records)
        else:
            display_records = []

        # Step 7: Return an action to open the tree view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contracts and Purchase Orders',
            'view_mode': 'tree',
            'res_model': 'contract.po.line',
            'view_id': self.env.ref('vendor_inherited.view_contract_po_tree').id,
            'target': 'current',
            'domain': [('branch_id', '=', self.id)],  # Show only active records
        }
