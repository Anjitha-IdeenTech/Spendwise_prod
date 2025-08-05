from docutils.frontend import validate_encoding_and_error_handler

from odoo import api, fields, models
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date ,datetime ,timedelta
from odoo.addons.bus.models.bus import dispatch
from werkzeug.urls import url_encode

from werkzeug.urls import url_encode
import pytz




class BidRequest(models.Model):
    _name = "bid.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bidding Request"

    name = fields.Char(string="Bid Request No", readonly=True, required=True, copy=False, default='New')
    # product_id = fields.Many2one('product.template', string="Product", store=True, force_save=True, required=True)
    # quantity = fields.Float(string="Quantity")
    # unit_price = fields.Float(string="Unit price")
    total_price = fields.Float(string="Total price")
    start_date = fields.Datetime(string="Requested Date")
    # time = fields.Float(string='Time')
    deadline = fields.Datetime(string='DeadLine')
    status = fields.Selection(
        selection=[('draft', 'DRAFT'), ('accept', 'ACCEPT'), ('reject', 'REJECT'), ('live', 'LIVE'),
                   ('complete', 'COMPLETE'), ('cancel', 'CANCEL')],
        string='Bidding Status',
        default='draft',
        required=True,
        tracking=True
    )
    # bidding_date = fields.Date(string="Bidding Date")
    request_from = fields.Many2one('res.users', string="Request from")
    request_to = fields.Many2one('res.partner', string="Request To")
    user_id = fields.Many2one('res.users', string="User Id")
    bidding_id = fields.Many2one('bidding', string="Bidding ID")
    product_requested_id = fields.Many2one('product.request', string="Product Request ID")
    product_request_line_id = fields.Many2one('product.request.line', string="Product Requested ID")
    updated_price = fields.Float(string="Price",compute='compute_total_price',store=True)
    rank = fields.Integer(string="Rank")
    bid_status = fields.Selection(selection=[('won', 'WON'), ('lose', 'Lose')],
                                  string='Bid Status',
                                  )

    bidding_request_products = fields.One2many('bidding.products.request', 'bidding_request_product_lines',
                                       string='Bidding Products', tracking=True)
    realtime_update = fields.Boolean(string="Time")
    remaining_time = fields.Char(string="Remaining Time", compute="_compute_remaining_time")
    terms = fields.Text(string='Terms & Conditions')

    @api.model
    def _notify_vendor_before_bidding(self):
        current_time_utc = fields.Datetime.now()
        print("UTC Time:", current_time_utc)
        notification_time_local = current_time_utc + timedelta(minutes=30)
        formatted_time = notification_time_local.replace(second=0, microsecond=0)
        print("Formatted UTC Notification Time for Comparison:", formatted_time)

        # Fetch bid requests that are in draft status
        bid_requests = self.env['bidding'].sudo().search([
            ('status', '=', 'bid'),
            ('start_date', '>=', current_time_utc),
            ('start_date', '<=', notification_time_local)
        ])
        print("the bid request are",bid_requests)

        for bid_request in bid_requests:

            formatted_request_time = bid_request.start_date.replace(second=0, microsecond=0)
            print("time request",formatted_request_time)
            time_diff = formatted_time - formatted_request_time

            # Check if the current notification time is close to the start time (within a 30-minute window)
            if abs(time_diff) <= timedelta(minutes=30):
                print(f"Bidding Request {bid_request.name} is within 30 minutes of start.")
                if bid_request.vendors:
                        for vendor in bid_request.vendors:
                            vendor_user = self.env['res.users'].sudo().search([('partner_id', '=', vendor.id)], limit=1)
                            if vendor_user:

                                subject = "Bidding Starts in 30 Minutes: Join Now!"
                                print("Bidding Request Name:", bid_request.name)

                                # Prepare the email body
                                body = (
                                    f"Dear {vendor.name},<br>"
                                    f"The bidding for <strong>{bid_request.name}</strong> starts in 3 minutes! "
                                    f"Please join the bidding promptly.<br>"
                                )

                                # Create the link to the bidding request
                                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                menu_id = self.env['ir.ui.menu'].sudo().search(
                                    [('name', '=', 'bidding')], limit=1) or False

                                url_params = {
                                    'id': bid_request.id,
                                    'action': self.env.ref('bidding.view_bid_request_form').id,
                                    'model': 'bid.request',
                                    'view_type': 'form',
                                    'menu_id': menu_id.id if menu_id else False,
                                }

                                params = '/web?#%s' % url_encode(url_params)
                                url = base_url + params if base_url else "#"

                                print(url)

                                # Get the author for the email
                                author = self.env['res.partner'].sudo().search(
                                    [('name', '=', 'Administrator')], limit=1)

                                # Complete the body with a call-to-action link
                                body += (
                                    f"<a href='{url}' style='display: inline-block; padding: 10px 20px; "
                                    f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                                    f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Join Bidding</a><br>"
                                )

                                # Prepare the mail values
                                if author:
                                    mail_values = {
                                        'subject': subject,
                                        'body_html': body,
                                        'email_to': vendor_user.login,
                                        'auto_delete': False,
                                        'author_id': author.id
                                    }
                                    # Create and send the email
                                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
                                    mail_record.send()  # Send the email immediately
                                    print(f"Email sent to vendor: {vendor_user.login}")

                            else:
                                print(f"No")

    @api.model
    def _disable_cron_jobs(self):

        live_bidding = self.env['bidding'].sudo().search_count([('status', '=', 'live')])
        if live_bidding > 0:
            crons = self.env['ir.cron'].sudo().search([
                ('id', 'in', [
              
                    self.env.ref('bidding.ir_cron_notify_vendor_bidding').id
                ])
            ])
            if crons:
                crons.write({'active': False})

    @api.depends('deadline', 'status')
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
                    record.status = 'complete'

            else:
                record.remaining_time = ""
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('bid.request') or 'New'
        result = super(BidRequest, self).create(vals)
        return result

    def write(self, vals):
        result = super(BidRequest, self).write(vals)
        if 'rank' in vals:
            print("WRITEEEEE")
            for record in self:
                self._check_top_vendor_rank(record)
        return result

    def _check_top_vendor_rank(self, record):
        print("CHEAKKK FUNNN")
        record.realtime_update = True
        print("CHEAKKK FUNNN111111")
        self.env['bus.bus']._sendone(
            'bid_request_channel',
            'top_vendor_rank',  # Change this to a specific event name
            {
                'type': 'bid_request_updated',
                'bidding_id': record.id,
                'event': 'top_vendor_rank'  # Add this field
            }
        )
        print("bussss")

    def reset_realtime_update(self):
        for rec in self:
            rec.realtime_update = False

    @api.depends('top_vendor_price')
    def _compute_realtime_update(self):
        print("CHEAKKK")
        for record in self:
            self._check_top_vendor_rank(record)

    @api.depends('bidding_request_products.quantity', 'bidding_request_products.unit_price')
    def compute_total_price(self):
        for record in self:
            total=0
            for rec in record.bidding_request_products:
                print("unit,quan", rec.quantity, rec.unit_price)
                total += rec.quantity * rec.unit_price
            # record.total_price = total
            record.updated_price = total

    def action_accept_bid(self):
        print("action_accept_bid")
        print(self.bidding_id.id)
        bidding_data = self.env['bidding'].sudo().search(
            [('id', '=', self.bidding_id.id), ('status', '=', 'bid')], limit=1)
        if not bidding_data:
            self.status = 'reject'
            raise ValidationError("The bidding process has already started or been completed")
        bidding_data.write({'vendors': [(4, self.request_to.id)]})
        self.updated_price = self.total_price
        self.status = "accept"

    def action_reject_bid(self):
        print("action_reject_bid")
        self.status = "reject"

    def action_draft_bid(self):
        print("action_draft_bid")
        self.status = "draft"

    # def action_open_bid(self):
    #     print(self.id)
    #     vendor_bid_data = self.env['vendor.bid'].sudo().search(
    #         [('bid_request_id', '=', self.id)])
    #     print(vendor_bid_data)
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Vendor Bid',
    #         'res_model': 'vendor.bid',
    #         'domain': [('id', 'in', vendor_bid_data.ids)],
    #         'view_mode': 'tree,form',
    #         'target': 'current'
    #     }

    def update_price(self):
        print("Update function")
        current_date = date.today()
        print("current_date ", current_date)
        bidding = self.env['bidding'].sudo().search(
            [('id', '=', self.bidding_id.id), ('status', '=', 'live')], limit=1)
        if bidding:
            total_price = sum(line.unit_price for line in self.bidding_request_products)
            self.total_price = total_price

            # Log the total price change into bid.price.history
            self.env['bid.price.history'].create({
                'bid_id':self.bidding_id.id,
                'bid_request_id': self.id,
                'total_price': total_price,
                'vendor_id': self.request_to.id,
            })
            # print("bidding.top_vendor_price : ", bidding.top_vendor_price)
            # print("self.updated_price : ", self.updated_price)
            # if bidding.top_vendor_price > self.updated_price:

                # for value in self.bidding_request_products:
                #     if value.old_price-value.unit_price<=float(value.denomination):
                #         print("old price,unit price,denomination,",value.old_price,value.unit_price,float(value.denomination))
                #         min_difference = float(value.denomination)
                #         product_name = value.product_id.name
                #         raise ValidationError("There should be a minimum difference of %s for product %s" % (min_difference, product_name))

                # Convert remaining_time string to timedelta
            remaining_time_parts = self.remaining_time.split()
            days = int(remaining_time_parts[0][:-1])  # Remove 'd' from the end
            time_parts = remaining_time_parts[1].split(':')
            hours, minutes, seconds = map(int, time_parts)
            remaining_timedelta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

            # Convert bidding.extension to timedelta (assuming it's stored in minutes)
            extension_period_timedelta = timedelta(minutes=bidding.extension_period)

            # Check if remaining time is less than extension_period
            if remaining_timedelta < extension_period_timedelta:
                extension_timedelta = timedelta(minutes=bidding.extension)
                new_deadline = bidding.deadline + extension_timedelta
                bidding.deadline = new_deadline
                    # Update deadline for all bid.request records with the same bidding_id
                related_bid_requests = self.env['bid.request'].sudo().search(
                    [('bidding_id', '=', self.bidding_id.id)])
                related_bid_requests.sudo().write({'deadline': new_deadline})
                self.bidding_id.update_price()
                # self.bidding_id.deadline = new_deadline

            for rec in self.bidding_id.bidding_line_ids:

                if rec.vendor.id == self.request_to.id:
                    rec.price = self.updated_price

            # vendor_bid = self.env['vendor.bid'].sudo().search(
            #     [('request_to', '=', self.request_to.id), ('bid_id', '=', self.bid_id.id)], limit=1)
            # if vendor_bid:
            #     vendor_bid.updated_price = self.updated_price

            bid_request_vendor = self.env['bid.request'].sudo().search(
                [('bidding_id', '=', self.bidding_id.id)], order='updated_price asc')
            num = 0
            print(bid_request_vendor)
            for vendors in bid_request_vendor:
                print("vendor",vendors.request_to.name,vendors.updated_price)
                num += 1
                vendors.rank = num
                for rec in self.bidding_id.bidding_line_ids:

                    if rec.vendor.id == vendors.request_to.id:
                        rec.rank = num
                if vendors.rank == 1:
                    bidding = self.env['bidding'].sudo().search(
                        [('id', '=', self.bidding_id.id)], limit=1)
                    bidding.top_vendor = vendors.request_to
                    bidding.top_vendor_price = vendors.updated_price
                print("vendors", vendors.rank)


            self.bidding_id.bid_cancel_check = True
            # if remaining_timedelta < extension_timedelta:
                # return {
                #     'deadline_extended': deadline_extended,
                #     'new_deadline': new_deadline.isoformat() if new_deadline else None
                # }
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'message': 'Price updated successfully'}
            }
            # else:
            #     raise ValidationError("The current price of the product is lower than the price you requested.")

class BiddingProducts(models.Model):
    _name = "bidding.products.request"
    _rec_name = "product_id"
    bidding_request_product_lines = fields.Many2one('bid.request', string='Bidding')

    product_id = fields.Many2one('product.template', string='Product')
    description = fields.Char(string="Description")
    brand = fields.Char('Brand', related='product_id.brand')
    oem = fields.Char('OEM', related='product_id.oem')
    uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_po_id')
    pack = fields.Float('Pack Size', related='product_id.pack_size')
    quantity = fields.Float(string='Quantity')
    avg_quantity_period = fields.Float(string='Contract Period Avg Qty',compute='_compute_avg_quantity_period')
    unit_price = fields.Float(string='Unit Price')
    old_price = fields.Float(string='Old Price')
    denomination = fields.Selection(
        selection=[('0', '0'), ('0.5', '0.5'), ('1', '1'), ('5', '5'), ('10', '10'), ('50', '50'), ('100', '100'),
                   ('500', '500'), ('1000', '1000'), ],
        string='Denomination',
        default='0',
        required=True, tracking=True
    )


    # @api.onchange('unit_price')
    # def onchange_unit_price(self):
    #     print("checkinggggggggggg")
    #     for record in self:
    #         remaining_time_str = record.bidding_request_product_lines.bidding_id.remaining_time
    #         print(f"Remaining Time String: {remaining_time_str}")

    #         try:
    #             remaining_time_parts = remaining_time_str.split()
    #             days = int(remaining_time_parts[0][:-1])  
    #             time_parts = remaining_time_parts[1].split(':')
    #             hours, minutes, seconds = map(int, time_parts)

    #             remaining_timedelta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    #             print(f"Parsed Remaining Time: {remaining_timedelta}")

                
    #             if remaining_timedelta < timedelta(minutes=1):
    #                 print("Remaining time is less than 1 minute! Extending deadline by 1 min.")

                    
    #                 bidding_record = record.bidding_request_product_lines.bidding_id
    #                 print("the id",bidding_record)
    #                 new_deadline = bidding_record.deadline + timedelta(minutes=1)
    #                 bidding_record.deadline = new_deadline
    #                 print("new,", new_deadline)

                    
    #                 related_bid_requests = self.env['bid.request'].sudo().search(
    #                     [('bidding_id', '=', bidding_record.id)]
    #                 )
    #                 print("the new ded",new_deadline)
    #                 related_bid_requests.sudo().write({'deadline': new_deadline})


    #         except Exception as e:
    #             print(f"Error parsing remaining time: {e}")

