from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging
_logger = logging.getLogger(__name__)

class StockPickingPortal(CustomerPortal):

    @http.route(['/my/receipts/<int:receipt_id>/update'], type='http', auth="user", methods=['POST'], website=True)
    def portal_my_receipt_update(self, receipt_id, **kw):
        try:
            receipt = request.env['stock.picking'].browse(receipt_id)
            if not receipt.exists() or receipt.partner_id != request.env.user.partner_id:
                return request.redirect('/my/')

            # Update the scheduled date
            if 'scheduled_date' in kw:
                receipt.sudo().write({'scheduled_date': kw.get('scheduled_date')})

            return request.redirect('/my/receipts/%s' % receipt_id)
        except Exception as e:
            _logger.error("Error updating receipt: %s", e)
            return request.redirect('/my/')
