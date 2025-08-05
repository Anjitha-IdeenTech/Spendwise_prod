from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import modules
from odoo.http import request, _logger
import requests


class Groups(models.Model):
    _name = 'groups'

    name = fields.Char(string="Request No", readonly=True, copy=False, default='New')
    group_name = fields.Char(string='Group Name')
    budget = fields.Float(string='Budget')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('groups') or 'New'
        result = super(Groups, self).create(vals)
        return result


class ProductGroups(models.Model):
    _name = 'products.group'

    sequence = fields.Char(string="Group No", readonly=True, copy=False, default='New')
    name = fields.Char(string='Product Group')
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        invisible=True
    )

    products_line = fields.One2many('product.groups.line','groups_line',string='Groups Lines',tracking=True)


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('product.group.code') or 'New'
        result = super(ProductGroups, self).create(vals)
        return result

class ProductGroupsLines(models.Model):
    _name = "product.groups.line"
    _description = "Products Groups Lines"

    groups_line = fields.Many2one('products.group', string='Products Line',invisible=True)
    product_id = fields.Many2one('product.template', string='Product')
    uom = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_po_id')
    quantity = fields.Float("Quantity")
    unit_price = fields.Float(string="Unit Price")

