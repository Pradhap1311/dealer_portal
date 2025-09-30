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

        # Fetch counts for summary cards
        total_orders_count = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['draft', 'sent', 'sale'])
        ])
        in_production_count = request.env['mrp.production'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('state', 'not in', ['done', 'cancel'])
        ])
        delivery_count = request.env['stock.picking'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('picking_type_code', '=', 'outgoing'),
            ('state', '=', 'done')
        ])

        all_invoices_for_home = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
        ])
        _logger.info("Dealer Portal Dashboard - _prepare_home_portal_values - All Outgoing Invoices for Partner %s: %s", partner.id, all_invoices_for_home.mapped('payment_state'))

        payments_count = all_invoices_for_home.search_count([
            ('payment_state', 'in', ['not_paid', 'partial'])
        ])

        values.update({
            'total_orders_count': total_orders_count,
            'in_production_count': in_production_count,
            'delivery_count': delivery_count,
            'payments_count': payments_count,
        })
        return values

    def _prepare_sale_portal_rendering_values(
        self, page=1, date_begin=None, date_end=None, sortby=None, quotation_page=False, filterby=None, **kwargs
    ):
        values = super()._prepare_sale_portal_rendering_values(page, date_begin, date_end, sortby, quotation_page, **kwargs)
        partner = request.env.user.partner_id

        if filterby == 'quotation':
            domain = self._prepare_quotations_domain(partner)
            values['current_filter_name'] = 'Quotations' # New variable for page title
        elif filterby == 'sale':
            domain = self._prepare_orders_domain(partner)
            values['current_filter_name'] = 'Sales Orders' # New variable for page title
        else: # 'all' or no filter
            domain = [('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])]
            values['current_filter_name'] = 'All Orders' # New variable for page title

        values['page_name'] = '' # Set page_name to empty for breadcrumbs

        # Update the domain in values to reflect the filterby selection
        values['domain'] = domain
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
            [('partner_id', '=', partner.id),
            ('state', 'not in', ['done', 'cancel'])]
        )

        all_outgoing_pickings = request.env['stock.picking'].sudo().search([
            ('partner_id', '=', partner.id),
            ('picking_type_code', '=', 'outgoing')
        ])
        _logger.info("Dealer Portal Dashboard - All Outgoing Pickings for Partner %s: %s", partner.id, all_outgoing_pickings.mapped('state'))

        pending_deliveries_count = all_outgoing_pickings.search_count([('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned'])])
        delivered_orders_count = all_outgoing_pickings.search_count([('state', '=', 'done')])
        cancelled_deliveries_count = all_outgoing_pickings.search_count([('state', '=', 'cancel')])

        all_invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
        ])
        _logger.info("Dealer Portal Dashboard - All Outgoing Invoices for Partner %s: %s", partner.id, all_invoices.mapped('payment_state'))

        not_paid_invoices_count = all_invoices.search_count([('payment_state', '=', 'not_paid')])
        partial_paid_invoices_count = all_invoices.search_count([('payment_state', '=', 'partial')])
        paid_invoices_count = all_invoices.search_count([('payment_state', '=', 'paid')])
        in_payment_invoices_count = all_invoices.search_count([('payment_state', '=', 'in_payment')])
        reversed_invoices_count = all_invoices.search_count([('payment_state', '=', 'reversed')])

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
            'page_name': 'dashboard',
        })
        return request.render("dealer_portal.dealer_dashboard", values)