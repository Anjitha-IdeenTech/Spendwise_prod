from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date

from odoo.tools.safe_eval import json


class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"
    _description = 'Purchase Order'

    tender_rfq_id = fields.Integer(string="Tender RFQ ID")

    bill_to = fields.Many2one('res.branch', "Bill To", required=True)

    ship_to = fields.Many2one('res.branch', "Ship To", required=True)

    contract_response_id = fields.Many2one('tender.request.response', 'Contract request response')

    # company_id = fields.Many2one('res.company', string="Company Id", tracking=True)
    location = fields.Many2one('res.company', string="Location", tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", tracking=True)
    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True)
    pr_budget_id = fields.Many2one('product.request.budget', 'PR Budget')
    budget_group_id = fields.Many2one('groups', string='Group')
    pr_id = fields.Many2one('product.request', string="Product Request",invisible=True , tracking=True,)

    exp_category = fields.Many2one('expense.category', 'Expense Category', required=True)

    exp_category_domain = fields.Char(
        compute="_compute_exp_category_domain",
        readonly=True,
        store=False,
    )


    is_readonly = fields.Boolean("Readonly")
    qty_editable = fields.Boolean("Update Quantity")

    # def button_confirm(self):


    def create(self, vals):
        self.clear_caches()
        return super(PurchaseOrderInherit, self).create(vals)

    def your_method(self):
        self.env['ir.rule'].clear_caches()


    def write(self, vals):
        self.clear_caches()
        return super(PurchaseOrderInherit, self).write(vals)

    @api.depends('expense_type')
    def _compute_exp_category_domain(self):
        for rec in self:
            category_domain = []
            if rec.expense_type:
                categories = self.env['expense.category'].sudo().search([
                    ('exp_type', '=', rec.expense_type)
                ])
                if categories:
                    expense_types = categories.mapped('exp_type')
                    if expense_types:
                        category_domain = [('exp_type', '=', expense_types)]

            rec.exp_category_domain = json.dumps(category_domain)

    # def button_confirm(self):
    #     print("button_confirm ")
    #
    #     if self.pr_budget_id:
    #         self.pr_budget_id.amount_used += self.amount_total
    #
    #         return super(PurchaseOrderInherit, self).button_confirm()
    #     else:
    #         return super(PurchaseOrderInherit, self).button_confirm()


    def button_cancel(self):
        if self.pr_budget_id:
            self.pr_budget_id.amount_used -= self.amount_total
        self.pr_budget_id = False
        return super().button_cancel()




class VendorPricelistInherit(models.Model):
    _inherit = "product.supplierinfo"

    company_ids = fields.Many2many(
        'res.company',
        'pricelist_company_rel',
        'pricelist',
        'company_id',
        string='Allowed Companies',
    )
