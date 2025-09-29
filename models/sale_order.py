# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    current_status = fields.Char(
        string='Current Status',
        compute='_compute_current_status',
        store=True,
        help="Current status of the sales order based on its stages and related documents."
    )
    expected_delivery_date = fields.Date(
        string='Expected Delivery Date',
        compute='_compute_expected_delivery_date',
        store=True,
        help="Expected delivery date calculated from product lead times and manufacturing/delivery processes."
    )
    payments_made = fields.Monetary(
        string='Payments Made',
        compute='_compute_payment_info',
        store=True,
        currency_field='currency_id',
        help="Total amount of payments made for this sales order."
    )
    balance_due = fields.Monetary(
        string='Balance Due',
        compute='_compute_payment_info',
        store=True,
        currency_field='currency_id',
        help="Remaining amount to be paid for this sales order."
    )
    payment_status = fields.Selection([
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('pending', 'Pending'),
    ],
        string='Payment Status',
        compute='_compute_payment_info',
        store=True,
        help="Current payment status of the sales order."
    )

    @api.depends('invoice_ids.payment_state', 'invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def _compute_payment_info(self):
        for order in self:
            total_invoiced = sum(order.invoice_ids.filtered(lambda inv: inv.state == 'posted').mapped('amount_total'))
            total_paid = sum(order.invoice_ids.filtered(lambda inv: inv.state == 'posted').mapped('amount_total')) - sum(order.invoice_ids.filtered(lambda inv: inv.state == 'posted').mapped('amount_residual'))
            balance = total_invoiced - total_paid

            order.payments_made = total_paid
            order.balance_due = balance

            if order.amount_total == 0:
                order.payment_status = 'pending'
            elif balance <= 0:
                order.payment_status = 'paid'
            elif balance > 0 and balance < order.amount_total:
                order.payment_status = 'partial'
            else:
                order.payment_status = 'pending'

    @api.depends('state', 'order_line.product_id.seller_ids.delay', 'picking_ids.state', 'picking_ids.scheduled_date', 'procurement_group_id.mrp_production_ids.state')
    def _compute_current_status(self):
        for order in self:
            status = 'Quotation'
            if order.state == 'sale':
                status = 'Confirmed'
                # Check for manufacturing orders
                mrp_productions = order.procurement_group_id.mrp_production_ids.filtered(lambda m: m.state not in ['done', 'cancel'])
                if mrp_productions:
                    status = 'In Production'
                else:
                    # Check for delivery orders
                    pickings = order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.state not in ['done', 'cancel'])
                    if pickings:
                        status = 'Ready' # Or 'In Delivery' depending on exact state
                    elif order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.state == 'done'):
                        status = 'Delivered'
            order.current_status = status

    @api.depends('order_line.product_id.seller_ids.delay', 'date_order', 'picking_ids.scheduled_date', 'procurement_group_id.mrp_production_ids.date_deadline')
    def _compute_expected_delivery_date(self):
        for order in self:
            expected_date = order.date_order.date() if order.date_order else fields.Date.today()

            # Consider product lead times
            max_product_delay = 0
            for line in order.order_line:
                if line.product_id.seller_ids:
                    # Guard against empty list for max()
                    max_product_delay = max(max_product_delay, max(line.product_id.seller_ids.mapped('delay') or [0]))
            expected_date += timedelta(days=max_product_delay)

            # Consider manufacturing lead times
            mrp_productions = order.procurement_group_id.mrp_production_ids
            if mrp_productions:
                # Filter out False values before calling max()
                mrp_dates = [d for d in mrp_productions.mapped('date_deadline') if d]
                if mrp_dates:
                    latest_mrp_date = max(mrp_dates)
                    if isinstance(latest_mrp_date, fields.Datetime):
                        expected_date = max(expected_date, latest_mrp_date.date())
                    elif isinstance(latest_mrp_date, fields.Date):
                        expected_date = max(expected_date, latest_mrp_date)

            # Consider delivery lead times (scheduled date of outgoing pickings)
            pickings = order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.scheduled_date)
            if pickings:
                # Filter out False values before calling max()
                picking_dates = [d for d in pickings.mapped('scheduled_date') if d]
                if picking_dates:
                    latest_picking_date = max(picking_dates)
                    if isinstance(latest_picking_date, fields.Datetime):
                        expected_date = max(expected_date, latest_picking_date.date())
                    elif isinstance(latest_picking_date, fields.Date):
                        expected_date = max(expected_date, latest_picking_date)

            order.expected_delivery_date = expected_date