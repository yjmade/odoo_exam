# -*- coding: utf-8 -*-
from openerp import http

# class Examin(http.Controller):
#     @http.route('/examin/examin/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/examin/examin/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('examin.listing', {
#             'root': '/examin/examin',
#             'objects': http.request.env['examin.examin'].search([]),
#         })

#     @http.route('/examin/examin/objects/<model("examin.examin"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('examin.object', {
#             'object': obj
#         })