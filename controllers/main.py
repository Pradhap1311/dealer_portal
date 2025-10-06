from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging
_logger = logging.getLogger(__name__)

class DealerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - Partner ID: %s", partner.id)
        _logger.info("DEBUG: partner.id in _prepare_home_portal_values: %s", partner.id)
        _logger.info("DEBUG: partner.commercial_partner_id.id in _prepare_home_portal_values: %s", partner.commercial_partner_id.id)

        # Fetch counts for summary cards
        total_orders_count = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['draft', 'sent', 'sale'])
        ])
        quote_count = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft')
        ])
        quote_sent_count = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '=', 'sent')
        ])
        confirmed_orders_count = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '=', 'sale')
        ])
        cancelled_orders_count = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', '=', 'cancel')
        ])
        orders_in_production = request.env['mrp.production'].sudo().search_count(
            [('partner_id', '=', partner.id)]
        )

        draft_mo_count = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'draft')])
        confirmed_mo_count = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'confirmed')])
        progress_mo_count = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'progress')])
        done_mo_count = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'done')])
        cancel_mo_count = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'cancel')])

        delivery_count = request.env['stock.picking'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('picking_type_code', '=', 'outgoing'),
        ])
        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - Calculated delivery_count: %s", delivery_count)

        draft_delivery_count = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'draft')])
        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - draft_delivery_count: %s", draft_delivery_count)
        waiting_delivery_count = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'waiting')])
        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - waiting_delivery_count: %s", waiting_delivery_count)
        ready_delivery_count = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'assigned')])
        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - ready_delivery_count: %s", ready_delivery_count)
        done_delivery_count = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'done')])
        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - done_delivery_count: %s", done_delivery_count)
        cancel_delivery_count = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'cancel')])
        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - cancel_delivery_count: %s", cancel_delivery_count)

        draft_invoice_count = request.env['account.move'].sudo().search_count([('partner_id', 'child_of', [partner.commercial_partner_id.id]), ('move_type', '=', 'out_invoice'), ('state', '=', 'draft')])
        open_invoice_count = request.env['account.move'].sudo().search_count([('partner_id', 'child_of', [partner.commercial_partner_id.id]), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])])
        paid_invoice_count = request.env['account.move'].sudo().search_count([('partner_id', 'child_of', [partner.commercial_partner_id.id]), ('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid')])
        cancel_invoice_count = request.env['account.move'].sudo().search_count([('partner_id', 'child_of', [partner.commercial_partner_id.id]), ('move_type', '=', 'out_invoice'), ('state', '=', 'cancel')])

        payments_count = draft_invoice_count + open_invoice_count + paid_invoice_count + cancel_invoice_count

        _logger.info("DEBUG: draft_invoice_count in _prepare_home_portal_values: %s", draft_invoice_count)
        _logger.info("DEBUG: payments_count in _prepare_home_portal_values: %s", payments_count)

        _logger.info("DEBUG: draft_invoice_count in _prepare_home_portal_values: %s", draft_invoice_count)
        _logger.info("DEBUG: payments_count in _prepare_home_portal_values: %s", payments_count)

        # Determine if the current user is an administrator
        is_admin = request.env.user.has_group('base.group_system')

        # Purchase Order Counts
        purchase_domain = []
        if not is_admin:
            purchase_domain = [('message_partner_ids', 'child_of', [request.env.user.partner_id.commercial_partner_id.id])]
        purchase_rfq_count = request.env['purchase.order'].sudo().search_count(purchase_domain + [('state', '=', 'draft')])
        purchase_quotes_sent_count = request.env['purchase.order'].sudo().search_count(purchase_domain + [('state', '=', 'sent')])
        purchase_confirmed_orders_count = request.env['purchase.order'].sudo().search_count(purchase_domain + [('state', '=', 'purchase')])
        purchase_cancelled_orders_count = request.env['purchase.order'].sudo().search_count(purchase_domain + [('state', '=', 'cancel')])

        # Vendor Bill Counts
        vendor_bill_domain = [('move_type', '=', 'in_invoice')]
        if not is_admin:
            vendor_bill_domain = [('partner_id', 'child_of', [request.env.user.partner_id.commercial_partner_id.id]), ('move_type', '=', 'in_invoice')]
        vendor_bill_draft_count = request.env['account.move'].sudo().search_count(vendor_bill_domain + [('state', '=', 'draft')])
        vendor_bill_posted_count = request.env['account.move'].sudo().search_count(vendor_bill_domain + [('state', '=', 'posted')])
        vendor_bill_paid_count = request.env['account.move'].sudo().search_count(vendor_bill_domain + [('payment_state', '=', 'paid')])
        vendor_bill_cancelled_count = request.env['account.move'].sudo().search_count(vendor_bill_domain + [('state', '=', 'cancel')])

        values.update({
            'total_orders_count': total_orders_count,
            'quote_count': quote_count,
            'quote_sent_count': quote_sent_count,
            'confirmed_orders_count': confirmed_orders_count,
            'cancelled_orders_count': cancelled_orders_count,
            'in_production_count': orders_in_production,
            'draft_mo_count': draft_mo_count,
            'confirmed_mo_count': confirmed_mo_count,
            'progress_mo_count': progress_mo_count,
            'done_mo_count': done_mo_count,
            'cancel_mo_count': cancel_mo_count,
            'delivery_count': delivery_count,
            'draft_delivery_count': draft_delivery_count,
            'waiting_delivery_count': waiting_delivery_count,
            'ready_delivery_count': ready_delivery_count,
            'done_delivery_count': done_delivery_count,
            'cancel_delivery_count': cancel_delivery_count,
            'payments_count': payments_count,
            'draft_invoice_count': draft_invoice_count,
            'open_invoice_count': open_invoice_count,
            'paid_invoice_count': paid_invoice_count,
            'cancel_invoice_count': cancel_invoice_count,
            'purchase_rfq_count': purchase_rfq_count,
            'purchase_quotes_sent_count': purchase_quotes_sent_count,
            'purchase_confirmed_orders_count': purchase_confirmed_orders_count,
            'purchase_cancelled_orders_count': purchase_cancelled_orders_count,
            'vendor_bill_draft_count': vendor_bill_draft_count,
            'vendor_bill_posted_count': vendor_bill_posted_count,
            'vendor_bill_paid_count': vendor_bill_paid_count,
            'vendor_bill_cancelled_count': vendor_bill_cancelled_count,
        })
        return values

    @http.route(['/my/manufacturing', '/my/manufacturing/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_manufacturing_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', '=', partner.id)]

        if filterby == 'draft':
            domain += [('state', '=', 'draft')]
            values['current_filter_name'] = 'Draft Manufacturing Orders'
        elif filterby == 'confirmed':
            domain += [('state', '=', 'confirmed')]
            values['current_filter_name'] = 'Confirmed Manufacturing Orders'
        elif filterby == 'progress':
            domain += [('state', '=', 'progress')]
            values['current_filter_name'] = 'In Progress Manufacturing Orders'
        elif filterby == 'done':
            domain += [('state', '=', 'done')]
            values['current_filter_name'] = 'Done Manufacturing Orders'
        elif filterby == 'cancel':
            domain += [('state', '=', 'cancel')]
            values['current_filter_name'] = 'Cancelled Manufacturing Orders'
        else:
            values['current_filter_name'] = 'All Manufacturing Orders'

        # Count for status cards
        values['draft_mo_count'] = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'draft')])
        values['confirmed_mo_count'] = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'confirmed')])
        values['progress_mo_count'] = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'progress')])
        values['done_mo_count'] = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'done')])
        values['cancel_mo_count'] = request.env['mrp.production'].sudo().search_count([('partner_id', '=', partner.id), ('state', '=', 'cancel')])

        # Paging
        mrp_productions_count = request.env['mrp.production'].sudo().search_count(domain)
        pager = request.website.pager(url='/my/manufacturing', total=mrp_productions_count, page=page, step=self._items_per_page)
        mrp_productions = request.env['mrp.production'].sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'mrp_productions': mrp_productions,
            'page_name': 'manufacturing',
            'pager': pager,
            'default_url': '/my/manufacturing',
            'searchbar_sortings': self._get_mrp_sortings(), # Need to define this method
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render("dealer_portal.portal_my_manufacturing_orders", values)

    @http.route(['/my/manufacturing/<int:mo_id>'], type='http', auth="user", website=True)
    def portal_my_manufacturing_order(self, mo_id, **kw):
        mrp_production = request.env['mrp.production'].sudo().browse(mo_id)
        if not mrp_production.exists():
            return request.redirect('/my/manufacturing')

        values = self._prepare_portal_layout_values()
        values.update({
            'mrp_production': mrp_production,
            'page_name': 'manufacturing_order_page',
        })
        return request.render("dealer_portal.portal_my_manufacturing_order_page", values)

    @http.route(['/my/delivery', '/my/delivery/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_delivery_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        _logger.info("Portal My Delivery Orders - Partner ID: %s", partner.id)

        domain = [('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing')]
        _logger.info("Portal My Delivery Orders - Initial Domain: %s", domain)

        if filterby == 'draft':
            domain += [('state', '=', 'draft')]
            values['current_filter_name'] = 'Draft Deliveries'
        elif filterby == 'waiting':
            domain += [('state', '=', 'waiting')]
            values['current_filter_name'] = 'Waiting Deliveries'
        elif filterby == 'assigned':
            domain += [('state', '=', 'assigned')]
            values['current_filter_name'] = 'Ready Deliveries'
        elif filterby == 'done':
            domain += [('state', '=', 'done')]
            values['current_filter_name'] = 'Done Deliveries'
        elif filterby == 'cancel':
            domain += [('state', '=', 'cancel')]
            values['current_filter_name'] = 'Cancelled Deliveries'
        else:
            values['current_filter_name'] = 'All Deliveries'

        # Count for status cards
        values['draft_delivery_count'] = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'draft')])
        values['waiting_delivery_count'] = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'waiting')])
        values['ready_delivery_count'] = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'assigned')])
        values['done_delivery_count'] = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'done')])
        values['cancel_delivery_count'] = request.env['stock.picking'].sudo().search_count([('partner_id', '=', partner.id), ('picking_type_code', '=', 'outgoing'), ('state', '=', 'cancel')])

        # Paging
        delivery_orders_count = request.env['stock.picking'].sudo().search_count(domain)
        pager = request.website.pager(url='/my/delivery', total=delivery_orders_count, page=page, step=self._items_per_page)
        delivery_orders = request.env['stock.picking'].sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'delivery_orders': delivery_orders,
            'page_name': 'delivery',
            'pager': pager,
            'default_url': '/my/delivery',
            'searchbar_sortings': self._get_delivery_sortings(), # Need to define this method
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render("dealer_portal.portal_my_delivery_orders", values)

    @http.route(['/my/delivery/<int:do_id>'], type='http', auth="user", website=True)
    def portal_my_delivery_order(self, do_id, **kw):
        delivery_order = request.env['stock.picking'].sudo().browse(do_id)
        if not delivery_order.exists():
            return request.redirect('/my/delivery')

        values = self._prepare_portal_layout_values()
        values.update({
            'delivery_order': delivery_order,
            'page_name': 'delivery_order_page',
        })
        return request.render("dealer_portal.portal_my_delivery_order_page", values)

    @http.route(['/my/payments', '/my/payments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payments(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        _logger.info("Portal My Payments - Partner ID: %s", partner.id)

        domain = [('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice')]
        _logger.info("Portal My Payments - Initial Domain: %s", domain)

        if filterby == 'draft':
            domain += [('state', '=', 'draft')]
            values['current_filter_name'] = 'Draft Invoices'
        elif filterby == 'open':
            domain += [('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])]
            values['current_filter_name'] = 'Open Invoices'
        elif filterby == 'paid':
            domain += [('payment_state', '=', 'paid')]
            values['current_filter_name'] = 'Paid Invoices'
        elif filterby == 'cancel':
            domain += [('state', '=', 'cancel')]
            values['current_filter_name'] = 'Cancelled Invoices'
        else:
            values['current_filter_name'] = 'All Invoices'

        # Count for status cards
        values['draft_invoice_count'] = request.env['account.move'].sudo().search_count([('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'draft')])
        values['open_invoice_count'] = request.env['account.move'].sudo().search_count([('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('payment_state', 'in', ['not_paid', 'partial'])])
        values['paid_invoice_count'] = request.env['account.move'].sudo().search_count([('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid')])
        values['cancel_invoice_count'] = request.env['account.move'].sudo().search_count([('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'cancel')])

        # Paging
        invoices_count = request.env['account.move'].sudo().search_count(domain)
        pager = request.website.pager(url='/my/payments', total=invoices_count, page=page, step=self._items_per_page)
        invoices = request.env['account.move'].sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'invoices': invoices,
            'page_name': 'payments',
            'pager': pager,
            'default_url': '/my/payments',
            'searchbar_sortings': self._get_payment_sortings(), # Need to define this method
            'sortby': sortby,
            'filterby': filterby,
        })
        return request.render("dealer_portal.portal_my_payments", values)

    @http.route(['/my/payments/<int:invoice_id>'], type='http', auth="user", website=True)
    def portal_my_payment(self, invoice_id, **kw):
        invoice = request.env['account.move'].sudo().browse(invoice_id)
        if not invoice.exists():
            return request.redirect('/my/payments')

        values = self._prepare_portal_layout_values()
        values.update({
            'invoice': invoice,
            'page_name': 'payment_page',
        })
        return request.render("dealer_portal.portal_my_payment_page", values)

    def _get_payment_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'invoice_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
        }

    def _get_delivery_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
        }

    def _get_mrp_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
        }

    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        values = self._prepare_sale_portal_rendering_values(page, date_begin, date_end, sortby, filterby=filterby, **kw)
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = values.get('domain', [])
        order = values.get('order', 'create_date desc') # Ensure order is set

        _logger.info("Portal My Orders - Domain: %s, Order: %s", domain, order)

        # Paging
        quotations_count = SaleOrder.search_count(domain)
        pager = request.website.pager(
            url="/my/orders",
            total=quotations_count,
            page=page,
            step=self._items_per_page,
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search}
        )

        # Content according to pager and domain
        orders = SaleOrder.sudo().search(domain, order=values.get('order'), limit=self._items_per_page, offset=pager['offset'])
        _logger.info("Portal My Orders - Fetched orders count for filterby %s: %s", filterby, len(orders))

        values.update({
            'orders': orders,
            'page_name': 'sales_orders',
            'pager': pager,
            'default_url': '/my/orders',
            'searchbar_sortings': self._get_sale_sortings(),
            'sortby': sortby,
            'filterby': filterby,
            'search': search,
            'quote_count': values.get('quote_count'),
            'quote_sent_count': values.get('quote_sent_count'),
            'confirmed_orders_count': values.get('confirmed_orders_count'),
            'cancelled_orders_count': values.get('cancelled_orders_count'),
        })
        return request.render("dealer_portal.portal_my_sales_orders", values)

    def _get_sale_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
            'amount': {'label': 'Amount', 'order': 'amount_total desc'},
        }

    def _prepare_sale_portal_rendering_values(
        self, page=1, date_begin=None, date_end=None, sortby=None, quotation_page=False, filterby=None, **kwargs
    ):
        values = super()._prepare_sale_portal_rendering_values(page, date_begin, date_end, sortby, quotation_page, **kwargs)
        partner = request.env.user.partner_id

        if filterby == 'quotation':
            domain = [('partner_id', '=', partner.id), ('state', 'in', ('draft', 'sent'))]
            values['current_filter_name'] = 'Quotations' # New variable for page title
        elif filterby == 'sent':
            domain = [('partner_id', '=', partner.id), ('state', '=', 'sent')]
            values['current_filter_name'] = 'Quotations Sent'
        elif filterby == 'sale':
            domain = [('partner_id', '=', partner.id), ('state', '=', 'sale')]
            values['current_filter_name'] = 'Sales Orders' # New variable for page title
        elif filterby == 'cancel':
            domain = [('partner_id', '=', partner.id), ('state', '=', 'cancel')]
            values['current_filter_name'] = 'Cancelled Orders'
        else: # 'all' or no filter
            domain = [('partner_id', '=', partner.id)]
            values['current_filter_name'] = 'All Orders' # New variable for page title

        values['page_name'] = '' # Set page_name to empty for breadcrumbs

        # Update the domain in values to reflect the filterby selection
        values['domain'] = domain

        # Sorting
        sort_by_selection = [
            ('date', 'Newest'),
            ('name', 'Reference'),
            ('amount', 'Amount'),
        ]
        if not sortby:
            sortby = 'date'
        order = 'create_date desc' if sortby == 'date' else 'name asc' if sortby == 'name' else 'amount_total desc'
        values['order'] = order
        values['sortby'] = sortby
        values['sort_by_selection'] = sort_by_selection

        # Fetch counts for sales order status cards
        partner_id = partner.id
        values['quote_count'] = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner_id),
            ('state', '=', 'draft')
        ])
        values['quote_sent_count'] = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner_id),
            ('state', '=', 'sent')
        ])
        values['confirmed_orders_count'] = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner_id),
            ('state', '=', 'sale')
        ])
        values['cancelled_orders_count'] = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner_id),
            ('state', '=', 'cancel')
        ])

        return values

    @http.route(['/my/dashboard'], type='http', auth="user", website=True)
    def portal_dealer_dashboard(self, **kw):
        user = request.env.user
        partner = user.partner_id

        _logger.info("Dealer Portal Dashboard - portal_dealer_dashboard - Partner ID: %s", partner.id)

        # Fetch KPIs
        total_orders = request.env['sale.order'].sudo().search_count(
            [('partner_id', '=', partner.id), ('state', 'in', ['draft', 'sent', 'sale'])]
        )

        orders_in_production = request.env['mrp.production'].sudo().search_count(
            [('partner_id', '=', partner.id)]
        )

        all_outgoing_pickings = request.env['stock.picking'].sudo().search([
            ('partner_id', '=', partner.id),
            ('picking_type_code', '=', 'outgoing')
        ])
        _logger.info("Dealer Portal Dashboard - All Outgoing Pickings for Partner %s: %s", partner.id, all_outgoing_pickings.mapped('state'))

        pending_deliveries_count = all_outgoing_pickings.search_count([('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned'])])
        delivered_orders_count = all_outgoing_pickings.search_count([('state', '=', 'done')])
        cancelled_deliveries_count = all_outgoing_pickings.search_count([('state', '=', 'cancel')])

        all_invoices = request.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
        ])
        _logger.info("Dealer Portal Dashboard - All Outgoing Invoices for Partner %s: %s", partner.id, all_invoices.mapped('payment_state'))

        not_paid_invoices_count = all_invoices.search_count([('payment_state', '=', 'not_paid')])
        partial_paid_invoices_count = all_invoices.search_count([('payment_state', '=', 'partial')])
        paid_invoices_count = all_invoices.search_count([('payment_state', '=', 'paid')])
        in_payment_invoices_count = all_invoices.search_count([('payment_state', '=', 'in_payment')])
        reversed_invoices_count = all_invoices.search_count([('payment_state', '=', 'reversed')])

        draft_invoices_count = request.env['account.move'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'draft')
        ])

        total_payments_count = not_paid_invoices_count + partial_paid_invoices_count + paid_invoices_count + \
                               in_payment_invoices_count + reversed_invoices_count + draft_invoices_count

        values = self._prepare_portal_layout_values()

        values.update({
            'total_orders': total_orders,
            'orders_in_production': orders_in_production,
            'pending_deliveries_count': pending_deliveries_count,
            'delivered_orders': delivered_orders_count,
            'cancelled_deliveries_count': cancelled_deliveries_count,
            'not_paid_invoices_count': not_paid_invoices_count,
            'partial_paid_invoices_count': partial_paid_invoices_count,
            'paid_invoices_count': paid_invoices_count,
            'in_payment_invoices_count': in_payment_invoices_count,
            'reversed_invoices_count': reversed_invoices_count,
            'total_payments_count': total_payments_count, # Add this new count
            'page_name': 'dashboard',
        })
        return request.render("dealer_portal.dealer_dashboard", values)