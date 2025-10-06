# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
import logging
_logger = logging.getLogger(__name__)

class MrpProductionPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(MrpProductionPortal, self)._prepare_portal_layout_values()
        values = super(MrpProductionPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        if request.env.user.has_group('base.group_system'):
            mrp_production_count = request.env['mrp.production'].sudo().search_count([])
        else:
            mrp_production_count = request.env['mrp.production'].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])
        values['mrp_production_count'] = mrp_production_count
        return values

    @http.route(['/my/manufacturing', '/my/manufacturing/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_mrp_productions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', clear_filter=False, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        MrpProduction = request.env['mrp.production']

        if clear_filter:
            filterby = None
            search = None

        domain = []
        if not request.env.user.has_group('base.group_system'):
            domain += [('partner_id', '=', partner.id)]

        # Map filterby parameter to actual MRP production states
        state_map = {
            'draft': 'draft',
            'confirmed': 'confirmed',
            'progress': 'progress',
            'to_close': 'to_close',
            'done': 'done',
            'cancel': 'cancel',
        }

        _logger.info("Portal: filterby parameter: %s", filterby)
        _logger.info("Portal: Initial domain: %s", domain)

        if filterby in state_map:
            domain += [('state', '=', state_map[filterby])]
        
        _logger.info("Portal: Final domain after filterby: %s", domain)

        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # Calculate counts for each state
        mrp_production_counts = {}
        for state_key, state_val in state_map.items():
            mrp_production_counts[state_key + '_mo_count'] = MrpProduction.sudo().search_count([('partner_id', '=', partner.id), ('state', '=', state_val)])
        
        # Total count for pager
        mrp_production_count = MrpProduction.sudo().search_count(domain)
        
        pager = portal_pager(
            url="/my/manufacturing",
            total=mrp_production_count,
            page=page,
            step=self._items_per_page
        )

        mrp_productions = MrpProduction.sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])
        _logger.info("Portal: Mrp Productions found: %s", mrp_productions)

        # Filter by sale order if provided
        sale_order_id = kw.get('sale_order_id')
        if sale_order_id:
            sale_order = request.env['sale.order'].sudo().browse(int(sale_order_id))
            if sale_order.exists() and sale_order.partner_id == partner:
                mrp_productions = mrp_productions.filtered(
                    lambda mo: mo.procurement_group_id == sale_order.procurement_group_id
                )

        _logger.info("Portal: sortby before template render: %s", sortby)
        values.update({
            'mrp_productions': mrp_productions,
            'page_name': 'mrp_production',
            'pager': pager,
            'default_url': '/my/manufacturing',
            'filterby': filterby, # Pass filterby to the template
            **mrp_production_counts, # Pass all counts to the template
            'searchbar_sortings': self._get_mrp_sortings(), # Add this line
            'sortby': sortby, # Add this line
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

        if not mrp_production or (not request.env.user.has_group('base.group_system') and mrp_production['partner_id'][0] != request.env.user.partner_id.id):
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

    def _get_mrp_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
            'state': {'label': 'Status', 'order': 'state asc'},
        }
