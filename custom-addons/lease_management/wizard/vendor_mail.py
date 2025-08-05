from odoo import models, fields, api,_
from odoo.tools import html2plaintext
from odoo.exceptions import UserError
from markupsafe import Markup
import logging
_logger = logging.getLogger(__name__)

class SendMailVendorWizard(models.TransientModel):
    _name = 'send.mail.vendor.wizard'
    _description = 'Send Mail Vendor Wizard'

    email_template_id = fields.Many2one('mail.template', string='Email Template', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    email_body = fields.Html(string='Email Body')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    email_from = fields.Char(string='From', readonly=True)
    email_to = fields.Char(string='Recipients', readonly=True)
    email_subject = fields.Char(string='Subject', readonly=True)

    @api.onchange('email_template_id')
    def _onchange_email_template(self):
        if self.email_template_id:
            print("the purchase is id",self.purchase_order_id)

            self.email_from = self.email_template_id.email_from
            self.email_to = self.vendor_id.email  # Assuming vendor has an email field
            self.email_subject = self.email_template_id.subject

            template_ctx = {
                'object': self.purchase_order_id,
                'vendor_id': self.vendor_id,
                'partner_id': self.vendor_id,  # Ensure the vendor data is accessible
                'user_id': self.env.user,

            }

            # Render the email body using _render_field for body_html
            email_body = self.email_template_id._render_field(
                'body_html',
                [self.purchase_order_id.id],
                template_ctx
            )
            self.email_body = Markup(email_body[self.purchase_order_id.id]).replace('\xa0', ' ')
            print("email body", self.email_body)



    def action_send(self):
        # Fetch the email template
        template = self.env['mail.template'].browse(self.email_template_id.id)

        # Log the email template for debugging
        _logger.info("Selected email template: %s", template.name if template else "None")

        # Check if the template is valid
        if not template.exists():
            raise UserError(_("The selected email template does not exist."))

        _logger.info("Sending email to %s using template %s", self.email_to, template.name)

        # Fetch the vendor user
        vendor_user = self.env['res.users'].search([('partner_id', '=', self.vendor_id.id)], limit=1)

        _logger.info("Fetched vendor user: %s (ID: %s)", vendor_user.name, vendor_user.id if vendor_user else "None")

        if not vendor_user:
            raise UserError(_('No vendor user found for the selected vendor. Please add a user for this vendor.'))

        try:
            email_subject = "Create ASN for the corresponding purchase order: {}".format(self.purchase_order_id.name)
            template.subject = email_subject  # Set the dynamic subject

            # Use the email_body from the wizard instead of the template
            email_body = self.email_body

            # Send the email with the customized body
            template.send_mail(
                self.purchase_order_id.id,
                force_send=True,
                email_values={
                    'subject': email_subject,
                    'body_html': email_body
                }
            )
            # Send the email
            # template.send_mail(self.purchase_order_id.id, force_send=True)
            _logger.info("Email sent successfully to %s", vendor_user.email)
            print("msg sent successfully")
        except Exception as e:
            _logger.error("Failed to send email: %s", str(e))
            raise UserError(_("An error occurred while sending the email: %s") % str(e))

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
