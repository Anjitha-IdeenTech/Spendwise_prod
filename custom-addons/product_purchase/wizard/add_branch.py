from odoo import models, fields, api
from odoo.exceptions import UserError

class AddBranchWizard(models.TransientModel):
    _name = 'add.branch.wizard'
    _description = 'Wizard to Add Branches'

    branch_ids = fields.Many2many(
        'res.branch',
        string="Additional Branches",
        domain=lambda self: self._get_available_branches()
    )

    def _get_available_branches(self):
        tender_id = self.env.context.get('active_id')
        if tender_id:
            tender = self.env['tenders'].browse(tender_id)
            excluded_branch_ids = tender.branch_ids.ids
            return [('id', 'not in', excluded_branch_ids), ('company_id', 'in', tender.company_ids.ids)]
        return []

    def action_add_branches(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            tender = self.env['tenders'].browse(active_id)
            tender_lines = self.env['product.tender.line'].search([('request_no', '=', tender.id)])
            if tender_lines.status == 'expire':
                raise UserError("Cannot add branches because the rate contract is expired.")
            for branch in self.branch_ids:
                for line in tender_lines:
                    line.write({'branch_ids': [(4, branch.id)]})
            tender.write({'branch_ids': [(4, branch.id) for branch in self.branch_ids]})
