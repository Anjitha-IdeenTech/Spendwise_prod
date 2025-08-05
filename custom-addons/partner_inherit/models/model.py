from odoo import models, fields, api



class ManufactureOrder(models.Model):
    _inherit = 'res.partner'

    company_types = fields.Selection(
        [
            ('sole_proprietorship', 'Sole Proprietorship'),
            ('partnership', 'Partnership'),
            ('llc', 'Limited Liability Company (LLC)')
        ],
        string="Company Type",
        help="Select the type of company for this vendor"
    )



class UserInheritType(models.Model):
    _inherit = "res.users"

    pending_email_date = fields.Date(string='Pending Email Sent Date', store=True)
