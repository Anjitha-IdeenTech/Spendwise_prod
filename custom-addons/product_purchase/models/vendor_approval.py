from datetime import datetime
from odoo import api, fields, models, _
import base64
import logging
import xlrd
from odoo.exceptions import ValidationError, MissingError, UserError

_logger = logging.getLogger(__name__)


class VendorApproval(models.Model):
    _name = "vendor.approval"

    name = fields.Char(string="VA Number", readonly=True, required=True, copy=False, default='New')
    company_id = fields.Many2one('res.company', string="Company Id")
    location = fields.Many2one('res.company', string="Location")
    department_id = fields.Many2one('hr.department', string="Department")
    vendor_approve_users_id = fields.One2many('vendor.approve.users',
                                              'vendor_approval_id',
                                              string='Vendor Approve Users',
                                              tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('vendor.approval') or 'New'
        result = super(VendorApproval, self).create(vals)
        return result

    @api.onchange('company_id')
    def onchange_in_company_id(self):
        # print(self.id)
        department_data = self.env['hr.department'].sudo().search([('company_id', '=', self.company_id.id)])
        department_list = []
        for department_line in department_data:
            department_list.append(department_line.id)
        print(department_list)
        res = {'domain': {'department_id': [('id', 'in', department_list)]}}


class VendorApproveUsers(models.Model):
    _name = "vendor.approve.users"

    user_id = fields.Many2one('res.users', string="User", required=True)
    company_id = fields.Many2one('res.company', string="Company Id", required=True)
    location = fields.Many2one('res.company', string="Location", required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    designation = fields.Many2one('hr.job', string="Designation", required=True)
    approve_order = fields.Integer(string="Order", required=True)

    vendor_approval_id = fields.Many2one('vendor.approval', string='Vendor Approval Id',
                                         invisible=True)

    # @api.onchange('company_id')
    # def onchange_in_company_id(self):
    #     self.department_id = ""
    #     self.location = ""
    #     self.designation = ""
    #     self.user_id = ""
    #     print("Inside company")
    #     department_data = self.env['hr.department'].sudo().search(
    #         [('company_id', '=', self.company_id.id)])
    #     dep_list = []
    #     for dep in department_data:
    #         dep_list.append(dep.id)
    #     print(dep_list)
    #     res = {'domain': {'department_id': [('id', 'in', dep_list)]}}
    #     return res
    #
    # @api.onchange('location')
    # def onchange_in_location(self):
    #     self.department_id = ""
    #     self.approve_order = ""
    #     self.designation = ""
    #     self.user_id = ""
    #
    @api.onchange('department_id')
    def onchange_in_department_id(self):
        print("Inside department")
        self.designation = ""
        self.user_id = ""
        self.approve_order = ""
        job_data = self.env['hr.job'].sudo().search(
            [('department_id', '=', self.department_id.id)])
        job_list = []
        for job in job_data:
            job_list.append(job.id)
        res = {'domain': {'designation': [('id', 'in', job_list)]}}
        print("job_list ", job_list)
        return res

    @api.onchange('designation')
    def onchange_in_designation(self):
        print("Inside designation")
        if self.designation.id:
            if self.designation and self.company_id and self.department_id:
                print(self.vendor_approval_id.company_id.id)
                print(self.vendor_approval_id.department_id.id)
                print(self.designation.id)
                approve_user_data = self.env['res.users.line'].sudo().search(
                    [('company_id', '=', self.company_id.id),
                     ('department_id', '=', self.department_id.id),
                     ('designation', '=', self.designation.id)], limit=1)
                if approve_user_data:
                    self.user_id = approve_user_data.res_user_id.id
                # else:
                #     # raise ValidationError("User not found")

    @api.onchange('approve_order')
    def onchange_in_approve_order(self):
        flag = 0
        try:
            approve_user_data = self.env['vendor.approve.users'].sudo().search(
                [('vendor_approval_id', '=', int(str(self.vendor_approval_id.id).split('_')[1]))])
            flag = 1
        except Exception as e:
            pass
