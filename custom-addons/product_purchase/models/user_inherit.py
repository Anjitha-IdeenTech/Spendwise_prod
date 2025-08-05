from odoo import api, fields, models, _
from odoo.tools.safe_eval import json
from odoo.exceptions import ValidationError


class UserInherit(models.Model):
    _inherit = "res.users"

    res_user_line_id = fields.One2many('res.users.line',
                                       'res_user_id',
                                       string='User Inherit Line',
                                       tracking=True)


    def action_archive(self):
        
        for user in self:
            related_lines = self.env['res.users.line'].search([('res_user_id', '=', user.id)])
            related_lines.unlink()    
        super(UserInherit, self).action_archive()


class UserInheritLine(models.Model):
    _name = "res.users.line"

    company_id = fields.Many2one('res.company', string="Company", required=True)
    # location = fields.Many2one('res.company', string="Location")
    branch_id = fields.Many2one('res.branch', string="Branch", required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    designation = fields.Many2one('hr.job', string="Designation", required=True)

    res_user_id = fields.Many2one('res.users', string='User Id',
                                  invisible=True)

    branch_domain = fields.Char(
        compute="_compute_branch_domain",
        readonly=True,
        store=False,
    )
    def create(self, vals):
        for record_dict in vals:
            if all(key in record_dict for key in ['branch_id', 'company_id', 'designation', 'res_user_id']):
                duplicate_branches = self.env['res.users.line'].search([
                    ('company_id', '=', record_dict['company_id']),
                    ('branch_id', '=', record_dict['branch_id']),
                    ('department_id', '=', record_dict.get('department_id')),
                    ('designation', '=', record_dict['designation']),
                    ('res_user_id', '!=', False)
                ])
                print("The fields are", record_dict['company_id'], record_dict['branch_id'],
                    record_dict.get('department_id'), record_dict['designation'])
                print("The duplicate is", duplicate_branches)
                if not duplicate_branches:
                    res = super(UserInheritLine, self).create(vals)
                    return res
                else:
                    branch_name = self.env['res.branch'].browse(record_dict['branch_id']).name
                    designation_name = self.env['hr.job'].browse(record_dict['designation']).name
                    company_name = self.env['res.company'].browse(record_dict['company_id']).name
                    user_names = ", ".join(branch.res_user_id.name for branch in duplicate_branches if branch.res_user_id)
                    if user_names:
                        raise ValidationError(
                            _("Branch %s with designation %s is already selected for company %s for the user %s") % (
                                branch_name, designation_name, company_name,user_names))


    def write(self, vals):
        for record in self:
            duplicate_branches = self.env['res.users.line'].search([
                ('company_id', '=', vals.get('company_id') or record.company_id.id),
                ('branch_id', '=', vals.get('branch_id') or record.branch_id.id),
                ('department_id', '=', vals.get('department_id') or record.department_id.id),
                ('designation', '=', vals.get('designation') or record.designation.id),
                ('res_user_id', '!=', False),
                ('id', '!=', record.id)
            ])
            print("The fields are", record.company_id, record.branch_id,
                record.department_id, record.designation)
            print("Duplicate branches:", duplicate_branches)
            if duplicate_branches:
                branch_name = record.branch_id.name if record.branch_id else ''
                company_name = record.company_id.name if record.company_id else ''
                designation_name = record.designation.name if record.designation else ''
                user_names = ", ".join(branch.res_user_id.name for branch in duplicate_branches if branch.res_user_id)
                if user_names:
                    raise ValidationError(
                        _("Branch %s with designation %s is already selected for company %s for the user %s") % (
                            branch_name,designation_name,company_name,user_names))
        return super(UserInheritLine, self).write(vals)

    @api.constrains('company_id', 'branch_id')
    def _check_duplicate_selection(self):
        for record in self:
            if record.branch_id and record.company_id and record.designation and record.res_user_id:
                duplicate_branches = self.env['res.users.line'].search([
                    ('res_user_id', '=', record.res_user_id.id),
                    ('company_id', '=', record.company_id.id),
                    ('branch_id', '=', record.branch_id.id),
                    ('department_id', '=', record.department_id.id),
                    ('id', '!=', record.id),
                    ('designation', '=', record.designation.id),
                ])
                if duplicate_branches:
                    raise ValidationError(_("Branch %s with designation %s is already selected for company %s for the user %s") % (
                        record.branch_id.name, record.designation.name, record.company_id.name, record.res_user_id.name))



    @api.depends('company_id')
    def _compute_branch_domain(self):
        for rec in self:
            branch_domain = []
            if rec.company_id:
                branches = self.env['res.branch'].sudo().search([
                    ('company_id', '=', rec.company_id.id)
                ])
                if branches:
                    branch_domain = [('id', 'in', branches.ids)]

            rec.branch_domain = json.dumps(branch_domain)

    # @api.onchange('company_id')
    # def onchange_in_company_id(self):
    #     # self.location = self.company_id
    #     print("self.company_id.id ", self.company_id.name)
    #     department_data = self.env['hr.department'].sudo().search([('company_id', '=', self.company_id.id)])
    #     print(department_data)
    #     department_list = []
    #     for departments in department_data:
    #         department_list.append(departments.id)
    #     print("department_list ", department_list)
    #     res = {'domain': {'department_id': [('id', 'in', department_list)]}}
    #     return res

    # @api.onchange('department_id')
    # def onchange_in_department_id(self):
    #     # self.location = self.company_id
    #     print("Inside department")
    #     print(self.department_id)
    #     job_data = self.env['hr.job'].sudo().search(
    #         [('department_id', '=', self.department_id.id)])
    #     # print(department_data)
    #     job_list = []
    #     for job in job_data:
    #         job_list.append(job.id)
    #     print(job_list)
    #     res = {'domain': {'designation': [('id', 'in', job_list)]}}
    #     return res
