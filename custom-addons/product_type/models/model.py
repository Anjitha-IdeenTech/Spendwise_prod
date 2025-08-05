from odoo import models, fields, api,_



class ProductTypes(models.Model):
    _name = 'product.types'

    name = fields.Char("Name")
    reference = fields.Char("Reference")
    disc = fields.Text("Description")



class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    product_type = fields.Many2one('product.types',"Product Category Type")

    detailed_type = fields.Selection(

        selection="_get_selection_diet_options"
    )

    def _get_selection_diet_options(self):
        return [('consu', _("Consumable")), ('product', _("Storable Product"))]