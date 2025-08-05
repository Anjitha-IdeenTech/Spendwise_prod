from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, MissingError, UserError
from werkzeug.urls import url_encode

class AsNotice(models.Model):
    _name = 'advanced.shipment.notice'

    name = fields.Char(string='Number', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Partner', default=lambda self: self._default_partner_id(),
                                  store=True, force_save=1)
    responsible_id = fields.Many2one('res.partner', string='Responsible User', default=lambda self: self.env.user.partner_id,
                                 readonly=True, store=True, force_save=1)
    purchase_representative = fields.Many2one('res.users', "Purchase Representative", store=True, force_save=1)
    po_no = fields.Many2one('purchase.order', "Purchase Order",
                            domain=lambda self: self._get_po_domain())
    po_name = fields.Char(string="PO Name", store=True,force_save= True)

    transfer = fields.Many2one('stock.picking', "Transfer No", store=True, force_save=1
                               )
    date_approve = fields.Datetime("PO Confirmation Date", store=True, force_save=1)
    asn_date = fields.Datetime("Advanced Shipment Date")
    state = fields.Selection([("draft", "Draft"), ("submit", "Submitted"),("delivered","Quantity Delivered")], string="Status", default="draft")
    invoice_no = fields.Char("Invoice Number")
    lr = fields.Char("LR Number")
    lr_date = fields.Date("LR Date")
    carrier = fields.Char("Carrier No")
    eway = fields.Char("E-way Bill No")
    utr = fields.Char("Payment UTR No")
    invoice_upload = fields.Binary("Upload Invoice")
    workorder_upload = fields.Binary("Additional Documents")
    total_amount = fields.Float("Total" , readonly=1,store=True)
    un_taxed_amount = fields.Float("Untaxed Total" , readonly=1,store=True)
    total_amount_supplied = fields.Float("Total Amount", compute='compute_total_supply_amount',store=True)
    total_amount_tax_supplied = fields.Float("Total Amount", compute='compute_total_supply_amount', store=True)

    user_id = fields.Many2one("res.users", "Login User",compute= '_compute_login',store=True)
    asn_line_ids = fields.One2many('asn.lines', 'asn_lines', string='ASN line')
    total_invoice_amount = fields.Float("Total Invoice Amount" ,store=True)
    branch = fields.Many2one('res.branch', "Branch")

    attachment_upload = fields.Many2many('ir.attachment', 'class_ir_attachments_asn_rel', 'class_id',
                                             'attachment_id',
                                             'Additional Invoice Uploads')

    @api.model
    def _default_partner_id(self):
        # Check if the current user belongs to the 'vendor_group'
        vendor_group = self.env.ref('vendor_portal.group_vendor_portal_user')  # Replace with your actual vendor group ID

        if vendor_group and self.env.user in vendor_group.users:
            return self.env.user.partner_id
        else:
            return False
    @api.onchange('po_no')
    def _compute_po_name(self):
        for record in self:
            if record.po_no:
                record.po_name = record.po_no.name
                if not record.partner_id:
                    record.partner_id = record.po_no.partner_id
            else:
                record.po_name = False

    @api.model
    def create(self, vals):
        record = super(AsNotice, self).create(vals)
        if 'po_no' in vals:
            record._compute_po_name()
        return record

    def write(self, vals):
        res = super(AsNotice, self).write(vals)
        if 'po_no' in vals:
            self._compute_po_name()
        return res

    @api.model
    def _get_po_domain(self):
        user = self.env.user

        domain = [('state', '=', 'purchase')]

        if user.has_group('vendor_portal.group_vendor_portal_user'):
            domain.append(('partner_id', '=', user.partner_id.id))

        return domain
        
    @api.depends('po_no')
    def _compute_login(self):
        self.user_id = self.partner_id.login
        print("User_id ",self.user_id)
    @api.depends('asn_line_ids.provide_qty', 'asn_line_ids.unit_price')
    def compute_total_supply_amount(self):
        for total in self:
            total_amount = 0.0
            total_tax_amount = 0.0
            for line_total in total.asn_line_ids:
                if line_total.provide_qty and line_total.unit_price:
                    line_amount = line_total.provide_qty * line_total.unit_price
                    total_amount += line_amount
                    if line_total.tax:
                        # Accessing the tax rate from the related record
                        tax_rate = line_total.tax.amount / 100.0
                        # Calculating tax amount for this line
                        line_tax_amount = line_amount * tax_rate
                        total_tax_amount += line_tax_amount
            total.total_amount_supplied = total_amount
            total.total_amount_tax_supplied = total_tax_amount +total_amount



    @api.onchange('po_no')
    def _onchange_partners(self):
        for datas in self:
            if datas.po_no:
                print(datas.po_no.order_line)
                datas.asn_line_ids = [(5, 0, 0)]
                datas.date_approve = datas.po_no.date_approve
                datas.purchase_representative = datas.po_no.user_id.id
                datas.branch = datas.po_no.bill_to
                line = []
                records = self.env['advanced.shipment.notice'].sudo().search(
                    [('po_no', '=', datas.po_no.id), ('state', '=', 'submit')])
                asn_qty = 0
                for po_lines in datas.po_no.order_line:
                    print(datas.po_no.name)
                    print(po_lines.product_qty)
                    print(po_lines.price_unit)
                    print(po_lines.taxes_id)
                    for asn_line in records.asn_line_ids:
                        if asn_line.product_id.id == po_lines.product_id.id:
                            asn_qty += asn_line.provide_qty
                    val = {
                        'product_id': po_lines.product_id.id,
                        'quantity': po_lines.product_uom_qty,
                        'unit_price': po_lines.price_unit,
                        'delivered': po_lines.qty_received,
                        'tax': po_lines.taxes_id.id,
                        'sub_total': po_lines.price_subtotal,
                    }
                    line.append((0, 0, val))
                datas.total_amount = datas.po_no.amount_total
                datas.un_taxed_amount = datas.po_no.amount_untaxed

                    # print(line)
                datas.asn_line_ids = line

                transfers = self.env['stock.picking'].sudo().search(
                    [('origin', '=', self.po_no.name), ('state', '=', 'assigned')])
                for transfer in transfers:
                    self.transfer = transfer.id
                    line = []
                    # for stck_lines in transfer.move_ids_without_package:
                    #     val = {
                    #         'product_id': stck_lines.product_id.id,
                    #         'quantity': stck_lines.product_uom_qty,
                    #     }
                    #     line.append((0, 0, val))
                    #     print(line)
                    # datas.asn_line_ids = line
    def action_revert(self):
        for rec in self:
            rec.state = 'draft'
            if rec.partner_id:
                subject = "The ASN has been reverted For PO: %s with ASN Date :%s" % (self.po_no.name, self.asn_date)

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'ASN')], limit=1) or False

                url_params = {
                    'id': self.id,
                    'action': self.env.ref('vendor_po.action_view_all_asn').id,
                    'model': 'advanced.shipment.notice',
                    'view_type': 'form',
                    'menu_id': menu_id.id if menu_id else False,
                }

                params = '/web?#%s' % url_encode(url_params)
                url = base_url + params if base_url else "#"

                print(url)

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"The ASN with the name <strong>{self.name}</strong> Is Reverted Back <strong>{self.po_no.pr_id.name}</strong> with Advance Shipment Date <strong>{self.asn_date}</strong>.<br>"
                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
                )
                # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"
                if author:
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': rec.partner_id.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)

    def action_submit(self):
        print("helloooo")
        # if self.transfer:
        #     if self.transfer.asn_created.state == 'submit':
        #         print(self.transfer.asn_created)
        #         raise ValidationError(_("This Transfer already have an asn, only after validation it can be created"))
        #     else:
        #         self.transfer.asn_created = self.id
        # else:
        #     raise ValidationError(_('No Waiting Transfer for assigning ASN'))
        self.po_name = self.po_no.name
        for rec in self.asn_line_ids:
            if rec.provide_qty > rec.quantity:
                raise ValidationError(_("Suppliable Quantity Cannot be greater than Demand Quantity"))
            elif rec.provide_qty == 0:
                raise ValidationError(_("Suppliable Quantity cannot be zero"))
        if self.invoice_upload:
            print("invoice total", self.total_invoice_amount, self.total_amount_tax_supplied)
            invoice_amount_int = int(self.total_invoice_amount)
            tax_supplied_int = int(self.total_amount_tax_supplied)
            if invoice_amount_int != tax_supplied_int:
                raise ValidationError(
                    _("Invoice Amount doesn't match the calculated amount for the suppliable quantity in PO"))
            print("workkkk")
            if self.asn_date:
                self.state='submit'
                transfer = self.env['stock.picking'].search([('id', '=', self.transfer.id)])
                for tr in transfer:
                    tr.asm_date = self.asn_date
            else:
                raise UserError("Please enter Advanced Shipment Date")
        else:
            raise UserError("Please Upload Invoice")
        if self.po_no.pr_id:
            subject = "ASN Created for PO: %s with ASN Date :%s" % (self.po_no.name, self.asn_date)

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'ASN')], limit=1) or False

            url_params = {
                'id': self.id,
                'action': self.env.ref('vendor_po.action_view_all_asn').id,
                'model': 'advanced.shipment.notice',
                'view_type': 'form',
                'menu_id': menu_id.id if menu_id else False,
            }

            params = '/web?#%s' % url_encode(url_params)
            url = base_url + params if base_url else "#"

            print(url)
            email_to_list = [
                self.env.user.login,
                self.po_no.pr_id.requested_by.login,
                'cor.orders@popularv.com'
            ]

            author = self.env['res.partner'].sudo().search(
                [('name', '=', 'Administrator')], limit=1)

            body = (
                f"Dear User, "
                f"A new ASN with the name <strong>{self.name}</strong> has been raised against Purchase Request by <strong>{self.po_no.pr_id.name}</strong> with Advance Shipment Date <strong>{self.asn_date}</strong>.<br>"
                f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Request</a> <br>"
            )
            # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
            # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
            # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
            # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
            # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
            # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"
            if author:
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': ','.join(email_to_list),
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('advanced.shipment.notice') or _('New')
        res = super(AsNotice, self).create(vals)
        print("is error")
        return res



class AsnLiness(models.Model):
    _name = "asn.lines"

    product_id = fields.Many2one('product.product', string='products',readonly=1,store=True)
    quantity = fields.Float(string='Demand Quantity',readonly=1,store=True)
    provide_qty = fields.Float(string='Quantity Suppliable')
    delivered = fields.Float(string='Delivered',readonly=1,store=True)
    unit_price = fields.Float(string='Unit Price',readonly=1,store=True)
    tax = fields.Many2one('account.tax',"Taxes",readonly=1,store=True)
    sub_total = fields.Char("Sub Total",readonly=1,store=True)
    remark = fields.Char(string="Remark")


    asn_lines = fields.Many2one('advanced.shipment.notice', string='Params')





class InvoicePaymentInherit(models.Model):
    _inherit = 'account.move'

    def action_register_payment(self):
        result = super(InvoicePaymentInherit, self).action_register_payment()
        if self.move_type=='in_invoice':
            purchase_order_id = self.invoice_line_ids.mapped('purchase_line_id').order_id
            print(purchase_order_id.name)
            purchase_id = self.env['purchase.order'].search([('id', '=',purchase_order_id.id)])
            if purchase_id:
                for purchase in purchase_id:
                    if purchase.picking_ids:
                        for picking in purchase.picking_ids:
                            print(picking.name)
                            asn_details = self.env['advanced.shipment.notice'].search([('transfer', '=',picking.id)])
                            if asn_details:
                                print(asn_details)
                                if asn_details.invoice_upload:
                                    print("passs")
                                    return result
                                else:
                                    raise UserError("Please ask vendor to upload Invoice to ASN.")
                            else:
                                return result
                else:
                    return result
            else:
                return result
        else:
            return result



# class ResCompanyInherit(models.Model):
#     _inherit = 'res.company'
#
#     branch_code = fields.Char('Branch Code')
