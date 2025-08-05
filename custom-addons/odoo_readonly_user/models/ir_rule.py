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
from odoo import api, models
from odoo.osv import expression


class IrRule(models.Model):
    """Inherits the ir rule for restricting the user from accessing data."""
    _inherit = 'ir.rule'

    @api.model
    def _compute_domain(self, model_name, mode):
        """Overrides the domain method to allow only read access
        to the user."""
        res = super()._compute_domain(model_name, mode)
        model = ['res.partner', 'res.users', 'res.branch', 'res.company',
                 'region.masters', 'division.masters',
                 'subdivision.masters', 'hr.department','hr.job','res.bank','res.partner.bank','account.tax','uom.category',
                          'vendor.limit','product.template','product.types','products.group','product.category','account.payment.term','pr.company',
                           'product.request.budget','expense.category','vendor.approval']
        if not self.env.user.has_group('lease_management.group_master_admin') \
                and mode in ('write', 'create', 'unlink') and\
                model_name in model:
            return expression.AND([res, expression.FALSE_DOMAIN])
        return res
