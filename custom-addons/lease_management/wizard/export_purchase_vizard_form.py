from odoo import models, fields, api


class ExportContractWizard(models.TransientModel):
    _name = 'export.purchase.wizard'
    _description = 'Export Purchase Wizard'

    filter_by = fields.Selection([
        ('location', 'Location'),
        ('vendor', 'Vendor')
    ], string="Filter By", required=True, default='location')

    location_ids = fields.Many2many('res.branch', string='Location', required=False)
    vendor_ids = fields.Many2many('res.partner', string='Vendor', required=False)
    report_type = fields.Selection([
        ('invoice', 'Invoice'),
        ('purchase_order', 'Purchase Order')
    ], string="Report Type", required=True, default='invoice')

    @api.onchange('filter_by')
    def _onchange_filter_by(self):
        if self.filter_by == 'location':
            self.vendor_ids = False
        elif self.filter_by == 'vendor':
            self.location_ids = False

    def action_export(self):
        data = {}

        if self.filter_by == 'location' and self.location_ids:
            data['location_ids'] = self.location_ids.ids
        elif self.filter_by == 'vendor' and self.vendor_ids:
            data['vendor_ids'] = self.vendor_ids.ids

        if self.report_type=='purchase_order':

            return self.env.ref('lease_management.report_purchase_detail_xlx').report_action(self, data=data)
        if self.report_type=='invoice':
            return self.env.ref('lease_management.report_invoice_detail_xlx').report_action(self, data=data)

