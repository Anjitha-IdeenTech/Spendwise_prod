from odoo import api, fields, models, _,tools
from odoo.exceptions import ValidationError, MissingError, UserError
from datetime import date
from num2words import num2words
import  locale
import logging
try:
    from num2words import num2words
except ImportError:
    num2words = None
from odoo.tools.safe_eval import json


class PoInhrerited(models.Model):
    _inherit = "purchase.order"
    _description = 'Purchase Order'

    terms_conditions = fields.Text("Terms and Conditions")
    is_terms = fields.Boolean("With Annexure")
    price_basis = fields.Char("Price Basis")
    warranty_terms = fields.Char("Warranty Terms")
    installation = fields.Char("Installation & Com")
    # dispatch = fields.Char("Dispatch Mode")
    dispatch = fields.Selection([('road', 'Road'), ('air', 'Air'), ('rail', 'Railway'), ('water', 'Water')], string="Dispatch Mode", default='road' ,tracking=True)

    # freight = fields.Char("Freight Insurance & P&F")
    freight = fields.Selection([('paid', 'Paid'), ('not', 'UnPaid')], string="Freight Insurance & P&F", default='paid',tracking=True)
    damage = fields.Char("Liquidated Damage")
    amc = fields.Char("AMC")
    note = fields.Text("Note to Vendor")
    date = fields.Date("Date",default=fields.Date.today)

    # buyer = fields.Many2one("res.users","Buyer Details")
    buyers = fields.Many2one('res.users',"Buyer", domain=lambda self: [
        ("groups_id", "=", self.env.ref("product_purchase.group_buyers").id)])
    contact = fields.Many2one("res.users","Contact Person", related='pr_id.requested_by')

    text_amount_ar = fields.Char(string="Montant", required=False, compute="amount_to_words")
    company_prefix = fields.Char(string="Name Prefix", compute='_compute_name_prefix', store=True)


    @api.depends('company_id.name')
    def _compute_name_prefix(self):
        for record in self:
            if '-' in record.company_id.name:
                record.company_prefix = record.company_id.name.split('-')[0]
            else:
                record.company_prefix = record.company_id.name

    def action_check_adrs(self):
        print("yess")

    def amount_to_text(self, amount, currency_id):
        self.ensure_one()

        def _num2words(number, lang):
            try:
                return num2words(number, lang='en_IN').title()
            except NotImplementedError:
                return num2words(number, lang='en_IN').title()

    @api.depends('amount_total')
    def amount_to_words(self):
        for record in self:
            currency_id = self.env['res.currency'].search([('name', '=', record.currency_id.name)], limit=1)
            if currency_id:
                record.text_amount_ar = self.amount_to_text(record.amount_total, currency_id)

                print(record.text_amount_ar)

    def amount_to_text(self, amount, currency_id, _name_=None):
        self.ensure_one()

        def _num2words(number, lang):
            try:
                words = num2words(number, lang='en_IN').title()
                # Remove commas from the words
                words = words.replace(',', '')
                return words
            except NotImplementedError:
                words = num2words(number, lang='en_IN').title()
                # Remove commas from the words
                words = words.replace(',', '')
                return words

        if num2words is None:
            logging.getLogger(_name_).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        formatted = "%.{0}f".format(currency_id.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].search([('code', '=', lang_code)])
        amount_words = tools.ustr('{amt_value} {amt_word}').format(
            amt_value=_num2words(integer_value, lang=lang.iso_code),
            amt_word=currency_id.currency_unit_label,
        )
        if not currency_id.is_zero(amount - integer_value):
            amount_words += ' ' + _('and') + tools.ustr(' {amt_value} {amt_word}').format(
                amt_value=_num2words(fractional_value, lang=lang.iso_code),
                amt_word=currency_id.currency_subunit_label,
            )
        if amount_words:
            amount_words = amount_words
        return amount_words


    def amount_total_in_words(self):
        # Replace 'self.amount_total' with your actual field
        amount = self.amount_total or 0.0
        words = num2words(amount, lang='en_IN')
        return words.capitalize()

    from num2words import num2words

    # def amount_total_in_words(self):
    #     amount = self.amount_total or 0.0
    #     words = num2words(amount, lang='en_IN', to='currency', currency='INR')
    #     return words.capitalize()





