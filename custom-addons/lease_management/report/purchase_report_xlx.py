import base64
import io
from odoo import models,_
from datetime import datetime


class PurchaseReportXlsx(models.AbstractModel):
    _name = 'report.lease_management.report_purchase_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('Purchase Report'))

        # Define headers
        headers = ['Purchase No', 'Vendor', 'Expense Category', 'Branches', 'Date', 'Products',
                   'Unit Price', 'Quantity', 'Tax', 'Product Code','status','purchase request','contract request']
        sheet.write_row(0, 0, headers)

        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        price_format = workbook.add_format({'num_format': '#,##0.00'})

        # Adjust column widths
        sheet.set_column(0, 9, 20)

        row = 1
        status_display_name = dict(self.env['purchase.order'].fields_get(allfields=['state'])['state']['selection'])

        # Handle location-based report generation
        if 'location_ids' in data:
            location_ids = data['location_ids']
            branches = self.env['res.branch'].search([('id', 'in', location_ids)])

            for branch in branches:
                purchase_orders = self.env['purchase.order'].search([('bill_to', 'in', [branch.id])])

                for po in purchase_orders:
                    for line in po.order_line:
                        sheet.write(row, 0, po.name)  # Purchase Number
                        sheet.write(row, 1, po.partner_id.name)  # Vendor Name
                        sheet.write(row, 2, po.exp_category.name)  # Expense Category
                        sheet.write(row, 3, po.branch_id.name)  # Branch Name
                        sheet.write_datetime(row, 4, po.date_order, date_format)  # Order Date
                        sheet.write(row, 5, line.product_id.name)  # Product Name
                        sheet.write_number(row, 6, line.price_unit, price_format)  # Unit Price
                        sheet.write_number(row, 7, line.product_qty)  # Quantity
                        sheet.write(row, 8, ', '.join(tax.name for tax in line.taxes_id))  # Tax
                        sheet.write(row, 9, line.product_id.default_code or 'N/A')
                        status_name = status_display_name.get(po.state, po.state)
                        sheet.write(row, 10, status_name)
                        sheet.write(row, 11, po.pr_id.name)
                        sheet.write(row, 12, po.ct_number.name)
                        row += 1

        # Handle vendor-based report generation
        elif 'vendor_ids' in data:
            vendor_ids = data['vendor_ids']
            vendors = self.env['res.partner'].search([('id', 'in', vendor_ids)])
            print("the vendor is",vendors)

            for vendor in vendors:
                purchase_orders = self.env['purchase.order'].search([('partner_id', 'in', [vendor.id])])

                for po in purchase_orders:
                    for line in po.order_line:
                        sheet.write(row, 0, po.name)  # Purchase Number
                        sheet.write(row, 1, po.partner_id.name)  # Vendor Name
                        sheet.write(row, 2, po.exp_category.name)  # Expense Category
                        sheet.write(row, 3, po.branch_id.name)  # Branch Name
                        sheet.write_datetime(row, 4, po.date_order, date_format)  # Order Date
                        sheet.write(row, 5, line.product_id.name)  # Product Name
                        sheet.write_number(row, 6, line.price_unit, price_format)  # Unit Price
                        sheet.write_number(row, 7, line.product_qty)  # Quantity
                        sheet.write(row, 8, ', '.join(tax.name for tax in line.taxes_id))  # Tax
                        sheet.write(row, 9, line.product_id.default_code or 'N/A')
                        status_name = status_display_name.get(po.state, po.state)
                        sheet.write(row, 10, status_name)
                        sheet.write(row, 11, po.pr_id.name)
                        sheet.write(row, 12, po.ct_number.name)
                        # Product Code
                        row += 1


class InvoiceReportXlsx(models.AbstractModel):
    _name = 'report.lease_management.report_invoice_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('invoice Report'))

        # Define headers
        headers = ['Invoice No','PR Number','PO Number', 'Vendor', 'Branches', 'Date', 'Products',
                   'Unit Price', 'Quantity', 'Tax', 'Product Code','status']
        sheet.write_row(0, 0, headers)

        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        price_format = workbook.add_format({'num_format': '#,##0.00'})

        # Adjust column widths
        sheet.set_column(0, 9, 20)
        status_display_name = dict(self.env['account.move'].fields_get(allfields=['state'])['state']['selection'])

        row = 1

        # Handle location-based report generation
        if 'location_ids' in data:
            location_ids = data['location_ids']
            branches = self.env['res.branch'].search([('id', 'in', location_ids)])

            for branch in branches:
                invoice_orders = self.env['account.move'].search([('branch_id', 'in', [branch.id])])

                for po in invoice_orders:
                    for line in po.invoice_line_ids:
                        sheet.write(row, 0, po.name)
                        sheet.write(row, 1, po.purchase_request.name)
                        sheet.write(row, 2, po.po_number.name)
                        sheet.write(row, 3, po.partner_id.name)
                        sheet.write(row, 4, po.branch_id.name)
                        sheet.write_datetime(row, 5, po.date, date_format)
                        sheet.write(row, 6, line.product_id.name)
                        sheet.write_number(row, 7, line.price_unit, price_format)
                        sheet.write_number(row, 8, line.quantity)
                        sheet.write(row, 9, ', '.join(tax.name for tax in line.tax_ids))
                        sheet.write(row, 10, line.product_id.default_code or 'N/A')
                        status_name = status_display_name.get(po.state, po.state)
                        sheet.write(row, 11, status_name)
                        row += 1

        # Handle vendor-based report generation
        elif 'vendor_ids' in data:
            vendor_ids = data['vendor_ids']
            vendors = self.env['res.partner'].search([('id', 'in', vendor_ids)])
            print("the vendor is",vendors)

            for vendor in vendors:
                invoice_orders = self.env['account.move'].search([('partner_id', 'in', [vendor.id])])

                for po in invoice_orders:
                    for line in po.invoice_line_ids:
                        sheet.write(row, 0, po.name)
                        sheet.write(row, 1, po.purchase_request.name)
                        sheet.write(row, 2, po.po_number.name)
                        sheet.write(row, 3, po.partner_id.name)
                        sheet.write(row, 4, po.branch_id.name)
                        sheet.write_datetime(row, 5, po.date, date_format)
                        sheet.write(row, 6, line.product_id.name)
                        sheet.write_number(row, 7, line.price_unit, price_format)
                        sheet.write_number(row, 8, line.quantity)
                        sheet.write(row, 9, ', '.join(tax.name for tax in line.tax_ids))
                        sheet.write(row, 10, line.product_id.default_code or 'N/A')
                        status_name = status_display_name.get(po.state, po.state)
                        sheet.write(row, 11, status_name)
                        row += 1

class LeaseReportXlsx(models.AbstractModel):
    _name = 'report.lease_management.report_lease_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('Lease Report'))

        # Define headers
        headers = ['Lease No','Vendor', 'Branches', 'start Date', 'End Date','Products',
                   'Unit Price', 'Quantity', 'Tax', 'Vendor Percentage','Vendor amount','Product Code','status']
        sheet.write_row(0, 0, headers)

        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        price_format = workbook.add_format({'num_format': '#,##0.00'})

        # Adjust column widths
        sheet.set_column(0, 9, 20)
        status_display_name = dict(self.env['account.move'].fields_get(allfields=['state'])['state']['selection'])

        row = 1

        # Handle location-based report generation
        if 'location_ids' in data:
            location_ids = data['location_ids']
            branches = self.env['res.branch'].search([('id', 'in', location_ids)])

            for branch in branches:
                leases = self.env['product.lease'].search([('bill_to', 'in', [branch.id])])

                for lease in leases:
                    # Loop through vendor_lease_request_line_ids to get vendor details
                    for vendor_line in lease.vendor_lease_request_line_ids:
                        for product_line in lease.product_lease_request_line_ids:
                            sheet.write(row, 0, lease.name)  # Lease No
                            sheet.write(row, 1, vendor_line.vendor_id.name)  # Vendor Name
                            sheet.write(row, 2,
                                        ', '.join(branch.name for branch in branch))  # Branches
                            sheet.write_datetime(row, 3, lease.start_date, date_format)  # Date
                            sheet.write_datetime(row, 4, lease.end_date, date_format)
                            sheet.write(row, 5, product_line.product.name)  # Products
                            sheet.write_number(row, 6, product_line.unit_price, price_format)  # Unit Price
                            sheet.write_number(row, 7, product_line.quantity)  # Quantity
                            sheet.write(row, 8, ', '.join(tax.name for tax in lease.tax))  # Tax names as a comma-separated string
                            sheet.write(row, 9, vendor_line.percentage_of_amount,price_format)
                            sheet.write(row, 10, vendor_line.amount)
                            sheet.write(row, 11, product_line.product.default_code or 'N/A')  # Product Code
                            status_name = status_display_name.get(lease.state, lease.state)
                            sheet.write(row, 10, status_name)
                            row += 1

        # Handle vendor-based report generation
        # Handle vendor-based report generation
        elif 'vendor_ids' in data:
            vendor_ids = data['vendor_ids']
            vendors = self.env['res.partner'].search([('id', 'in', vendor_ids)])
            print("the vendor is", vendors)

            for vendor in vendors:
                # Get leases for each vendor via vendor_lease_request_line_ids
                leases = self.env['product.lease'].search([
                    ('vendor_lease_request_line_ids.vendor_id', '=', vendor.id)
                ])

                for lease in leases:
                    # Now filter only the vendor lines that match this vendor
                    vendor_lines = lease.vendor_lease_request_line_ids.filtered(lambda l: l.vendor_id == vendor)

                    for vendor_line in vendor_lines:
                        for product_line in lease.product_lease_request_line_ids:
                            sheet.write(row, 0, lease.name)  # Lease No
                            sheet.write(row, 1, vendor_line.vendor_id.name)  # Vendor Name
                            sheet.write(row, 2,
                                        ', '.join(branch.name for branch in lease.bill_to))  # Branches
                            sheet.write_datetime(row, 3, lease.start_date, date_format)  # Date
                            sheet.write_datetime(row, 4, lease.end_date, date_format)
                            sheet.write(row, 5, product_line.product.name)  # Products
                            sheet.write_number(row, 6, product_line.unit_price, price_format)  # Unit Price
                            sheet.write_number(row, 7, product_line.quantity)  # Quantity
                            sheet.write(row, 8, ', '.join(
                                tax.name for tax in lease.tax))  # Tax names as a comma-separated string
                            sheet.write(row, 9, vendor_line.percentage_of_amount, price_format)
                            sheet.write(row, 10, vendor_line.amount)
                            sheet.write(row, 11, product_line.product.default_code or 'N/A')  # Product Code
                            status_name = status_display_name.get(lease.state, lease.state)
                            sheet.write(row, 10, status_name)
                            row += 1
