
from odoo import models, fields, api ,_
from odoo.exceptions import ValidationError, MissingError, UserError
from werkzeug.urls import url_encode

class DeadlineExtend(models.TransientModel):
    _name = 'deadline.extend.wizard'
    _description = "Deadline Extension"

    contract = fields.Many2one('tenders', string='Contract Request', readonly=True)
    current_deadline = fields.Datetime(string='Current Deadline ')
    extend_date  = fields.Datetime(string='Deadline Extended to')


    @api.onchange('contract')
    def onchange_contract(self):
        if self.contract:
            self.current_deadline = self.contract.deadline

    def confirm(self):
        if self.contract.state =='deadline_reach':
            self.contract.contract_id.state = 'pending'
            self.contract.contract_id.deadline = self.extend_date
            self.contract.deadline = self.extend_date
            self.contract.state = 'vendor_approval'
        else:
            self.contract.contract_id.deadline = self.extend_date
            self.contract.deadline = self.extend_date


