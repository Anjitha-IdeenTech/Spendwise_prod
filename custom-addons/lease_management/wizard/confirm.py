# product_category_wizard.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError, MissingError, UserError

class Confirmlease(models.TransientModel):
    _name = 'confirm.lease.wizard'
    _description = "Confirm Purchase Request"

    lease_id = fields.Many2one('product.lease', string='Product Request Id',
                            invisible=True,required= True)

    name = fields.Char(string="Request No", readonly=True, required=True, copy=False, )
    requested_date = fields.Date(string="Requested Date", readonly=True)

    product_id = fields.Many2one('product.template',string="Product")

    requested_by = fields.Many2one('res.users', 'Requested By',  readonly=True)

    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True)


    bill_to = fields.Many2one('res.branch', "Bill To", readonly=True)

    ship_to = fields.Many2one('res.branch', "Ship To", readonly=True)

    expense_type = fields.Selection([('cap', 'CapEx'), ('op', 'OpEx')], string='Expense Type', tracking=True,
                                    readonly=True)

    vendor_id = fields.Many2one('res.partner', string="Vendor")

    exp_category = fields.Many2one('expense.category', 'Expense Category', required=True,readonly=True)

    exp_category_domain = fields.Char(

        readonly=True,
        store=False,
    )

    total_price = fields.Float(string="Total Price", readonly=True)

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")


    department_id = fields.Many2one('hr.department', string="Department", required=True,readonly=True)

    group_id = fields.Many2one('groups', string='Group')

    contract_selection = fields.Selection([
        ('with_contract', 'With Contract'),
        ('one_time', 'One Time'),
    ], 'Purchase Type', default='with_contract')

    budget_details = fields.Many2one('product.request.budget', string='Budget',readonly=True)
    budget_amount_avail = fields.Float(string="Budget Remaining")

    def confirm_pr_wizard(self):
        self.lease_id.action_request()
    # return {'type': 'ir.actions.act_window_close'}





class ConfirmPR(models.TransientModel):
    _name = 'confirm.pr.wizard'
    _description = "Confirm Purchase Request"