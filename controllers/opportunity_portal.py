# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

class OpportunityPortal(CustomerPortal):

    _items_per_page = 20

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        # Call the original home method from CustomerPortal
        values = super().home(**kw)
        # Now, update the values with our custom counts
        partner = request.env.user.partner_id
        CrmLead = request.env['crm.lead'].sudo()
        PurchaseOrder = request.env['purchase.order'].sudo()

        # Check if CRM module is installed
        is_crm_installed = bool(request.env['ir.module.module'].sudo().search([('name', '=', 'crm'), ('state', '=', 'installed')]))
        values.qcontext['is_crm_installed'] = is_crm_installed

        if is_crm_installed:
            CrmLead = request.env['crm.lead'].sudo()
            # Opportunities counts
            opportunity_base_domain = [
                ('type', '=', 'opportunity'),
            ]
            if not request.env.user.has_group('base.group_system'):
                opportunity_base_domain += [('partner_id', 'child_of', [partner.commercial_partner_id.id])]
            opportunities_count = CrmLead.search_count(opportunity_base_domain)
            values.qcontext['opportunities_count'] = opportunities_count # Access qcontext for template values
        else:
            values.qcontext['opportunities_count'] = 0 # Default to 0 if CRM is not installed

        # Purchase counts
        purchase_base_domain = []
        if not request.env.user.has_group('base.group_system'):
            purchase_base_domain = [('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])]

        purchase_rfq_count = PurchaseOrder.search_count(purchase_base_domain + [('state', '=', 'draft')])
        purchase_quotes_sent_count = PurchaseOrder.search_count(purchase_base_domain + [('state', '=', 'sent')])
        purchase_confirmed_orders_count = PurchaseOrder.search_count(purchase_base_domain + [('state', '=', 'purchase')])
        
        values.qcontext['purchase_rfq_count'] = purchase_rfq_count
        values.qcontext['purchase_quotes_sent_count'] = purchase_quotes_sent_count
        values.qcontext['purchase_confirmed_orders_count'] = purchase_confirmed_orders_count
        
        
        # Payments counts
        AccountPayment = request.env['account.payment'].sudo()
        AccountMove = request.env['account.move'].sudo()
        
        payments_count = AccountPayment.search_count([('partner_id', '=', partner.id)])
        vendor_bill_draft_count = AccountMove.search_count([('partner_id', '=', partner.id), ('move_type', '=', 'in_invoice'), ('state', '=', 'draft')])
        vendor_bill_posted_count = AccountMove.search_count([('partner_id', '=', partner.id), ('move_type', '=', 'in_invoice'), ('state', '=', 'posted')])
        
        values.qcontext['payments_count'] = payments_count
        values.qcontext['vendor_bill_draft_count'] = vendor_bill_draft_count
        values.qcontext['vendor_bill_posted_count'] = vendor_bill_posted_count

        # Check if CRM module is installed
        is_crm_installed = bool(request.env['ir.module.module'].sudo().search([('name', '=', 'crm'), ('state', '=', 'installed')]))
        values.qcontext['is_crm_installed'] = is_crm_installed
        
        return values

    def _prepare_home_portal_values(self, counters):
        # This method is no longer directly called by home, but might be called by super()
        # We keep it for consistency, but the main logic is now in the overridden home method.
        values = super()._prepare_home_portal_values(counters)
        return values

    def _get_opportunity_searchbar_sortings(self):
        return {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Opportunity', 'order': 'name asc'},
            'stage': {'label': 'Stage', 'order': 'stage_id asc'},
        }

    def _get_opportunity_searchbar_filters(self):
        is_crm_installed = bool(request.env['ir.module.module'].sudo().search([('name', '=', 'crm'), ('state', '=', 'installed')]))
        if not is_crm_installed:
            return {'all': {'label': 'All', 'domain': []}} # Return default if CRM is not installed

        stages = request.env['crm.stage'].sudo().search([])
        filters = {'all': {'label': 'All', 'domain': []}}
        for stage in stages:
            filters[str(stage.id)] = {'label': stage.name, 'domain': [('stage_id', '=', stage.id)]}
        return filters

    @http.route(['/my/opportunities', '/my/opportunities/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_opportunities(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        is_crm_installed = bool(request.env['ir.module.module'].sudo().search([('name', '=', 'crm'), ('state', '=', 'installed')]))
        if not is_crm_installed:
            return request.render("http_routing.404") # Or a custom message

        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        CrmLead = request.env['crm.lead'].sudo()

        base_domain = [
            ('type', '=', 'opportunity'),
        ]
        
        # If not admin, restrict to partner's opportunities
        if not request.env.user.has_group('base.group_system'):
            base_domain += [('partner_id', 'child_of', [partner.commercial_partner_id.id])]
        domain = list(base_domain)

        # Apply filterby
        searchbar_filters = self._get_opportunity_searchbar_filters()
        if filterby and filterby in searchbar_filters:
            domain += searchbar_filters[filterby]['domain']
        else:
            filterby = 'all'

        # Apply search
        if search and search_in:
            if search_in == 'content':
                domain += ['|', ('name', 'ilike', search), ('description', 'ilike', search)]
            elif search_in == 'partner':
                domain += [('partner_id', 'ilike', search)]
            elif search_in == 'stage':
                domain += [('stage_id', 'ilike', search)]

        # Apply sorting
        searchbar_sortings = self._get_opportunity_searchbar_sortings()
        if sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Counts for different stages (using base_domain)
        stage_counts = {}
        for stage_id, stage_filter in searchbar_filters.items():
            if stage_id != 'all':
                stage_counts[stage_id] = CrmLead.search_count(base_domain + stage_filter['domain'])
        
        # Fetch opportunities for display
        opportunities_count = CrmLead.search_count(domain)
        pager = request.website.pager(
            url="/my/opportunities",
            total=opportunities_count,
            page=page,
            step=self._items_per_page,
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search, 'search_in': search_in}
        )
        opportunities = CrmLead.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'opportunities': opportunities,
            'stage_counts': stage_counts,
            'page_name': 'opportunities',
            'pager': pager,
            'default_url': '/my/opportunities',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'search': search,
            'search_in': search_in,
        })
        return request.render("dealer_portal.portal_my_opportunities", values)

    @http.route(['/my/opportunities/<int:opportunity_id>'], type='http', auth="user", website=True)
    def portal_my_opportunity(self, opportunity_id, **kw):
        opportunity = request.env['crm.lead'].sudo().browse(opportunity_id)
        if not opportunity.exists():
            return request.redirect('/my/opportunities')

        values = self._prepare_portal_layout_values()
        values.update({
            'opportunity': opportunity,
            'page_name': 'opportunity_page',
        })
        return request.render("dealer_portal.portal_my_opportunity_page", values)
