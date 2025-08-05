import base64
import io
from odoo import models,_
from datetime import datetime


class PatientCardXlsx(models.AbstractModel):
    _name = 'report.product_purchase.report_contract_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('Contract Report'))

        # Define your headers
        headers = ['Contract No', 'Vendor', 'Expense Category', 'Branches', 'Start Date', 'End Date', 'Products',
                   'Unit Price']
        sheet.write_row(0, 0, headers)

        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        price_format = workbook.add_format({'num_format': '#,##0.00'})

        # Adjust column widths to prevent "###" in cells
        sheet.set_column(0, 0, 20)  # Contract No column width
        sheet.set_column(1, 1, 30)  # Vendor column width
        sheet.set_column(2, 2, 30)  # Expense Category column width
        sheet.set_column(3, 3, 40)  # Branches column width
        sheet.set_column(4, 5, 15)  # Start Date and End Date column widths
        sheet.set_column(6, 6, 30)  # Product column width
        sheet.set_column(7, 7, 15)  # Unit Price column width

        # Fetching related contracts based on selected wizard filters
        location_ids = data['location_ids']  # Multiple location IDs
        exp_category_ids = data.get('exp_category_ids', []) # Expense category ID
        filter_by = data.get('filter_by', 'active')

        # Fetch branches based on location_ids
        branches = self.env['res.branch'].search([('id', 'in', location_ids)])

        row = 1
        for branch in branches:
            # Write the branch name as a header
            # sheet.write(row, 0, _('Branch: ') + branch.name)
            # row += 1

            # Fetch contracts related to the current branch and expense category
            if filter_by == 'active':
                contracts = self.env['product.tender.line'].search([
                    ('branch_ids', 'in', [branch.id]),
                    ('exp_category', 'in', exp_category_ids),('status','=','active')
                ])
            else:
                contracts = self.env['product.tender.line'].search([
                    ('branch_ids', 'in', [branch.id]),
                    ('exp_category', 'in', exp_category_ids),('status','!=','active')
                ])
            if contracts:
                # Write contract details under the branch
                for contract in contracts:
                    # For each contract, loop through the product lines and write the details for every product
                    for product_line in contract.product_product_line:
                        sheet.write(row, 0, contract.name)  # Contract Number
                        sheet.write(row, 1, contract.vendor.name)  # Vendor Name
                        sheet.write(row, 2, contract.exp_category.name)  # Expense Category
                        sheet.write(row, 3, branch.name)  # Branches

                        # Dates
                        sheet.write_datetime(row, 4, contract.start_date, date_format)  # Start Date
                        sheet.write_datetime(row, 5, contract.end_date, date_format)  # End Date

                        # Products and unit price
                        sheet.write(row, 6, product_line.product_id.name)  # Product
                        sheet.write_number(row, 7, product_line.unit_price, price_format)  # Unit Price
                        row += 1
            else:
                # If no contracts are found for the branch, skip and move to the next branch
                sheet.write(row, 0, _('No contracts found for this branch'))
                row += 1

