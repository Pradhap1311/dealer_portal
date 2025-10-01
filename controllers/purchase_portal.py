# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

class PurchasePortal(CustomerPortal):

    _items_per_page = 20

    def _get_purchase_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
            'amount': {'label': 'Amount', 'order': 'amount_total desc'},
        }

    def _get_purchase_searchbar_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
            'amount': {'label': 'Amount', 'order': 'amount_total desc'},
        }

    def _get_purchase_searchbar_filters(self):
        return {
            'all': {'label': 'All', 'domain': []},
            'rfq': {'label': 'Requests for Quotation', 'domain': [('state', '=', 'draft')]},
            'sent': {'label': 'Quotations Sent', 'domain': [('state', '=', 'sent')]},
            'confirmed': {'label': 'Purchase Orders', 'domain': [('state', '=', 'purchase')]},
            'cancelled': {'label': 'Cancelled', 'domain': [('state', '=', 'cancel')]},
        }

    @http.route(['/my/purchase', '/my/purchase/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_purchase_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PurchaseOrder = request.env['purchase.order'].sudo()

        base_domain = []
        # If not admin, restrict to partner's purchase orders
        if not request.env.user.has_group('base.group_system'):
            base_domain = [('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])]

        domain = list(base_domain) # Start with a copy of base_domain

        # Apply filterby
        searchbar_filters = self._get_purchase_searchbar_filters()
        if filterby and filterby in searchbar_filters:
            domain += searchbar_filters[filterby]['domain']
        else:
            filterby = 'all'

        # Counts for different states (using base_domain)
        rfq_count = PurchaseOrder.search_count(base_domain + [('state', '=', 'draft')])
        quotes_sent_count = PurchaseOrder.search_count(base_domain + [('state', '=', 'sent')])
        confirmed_orders_count = PurchaseOrder.search_count(base_domain + [('state', '=', 'purchase')])
        cancelled_orders_count = PurchaseOrder.search_count(base_domain + [('state', '=', 'cancel')])

        # Paging
        purchase_orders_count = PurchaseOrder.search_count(domain)
        pager = request.website.pager(
            url="/my/purchase",
            total=purchase_orders_count,
            page=page,
            step=self._items_per_page,
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search, 'search_in': search_in}
        )
        # Apply sorting
        searchbar_sortings = self._get_purchase_searchbar_sortings()
        if sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        purchase_orders = PurchaseOrder.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'purchase_orders': purchase_orders,
            'rfq_count': rfq_count,
            'quotes_sent_count': quotes_sent_count,
            'confirmed_orders_count': confirmed_orders_count,
            'cancelled_orders_count': cancelled_orders_count,
            'page_name': 'purchase',
            'pager': pager,
            'default_url': '/my/purchase',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'search': search,
            'search_in': search_in,
        })
        return request.render("dealer_portal.portal_my_purchase", values)