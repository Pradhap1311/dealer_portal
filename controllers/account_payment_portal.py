# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError

class AccountPaymentPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(AccountPaymentPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        account_payment_count = request.env['account.payment'].search_count([
            ('partner_id', '=', partner.id)
        ])
        values['account_payment_count'] = account_payment_count
        values['default_url_account_payments'] = '/my/account_payments'
        return values

    @http.route(['/my/account_payments', '/my/account_payments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_account_payments(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        AccountPayment = request.env['account.payment']
        AccountMove = request.env['account.move']

        domain = [('partner_id', '=', partner.id)]

        # Sorting and Filtering
        sort_by_selection = [
            ('date', 'Newest'),
            ('amount', 'Amount'),
        ]
        filter_by_selection = [
            ('all', 'All'),
            ('draft', 'Draft'),
            ('posted', 'Posted'), # Changed from 'open' to 'posted' for account.payment state
            ('reconciled', 'Reconciled'), # Changed from 'paid' to 'reconciled' for account.payment state
            ('cancel', 'Cancelled'),
        ]

        if not sortby:
            sortby = 'date'
        order = 'date desc' if sortby == 'date' else 'amount desc'

        if not filterby:
            filterby = 'all'

        if filterby == 'draft':
            domain += [('state', '=', 'draft')]
        elif filterby == 'posted': # Changed from 'open' to 'posted'
            domain += [('state', '=', 'posted')]
        elif filterby == 'reconciled': # Changed from 'paid' to 'reconciled'
            domain += [('state', '=', 'reconciled')]
        elif filterby == 'cancel':
            domain += [('state', '=', 'cancel')]

        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # Invoice counts for status cards (these still refer to account.move, so payment_state is correct here)
        draft_invoice_count = AccountMove.search_count([('partner_id', '=', partner.id), ('state', '=', 'draft')])
        open_invoice_count = AccountMove.search_count([('partner_id', '=', partner.id), ('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial'))])
        paid_invoice_count = AccountMove.search_count([('partner_id', '=', partner.id), ('state', '=', 'posted'), ('payment_state', '=', 'paid')])
        cancel_invoice_count = AccountMove.search_count([('partner_id', '=', partner.id), ('state', '=', 'cancel')])

        # count for pager
        account_payment_count = AccountPayment.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/account_payments",
            total=account_payment_count,
            page=page,
            step=self._items_per_page,
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search}
        )

        # content according to pager and domain
        account_payments = AccountPayment.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'account_payments': account_payments,
            'page_name': 'account_payment',
            'pager': pager,
            'default_url': '/my/account_payments',
            'sortby': sortby,
            'sort_by_selection': sort_by_selection,
            'filterby': filterby,
            'filter_by_selection': filter_by_selection,
            'search': search,
            'draft_invoice_count': draft_invoice_count,
            'open_invoice_count': open_invoice_count,
            'paid_invoice_count': paid_invoice_count,
            'cancel_invoice_count': cancel_invoice_count,
        })
        return request.render("dealer_portal.portal_my_account_payments_list", values)

    @http.route(['/my/account_payments/<int:payment_id>'], type='http', auth="user", website=True)
    def portal_my_account_payment_detail(self, payment_id, **kw):
        try:
            account_payment = request.env['account.payment'].browse([payment_id]).sudo().read(['name', 'partner_id', 'date', 'amount', 'currency_id', 'state', 'journal_id'])[0]
        except (
            AccessError,
            MissingError
        ):
            return request.redirect('/my')

        if not account_payment or account_payment['partner_id'][0] != request.env.user.partner_id.id:
            return request.redirect('/my')

        values = self._prepare_portal_layout_values()
        values.update({
            'account_payment': account_payment,
            'page_name': 'account_payment_detail',
        })
        return request.render("dealer_portal.portal_my_account_payment_detail", values)