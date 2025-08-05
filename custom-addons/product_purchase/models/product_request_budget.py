from datetime import datetime
from odoo import api, fields, models, _
# import datetime
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import json


class ProductRequestBudget(models.Model):
    _name = "product.request.budget"
    _description = "Product Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="TRN", readonly=True, required=True, copy=False, default='New')
    company_id = fields.Many2one('res.company', string="Company", tracking=True,default=lambda self: self.env.company)
    # location = fields.Many2one('res.company', string="Location", tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", tracking=True)
    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True)
    from_date = fields.Date("From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    amount_allowed = fields.Float(string="Amount Allotted", tracking=True)
    amount_used = fields.Float(string="Amount Used", tracking=True,readonly=True)
    amount_available = fields.Float(string="Amount Remaining", tracking=True,compute='_compute_remaining_amount')
    po = fields.Char(string="Purchase Request", readonly=True)
    exp_category = fields.Many2one('expense.category', 'Expense Category', required=True)
    branch_id = fields.Many2one('res.branch', "Branch", required=True)

    exp_category_domain = fields.Char(
        compute="_compute_exp_category_domain",
        readonly=True,
        store=False,
    )
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)

    @api.depends('amount_allowed','amount_used')
    def _compute_remaining_amount(self):
        for record in self:
            if record.amount_allowed:
                record.amount_available = record.amount_allowed - record.amount_used
            else:
                record.amount_available = 0


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

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.request.budget') or 'New'

        result = super(ProductRequestBudget, self).create(vals)
        return result

    @api.onchange('company_id')
    def onchange_in_company_id(self):
        # print(self.id)
        department_data = self.env['hr.department'].sudo().search([('company_id', '=', self.company_id.id)])
        department_list = []
        for department_line in department_data:
            department_list.append(department_line.id)
        print(department_list)
        res = {'domain': {'department_id': [('id', 'in', department_list)]}}

    def action_open_purchase_order(self):
        print("action_open_purchase_order")
        po_data = self.env['purchase.order'].sudo().search(
            [('pr_budget_id', '=', self.id)])
        print(po_data)
        if po_data:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Order',
                'res_model': 'purchase.order',
                'domain': [('pr_budget_id', '=', self.id)],
                'view_mode': 'tree,form',
                'target': 'current'
            }
