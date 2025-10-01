# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(MrpProduction, self).create(vals_list)

        return res

    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        compute='_compute_partner_id', store=True,
        help="Customer associated with this manufacturing order."
    )
    workorder_completion_percentage = fields.Float(
        string='Work Order Completion %',
        compute='_compute_workorder_completion_percentage',
        store=True,
        digits=(3, 2),
        help="Percentage of completed work orders for this manufacturing order."
    )
    expected_delivery_date = fields.Date(
        string='Expected Delivery Date',
        compute='_compute_expected_delivery_date',
        store=True,
        help="Expected delivery date for the manufacturing order, considering delivery lead time."
    )

    @api.depends('origin', 'picking_ids.partner_id')
    def _compute_partner_id(self):
        for production in self:
            partner = False
            # Try to find partner from sale order
            if production.origin:
                sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
                if sale_order and sale_order.partner_id:
                    partner = sale_order.partner_id
            # If not found, try from picking
            if not partner and production.picking_ids:
                for picking in production.picking_ids:
                    if picking.partner_id:
                        partner = picking.partner_id
                        break
            production.partner_id = partner

    @api.depends('workorder_ids.state')
    def _compute_workorder_completion_percentage(self):
        for production in self:
            total_workorders = len(production.workorder_ids)
            if total_workorders:
                done_workorders = len(production.workorder_ids.filtered(lambda wo: wo.state == 'done'))
                production.workorder_completion_percentage = (done_workorders / total_workorders) * 100
                _logger.info("MRP Production %s: Work Order Completion %% computed as %.2f%% (%s done out of %s)", production.name, production.workorder_completion_percentage, done_workorders, total_workorders)
            else:
                production.workorder_completion_percentage = 0.0
                _logger.info("MRP Production %s: Work Order Completion %% set to 0.0%% (no work orders)", production.name)

    @api.depends('date_deadline', 'create_date') # Updated dependency
    def _compute_expected_delivery_date(self):
        for production in self:
            base_date = fields.Date.today() # Default to today

            # Safely try to get date_deadline
            if hasattr(production, 'date_deadline') and production.date_deadline:
                base_date = production.date_deadline.date()
            elif production.create_date: # Fallback to create_date if no other date is available
                base_date = production.create_date.date()

            # Consider delivery lead times from associated outgoing pickings
            outgoing_pickings = production.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.delivery_lead_time)
            if outgoing_pickings:
                max_delivery_delay = max(outgoing_pickings.mapped('delivery_lead_time'))
                base_date += timedelta(days=max_delivery_delay)

            production.expected_delivery_date = base_date