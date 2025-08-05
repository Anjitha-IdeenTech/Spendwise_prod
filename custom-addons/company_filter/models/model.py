import werkzeug
from werkzeug.urls import url_encode

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError, MissingError, UserError
from odoo import http
from odoo.http import request
import datetime


class AllowedCompanies(models.Model):
    _name = "allowed.companies"
    _auto = False
    _description = "Allowed Companies"

    company_id = fields.Many2one("res.company","Company")
    parent_company_id = fields.Many2one("res.company","Parent Company")
    state = fields.Many2one("res.country.state","State")
    city = fields.Char("City")
    users = fields.Many2one("res.users","Users")
    id = fields.Char("ID")
    sequence = fields.Integer("Sequence")
    com_id = fields.Integer("Company ID")




    def button_add_companies(self):



        view_context = self.env.context
        print(view_context)



        # # allowed_companies = view_context.get('allowed_company_ids', False)
        # #
        # # print(allowed_companies ,"ALLOWED COMPANIEEEEEEEEEEEEEEEEEEEEEEEEES")
        # #
        #
        # # self.env.context = dict(self.env.context)
        # # selected_companies = self.with_context({'active_id':'2', 'active_ids': [2]})
        # selected_ids = self.env.context.get('active_ids', [])
        # #
        # # print(selected_ids)
        # #
        # # selected_companies = self.with_context(allowed_company_ids=selected_ids).sudo()
        #
        # # Update the dictionary with the new allowed_company_ids
        # updated_data = view_context.copy()
        # updated_data['allowed_company_ids'] = selected_ids
        #
        # # Use the updated dictionary
        # selected_companies = self.with_context(allowed_company_ids=selected_ids).sudo()
        #
        #
        #
        # print(selected_companies,"selected")
        # pass

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Company Allocations')], limit=1) or False

        url_params = {
            # 'id': self.id,
            'action': self.env.ref('company_filter.action_view_allowed_companies').id,
            'model': 'allowed.companies',
            'view_type': 'list',
            # 'menu_id': self.env.ref('product_purchase.product_purchase').id,
            'menu_id': menu_id.id,
        }
        url_test = "cids=1%2C2&action=605&model=allowed.companies&view_type=list&menu_id=471"
        params = '/web?#%s' % url_encode(url_params)
        view_url = base_url + params if base_url else "#"

        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['allowed.companies'].browse(selected_ids)
        result = f"&cids={''.join([f'%2C{x.com_id}' if x != selected_records[0] else str(x.com_id) for x in selected_records])}"
        print(result)
        view_url = base_url + params + result if base_url else "#"
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", view_url)

        action = {
            'type': 'ir.actions.act_url',
            'url': view_url,
            'target': 'new',
            # 'target': '_blank',
        }
        return action



    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, 'allowed_companies')
        self._cr.execute("""
            CREATE OR REPLACE VIEW allowed_companies AS (
            
                SELECT row_number() over(ORDER BY allowed_companies.cid) AS id,
                Dense_rank() over(ORDER BY allowed_companies.cid) AS sequence,
                    allowed_companies.cid AS company_id,
                    allowed_companies.user_id AS users,
                    companies.parent_id AS parent_company_id,
                    partner.state_id as state,
                    partner.city as city,
					companies.id as com_id
                FROM
                    res_company_users_rel allowed_companies
                LEFT JOIN res_company companies ON (allowed_companies.cid = companies.id)
                LEFT JOIN res_partner partner ON (companies.partner_id = partner.id)
            
            
            
               
            )
        """)

#         SELECT
#         row_number()
#         over(ORDER
#         BY
#         allowed_companies.cid) AS
#         id,
#         Dense_rank()
#         over(ORDER
#         BY
#         allowed_companies.cid) AS
#         sequence,
#         allowed_companies.cid
#         AS
#         company_id,
#         allowed_companies.user_id
#         AS
#         users,
#         companies.parent_id
#         AS
#         parent_company_id,
#         partner.state_id as state,
#         partner.city as city
#
#     FROM
#     res_company_users_rel
#     allowed_companies
#
#
# LEFT
# JOIN
# res_company
# companies
# ON(allowed_companies.cid = companies.id)
# LEFT
# JOIN
# res_partner
# partner
# ON(companies.partner_id = partner.id)
#


