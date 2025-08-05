from odoo import models, fields, api , _
from odoo.exceptions import ValidationError, MissingError, UserError

class RegionMaster(models.Model):
    _name = "region.masters"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Region Master"

    name = fields.Char(string="Region Name", required=True, copy=False,tracking=True )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking= True)
    region_code = fields.Char(string="Region Code", copy=False, tracking= True )
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = f"{record.name} ({record.region_code})"
    #         result.append((record.id, name))
    #     return result

class DivisionMaster(models.Model):
    _name = "division.masters"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Division Master"

    name = fields.Char(string="Division Name", required=True, copy=False,tracking=True )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking= True)
    division_code = fields.Char(string="Division Code", copy=False, tracking= True )
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = f"{record.name} ({record.division_code})"
    #         result.append((record.id, name))
    #     return result

class SubDivisionMaster(models.Model):
    _name = "subdivision.masters"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sub Division Master"

    name = fields.Char(string="Sub Division Name", required=True, copy=False,tracking=True )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking= True)
    subdivision_code = fields.Char(string="Sub Division Code", copy=False, tracking= True )
    active = fields.Boolean(string='Active', default=True, tracking=True, store=True)

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = f"{record.name} ({record.subdivision_code})"
    #         result.append((record.id, name))
    #     return result