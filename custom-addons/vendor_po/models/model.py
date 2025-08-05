from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, MissingError, UserError

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    suppl_qty = fields.Float(string='Vendor Suppliable',store = True)
class StockDeliveryDate(models.Model):
    _inherit = 'stock.picking'

    delivery_commitment = fields.Datetime(string="Delivery Commitment Date", store=True)
    asm_date = fields.Datetime(string="Advanced Shipment Date", store=True)
    asn_created = fields.Many2one('advanced.shipment.notice', string='ASN',domain="[('po_name', '=', origin),('state','=','submit')]",default=False)
    invoice = fields.Binary("Vendor Invoice")
    attachment_upload = fields.Many2many('ir.attachment', 'class_ir_attachments_receive_rel', 'class_id',
                                             'attachment_id',
                                             'Additional Uploads')
    bill_need = fields.Boolean("Bill Need",compute='compute_bill_need',default = True)
    
    @api.onchange('asn_created')
    def compute_bill_need(self):
        if self.asn_created:
            self.bill_need = False
        else:
            self.bill_need = True

    @api.model
    def create(self, vals):

        vals['asn_created'] = False
        return super(StockDeliveryDate, self).create(vals)
    # def _get_asn_domain(self):
    #     # Print debugging information to understand the context
    #     print("Current stock picking ID:", self.id)
    #     print("Current stock picking origin:", self.origin)
    #
    #     # Search for advanced shipment notices related to the current stock picking
    #     asn_records = self.env['advanced.shipment.notice'].sudo().search(
    #         [('po_name', '=', self.origin), ('state', '=', 'submit')])
    #     print("Found ASN records:", asn_records)
    #
    #     # Construct the domain based on whether ASN records are found or not
    #     if asn_records:
    #         domain = [('id', 'in', asn_records.ids)]
    #     else:
    #         domain = [('id', '=', False)]
    #
    #     print("Computed domain:", domain)
    #     return domain

    def button_validate(self):
        for record in self:
            if record.origin:
                # Check if there is any ASN with po_name equal to origin
                asn_count = self.env['advanced.shipment.notice'].sudo().search_count([('po_name', '=', record.origin),('state','=','submit')])
                if asn_count > 0 and not record.asn_created :
                    raise ValidationError(
                        "An ASN already exists for this origin. Please choose another or modify the existing ASN.")
        # Call the parent class method to retain the original functionality
        super().button_validate()
        # Add your custom logic here
        stock_picking_ids = self.env['stock.picking'].sudo().search([
            ('origin', '=', self.origin), ('state', '=', 'assigned')])
        if not stock_picking_ids:
            po =  self.env['purchase.order'].sudo().search([
            ('name', '=', self.origin)])
            model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', po.id), ('status', '=', 'open')])

            if pending_action:
                for rec in pending_action:
                    rec.name = f"{po.name} Complete Products Received"
                    rec.status = 'closed'
        else:
            po = self.env['purchase.order'].sudo().search([
                ('name', '=', self.origin)])
            model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', po.id), ('status', '=', 'open')])

            if pending_action:
                for rec in pending_action:
                    rec.name = f"{po.name} Partial Products Received"
        self.user_id = self.env.user.id

    @api.onchange('asn_created')
    def onchange_done(self):
        for rec in self.move_ids_without_package:
            for record in self.asn_created.asn_line_ids:
                if rec.product_id == record.product_id:
                    rec.suppl_qty = record.provide_qty
                    rec.quantity_done = record.provide_qty
        self.asm_date = self.asn_created.asn_date

    def view_asn(self):
        print("ASNNN")
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Advanced Shipment Notice',
                'view_mode': 'tree,form',
                'res_model': 'advanced.shipment.notice',
                'domain': [('po_name', '=', rec.origin)],
                'target': 'current'
            }
    def cancel_balance_stock(self):
        asn = self.env['advanced.shipment.notice'].sudo().search_count(
            [('po_name', '=', self.name), ('state', '=', 'submit')])
        if asn:
            if self.asn_created :
                for rec in self.move_ids_without_package:
                    if rec.quantity_done != 0:
                        break

                else:
                    raise ValidationError(_("Quantity is zero , Can cancel directly"))

                stock_picking_count = self.env['stock.picking'].sudo().search_count([
                    ('origin', '=', self.origin),
                ])

                print("count",stock_picking_count)
                if stock_picking_count <= 1:
                    raise ValidationError(
                        _('Only one Transfer ,Canceling the purchase order might be more appropriate.'))


                stock_picking_ids2 = self.env['stock.picking'].sudo().search([
                    ('origin', '=', self.origin), ('state', '=', 'assigned')
                    # Assuming 'origin' is a field on the stock.picking model
                ])
                print("self", stock_picking_ids2)
                self.with_context(skip_backorder=True).button_validate()
                stock_picking_ids = self.env['stock.picking'].sudo().search([
                    ('origin', '=', self.origin), ('state', '=', 'assigned')
                    # Assuming 'origin' is a field on the stock.picking model
                ])
                print("stock_picking_ids",stock_picking_ids)
                stock_picking_ids.action_cancel()
                po = self.env['purchase.order'].sudo().search([
                    ('name', '=', self.origin)])
                model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', po.id), ('status', '=', 'open')])

                if pending_action:
                    for rec in pending_action:
                        rec.status = 'closed'
            else:
                raise ValidationError(_("No ASN selected"))



class PurchaseVendorUser(models.Model):
    _inherit = 'purchase.order'

    vendor_user_id = fields.Many2one('res.users', string='Vendor User', compute='_compute_vendor_user_id',
        store=True,readonly=False)
    delivery_commitment = fields.Boolean("Delivery Commited")
    asm_date = fields.Boolean("ASN Date")
    menu_1 = fields.Boolean("Second menu")

    def view_asn(self):
        print("ASNNN")
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Advanced Shipment Notice',
                'view_mode': 'tree,form',
                'res_model': 'advanced.shipment.notice',
                'domain': [('po_name', '=', rec.origin)],
                'target': 'current'
            }

    @api.model
    def create(self, values):
        if self.env.user.has_group('vendor_portal.group_vendor_portal_user'):
            raise UserError(_('You are not allowed to create/ edit PO. Please contact Administrator.'))

        record = super(PurchaseVendorUser, self).create(values)
        record._compute_vendor_user_id()
        return record
    def unlink(self):
        if self.env.user.has_group('vendor_portal.group_vendor_portal_user'):
            raise UserError(_('You are not allowed to delete this PO. Please contact Administrator.'))
        else:
            return super(PurchaseVendorUser, self).unlink()

    def toggle_active(self):
        for order in self:
            if self.env.user.has_group('vendor_portal.group_vendor_portal_user'):
                raise UserError(_('You can not archive/ unarchive this PO. Please contact Administrator.'))
            return super(PurchaseVendorUser, order).toggle_active()

    def action_rfq_send(self):
        self.email_sent = True
        print("hiiiiiiiiiiiiiiiiii")
        if self.env.user.has_group('vendor_portal.group_vendor_portal_user'):
            raise UserError(_('You are not allowed to delete this PO. Please contact Administrator.'))
        else:
            return super(PurchaseVendorUser, self).action_rfq_send()






    def button_delivery_commit(self):
        print("helloooo")
        action = self.env["ir.actions.actions"]._for_xml_id('vendor_po.update_commitment_date_action')
        action['context'] = {'default_purchase_id': self.id}

        # action = self.env.ref(
        #     'sale_confirmation_date.update_confirmation_date_action').read()[0]
        return action

    def button_adv_shipment_date(self):
        print("hiiiiiiiiiiiii")

        transfer_lines =[]
        for transfer in self.picking_ids:
            print(transfer)
            if transfer.state == 'assigned':
                for lines in transfer.move_ids_without_package:
                    print(lines)
                    transfer_lines.append((0, 0, {
                        'product_id': lines.product_id.id,
                        'quantity': lines.product_uom_qty,
                        # 'p_line_lot': lines.lot_name
                    }))
                    print(transfer_lines)

                vals={

                    'partner_id': self.partner_id.id,
                    'purchase_representative': self.user_id.id,
                    'po_no': self.id,
                    'transfer': transfer.id,
                    'asn_line_ids': transfer_lines,
                    'date_approve': self.date_approve,

                }
                # asn = self.env['advanced.shipment.notice'].search([('transfer', '=', transfer.id,)], limit=1) or False
                # if asn:
                #     raise UserError(
                # f"Advanced Shipment Notice for {transfer.name} is already created.")


                new_package = self.env['advanced.shipment.notice'].create(vals)
                self.env.cr.commit()
                new_pack = self.env['advanced.shipment.notice'].search([('id', '=', new_package.id)], limit=1) or False
                context = dict(self.env.context)
                context['form_view_initial_mode'] = 'edit'
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Advanced Shipment Notice',
                    'res_model': 'advanced.shipment.notice',
                    'view_mode': 'form',
                    'res_id': new_package.id,
                    'target': 'current',
                    'context': {
                        'form_view_initial_mode': 'edit',
                    },

                }



        # action = self.env["ir.actions.actions"]._for_xml_id('vendor_po.update_advanced_shipmnt_date_action')
        # action['context'] = {'default_purchase_id': self.id}
        #
        # return action

    @api.depends('vendor_user_id')
    def _compute_vendor_user_id(self):
        # print("ddddddd")
        # print("partner", self.partner_id.id)
        # print("partner name", self.partner_id.name)
        # for user in self:
        for rec in self:
            if rec.partner_id:
                vendor_partner_id = self.env['res.partner'].sudo().search([
                    ('id', '=', rec.partner_id.id)])
                print("partner vendor",vendor_partner_id)
                vendor_user_id = self.env['res.users'].sudo().search([
                ('partner_id', '=', rec.partner_id.id)])
                print(vendor_user_id.login)
                print(vendor_user_id.id)
                if vendor_user_id:
                    self.vendor_user_id = vendor_user_id.id
                else:
                    self.vendor_user_id = False
            else:
                self.vendor_user_id = False

    def cancel_balance(self):
        stock_picking_ids = self.env['stock.picking'].sudo().search([
            ('origin', '=', self.name),('state','=','assigned')  # Assuming 'origin' is a field on the stock.picking model
        ])
        stock_picking_count = self.env['stock.picking'].sudo().search_count([
            ('origin', '=', self.name),
        ])
        asn = self.env['advanced.shipment.notice'].sudo().search_count(
            [('po_name', '=', self.name), ('state', '=', 'submit')])
        print("stock picking",stock_picking_ids)
        if stock_picking_ids:
            if stock_picking_ids and asn:

                print("asn lines",asn)
                raise (_('Use Cancel Balance from the pending transfer ,since an Advanced Shipment Notice is present for the transfer '))
            else :
                if stock_picking_count <= 1 :
                    raise ValidationError(_('Only one Transfer ,Canceling the purchase order might be more appropriate.'))

                else:
                    stock_picking_ids.action_cancel()
                    
                    model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
                    pending_action = self.env['pending.actions'].sudo().search(
                        [('model', '=', model.id), ('record', '=', self.id), ('status', '=', 'open')])

                    if pending_action:
                        for rec in pending_action:
                            rec.status = 'closed'

        else:
            raise ValidationError(_('NO transfer is pending'))




class Partner(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char(
        string='GST NO',
        index=True,
        help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements."
    )

