from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date

class VendorPrLimit(models.Model):
    _name = 'vendor.limit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vendor PR Limit'
    _rec_name = 'vendor_id'


    vendor_id = fields.Many2one('res.partner', string="Vendor",tracking=True)
    start_date = fields.Date(string="From Date", default=lambda self: fields.Date.today(),tracking=True)
    end_date = fields.Date(string="To Date",tracking=True )
    vendor_budget = fields.Float(string="Vendor Budget",tracking=True)
    amount_used = fields.Float(string="Vendor PR Amount Used")
    balance_amount = fields.Float(string="Vendor Remaining Balance",compute='_compute_balance_amount',save=True)
    status = fields.Selection(
        selection=[('draft', 'DRAFT'),('active','Active'),('expire','Expired'),('terminate','Terminated')],
        string='Status',
        default='draft',
        required=True
        , tracking=True
    )
    terminate_date = fields.Date(string="Termination Date" ,tracking=True)
    active = fields.Boolean(string="Active", readonly=True,compute='_compute_active')

    @api.depends('status')
    def _compute_active(self):
        for record in self:
            record.active = record.status == 'active'

    @api.depends('vendor_budget', 'amount_used')
    def _compute_balance_amount(self):
        for record in self:
            record.balance_amount = record.vendor_budget - record.amount_used

    def activate(self):
        self.status = 'active'

    def log_reason_wizard(self):
        return {
            'name': 'Log Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'log.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


    @api.model
    def create(self, vals):
        vendor = vals.get('vendor_id')
        records = self.env['vendor.limit'].sudo().search(
                            [('vendor_id', '=', vendor),('status','=','active')], limit=1)
        if records:
            raise UserError(_("A vendor can only have one active limit record."))
            return False
        else:
            result = super(VendorPrLimit, self).create(vals)

            return result
class LogReasonWizard(models.TransientModel):
    _name = 'log.reason.wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    reason = fields.Text(string="Reason")

    def confirm_reason(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        active_record = self.env[active_model].browse(active_id)
        for rec in active_record:
            rec.status = 'terminate'
            rec.terminate_date = date.today()
            rec.message_post(
                body="Terminated on %s due to reason: %s" % (date.today(), self.reason)
            )
        return {'type': 'ir.actions.act_window_close'}
