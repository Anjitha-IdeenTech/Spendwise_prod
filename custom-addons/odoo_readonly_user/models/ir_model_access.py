# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, tools


class IrModelAccess(models.Model):
    """Inherits the ir model access for restricting
     the user from accessing data."""
    _inherit = 'ir.model.access'

    @api.model
    @tools.ormcache_context('self.env.uid', 'self.env.su', 'model', 'mode',
                            'raise_exception', keys=('lang',))
    def check(self, model, mode, raise_exception=True):
        """Overrides the default check method to allow
         only read access to the user."""
        company_models = ['res.branch', 'res.company','region.masters','division.masters','subdivision.masters','hr.department','hr.job']
        bank_models = ['res.bank','res.partner.bank','account.tax','uom.category']
        product_models = ['product.template','product.types','products.group','product.category']
        workflow_models =['pr.company','product.request.budget','expense.category','vendor.approval']
        vendor_models =['res.partner','vendor.limit']
        user_models =['res.users']
        editable_models = ['res.partner', 'res.users', 'res.branch', 'res.company',
                 'region.masters', 'division.masters',
                 'subdivision.masters', 'hr.department','hr.job','res.bank','res.partner.bank','account.tax','uom.category',
                          'vendor.limit','product.template','product.types','products.group','product.category','account.payment.term','pr.company',
                           'product.request.budget','expense.category','vendor.approval']
        res = super().check(model, mode, raise_exception=raise_exception)
        # print("hi",self.env['ir.model.access'].search([('model_id.model', '=', 'product_purchase')]))
        # if not self.env.user.has_group('lease_management.group_master_admin')\
        #         and mode in ('write', 'create', 'unlink') and model in editable_models:
        #     return False
        if not self.env.user.has_group('lease_management.group_record_company')\
                and mode in ('write', 'create', 'unlink') and model in company_models:
            return False
        if not self.env.user.has_group('lease_management.group_record_bank') \
                and mode in ('write', 'create', 'unlink') and model in bank_models:
            return False

        if not self.env.user.has_group('lease_management.group_record_product') \
                and mode in ('write', 'create', 'unlink') and model in product_models:
            return False
        if not self.env.user.has_group('lease_management.group_record_workflow') \
                and mode in ('write', 'create', 'unlink') and model in workflow_models:
            return False
        if not self.env.user.has_group('lease_management.group_master_admin') \
                and mode in ('write', 'create', 'unlink') and model in user_models:
            return False
        if not self.env.user.has_group('lease_management.group_record_user') \
                and mode in ('write', 'create', 'unlink') and model in vendor_models:
            return False
        return res
