# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class AccountPaymentPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(AccountPaymentPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        account_payment_count = request.env['account.payment'].search_count([
            ('partner_id', '=', partner.id)
        ])
        values['account_payment_count'] = account_payment_count
        return values

    @http.route(['/my/payments', '/my/payments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_account_payments(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        AccountPayment = request.env['account.payment']

        domain = [('partner_id', '=', partner.id)]

        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        account_payment_count = AccountPayment.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/payments",
            total=account_payment_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and domain
        account_payments = AccountPayment.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'account_payments': account_payments,
            'page_name': 'account_payment',
            'pager': pager,
            'default_url': '/my/payments',
        })
        return request.render("dealer_portal.portal_my_payments", values)

    @http.route(['/my/payments/<int:payment_id>'], type='http', auth="user", website=True)
    def portal_my_account_payment_detail(self, payment_id, **kw):
        try:
            account_payment = request.env['account.payment'].browse([payment_id])
        except (
            AccessError,
            MissingError
        ):
            return request.redirect('/my')

        if not account_payment or account_payment.partner_id != request.env.user.partner_id:
            return request.redirect('/my')

        values = self._prepare_portal_layout_values()
        values.update({
            'account_payment': account_payment,
            'page_name': 'account_payment_detail',
        })
        return request.render("dealer_portal.portal_my_payment_detail", values)