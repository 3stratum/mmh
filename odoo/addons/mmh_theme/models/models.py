# -*- coding: utf-8 -*-

from openerp import models, fields, api

class mmh_theme(models.Model):

    _name = 'mmh_theme.mmh_theme'
#    name = fields.Char(string="MMH Theme")
    
    show_database_selection = fields.Boolean(string="Show Database Selection at Login", default=True)
    show_manage_databases = fields.Boolean(string="Show Database Management Option at Login", default=True)

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100