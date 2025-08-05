from odoo import models, fields, api

class ExportContractWizard(models.TransientModel):
    _name = 'export.contract.wizard'
    _description = 'Export Contract Wizard'


    filter_by = fields.Selection([
        ('active', 'Active'),
        ('no_active', 'Not Active')
    ], string="Filter By", required=True, default='active')

    location_ids = fields.Many2many('res.branch', string='Location', required=True)
    exp_category_ids = fields.Many2many('expense.category', string='Expense Category', required=True)

    def action_export(self):
        data = {
            'location_ids': self.location_ids.ids,  # Pass multiple location IDs
            'exp_category_ids': self.exp_category_ids.ids,
            'filter_by': self.filter_by,
        }

        report_action = self.env.ref('product_purchase.report_contract_detail_xlx').report_action(self, data=data)
        return report_action

