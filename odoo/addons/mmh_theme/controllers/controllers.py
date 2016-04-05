# -*- coding: utf-8 -*-
from openerp import http

# class MmhTheme(http.Controller):
#     @http.route('/mmh_theme/mmh_theme/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mmh_theme/mmh_theme/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mmh_theme.listing', {
#             'root': '/mmh_theme/mmh_theme',
#             'objects': http.request.env['mmh_theme.mmh_theme'].search([]),
#         })

#     @http.route('/mmh_theme/mmh_theme/objects/<model("mmh_theme.mmh_theme"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mmh_theme.object', {
#             'object': obj
#         })