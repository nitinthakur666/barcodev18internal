# -*- coding: utf-8 -*-
# from odoo import http


# class Sales300Connector(http.Controller):
#     @http.route('/sales300_connector/sales300_connector', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales300_connector/sales300_connector/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales300_connector.listing', {
#             'root': '/sales300_connector/sales300_connector',
#             'objects': http.request.env['sales300_connector.sales300_connector'].search([]),
#         })

#     @http.route('/sales300_connector/sales300_connector/objects/<model("sales300_connector.sales300_connector"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales300_connector.object', {
#             'object': obj
#         })
