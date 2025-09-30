# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class StockPickingPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(StockPickingPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        stock_picking_count = request.env['stock.picking'].search_count([
            ('partner_id', '=', partner.id),
            ('picking_type_code', '=', 'outgoing')
        ])
        values['stock_picking_count'] = stock_picking_count
        return values

    @http.route(['/my/delivery', '/my/delivery/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_stock_pickings(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        StockPicking = request.env['stock.picking']

        domain = [('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing')]

        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        stock_picking_count = StockPicking.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/delivery",
            total=stock_picking_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and domain
        stock_pickings_records = StockPicking.search(domain, limit=self._items_per_page, offset=pager['offset']).sudo()

        # If coming from a sale order, filter by it
        sale_order_id = kw.get('sale_order_id')
        if sale_order_id:
            sale_order = request.env['sale.order'].sudo().browse(int(sale_order_id))
            if sale_order.exists() and sale_order.partner_id == partner:
                stock_pickings_records = stock_pickings_records.filtered(lambda p: p.sale_id == sale_order)
        
        stock_pickings = stock_pickings_records.read(['name', 'scheduled_date', 'state'])

        values.update({
            'stock_pickings': stock_pickings,
            'page_name': 'stock_picking',
            'pager': pager,
            'default_url': '/my/delivery',
        })
        return request.render("dealer_portal.portal_my_stock_pickings", values)

    @http.route(['/my/delivery/<int:picking_id>'], type='http', auth="user", website=True)
    def portal_my_stock_picking_detail(self, picking_id, **kw):
        try:
            stock_picking = request.env['stock.picking'].browse([picking_id]).sudo().read(['name', 'scheduled_date', 'state', 'origin', 'move_ids_without_package', 'partner_id'])[0]
        except (
            AccessError,
            MissingError
        ):
            return request.redirect('/my')

        if not stock_picking or stock_picking['partner_id'][0] != request.env.user.partner_id.id:
            return request.redirect('/my')

        # Fetch the stock.move records and their product details
        moves = request.env['stock.move'].sudo().browse(stock_picking['move_ids_without_package']).read(['product_id', 'product_uom_qty', 'product_uom', 'state'])

        values = self._prepare_portal_layout_values()
        values.update({
            'stock_picking': stock_picking,
            'moves': moves, # Pass the fetched moves to the template
            'page_name': 'stock_picking_detail',
        })
        return request.render("dealer_portal.portal_my_stock_picking_detail", values)