from odoo import api, fields, models
from odoo.exceptions import ValidationError, MissingError, UserError


class AddToBiddingWizard(models.TransientModel):
    _name = "add.to.bidding.wizard"
    _description = "Bidding"

    name = fields.Char(string="Name")
    bidding = fields.Many2one('bidding', string="Bidding Group")
    product_id = fields.Many2one('product.template', string="Product", store=True, force_save=True)
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    total_price = fields.Float(string="Total Price")
    status = fields.Selection([
        ('draft', 'draft'),
        ('accept', 'Accept'),
        ('cancel', 'Cancel')], string='Tender Status')
    requested_date = fields.Date(string="Requested Date")
    time = fields.Float(string='Time')
    deadline = fields.Date(string='DeadLine')
    expected_date = fields.Date(string="Expected Date")
    bidding_date = fields.Date(string="Bidding Date")
    request_from = fields.Many2one('res.partner', string="Request from")
    request_to = fields.Many2one('res.partner', string="Request To")
    product_requested_id = fields.Integer(string="Product Request Id")
    user_id = fields.Many2one('res.users', string="User")
    bidding_id = fields.Many2one('bidding', string="Bidding ID")
    response_id = fields.Many2one('tender.request.response', string="User")

    def add_to_bidding(self):
        print("Inside action_add_to_bidding")
        # print(self.bidding.product.id)
        # print(self.product_id.id)
        print('request_to', self.request_to)
        if not self.bidding.product.id == self.product_id.id:
            raise ValidationError('Invalid Bidding!! (products are different)')
        else:
            # pass
            print("Add button click")
            # print("self.response_id.bid_check", self.response_id.bid_check)
            # self.response_id.bid_check = True
            # print("self.response_id.status", self.response_id.bid_check)
            print(
                {
                    'product_id': self.product_id.id,
                    'quantity': self.quantity,
                    'unit_price': self.unit_price,
                    'total_price': self.total_price,
                    'date': self.requested_date,
                    'time': self.time,
                    'deadline': self.bidding.deadline,
                    'status': self.status,
                    'bidding_date': self.bidding.date,
                    'request_from': self.request_from.id,
                    'request_to': self.request_to.id,
                    'user_id': self.user_id.id,
                    'bidding_id': self.bidding.id,
                    'response_id': self.response_id.bid_check,
                    'product_requested_id': self.product_requested_id
                }
            )
            bid_request = self.env['bid.request']
            bid_request.create({
                                'product_id': self.product_id.id,
                                'quantity': self.quantity,
                                'unit_price': self.unit_price,
                                'total_price': self.total_price,
                                'date': self.requested_date,
                                'time': self.time,
                                'deadline': self.bidding.deadline,
                                # 'status': self.status,
                                'bidding_date': self.bidding.date,
                                'request_from': self.request_from.id,
                                'request_to': self.request_to.id,
                                'user_id': self.user_id.id,
                                'bidding_id': self.bidding.id,
                                'product_requested_id': self.product_requested_id
                            })
            self.response_id.bid_check = True

    def action_create_bidding(self):
        print("Pass !!!!")
        pass

    @api.model
    def default_get(self, fields):
        res = super(AddToBiddingWizard, self).default_get(fields)
        # Set the value of example_field based on the context
        res['name'] = self.env.context.get('name')
        res['product_id'] = self.env.context.get('product_id')
        res['quantity'] = self.env.context.get('quantity')
        res['unit_price'] = self.env.context.get('unit_price')
        res['total_price'] = self.env.context.get('total_price')
        res['requested_date'] = self.env.context.get('requested_date')
        res['time'] = self.env.context.get('time')
        res['deadline'] = self.env.context.get('deadline')
        res['status'] = self.env.context.get('status')
        res['bidding_date'] = self.env.context.get('bidding_date')
        res['request_from'] = self.env.context.get('request_from')
        res['request_to'] = self.env.context.get('request_to')
        res['user_id'] = self.env.context.get('user_id')
        res['bidding_id'] = self.env.context.get('bidding_id')
        res['response_id'] = self.env.context.get('response_id')
        print("Default Get")
        print(res)

        return res


