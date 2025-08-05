from datetime import date

from werkzeug.urls import url_encode

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import modules
from odoo.http import request, _logger
import requests


class VendorIntake(models.Model):
    _name = 'vendor.intake'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vendor Onboarding'

    # name = fields.Char(string='Number', required=True, copy=False, readonly=True,
    #                        default=lambda self: _('New'))
    name = fields.Char("Name", tracking=True)
    street = fields.Char("Street")
    address1 = fields.Char("Address 1")
    address2 = fields.Char("Address 2")
    city = fields.Char("City")
    zip = fields.Char("Pincode")
    gst = fields.Char("VAT No", tracking=True)
    pan = fields.Char("Pan No", tracking=True)
    tel = fields.Char("Telephone No", tracking=True)
    mob = fields.Char("Mobile No", tracking=True)
    mail_id = fields.Char("Email ID", tracking=True)
    state_id = fields.Char("State")
    state_ids = fields.Many2one('res.country.state', "State")
    country_id = fields.Many2one(string="Country", comodel_name='res.country', help="Country")
    # user_id = fields.Many2one('res.users', string='Contact User', default=lambda self: self.env.user,)
    ref = fields.Char("Vendor Reference")
    contactperson = fields.Char("Contact Person 1")
    contactperson2 = fields.Char("Contact Person 2")
    msme = fields.Char("MSME Category")
    remarks = fields.Text("Remarks")
    states = fields.Selection(
        [("draft", "Draft"), ("review", "Review"), ("approved", "Approved"), ("vendor", "Vendor Registered"),
         ("done", "User Generated"), ("cancelled", "Cancel")],
        string="Status", default="draft", tracking=True)

    bank = fields.Char(string='Bank Name')
    bank_acc_no = fields.Char(string='Account No')
    branch = fields.Char(string="Branch")
    ifsc = fields.Char(string="IFSC Code")

    msme_number = fields.Char(string="MSME Number")
    vendor_category = fields.Many2one("product.category", string="Vendor Category")
    # company_type = fields.Char(string="Company Type")
    company_type = fields.Selection([
        ('type1', 'Companies Limited by Shares'),
        ('type2', 'Companies Limited by Guarantee'),
        ('type3', 'Unlimited Companies'),
        ('type4', 'One Person Companies (OPC)'),
        ('type5', 'Private Companies'),
        ('type6', 'Public Companies'),
        ('type7', 'Holding and Subsidiary Companies'),
        ('type8', 'Associate Companies'),
        ('type9', 'Companies in terms of Access to Capital'),
        ('type10', 'Government Companies'),
        ('type11', 'Foreign Companies'),
        ('type12', 'Charitable Companies'),
        ('type13', 'Dormant Companies'),
        ('type14', 'Nidhi Companies'),
        ('type15', 'Public Financial Institutions'),
    ], string="Company Type")
    website = fields.Char(string="Website Link")
    gst_file = fields.Binary(string='Uploaded File')
    pan_card = fields.Binary(string='Pan Card file')
    bank_file = fields.Binary(string='Statement Copy file')
    bank_cheque_file = fields.Binary(string='Bank Cheque file')
    vendor_approve_users = fields.Many2many(
        'res.users',
        'vendor_request_approve_users_rel',
        'request_id',
        'user_id',
        string='Approve Users',
    )

    vendor_approved_users = fields.Many2many(
        'res.users',
        'vendor_request_approved_users_rel',
        'request_id',
        'user_id',
        string='Approved Users',
    )

    approve_check = fields.Boolean(compute="_approve_check", string="Approve Check", default=False)
    next_approve_user_id = fields.Many2many('res.users', string="Next Approve User ID")
    user_approve_check = fields.Boolean(string="User Approve check", compute="_compute_total", default=False)
    vendor_approve_line = fields.One2many('vendor.approve.line',
                                          'vendor_intake_id',
                                          string='Vendor Approve Line',
                                          tracking=True)

    # company_id = fields.Many2one("res.company", "Company")
    # location = fields.Many2one("res.company", "Location")
    # department = fields.Many2one("hr.department", "Department", domain="[('company_id', '=', company_id)]")
    # vendor_representative = fields.Many2one("res.users", "Representative")

    company_id = fields.Many2one("res.company", "Company", default=lambda self: self.env.company.id)
    location = fields.Many2one("res.company", "Location", default=lambda self: self.env.company.id)
    department = fields.Many2one('hr.department', string="Department",
                                    default=lambda self: self._get_default_department())
    vendor_representative = fields.Many2one("res.users", "Representative")

    approve_users = fields.Many2many(
        'res.users',
        'rel_vd_apprvers',
        'vd_id',
        'users_v',
        string='Approve Users',
    )
    approved_users = fields.Many2many(
        'res.users',
        'approved_vd_relation',
        'vd_apprved',
        'user_id_vd',
        string='Approved Users',
    )

    next_approve_user = fields.Many2many(
        'res.users',
        'next_aprved_vd',
        'next_vd',
        'users_id_vd',
        string='Next Approver', )
    is_an_approver = fields.Boolean("Approver", compute='compute_is_an_approver')

    payment_terms = fields.Many2one('account.payment.term', "Payment Terms", required=True)
    credit_terms = fields.Many2one('account.payment.term', "Credit Terms", required=True)
    bank_beneficiary = fields.Char(string='Bank Beneficiary Name')
    bank_upi = fields.Char(string='Bank UPI ID')
    dan_number = fields.Char(string='DAN Number')
    msme_file = fields.Binary(string='MSME Certificate')

    ############### Price List #########

    vendor_price_line = fields.One2many('vendor.pricelist.line',
                                        'vendor_intake_ids',
                                        string='Vendor Price List',
                                        tracking=True)

    def _get_default_department(self):
        default_department = self.env['hr.department'].search([('name','=','Procurement')], limit=1)
        return default_department.id if default_department else False

    @api.model
    def create(self, vals):
        res = super(VendorIntake, self).create(vals)

        user = self.env['res.users'].sudo().search(
            [('groups_id', 'in', self.env.ref('vendor_portal.group_admin_vendor_portal').id)], limit=1)

        if res and user:
            model = self.env['ir.model'].sudo().search([('model', '=', 'vendor.intake')], limit=1)
            pending_vals = {
                'model': model.id,
                'name': res.name,
                'record': res.id,
                'date': date.today(),
                'approve_users': [(6, 0, [user.id])]
            }

            # Create pending actions record
            self.env['pending.actions'].sudo().create(pending_vals)

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = self.env['ir.ui.menu'].sudo().search(
                [('name', '=', 'Vendors Portal')], limit=1) or False

            url_params = {
                'id': res.id,
                'action': self.env.ref('vendor_portal.action_view_vendor_intake').id,
                'model': 'vendor.intake',
                'view_type': 'form',
                'menu_id': menu_id.id if menu_id else False,
            }

            params = '/web?#%s' % url_encode(url_params)
            view = base_url + params if base_url else "#"

            author = self.env['res.partner'].sudo().search(
                [('name', '=', 'Administrator')], limit=1) or False

            body = (
                f"Dear User,A new Vendor Onboarding request {res.name} has been registered .<br><br>"
                f"<a href='{view}' style='display: inline-block; padding: 10px 20px; "
                f"background-color: #008CBA; color: white; text-align: center; text-decoration: none; "
                f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>View Entries</a> <br>"

                # f"<a href='{approval_url}' style='display: inline-block; padding: 10px 20px; "
                # f"background-color: #4CAF50; color: white; text-align: center; text-decoration: none; "
                # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Approve</a> <space>"
                # f"<a href='http://your_domain/reject' style='display: inline-block; padding: 10px 20px; "
                # f"background-color: #F44336; color: white; text-align: center; text-decoration: none; "
                # f"font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 5px;'>Reject</a><br>"

            )

            if user.login:
                mail_values = {
                    'subject': 'Vendor Onboarding Request',
                    'body_html': body,
                    'email_to': user.login,
                    'auto_delete': False,
                    'author_id': author.id
                }
                mail_record = self.env['mail.mail'].sudo().create(mail_values)

        return res
    def action_generate_vendor(self):
        print("kkkkkk")
        if self.gst and self.mail_id:
            vendor_exist = self.env['res.partner'].sudo().search([
                ('vat', '=', self.gst)])
            if not vendor_exist:
                vendor_generated = self.env['res.partner'].sudo().create({
                    "name": self.name,
                    "street": self.address1,
                    "street2": self.street,
                    "city": self.city,
                    "state_id": self.state_ids.id,
                    "zip": self.zip,
                    "email": self.mail_id,
                    "vat": self.gst,
                    "property_supplier_payment_term_id": self.payment_terms.id,
                    "mobile": self.mob,
                    "phone": self.tel,
                })

                # if vendor_generated and self.vendor_price_line:
                #     for lines in self.vendor_price_line:
                #         vals = {
                #             'company_id':  False,
                #             'name': vendor_generated.id,
                #             'product_tmpl_id': lines.product.id,
                #             'min_qty': lines.qty,
                #             'price': lines.price,
                #             'delay': lines.delay,
                #             # 'currency_id':"INR",
                #         }
                #         company_ids_to_add = [(6, 0, lines.company.ids)]
                #         vals['company_ids'] = company_ids_to_add
                #         price_list = self.env['product.supplierinfo'].sudo().create(vals)
            else:
                raise UserError("GST No already exist")

            self.states = 'vendor'

    @api.depends('next_approve_user')
    def compute_is_an_approver(self):
        for rec in self:
            rec.is_an_approver = self.env.user.id in rec.next_approve_user.mapped('id')

    def action_review(self):
        if not self.company_id or not self.department or not self.location:
            raise UserError("Please fill in all Company Details: Company, Department, and Location")
        if not self.vendor_price_line:
            raise UserError("Please Create Products & Price lists")

        vendor_approval = request.env['vendor.approval'].sudo().search([('company_id', '=', self.company_id.id),
                                                                        ('department_id', '=', self.department.id),
                                                                        ], limit=1)
        if vendor_approval:
            line = []
            for approvers in vendor_approval.vendor_approve_users_id:
                self.write({'approve_users': [(4, approvers.user_id.id)]})
                vals = {
                    'user_id': approvers.user_id.id,
                    'company_id': approvers.company_id.id,
                    'location': approvers.location.id,
                    'department_id': approvers.department_id.id,
                    'designation': approvers.designation.id,
                    'approve_order': approvers.approve_order,
                }
                line.append((0, 0, vals))
            self.vendor_approve_line = line
            next_approver_user_ids = [next_approver.user_id.id for next_approver in self.vendor_approve_line if
                                      next_approver.approve_order == 1]
            print(next_approver_user_ids, "This print")
            if all(item is not False for item in next_approver_user_ids):
                self.write({'next_approve_user': [(6, 0, next_approver_user_ids)]})
                self.states = 'review'

                model = self.env['ir.model'].sudo().search([('model', '=', 'vendor.intake')], limit=1)
                print(model.id)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id)], limit=1)

                print(pending_action)
                if pending_action:
                    pending_action.status = 'closed'

                model = self.env['ir.model'].sudo().search([('model', '=', 'vendor.intake')], limit=1)
                if model:
                    pending_vals = {
                        'model': model.id,
                        'name': self.name,
                        'record': self.id,
                        'date': date.today(),
                        'approve_users': [(6, 0, next_approver_user_ids)] if next_approver_user_ids else False
                    }
                    self.env['pending.actions'].sudo().create(pending_vals)
                else:
                    pass

        else:
            raise UserError("No vendor workflow found for this company")

    @api.depends("user_approve_check")
    def _compute_total(self):
        print('Inside user_approve_check')
        for rec in self:
            if self.env.user in rec.next_approve_user_id:
                rec.user_approve_check = True
            else:
                rec.user_approve_check = False

    def _approve_check(self):
        self.approve_check = False
        if self.vendor_approved_users and (
                self.env.user.id in [user_ids.id for user_ids in self.vendor_approved_users]):
            self.approve_check = True
            print("True")
        else:
            self.approve_check = False
            print(self.states)
            print("False")

    def action_approve(self):
        self.ref = self.env['ir.sequence'].next_by_code('vendor.intake')
        self.states = 'approved'

    def action_done(self):
        if self.states == 'vendor':
            print("hhhhh")
            password = self.ref
            vendor = self.env['res.partner'].sudo().search([
                    ('vat', '=', self.gst),('name','=',self.name)])
            user_generated = self.env['res.users'].sudo().create({
                'name': self.name,
                'login': self.mail_id,
                'password': password,
                'partner_id': vendor.id,
            })
            body = (
                    "Dear Vendor,Your vendor registration has been successfully approved and your Login id is" + " " + self.mail_id + " "
                                                                                                                                      "Password is" + " " + password)
            vals = {
                'subject': 'Vendor Login Credentials',
                'body_html': body,
                'email_to': self.mail_id,
                'auto_delete': False,
                # 'email_from': ,
            }
            # print(vals)
            mail_id = self.env['mail.mail'].sudo().create(vals)
            mail_id.sudo().send()
            self.states = 'done'

        else:
            if self.gst and self.mail_id:
                vendor_exist = self.env['res.partner'].sudo().search([
                    ('vat', '=', self.gst)])
                if vendor_exist:
                    raise UserError("Vendor GST is already exist")
                else:
                    vendor_generated = self.env['res.partner'].sudo().create({
                        "name": self.name,
                        "street": self.address1,
                        "street2": self.street,
                        "city": self.city,
                        "state_id": self.state_ids.id,
                        "zip": self.zip,
                        "email": self.mail_id,
                        "vat": self.gst,
                        "property_supplier_payment_term_id": self.payment_terms.id,
                        "mobile": self.mob,
                        "phone": self.tel,
                    })

                # if vendor_generated and self.vendor_price_line:
                #     for lines in self.vendor_price_line:
                #         print(lines)
                #
                #         vals = {
                #             'company_id':  False,
                #             'name': vendor_generated.id,
                #             'product_tmpl_id': lines.product.id,
                #             'min_qty': lines.qty,
                #             'price': lines.price,
                #             'delay': lines.delay,
                #             # 'currency_id':"INR",
                #         }
                #         company_ids_to_add = [(6, 0, lines.company.ids)]
                #         vals['company_ids'] = company_ids_to_add
                #
                #         print(vals)
                #         price_list = self.env['product.supplierinfo'].sudo().create(vals)

                    user_exist = self.env['res.users'].sudo().search([('name', '=', self.name),
                                                                      ('login', '=', self.mail_id)])
                    if user_exist:
                        raise UserError("Login already exist")
                    else:
                        password = self.ref
                        user_generated = self.env['res.users'].sudo().create({
                            'name': self.name,
                            'login': self.mail_id,
                            'password': password,
                            'partner_id': vendor_generated.id,
                        })
                body = (
                        "Dear Vendor,Your vendor registration has been successfully approved and your Login id is" + " " + self.mail_id + " "
                                                                                                                                          "Password is" + " " + password)
                vals = {
                    'subject': 'Vendor Login Credentials',
                    'body_html': body,
                    'email_to': self.mail_id,
                    'auto_delete': False,
                    # 'email_from': ,
                }
                # print(vals)
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()
                self.states = 'done'
            else:
                raise UserError("Please ensure GST and Mail Id are entered correctly")


    def action_draft(self):
        if self.states == "done":
            user_found = self.env['res.users'].sudo().search([('name', '=', self.name),
                                                              ('login', '=', self.mail_id)])
            if user_found:
                raise UserError("Please delete the related User & Vendor to countinue")
            else:
                self.states = 'approved'

        else:
            self.states = 'draft'
            self.approve_users = [(5, 0, 0)]
            self.next_approve_user = [(5, 0, 0)]
            self.approved_users = [(5, 0, 0)]
            self.vendor_approve_line.unlink()


    def action_approval(self):
        print("Hellooo users")
        print(self.env.user.id)
        self.write({'approved_users': [(4, self.env.user.id)]})
        # self.is_an_approver = False
        self.write({'next_approve_user': [(3, self.env.user.id)]})
        approver = self.env['vendor.approve.line'].sudo().search(
            [('vendor_intake_id', '=', self.id), ('user_id', '=', self.env.user.id)])
        for record in approver:
            record.write({'status': 'accept'})

        approve_users = self.env['vendor.approve.line'].sudo().search(
            [('vendor_intake_id', '=', self.id)], order='approve_order asc')

        user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
        # user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
        current_order = None
        next_user = None

        for user in user_ids:
            if self.env.user.id == user['u_id']:
                current_order = user['order']

        if current_order is not None:
            for user in user_ids:
                if user['order'] == current_order + 1:
                    next_user = user

        if next_user:
            next_user_id = next_user['u_id']
            next_order = next_user['order']
            self.write({'next_approve_user': [(4, next_user_id)]})

            print("Next User ID:", next_user_id)
            print("Next Order:", next_order)
        else:
            all_approved = all(approver.status == 'accept' for approver in approve_users)

            if all_approved:
                self.states = 'approved'
                self.ref = self.env['ir.sequence'].next_by_code('vendor.intake')

                model = self.env['ir.model'].sudo().search([('model', '=', 'vendor.intake')], limit=1)
                print(model.id)
                pending_action = self.env['pending.actions'].sudo().search(
                    [('model', '=', model.id), ('record', '=', self.id),('status','=','open')], limit=1)

                print(pending_action)
                if pending_action:
                    pending_action.status = 'closed'



                # Change the state to the desired value when all statuses are 'approve'
                # self.write({'state': 'approved_state'})
            else:
                # Handle the case when not all statuses are 'approve'
                # self.write({'state': 'pending_state'})
                print("not approved")

            # self.state = 'approve'
            print("Current user is the last approver or not found.")

        # self.write({'vendor_approved_users': [(4, self.env.user.id)]})
        # # print(self.approve_users)
        # # print(self.approved_users)
        # approve_users = self.env['vendor.approve.line'].sudo().search(
        #     [('vendor_intake_id', '=', self.id), ('user_id', '=', self.env.user.id)], limit=1)
        #
        # approve_users.write({
        #     'status': 'accept'
        # })
        #
        # if self.vendor_approved_users == self.vendor_approve_users:
        #     self.states = 'approved'
        #     self.action_done()
        # else:
        #     approve_users = self.env['vendor.approve.line'].sudo().search([('vendor_intake_id', '=', self.id)],
        #                                                                   order='approve_order asc')
        #
        #     user_ids = [{'u_id': user.user_id.id, 'order': user.approve_order} for user in approve_users]
        #     # print(user_ids)
        #
        #     order_list = list(set([order_id.approve_order for order_id in approve_users]))
        #     order_list.sort()
        #     approve_dict = {}
        #     print("order_list ", order_list)
        #     for order in order_list:
        #         for user in user_ids:
        #             if user['order'] == order:
        #                 if order in approve_dict:
        #                     approve_dict[order].append({'u_id': user['u_id'], 'order': user['order']})
        #                 else:
        #                     approve_dict[order] = [{'u_id': user['u_id'], 'order': user['order']}]
        #
        #     print("approve_dict ", approve_dict)
        #
        #     record_to_remove = self.env['res.users'].browse(self.env.user.id)
        #     self.next_approve_user_id -= record_to_remove
        #
        #     if not self.next_approve_user_id:
        #         for order in order_list:
        #             for order_list_users in approve_dict[order]:
        #                 if self.env.user.id == order_list_users['u_id']:
        #                     try:
        #                         if approve_dict[order + 1]:
        #                             for users in approve_dict[order + 1]:
        #                                 self.write({'next_approve_user_id': [(4, users['u_id'])]})
        #                     except:
        #                         print("order+1 ", order + 1)
        #                         print("order_list[-1] ", order_list[-1])
        #                         flag = 0
        #                         for i in range(order + 1, order_list[-1] + 1):
        #                             print("i: ", i)
        #                             print("len(order_list) : ", len(order_list))
        #                             try:
        #                                 if approve_dict[i]:
        #                                     for users in approve_dict[i]:
        #                                         print("write")
        #                                         self.write({'next_approve_user_id': [(4, users['u_id'])]})
        #                                         flag = 1
        #                             except:
        #                                 print("pass")
        #                                 pass
        #                             if flag:
        #                                 break


    def action_decline(self):
        self.states = 'cancelled'


    class VendorApproveLine(models.Model):
        _name = "vendor.approve.line"
        _description = "Vendor Approve Line"

        vendor_intake_id = fields.Many2one('vendor.intake', string='Product Request Id',
                                           invisible=True)

        user_id = fields.Many2one('res.users', string="User")
        company_id = fields.Many2one('res.company', string="Company Id")
        location = fields.Many2one('res.company', string="Location")
        department_id = fields.Many2one('hr.department', string="Department")
        emp_name = fields.Many2one('hr.employee', string="Employee")
        designation = fields.Many2one('hr.job', string="Designation")
        approve_order = fields.Integer(string="Order")
        status = fields.Selection(
            selection=[('draft', 'Draft'), ('accept', 'Accept'), ('cancel', 'Cancel'), ('delegate', 'Delegated')],
            string='Status',
            default='draft',
            required=True, tracking=True
        )



    class VendorPricelistLine(models.Model):
        _name = "vendor.pricelist.line"
        _description = "Vendor Price List Line"

        vendor_intake_ids = fields.Many2one('vendor.intake', string='Product Request Id',
                                            invisible=True)

        product = fields.Many2one('product.template', 'Product', Tracking=True)
        qty = fields.Float("Minimum Quantity")
        price = fields.Float("Unit Price")
        delay = fields.Integer("Lead Time")
        company = fields.Many2many('res.company', 'price_list_loc_rel', 'vd_pr', 'loc',
                                   "Locations", check_company=False)




# class ResUsersInherited(models.Model):
#     _inherit = "res.users"
#
#     company_id = fields.Many2many("default ")