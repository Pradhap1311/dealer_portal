# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import timedelta

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_lead_time = fields.Integer(
        string='Delivery Lead Time (Days)',
        compute='_compute_delivery_lead_time',
        store=True,
        help="Estimated delivery lead time in days."
    )

    @api.depends('move_ids_without_package.product_id.seller_ids.delay')
    def _compute_delivery_lead_time(self):
        for picking in self:
            max_delay = 0
            for move in picking.move_ids_without_package:
                if move.product_id.seller_ids:
                    max_delay = max(max_delay, max(move.product_id.seller_ids.mapped('delay')))
            picking.delivery_lead_time = max_delay