from odoo import api,fields,models,_
from odoo.exceptions import ValidationError
class VendorModification(models.Model):
    _inherit = 'res.partner'

    product_category = fields.Many2many(
        'product.category',
        'vendor_product_category_rel',
        'id',
        'name',
        string='Product Categories',
    )
    category = fields.Char("Category")
    login = fields.Many2one("res.users","Login User",compute="_compute_login_user")
    vendor_code = fields.Char(string="Vendor Code")
    street = fields.Char(required=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]", required=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', required=True)
    vat = fields.Char(required=True)



    def action_generate_user(self):
        if self.email:
            existing_user = self.env['res.users'].sudo().search([('partner_id', '=', self.id)], limit=1)
            if existing_user:
                raise ValidationError("A user already exists for this vendor.")
            user_generated = self.env['res.users'].sudo().create({
                'name': self.name,
                'login': self.email,
                # 'password': ,
                'partner_id': self.id,
            })
            user_generated.action_reset_password()

            company = self.env.company
            print("the company is", company)

            company_branches = self.env['res.branch'].search([('company_id', '=', company.id)])
            print("all branches", company_branches)
            user_generated.write({'branch_ids': [(6, 0, company_branches.ids)]})

        else:
            raise ValidationError("Please Enter User Email address")
        user_group1 = self.env.ref(
            'vendor_portal.group_vendor_portal_user')
        user_group2 = self.env.ref(
            'product_purchase.group_user_vendor')
        user_group3 = self.env.ref('account.group_account_invoice')
        if user_group1 and user_group2 and user_group3:
            user_group1.write({'users': [(4, user_generated.id)]})
            user_group2.write({'users': [(4, user_generated.id)]})
            user_group3.write({'users': [(4, user_generated.id)]})
        unwanted_categories = self.env['ir.module.category'].search([('name', 'in',
                                                                      ['Sales', 'Purchase', 'expenses', 'Expenses',
                                                                       'Project', 'Events', 'Invoicing',
                                                                       'Inventory', 'Point of Sale', 'Manufacturing',
                                                                       'Technical', 'Contracts', 'Website',
                                                                       'Employees', 'Other Extra Rights',
                                                                       'Extra Rights', 'Attendances', 'Events',
                                                                       'Employee Hourly Cost', 'Recruitment',
                                                                       'Attendances'])])
        if unwanted_categories:
            unwanted_groups = self.env['res.groups'].search([('category_id', 'in', unwanted_categories.ids)])
            if unwanted_groups:
                for group in unwanted_groups:
                    group.write({'users': [(3, user_generated.id)]})
                    user_group3.write({'users': [(4, user_generated.id)]})

    def _compute_login_user(self):
        for rec in self:
            if rec.name:
                vendor_user_id = self.env['res.users'].sudo().search([
                ('partner_id', '=', rec.id)])
                print(vendor_user_id.login)
                print(vendor_user_id.id)
                if vendor_user_id:
                    self.login = vendor_user_id.id
                else:
                    self.login = False
            else:
                self.login = False