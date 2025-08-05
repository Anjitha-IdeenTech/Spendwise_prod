from datetime import datetime
from odoo import api, fields, models, _
# import datetime
import base64
import logging
import xlrd
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo.tools.safe_eval import json

_logger = logging.getLogger(__name__)


class PrCompany(models.Model):
    _name = "pr.company"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Workflow"

    name = fields.Char(string="PR Company Number", readonly=True, required=True, copy=False, default='New')
    company_id = fields.Many2one('res.company', string="Company",default=lambda self: self.env.company, required=True,tracking=True)
    branch_id = fields.Many2one('res.branch', string="Branch",tracking=True)
    # location = fields.Many2one('res.company', string="Location")
    department_id = fields.Many2one('hr.department', string="Department",tracking=True)
    # , domain = "[('company_id','=',company_id)]"

    pr_approve_users_id = fields.One2many('pr.approve.users',
                                          'pr_company_id',
                                          string='Pr Approve Users',
                                          tracking=True)

    # product_request_budget_ids = fields.One2many('product.request.budget',
    #                                              'product_budget_id',
    #                                              string='Product Budget Line',
    #                                              tracking=True)

    from_amount = fields.Integer(string="From Amount",tracking=True)
    to_amount = fields.Integer(string="To Amount",tracking=True)
    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', required=True)
    type = fields.Selection(
        selection=[('pr', 'Purchase Request'), ('lease', 'Lease'), ('purchase', 'Purchase Order'),
                ('renewal', 'Tender Renewal'), ('contract', 'Contract'),('need_cr','Need for Contract'),('legal_workflow','Legal Workflow'),('accounting','Accounting'),('payment','Payment')],
        string='Workflow Type',
        required=True, tracking=True
    )
    exp_category = fields.Many2one('expense.category', 'Expense Category',tracking=True)

    exp_category_domain = fields.Char(
        compute="_compute_exp_category_domain",
        readonly=True,
        store=False,
    )

    branch_domain = fields.Char(
        compute="_compute_branch_domain",
        readonly=True,
        store=False,
    )

    _sql_constraints = [
        ('unique_pr_company',
         'unique (company_id, branch_id, department_id, expense_type, type)',
         'This combination of Company, Branch, Department, Expense Type, and Type already exists')
    ]
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)

    @api.depends('company_id')
    def _compute_branch_domain(self):
        for rec in self:
            branch_domain = []
            if rec.company_id:
                branches = self.env['res.branch'].sudo().search([
                    ('company_id', '=', rec.company_id.id)
                ])
                if branches:
                    branch_domain = [('id', 'in', branches.ids)]

            rec.branch_domain = json.dumps(branch_domain)


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
            # print(self.company_id.name)
            vals['name'] = self.env['ir.sequence'].next_by_code('pr.company') or 'New'
        result = super(PrCompany, self).create(vals)
        return result

    # @api.onchange('company_id')
    # def onchange_in_company_id(self):
    #     # print(self.id)
    #     department_data = self.env['hr.department'].sudo().search([('company_id', '=', self.company_id.id)])
    #     department_list = []
    #     for department_line in department_data:
    #         department_list.append(department_line.id)
    #     print(department_list)
    #     res = {'domain': {'department_id': [('id', 'in', department_list)]}}


class PrApproveUsers(models.Model):
    _name = "pr.approve.users"

    user_id = fields.Many2one('res.users', string="User")
    company_id = fields.Many2one('res.company', string="Company", required=True)
    # location = fields.Many2one('res.company', string="Location", required=True)
    branch_id = fields.Many2one('res.branch', string="Branch",required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    designation = fields.Many2one('hr.job', string="Designation", required=True)
    approve_order = fields.Integer(string="Order", required=True)

    pr_company_id = fields.Many2one('pr.company', string='Pr Company Id',
                                    invisible=True)

    branch_line_domain = fields.Char(
        compute="_compute_branch_line_domain",
        readonly=True,
        store=False,
    )

    @api.depends('company_id')
    def _compute_branch_line_domain(self):
        for rec in self:
            branch_domain = []
            if rec.company_id:
                branches = self.env['res.branch'].sudo().search([
                    ('company_id', '=', rec.company_id.id)
                ])
                if branches:
                    branch_domain = [('id', 'in', branches.ids)]

            rec.branch_line_domain = json.dumps(branch_domain)

    # @api.onchange('company_id')
    # def onchange_in_company_id(self):
    #     self.department_id = ""
    #     self.location = ""
    #     self.designation = ""
    #     self.user_id = ""
    #     print("Inside company")
    #     department_data = self.env['hr.department'].sudo().search(
    #         [('company_id', '=', self.company_id.id)])
    #     dep_list = []
    #     for dep in department_data:
    #         dep_list.append(dep.id)
    #     print(dep_list)
    #     res = {'domain': {'department_id': [('id', 'in', dep_list)]}}
    #     return res

    @api.onchange('location')
    def onchange_in_location(self):
        self.department_id = ""
        self.approve_order = ""
        self.designation = ""
        self.user_id = ""

    # @api.onchange('department_id')
    # def onchange_in_department_id(self):
    #     print("Inside department")
    #     self.designation = ""
    #     self.user_id = ""
    #     self.approve_order = ""
    #     job_data = self.env['hr.job'].sudo().search(
    #         [('department_id', '=', self.department_id.id)])
    #     job_list = []
    #     for job in job_data:
    #         job_list.append(job.id)
    #     res = {'domain': {'designation': [('id', 'in', job_list)]}}
    #     print("job_list ", job_list)
    #     return res
    #
    # @api.onchange('designation')
    # def onchange_in_designation(self):
    #     print("Inside designation")
    #     if self.designation.id:
    #         if self.designation and self.company_id and self.department_id:
    #             print(self.pr_company_id.company_id.id)
    #             print(self.pr_company_id.department_id.id)
    #             print(self.designation.id)
    #             approve_user_data = self.env['res.users.line'].sudo().search(
    #                 [('company_id', '=', self.company_id.id),
    #                  ('department_id', '=', self.department_id.id),
    #                  ('branch_id', '=', self.branch_id.id),
    #                  ('designation', '=', self.designation.id)], limit=1)
    #             if approve_user_data:
    #                 self.user_id = approve_user_data.res_user_id.id
    #             # else:
    #             #     raise ValidationError("User not found")

    @api.onchange('approve_order')
    def onchange_in_approve_order(self):
        flag = 0
        try:
            approve_user_data = self.env['pr.approve.users'].sudo().search(
                [('pr_company_id', '=', int(str(self.pr_company_id.id).split('_')[1]))])
            flag = 1
        except Exception as e:
            pass

# class ProductRequestBudget(models.Model):
#     _name = "product.request.budget"
#     _description = "Product Request"
#
#     # company_id = fields.Many2one('res.company', string="Company Id")
#     # location = fields.Many2one('res.company', string="Location")
#     # department_id = fields.Many2one('hr.department', string="Department")
#     from_date = fields.Date("From Date", required=True)
#     to_date = fields.Date(string="To Date", required=True)
#     amount_allowed = fields.Float(string="Amount Allowed")
#     amount_used = fields.Float(string="Amount Used")
#     amount_available = fields.Float(string="Amount Available")
#     product_budget_id = fields.Many2one('pr.company', string='Pr Company Id',
#                                     invisible=True)
