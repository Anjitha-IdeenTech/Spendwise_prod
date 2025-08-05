from odoo import api, fields, models, _
from odoo.tools.safe_eval import json
from odoo.exceptions import ValidationError



class UserInheritType(models.Model):
    _inherit = "res.users"

    mobile_number = fields.Char(
        string='Mobile Number',
        help='Mobile phone number of the user'
    )
    email_date = fields.Date(string='Email Sent Date',store=True)