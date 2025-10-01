# -*- coding: utf-8 -*-

from odoo import api, models

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(MrpProduction, self).create(vals_list)
        # Invalidate cache for mrp.production model to ensure counts are updated
        self.env.cache.invalidate([self.env['mrp.production']], ['id'])
        return res