from odoo import api,fields,models,_
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_upload = fields.Binary(string="Invoice Upload")

    attachment_upload = fields.Many2many('ir.attachment', 'class_ir_attachments_invoice_rel', 'class_id',
                                         'attachment_id',
                                         'Additional Uploads')
    type_name = fields.Char(string="Attachment Name", compute='_compute_type_input')

    @api.depends('message_attachment_count')
    def _compute_type_input(self):
        """Compute the attachment name if an invoice is uploaded."""
        for record in self:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', record.id)
            ])
            print("the attachment is", attachments)
            if attachments:
                record.type_name = attachments[-1].name  # Get the latest attachment name
            elif record.invoice_upload:
                # Use the filename of the invoice_upload field
                record.type_name = "Invoice Uploaded"
            else:
                # Default message if neither has data
                record.type_name = "No invoice uploaded"

    # @api.model
    # def create(self, vals):
    #     res = super(AccountMove, self).create(vals)
    #     # Your logic to search for record in ASN model and assign binary field
    #     if 'invoice_origin' in vals:
    #         print('yessss')
    #         asn_record = self.env['advanced.shipment.notice'].search([('po_no.name', '=', vals['invoice_origin'])], limit=1)
    #         print("asn",asn_record)
    #         if asn_record:
    #             res.invoice_upload = asn_record.invoice_upload
    #
    #     return res