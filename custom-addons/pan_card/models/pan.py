from odoo import models, fields, api



class ManufactureOrder(models.Model):
    _inherit = 'res.partner'

    pan = fields.Char("PAN Number",required=True)
    # vendor_category = fields.Char("Category")
    gst_file = fields.Binary(string='GST Certificate')
    pan_card_file = fields.Binary(string='PAN Card Certificate')
    bank_statement_file = fields.Binary(string='Bank Statement')
    bank_cheque_file = fields.Binary(string='Cancelled Bank Cheque')
    msme_file = fields.Binary(string='MSME Certificate (if Applicable)')
    partnership_deed_file = fields.Binary(string='Partnership Deed (if Applicable)')
    msme_registered = fields.Boolean(string="MSME Registered")
    msme_number = fields.Char(string="MSME Number")

    def auto_correct(self):
        records = self.env['res.partner'].sudo().search([('company_type', '=', 'company')])
        print("total company vendors",len(records))
        for rec in records:
            if rec.msme_file:
                rec.msme_registered = True

    # @api.constrains('msme_number')
    # def _check_msme_number(self):
    #     for record in self:
    #         if record.msme_registered and not record.msme_number:
    #             raise ValidationError("MSME Number is required when MSME Registered is toggled.")

    # @api.onchange('msme_registered')
    # def _onchange_msme_registered(self):
    #     if not self.msme_registered:
    #         self.msme_number = False



class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    branch_code = fields.Char('Branch Code')
    division = fields.Char('Division')
    sub_division = fields.Char('Sub Divisosn')
    region = fields.Char('Region')
    main = fields.Char('Main/Child')
    pan = fields.Char('PAN No')
    gst_file = fields.Binary(string='GST Certificate')
    pan_card_file = fields.Binary(string='PAN Card Certificate')
    bank_statement_file = fields.Binary(string='Bank Statement')
    bank_cheque_file = fields.Binary(string='Cancelled Bank Cheque')
    msme_file = fields.Binary(string='MSME Certificate (if Applicable)')
    partnership_deed_file = fields.Binary(string='Partnership Deed (if Applicable)')


class BankDetailsInh(models.Model):
    _inherit = 'res.partner.bank'

    ifsc = fields.Char("IFSC Code")
    