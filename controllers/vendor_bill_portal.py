# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

class VendorBillPortal(CustomerPortal):

    _items_per_page = 20

    def _get_vendor_bill_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'invoice_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
            'amount': {'label': 'Amount', 'order': 'amount_total desc'},
        }

    def _get_vendor_bill_searchbar_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'invoice_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
            'amount': {'label': 'Amount', 'order': 'amount_total desc'},
        }

    def _get_vendor_bill_searchbar_filters(self):
        return {
            'all': {'label': 'All', 'domain': []},
            'draft': {'label': 'Draft', 'domain': [('state', '=', 'draft')]},
            'posted': {'label': 'Posted', 'domain': [('state', '=', 'posted')]},
            'paid': {'label': 'Paid', 'domain': [('payment_state', '=', 'paid')]},
            'cancelled': {'label': 'Cancelled', 'domain': [('state', '=', 'cancel')]},
        }

    @http.route(['/my/vendor_bills', '/my/vendor_bills/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_vendor_bills(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        AccountMove = request.env['account.move'].sudo()

        domain = [
            ('move_type', '=', 'in_invoice'),
        ]
        
        # If not admin, restrict to partner's vendor bills
        if not request.env.user.has_group('base.group_system'):
            domain += [('partner_id', 'child_of', [partner.commercial_partner_id.id])]

        # Apply filterby
        searchbar_filters = self._get_vendor_bill_searchbar_filters()
        if filterby and filterby in searchbar_filters:
            domain += searchbar_filters[filterby]['domain']
        else:
            filterby = 'all'

        # Apply search
        if search and search_in:
            if search_in == 'content':
                domain += ['|', ('name', 'ilike', search), ('ref', 'ilike', search)]
            elif search_in == 'partner':
                domain += [('partner_id', 'ilike', search)]

        # Apply sorting
        searchbar_sortings = self._get_vendor_bill_searchbar_sortings()
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Counts for different states
        vendor_bill_draft_count = AccountMove.search_count(domain + [('state', '=', 'draft')])
        vendor_bill_posted_count = AccountMove.search_count(domain + [('state', '=', 'posted')])
        vendor_bill_paid_count = AccountMove.search_count(domain + [('payment_state', '=', 'paid')])
        vendor_bill_cancelled_count = AccountMove.search_count(domain + [('state', '=', 'cancel')])

        # Fetch vendor bills for display
        vendor_bills_count = AccountMove.search_count(domain)
        pager = request.website.pager(
            url="/my/vendor_bills",
            total=vendor_bills_count,
            page=page,
            step=self._items_per_page,
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search, 'search_in': search_in}
        )
        vendor_bills = AccountMove.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'vendor_bills': vendor_bills,
            'vendor_bill_draft_count': vendor_bill_draft_count,
            'vendor_bill_posted_count': vendor_bill_posted_count,
            'vendor_bill_paid_count': vendor_bill_paid_count,
            'vendor_bill_cancelled_count': vendor_bill_cancelled_count,
            'page_name': 'vendor_bills',
            'pager': pager,
            'default_url': '/my/vendor_bills',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'search': search,
            'search_in': search_in,
        })
        return request.render("dealer_portal.portal_my_vendor_bills", values)