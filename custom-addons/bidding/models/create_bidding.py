from datetime import datetime ,timedelta
from odoo import api, fields, models, _
# import datetime
import base64
import logging
import xlrd
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo.addons.bus.models.bus import dispatch


_logger = logging.getLogger(__name__)


class Bidding(models.Model):
    _name = "bidding"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bidding"

    contract = fields.Many2one('tenders', string="Contract Request")
    name = fields.Char(string="Bidding No", readonly=True, required=True, copy=False, default='New')
    product_request_id = fields.Many2one('product.request', string="Purchase Request",
                                         domain="[('status', '=', 'wait')]")
    product_request_line_id = fields.Many2one('product.request.line', string="Purchase Request")
    # product = fields.Many2one('product.template', string="Product")
    # quantity = fields.Float(string="Quantity", required=True)
    # unit_price = fields.Float(string="Unit price", required=True)
    start_date = fields.Datetime(string="Start Date and time", required=True)
    time = fields.Float(string='Time')
    status = fields.Selection(
        selection=[('draft', 'DRAFT'), ('bid', 'BIDDING'),('live', 'LIVE'), ('cancel', 'CANCEL'), ('complete', 'COMPLETE')],
        string='Bidding Status',
        default='draft',
        required=True
    )
    deadline = fields.Datetime(string='DeadLine', required=True)
    vendors = fields.Many2many("res.partner", string="Accepted Vendors")
    top_vendor = fields.Many2one("res.partner", string="Top Vendor", tracking=True)
    top_vendor_price = fields.Float(string="Updating Price")
    bid_request_id = fields.Many2one(string="Bid Request ID")
    duration = fields.Float(string="Duration")
    task_timer = fields.Boolean(string='Timer', default=False)
    is_user_working = fields.Boolean(
        'Is Current User Working', compute='_compute_is_user_working',
        help="Technical field indicating whether the current user is working. ")
    bid_cancel_check = fields.Boolean(string="Bid Cancel Button Check")
    request_from = fields.Many2one('res.users', string="Request from")
    terms = fields.Text(string='Terms & Conditions')


    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'New') == 'New':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('bidding') or 'New'
    #
    #     result = super(Bidding, self).create(vals)
    #
    #     return result

    bidding_line_ids = fields.One2many('bidding.line', 'bidding_id',
                                       string='Bidding Lines', tracking=True)
    bidding_products = fields.One2many('bidding.products', 'bidding_product_lines',
                                       string='Bidding Products', tracking=True)
    realtime_update = fields.Boolean(string="Time")
    remaining_time = fields.Char(string="Remaining Time", compute="_compute_remaining_time")
    extension = fields.Integer(string="Extension Duration (minutes)")
    extension_period = fields.Integer(string="Extension Applied in last (minutes)")
    price_history_ids = fields.One2many('bid.price.history', 'bid_id', string="Price History")
    is_bidding_expired = fields.Boolean(string="Is Bidding Expired",store=True)


    def action_open_ctr(self):
        print("in ctr open")
        if self.contract.contracting_method == 'multi':
            print("Multiii")
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract Request',
                'view_mode': 'tree,form',
                'res_model': 'tenders',
                'domain': [('main_rfq', '=', self.contract.main_rfq.id)],
                'target': 'current'
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract Request',
                'view_mode': 'form',
                'res_model': 'tenders',
                'res_id': self.contract.id,

                'target': 'current'
            }

    def update_price(self):
        print("Update function bidding")


        remaining_time_parts = self.remaining_time.split()
        days = int(remaining_time_parts[0][:-1])  # Remove 'd' from the end
        time_parts = remaining_time_parts[1].split(':')
        hours, minutes, seconds = map(int, time_parts)
        remaining_timedelta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


        extension_period_timedelta = timedelta(minutes=self.extension_period)


        if remaining_timedelta < extension_period_timedelta:

            extension_timedelta = timedelta(minutes=self.extension)


            new_deadline = self.deadline + extension_timedelta
            self.deadline = new_deadline

    def bid_again(self):
        for rec in self:
            if rec.status == 'complete':
               
                deadline_plus_15 = rec.deadline + timedelta(minutes=15)
                current_time = fields.Datetime.now()

                if current_time > deadline_plus_15:
                    rec.is_bidding_expired = True

                if not rec.is_bidding_expired:
                    new_deadline = fields.Datetime.now() + timedelta(minutes=15)
                    rec.write({'deadline': new_deadline, 'status': 'live'})

                    bid_requests = self.env['bid.request'].sudo().search(
                        [('bidding_id', '=', rec.id), ('status', 'in', ['complete'])]
                    )
                    for bid in bid_requests:
                        bid.status = 'live'
                        bid.deadline = new_deadline

                    rec.message_post(body="Bidding has been restarted with an extended deadline.")
                else:
                    raise ValidationError(
                        "Re-start time ended. You can only restart bidding 15 minutes after completion.")
            else:
                raise ValidationError("Bidding is already active or not eligible for re-bidding.")


    @api.depends('start_date', 'deadline', 'status')
    def _compute_remaining_time(self):
        for record in self:
            if record.status == 'live' and record.deadline:
                now = datetime.now()
                if now < record.deadline:
                    remaining = record.deadline - now
                    days, seconds = remaining.days, remaining.seconds
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    seconds = seconds % 60
                    record.remaining_time = f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    record.remaining_time = "Expired"
            else:
                record.remaining_time = ""
            if record.status == 'complete':
                bid_request = self.env['bid.request'].sudo().search(
                    [('bidding_id', '=', self.id), ('status', '=', 'live')])
                for bid in bid_request:
                    bid.status = 'complete'


    @api.model
    def _cron_update_bidding_status(self):
        print("Inside CRON")
        now = fields.Datetime.now()

        biddings_to_start = self.search([
            ('status', '=', 'bid'),
            ('start_date', '<=', now),
            ('deadline', '>', now)
        ])
        for rec in biddings_to_start:
            print("inside for")
            if len(rec.vendors) <= 1:
                print("CANCELLLLL",len(self.vendors))
                rec.status = 'cancel'
                rec.message_post(
                                body="Bidding was cancelled, No enough vendors for bidding")
                bid_request = self.env['bid.request'].sudo().search(
                    [('bidding_id', '=', rec.id)])
                for reco in bid_request:
                    reco.status = 'cancel'
                    reco.message_post(
                                body="Bidding was cancelled")

            else:
                print("Inside else")
                rec.write({'status': 'live'})
                for rec0 in biddings_to_start:

                    bid_request = self.env['bid.request'].sudo().search(
                        [('bidding_id', '=', rec0.id), ('status', '=', 'accept')])
                    print("Request ",bid_request)
                    for reco in bid_request:
                        reco.write({'status': 'live'})
                    bid_request_cancel = self.env['bid.request'].sudo().search(
                        [('bidding_id', '=', rec0.id), ('status', '=', 'draft')])
                    for record in bid_request_cancel:
                        record.write({'status': 'cancel'})


                
                crons = self.env['ir.cron'].sudo().search([
                    ('id', 'in', [
                        self.env.ref('lease_management.ir_cron_send_mail').id,

                        self.env.ref('bidding.ir_cron_notify_vendor_bidding').id,
                        self.env.ref('mail.ir_cron_mail_scheduler_action').id
                    ])
                ])
                print("the cron is",crons)
                if crons:
                    crons.sudo().write({'active': False})
                # biddings_to_complete = self.search([
                #     ('status', '=', 'live'),
                #     ('deadline', '<=', now)
                # ])
                # biddings_to_complete.write({'status': 'complete'})
    @api.model
    def create(self, vals_list):
        if vals_list.get('name', 'New') == 'New':
            vals_list['name'] = self.env['ir.sequence'].next_by_code('bidding') or 'New'

        result = super(Bidding, self).create(vals_list)

        return result

    def write(self, vals):
        result = super(Bidding, self).write(vals)
        if 'top_vendor_price' in vals:
            print("WRITEEEEE")
            for record in self:
                self._check_top_vendor_price_change(record)
        return result

    def _check_top_vendor_price_change(self, record):
        print("CHEAKKK FUNNN")
        record.realtime_update = True
        print("CHEAKKK FUNNN111111")
        val = self.env['bus.bus']._sendone(
            'bidding_channel',
            'top_vendor_price_changed',  # Change this to a specific event name
            {
                'type': 'bidding_updated',
                'bidding_id': record.id,
                'event': 'top_vendor_price_changed'  # Add this field
            }
        )
        print("bussss", val)

    def reset_realtime_update(self):
        for rec in self:
            rec.realtime_update = False

    @api.depends('top_vendor_price')
    def _compute_realtime_update(self):
        print("CHEAKKK")
        for record in self:
            self._check_top_vendor_price_change(record)

    # @api.depends('top_vendor_price')
    # def reset_realtime_update(self):
    #     for record in self:
    #         print("workingggg,onchange false")
    #         record.realtime_update = False

    @api.onchange('product')
    def onchange_in_product(self):
        if self.product and self.product_request_id:
            bid = self.env['bidding'].sudo().search(
                [('product_request_id', '=', self.product_request_id.id), ('product', '=', self.product.id)], limit=1)
            if bid:
                raise ValidationError("Bid already created")
            pr_line_data = self.env['product.request.line'].sudo().search(
                [('product_request_id', '=', self.product_request_id.id), ('product', '=', self.product.id)], limit=1)
            if pr_line_data:
                self.quantity = pr_line_data.quantity
                self.unit_price = pr_line_data.unit_price
                self.product_request_line_id = pr_line_data.id
            else:
                raise ValidationError("Product not found")

    @api.onchange('product_request_id')
    def onchange_in_product_request_id(self):
        product_data = self.env['product.request.line'].sudo().search(
            [('product_request_id', '=', self.product_request_id.id)])
        product_list = []
        for product_line in product_data:
            product_list.append(product_line.product.id)
        res = {'domain': {'product': [('id', 'in', product_list)]}}
        return res


    def start_bidding(self):
        if len(self.vendors) <= 1:
            raise ValidationError(_("There aren't enough vendors for the bidding."))
        else:
            bid_request = self.env['bid.request'].sudo().search(
                [('bidding_id', '=', self.id), ('status', '=', 'accept')])
            for bid in bid_request:
                bid.status = 'live'
            self.status = 'live'

    def cancel_bidding(self):
        bidding_vendors = self.env['bid.request'].sudo().search(
            [('bidding_id', '=', self.id), ('status', '!=', 'reject')])
        for vendor_bid in bidding_vendors:
            vendor_bid.status = 'cancel'
        self.status = 'cancel'

    def end_bidding(self):

        crons = self.env['ir.cron'].sudo().search([
            ('id', 'in', [
                self.env.ref('lease_management.ir_cron_send_mail', raise_if_not_found=False).id,
                self.env.ref('bidding.ir_cron_notify_vendor_bidding', raise_if_not_found=False).id,
                self.env.ref('mail.ir_cron_mail_scheduler_action', raise_if_not_found=False).id
            ]),
            ('active', '=', False) 
        ])

        if crons:
            crons.sudo().write({'active': True})
            print("Crons reactivated:", crons)
        print("ENDINGGGG",self.id)
        if self.status == 'live':
            self.status = 'complete'
            # bid_request = self.env['bid.request'].sudo().search(
            #     [('bidding_id', '=', self.id),('status', '=','live')])
            # # for n in bid_request:
            # #     n.status = 'complete'
            bidding_vendors_data = self.env['bidding.line'].sudo().search(
                [('bidding_id', '=', self.id)])
            if not bidding_vendors_data:
                print("the bidding vendors are",bidding_vendors_data)
                raise ValidationError(
                    "No vendors participated in the bidding. Consequently, it is advisable to cancel the bid.")
            if self.contract and self.top_vendor:
                if self.contract.contracting_method == 'multi':
                    tender = self.env['tenders'].sudo().search(
                        [('main_rfq', '=', self.contract.main_rfq.id)])
                    print("the tender is",tender)
                    bid_request_vendor = self.env['bid.request'].sudo().search(
                        [('bidding_id', '=', self.id)])
                    print("Request id", bid_request_vendor)
                    for reco in tender:
                        for record in bid_request_vendor:
                            print("the request",record.request_to.name)
                            if record.request_to == reco.vendor_id:
                                reco.state = 'vendor_approved'
                                print("here")
                                for rec in record.bidding_request_products:
                                    for ctr in reco.contracts_request_line:
                                        if rec.product_id.id == ctr.product_id.id:
                                            ctr.vendor_price = rec.unit_price
                                            ctr.quantity = rec.quantity
                        related_vendor_contracts = self.env['contract'].search([('tender_id', '=', reco.id)])
                        print("the related contracts are", related_vendor_contracts)

                        for vendor_contract in related_vendor_contracts:
                            for record in bid_request_vendor:
                                if record.request_to == vendor_contract.vendor_id:
                                # vendor_contract.contract_status = 'cancel'
                                #     vendor_contract.vendor_request_status = 'accept'
                                    vendor_contract.state = 'accept'
                                    for rec in record.bidding_request_products:
                                        for ctr in vendor_contract.vendor_contract_line:
                                            if rec.product_id.id == ctr.product_id.id:
                                                ctr.vendor_price = rec.unit_price
                                                ctr.quantity = rec.quantity
                    bid_request = self.env['bid.request'].sudo().search(
                        [('bidding_id', '=', self.id), ('status', '=', 'live')])
                    for n in bid_request:
                        n.status = 'complete'

                else:
                    # Set the vendor_id field to the top_vendor record
                    self.contract.vendor_id = self.top_vendor
                    bid_request_vendor = self.env['bid.request'].sudo().search(
                        [('bidding_id', '=', self.id), ('request_to', '=', self.top_vendor.id)], limit=1)
                    print("Request id",bid_request_vendor)
                    for rec in bid_request_vendor.bidding_request_products:
                        for ctr in self.contract.contracts_request_line:
                            if rec.product_id.id == ctr.product_id.id:
                                ctr.unit_price = rec.unit_price


class BiddingProducts(models.Model):
    _name = "bidding.products"
    _rec_name = "product_id"
    bidding_product_lines = fields.Many2one('bidding', string='Bidding')

    product_id = fields.Many2one('product.template', string='Product')
    description = fields.Char(string="Description")
    brand = fields.Char('Brand', related='product_id.brand')
    oem = fields.Char('OEM', related='product_id.oem')
    uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_po_id')
    pack = fields.Float('Pack Size', related='product_id.pack_size')
    quantity = fields.Float(string='Quantity')
    avg_quantity_period = fields.Float(string='Contract Period Avg Qty',compute='_compute_avg_quantity_period')
    unit_price = fields.Float(string='Unit Price')
    denomination = fields.Selection(
        selection=[('0','0'),('0.5', '0.5'), ('1', '1'), ('5', '5'), ('10', '10'),('50', '50'),('100', '100'),('500', '500'),('1000', '1000'),],
        string='Denomination',
        default='0',
        required=True, tracking=True
    )
class BiddingLine(models.Model):
    _name = "bidding.line"
    _description = "Bidding Line"
    _order = 'price asc'

    vendor = fields.Many2one("res.partner", string="Vendors")
    price = fields.Float(string="Price")
    rank = fields.Integer(string="Rank")
    bidding_id = fields.Many2one('bidding', string="Bidding", tracking=True)


class BidPriceHistory(models.Model):
    _name = "bid.price.history"
    _description = "Bid Total Price History"

    bid_id = fields.Many2one('bidding', string="Bidding", required=True, ondelete='cascade')
    bid_request_id = fields.Many2one('bid.request', string="Bid Request", required=True, ondelete='cascade')
    total_price = fields.Float(string="Updated Total Price", required=True)
    update_time = fields.Datetime(string="Update Time", default=fields.Datetime.now)
    vendor_id = fields.Many2one('res.partner', string="Vendor", required=True)


