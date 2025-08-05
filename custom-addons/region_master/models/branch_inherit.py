from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date


class BranchInherit(models.Model):
    _inherit = "res.branch"

    region = fields.Many2one('region.masters', string='Region', tracking= True, required=True)
    division = fields.Many2one('division.masters', string='Division', tracking= True)
    sub_division = fields.Many2one('subdivision.masters', string='Sub Division', tracking= True)