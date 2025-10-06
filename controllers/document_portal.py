# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo.osv import expression # Added import

class DocumentPortal(CustomerPortal):

    _items_per_page = 20

    def _get_document_source_name(self, document):
        if document.res_model and document.res_id:
            record = request.env[document.res_model].sudo().browse(document.res_id)
            if record.exists():
                return f"{record._description} ({record.display_name})"
        return "N/A"

    def _get_document_searchbar_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Name', 'order': 'name asc'},
            'type': {'label': 'Type', 'order': 'mimetype asc'},
        }

    @http.route(['/my/documents', '/my/documents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_documents(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', category=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Attachment = request.env['ir.attachment'].sudo()

        category_domains = {
            'sales': [('res_model', '=', 'sale.order')],
            'purchase': [('res_model', '=', 'purchase.order')],
            'mo': [('res_model', '=', 'mrp.production')],
            'payments': [('res_model', 'in', ['account.payment', 'account.move'])],
            'vendor_bills': [('res_model', '=', 'account.move')], # Simplified
            'crm': [('res_model', '=', 'crm.lead')],
            'deliveries': [('res_model', '=', 'stock.picking')], # Added deliveries
        }

        # Build a domain for all documents related to the current partner
        partner_related_domains = []

        # If not admin, restrict to partner's documents
        if not request.env.user.has_group('base.group_system'):
            # Documents directly attached to the partner
            partner_related_domains.append([('res_model', '=', 'res.partner'), ('res_id', '=', partner.id)])

        # Documents attached to Sales Orders of the partner
        sale_orders = request.env['sale.order'].sudo().search([('partner_id', '=', partner.id)])
        if sale_orders:
            partner_related_domains.append([('res_model', '=', 'sale.order'), ('res_id', 'in', sale_orders.ids)])

        # Documents attached to Purchase Orders of the partner
        purchase_orders = request.env['purchase.order'].sudo().search([('partner_id', '=', partner.id)])
        if purchase_orders:
            partner_related_domains.append([('res_model', '=', 'purchase.order'), ('res_id', 'in', purchase_orders.ids)])

        # Documents attached to Account Moves (payments/vendor bills) of the partner
        account_moves = request.env['account.move'].sudo().search([('partner_id', '=', partner.id)])
        if account_moves:
            partner_related_domains.append([('res_model', '=', 'account.move'), ('res_id', 'in', account_moves.ids)])

        # Documents attached to CRM Leads of the partner
        crm_leads = request.env['crm.lead'].sudo().search([('partner_id', '=', partner.id)])
        if crm_leads:
            partner_related_domains.append([('res_model', '=', 'crm.lead'), ('res_id', 'in', crm_leads.ids)])

        # Documents attached to MOs (Manufacturing Orders)
        # mrp.production does not have a direct partner_id.
        # MOs are usually linked to sales orders or other documents.
        # For now, we will not filter MOs by partner directly here.
        # If MOs need to be filtered by partner, a more complex logic
        # involving sales orders or products linked to the partner would be needed.
        # For now, we will include all MOs in the domain if the category is 'mo'.
        # This will be further filtered by the category_domains.

        # Documents attached to Deliveries (Stock Picking) of the partner
        stock_pickings = request.env['stock.picking'].sudo().search([('partner_id', '=', partner.id)])
        if stock_pickings:
            partner_related_domains.append([('res_model', '=', 'stock.picking'), ('res_id', 'in', stock_pickings.ids)])

        # Combine all partner-related domains with OR
        if not request.env.user.has_group('base.group_system'):
            if partner_related_domains:
                partner_base_domain = expression.OR(partner_related_domains)
            else:
                partner_base_domain = [] # No related documents
            domain = list(partner_base_domain)
        else:
            domain = [] # Admin sees all documents (before category filter)

        if category and category in category_domains:
            domain += category_domains[category]
        else:
            category = 'all' # Default category
        
        # Apply search
        if search and search_in:
            if search_in == 'content':
                domain += ['|', ('name', 'ilike', search), ('description', 'ilike', search)]
            elif search_in == 'type':
                domain += [('mimetype', 'ilike', search)]

        # Apply sorting
        searchbar_sortings = self._get_document_searchbar_sortings()
        if sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Filter out attachments not linked to any Odoo record
        domain.append(('res_model', '!=', False))
        domain.append(('res_id', '!=', 0))

        # Exclude system/theme related attachments
        excluded_res_models = [
            'ir.ui.view', 'ir.qweb', 'ir.asset', 'website', 'theme.ir.ui.view',
            'ir.ui.view.custom', 'website.page', 'website.menu', 'base.module.install.request'
        ]
        domain.append(('res_model', 'not in', excluded_res_models))

        # Fetch documents for display
        documents_count = Attachment.search_count(domain)
        pager = request.website.pager(
            url="/my/documents",
            total=documents_count,
            page=page,
            step=self._items_per_page,
            url_args={'sortby': sortby, 'search': search, 'search_in': search_in, 'category': category}
        )
        documents = Attachment.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'documents': documents,
            'documents_count': documents_count,
            'page_name': 'documents',
            'pager': pager,
            'default_url': '/my/documents',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
            'category': category, # Pass category to template
            'document_portal_controller': self, # Pass controller instance to template
        })
        return request.render("dealer_portal.portal_my_documents", values)

    @http.route(['/my/documents/<int:document_id>'], type='http', auth="user", website=True)
    def portal_my_document(self, document_id, **kw):
        attachment = request.env['ir.attachment'].sudo().browse(document_id)

        if not attachment.exists():
            return request.redirect('/my/documents')

        # Check if the user has access to this document (e.g., through partner_id or other related records)
        # This is a basic check, you might need more sophisticated access control
        partner = request.env.user.partner_id
        has_access = False
        if request.env.user.has_group('base.group_system'):
            has_access = True
        elif attachment.res_model == 'res.partner' and attachment.res_id == partner.id:
            has_access = True
        elif attachment.res_model and attachment.res_id:
            record = request.env[attachment.res_model].sudo().browse(attachment.res_id)
            if record.exists() and hasattr(record, 'partner_id') and record.partner_id == partner:
                has_access = True
            # Add more conditions here for other related models if necessary

        if not has_access:
            return request.redirect('/my/documents') # Or return a 403 forbidden page

        if attachment.mimetype == 'application/pdf':
            # Serve PDF inline
            pdf_content = attachment.raw
            headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'inline; filename="%s"' % attachment.name)
            ]
            return request.make_response(pdf_content, headers)
        else:
            # For other file types, redirect to the standard download route
            return request.redirect(f'/web/content/{document_id}?download=true')
