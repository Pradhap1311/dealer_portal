# -*- coding: utf-8 -*-

from odoo import fields, models

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        compute='_compute_sale_order_id',
        store=True,
        help="Sales Order linked to the Manufacturing Order of this Work Order."
    )

    def _compute_sale_order_id(self):
        for workorder in self:
            sale_order = False
            if workorder.production_id:
                # Try to get sale order from sale_line_id first
                if workorder.production_id.sale_line_id and workorder.production_id.sale_line_id.order_id:
                    sale_order = workorder.production_id.sale_line_id.order_id
                # If not found, try procurement_group_id
                elif workorder.production_id.procurement_group_id and workorder.production_id.procurement_group_id.sale_id:
                    sale_order = workorder.production_id.procurement_group_id.sale_id
            workorder.sale_order_id = sale_order
