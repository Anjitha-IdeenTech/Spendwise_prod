from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'


    pan = fields.Char(string='Pan Number',related='partner_id.pan')