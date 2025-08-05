from odoo import api, fields, models ,_
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date, datetime
from werkzeug.urls import url_encode


class AddToBiddingWizard(models.TransientModel):
    _name = "add.to.bidding.wizard"
    _description = "Bidding"


    name = fields.Char(string="Name")
    # bidding = fields.Many2one('bidding', string="Bidding Group", domain="[('status', '=', 'draft')]")
    # product_id = fields.Many2one('product.template', string="Product", domain= 'product_id_domain')
    # quantity = fields.Float(string="Quantity")
    # unit_price = fields.Float(string="Unit Price")
    # total_price = fields.Float(string="Total Price")
    # status = fields.Selection([
    #     ('draft', 'draft'),
    #     ('accept', 'Accept'),
    #     ('cancel', 'Cancel')], string='Tender Status')
    requested_date = fields.Datetime(string="Start date and time")
    time = fields.Float(string='Time')
    deadline = fields.Datetime(string='DeadLine')
    # expected_date = fields.Date(string="Expected Date")
    # bidding_date = fields.Date(string="Bidding Date")
    request_from = fields.Many2one('res.users', string="Request from")
    request_to = fields.Many2many('res.partner', string="Request To", domain="[('id', 'in', allowed_partner_ids)]")
    # product_requested_id = fields.Integer(string="Product Request Id")
    user_id = fields.Many2one('res.users', string="User")
    bidding_id = fields.Many2one('bidding', string="Bidding ID")
    pr_id = fields.Many2one('product.request', string="PR ID")
    tender_id = fields.Many2one('tenders', string="tenders")
    product_id_domain = fields.Char(string="Product ID Domain")
    extension = fields.Integer(string="Extension Duration (minutes)")
    extension_period = fields.Integer(string="Extension Applied in last (minutes)")
    # @api.onchange('product_id')
    # def _compute_quantity_price(self):
    #     if self.tender_id and self.product_id:
    #         for rec in self.tender_id.contracts_request_line:
    #             if rec.product_id == self.product_id:
    #                 self.quantity = rec.quantity
    #                 self.unit_price = rec.unit_price

    allowed_partner_ids = fields.Many2many('res.partner', compute='_compute_allowed_partner_ids')
    terms = fields.Text(string='Terms & Conditions')

    @api.model
    def _compute_allowed_partner_ids(self):
        for record in self:
            if record.tender_id and record.tender_id.contracting_method == 'multi':
                tender_records = self.env['tenders'].sudo().search([
                    ('main_rfq', '=', record.tender_id.main_rfq.id),

                ])
                print("domain", tender_records)
                record.allowed_partner_ids = tender_records.mapped('vendor_id')
            else:
                record.allowed_partner_ids = self.env['res.partner'].search([])

    @api.onchange('tender_id')
    def onchange_tender_id(self):
        self._compute_allowed_partner_ids()

    def add_to_bidding(self):
        for record in self.request_to:
            if not record.login:
                raise ValidationError(_("No user for the selected vendor: %s" % record.name))
        if self.tender_id.contracting_method == 'multi':
            tender_records = self.env['tenders'].sudo().search(
                [('main_rfq', '=', self.tender_id.main_rfq.id), ('state', '=', 'vendor_approved')]
            )

            total_price = 0
            product_lines = []
            if tender_records:
                # Find the tender record with the lowest total_vendor_price
                lowest_tender = min(tender_records, key=lambda t: t.total_vendor_price)
                print("lowest tender",lowest_tender)
                for line in lowest_tender.contracts_request_line:
                    product_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'unit_price': line.vendor_price,

                    }))
                    total_price += line.quantity * line.vendor_price
            bid = self.env['bidding']
            rec = bid.create({
                'status': 'bid',
                # 'total_price': self.quantity * self.unit_price,
                'top_vendor_price': total_price,
                'start_date': self.requested_date,
                # 'time': self.time,
                'deadline': self.deadline,
                # 'status': self.status,
                # 'bidding_date': datetime.now(),
                'request_from': self.env.user.id,
                # 'request_to': self.request_to.ids,
                # 'user_id': self.request_to.user_id.id,
                # 'bidding_id': self.bidding.id,
                'bidding_products': product_lines,
                'product_request_id': self.tender_id.product_requested_id.id,
                'contract': self.tender_id.id,
                'extension': self.extension,
                'extension_period': self.extension_period,
                'terms': self.terms,
            })

            if self.tender_id:
                self.tender_id.bidding_id = rec.id
            line = self.env['bidding.line']
            for vendor in self.request_to:
                lines = line.create({
                    'vendor': vendor.id,
                    'price': total_price,
                    'bidding_id': rec.id,
                })

            bid_request = self.env['bid.request']
            print("out")
            for record in self.request_to:
                print("the record is for test", record)

                user = self.env['res.users'].search([('partner_id', '=', record.id)]).id,
                print("check user", user)
                bid_name=bid_request.create({
                    # 'product_id': self.product_id.id,
                    # 'quantity': self.quantity,
                    # 'unit_price': self.unit_price,
                    'total_price': total_price,
                    'start_date': self.requested_date,
                    # 'time': self.time,
                    'deadline': self.deadline,
                    # 'status': self.status,
                    # 'bidding_date': self.requested_date,

                    'request_from': self.request_from.id,
                    'request_to': record.id,

                    'bidding_id': self.tender_id.bidding_id.id,
                    'product_requested_id': self.pr_id.id,
                    'bidding_request_products': product_lines,
                    'user_id': user,
                    'terms': self.terms,
                })
                subject = "New Bidding Request Raised: %s" % bid_name.name
                print("Name", record.name)

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Bidding')], limit=1) or False

                url_params = {
                    'id': record.id,
                    'action': self.env.ref('bidding.view_bid_request_details_tree').id,
                    'model': 'bid.request',
                    'view_type': 'form',
                    'menu_id': menu_id.id if menu_id else False,
                }

                params = '/web?#%s' % url_encode(url_params)
                url = base_url + params if base_url else "#"

                print(url)
                # email_to_list = [user.email if user.email else user.login for user in buyer_users]

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A new Bidding Request with the name <strong>{bid_name.name}</strong> has been raised.Please Accept.<br>"
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
                    user = self.env['res.users'].search([('partner_id', '=', record.id)])
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': user.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
            self.tender_id.bid_request_check = True
        else:
            total_price = 0
            product_lines = []
            for line in self.tender_id.contracts_request_line:
                product_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity':line.quantity,
                    'unit_price': line.unit_price,

                }))
                total_price += line.quantity * line.unit_price
            bid = self.env['bidding']
            rec = bid.create({
                'status':'bid',
                # 'total_price': self.quantity * self.unit_price,
                'top_vendor_price':total_price,
                'start_date': self.requested_date,
                # 'time': self.time,
                'deadline': self.deadline,
                # 'status': self.status,
                # 'bidding_date': datetime.now(),
                'request_from': self.env.user.id,
                # 'request_to': self.request_to.ids,
                # 'user_id': self.request_to.user_id.id,
                # 'bidding_id': self.bidding.id,
                'bidding_products':product_lines,
                'product_request_id': self.tender_id.product_requested_id.id,
                'contract': self.tender_id.id,
                'extension': self.extension,
                'extension_period': self.extension_period,
                'terms': self.terms,
            })

            if self.tender_id:
                self.tender_id.bidding_id = rec.id
            line = self.env['bidding.line']
            for vendor in self.request_to:
                lines = line.create({
                    'vendor': vendor.id,
                    'price': total_price,
                    'bidding_id': rec.id,
                })


            bid_request = self.env['bid.request']
            print("out")
            for record in self.request_to:
                print("the record is for test",record)

                user= self.env['res.users'].search([('partner_id', '=', record.id)]).id,
                print("check user",user)
                bid_name=bid_request.create({
                    # 'product_id': self.product_id.id,
                    # 'quantity': self.quantity,
                    # 'unit_price': self.unit_price,
                    'total_price': total_price,
                    'start_date': self.requested_date,
                    # 'time': self.time,
                    'deadline': self.deadline,
                    # 'status': self.status,
                    # 'bidding_date': self.requested_date,

                    'request_from': self.request_from.id,
                    'request_to': record.id,

                    'bidding_id': self.tender_id.bidding_id.id,
                    'product_requested_id': self.pr_id.id,
                    'bidding_request_products':product_lines,
                    'user_id': user,
                    'terms': self.terms,
                })
                subject = "New Bidding Request Raised: %s" % bid_name.name
                print("Name", record.name)

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                menu_id = self.env['ir.ui.menu'].sudo().search(
                    [('name', '=', 'Bidding')], limit=1) or False

                url_params = {
                    'id': record.id,
                    'action': self.env.ref('bidding.view_bid_request_details_tree').id,
                    'model': 'bid.request',
                    'view_type': 'form',
                    'menu_id': menu_id.id if menu_id else False,
                }

                params = '/web?#%s' % url_encode(url_params)
                url = base_url + params if base_url else "#"

                print(url)
                # email_to_list = [user.email if user.email else user.login for user in buyer_users]

                author = self.env['res.partner'].sudo().search(
                    [('name', '=', 'Administrator')], limit=1)

                body = (
                    f"Dear User, "
                    f"A new Bidding Request with the name <strong>{bid_name.name}</strong> has been raised.Please Accept.<br>"
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
                    user = self.env['res.users'].search([('partner_id', '=', record.id)])
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': user.login,
                        'auto_delete': False,
                        'author_id': author.id
                    }
                    mail_record = self.env['mail.mail'].sudo().create(mail_values)
            self.tender_id.bid_request_check = True


    # @api.model
    # def default_get(self, fields_list):
    #     res = super(AddToBiddingWizard, self).default_get(fields_list)
    #     tender_id = self.env.context.get('default_tender_id')
    #     if tender_id:
    #         tender = self.env['tenders'].browse(tender_id)
    #         if tender:
    #             contract_lines = tender.contracts_request_line
    #             product_ids = contract_lines.mapped('product_id.id')
    #             res['product_id_domain'] = [('id', 'in', product_ids)] if product_ids else [('id', '!=', 0)]
    #     return res
    #
    # product_id_domain = fields.Char(string="Product ID Domain")
    # @api.model
    # def default_get(self, fields):
    #     res = super(AddToBiddingWizard, self).default_get(fields)
    #     # Set the value of example_field based on the context
    #     res['name'] = self.env.context.get('name')
    #     res['product_id'] = self.env.context.get('product_id')
    #     res['pr_id'] = self.env.context.get('pr_id')
    #     res['quantity'] = self.env.context.get('quantity')
    #     res['unit_price'] = self.env.context.get('unit_price')
    #     res['total_price'] = self.env.context.get('total_price')
    #     res['requested_date'] = self.env.context.get('requested_date')
    #     res['time'] = self.env.context.get('time')
    #     res['deadline'] = self.env.context.get('deadline')
    #     res['status'] = self.env.context.get('status')
    #     res['bidding_date'] = self.env.context.get('bidding_date')
    #     res['request_from'] = self.env.context.get('request_from')
    #     res['request_to'] = self.env.context.get('request_to')
    #     res['user_id'] = self.env.context.get('user_id')
    #     res['bidding_id'] = self.env.context.get('bidding_id')
    #     res['tender_id'] = self.env.context.get('tender_id')
    #     print("Default Get")
    #     print(res)
    #
    #     return res
