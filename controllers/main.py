# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class DealerPortal(CustomerPortal):

    @http.route(['/my/dashboard'], type='http', auth="user", website=True)
    def portal_dealer_dashboard(self, **kw):
        user = request.env.user
        partner = user.partner_id

        # Fetch KPIs
        total_orders = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner.id),
        ])

        orders_in_production = request.env['mrp.production'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', 'not in', ['done', 'cancel'])
        ])

        delivered_orders = request.env['stock.picking'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('picking_type_code', '=', 'outgoing'),
            ('state', '=', 'done')
        ])

        outstanding_payments = request.env['account.move'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ])

        values = self._prepare_portal_layout_values()
        values.update({
            'total_orders': total_orders,
            'orders_in_production': orders_in_production,
            'delivered_orders': delivered_orders,
            'outstanding_payments': outstanding_payments,
            'page_name': 'dashboard',
        })
        return request.render("dealer_portal.dealer_dashboard", values)