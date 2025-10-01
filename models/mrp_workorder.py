# -*- coding: utf-8 -*-

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def write(self, vals):
        res = super(MrpWorkorder, self).write(vals)
        # Trigger recomputation of workorder_completion_percentage on the parent mrp.production
        if 'state' in vals and self.production_id:
            _logger.info("Workorder %s state changed to %s. Triggering recomputation for MO %s.", self.name, vals['state'], self.production_id.name)
            self.production_id._compute_workorder_completion_percentage()
        return res