from odoo import models, fields, api
from odoo.exceptions import ValidationError

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

   
    def unlink(self):
        for attachment in self:
            if attachment.datas:
                if attachment.res_model == 'tenders':
                    record = self.env['tenders'].sudo().search([('id', '=', attachment.res_id)], limit=1)
                    if record.state not in ('draft', 'rfq'):
                        raise ValidationError("Deletion of this attachment is not allowed.")

                elif attachment.res_model == 'product.request':
                    record = self.env['product.request'].sudo().search([('id', '=', attachment.res_id)], limit=1)
                    if record.status not in ('draft', 'revert'):
                        raise ValidationError("Deletion of this attachment is not allowed.")

                elif attachment.res_model == 'product.lease':
                    record = self.env['product.lease'].sudo().search([('id', '=', attachment.res_id)], limit=1)
                    if record.state not in ('draft', 'revert'):
                        raise ValidationError("Deletion of this attachment is not allowed.")
        return super(IrAttachment, self).unlink()