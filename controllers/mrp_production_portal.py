# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError

class MrpProductionPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(MrpProductionPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        mrp_production_count = request.env['mrp.production'].search_count([
            ('partner_id', '=', partner.id)
        ])
        values['mrp_production_count'] = mrp_production_count
        return values

    @http.route(['/my/manufacturing', '/my/manufacturing/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_mrp_productions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        MrpProduction = request.env['mrp.production']

        domain = [('partner_id', '=', partner.id)]
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        mrp_production_count = MrpProduction.search_count(domain)
        pager = portal_pager(
            url="/my/manufacturing",
            total=mrp_production_count,
            page=page,
            step=self._items_per_page
        )

        mrp_productions = MrpProduction.search(domain, limit=self._items_per_page, offset=pager['offset'])

        # Filter by sale order if provided
        sale_order_id = kw.get('sale_order_id')
        if sale_order_id:
            sale_order = request.env['sale.order'].sudo().browse(int(sale_order_id))
            if sale_order.exists() and sale_order.partner_id == partner:
                mrp_productions = mrp_productions.filtered(
                    lambda mo: mo.procurement_group_id == sale_order.procurement_group_id
                )

        values.update({
            'mrp_productions': mrp_productions,
            'page_name': 'mrp_production',
            'pager': pager,
            'default_url': '/my/manufacturing',
        })
        return request.render("dealer_portal.portal_my_mrp_productions", values)

    @http.route(['/my/manufacturing/<int:mo_id>'], type='http', auth="user", website=True)
    def portal_my_mrp_production_detail(self, mo_id, **kw):
        try:
            mrp_production = request.env['mrp.production'].browse([mo_id]).sudo().read([
                'name', 'partner_id', 'move_raw_ids', 'workorder_ids',
                'move_byproduct_ids', 'product_id', 'product_qty',
                'product_uom_id', 'origin', 'state', 'date_start',
                'workorder_completion_percentage'
            ])[0]

        except (AccessError, MissingError):
            return request.redirect('/my')

        if not mrp_production or mrp_production['partner_id'][0] != request.env.user.partner_id.id:
            return request.redirect('/my')

        # Related records
        raw_moves = request.env['stock.move'].sudo().browse(mrp_production['move_raw_ids']).read([
            'product_id', 'product_uom_qty', 'product_uom', 'state'
        ])
        workorders = request.env['mrp.workorder'].sudo().browse(mrp_production['workorder_ids']).read([
            'name', 'workcenter_id', 'state', 'duration'
        ])
        byproduct_moves = request.env['stock.move'].sudo().browse(mrp_production['move_byproduct_ids']).read([
            'product_id', 'product_uom_qty', 'product_uom', 'state'
        ])

        values = self._prepare_portal_layout_values()
        values.update({
            'mrp_production': mrp_production,
            'raw_moves': raw_moves,
            'workorders': workorders,
            'byproduct_moves': byproduct_moves,
            'page_name': 'mrp_production_detail',
        })
        return request.render("dealer_portal.portal_my_mrp_production_detail", values)
