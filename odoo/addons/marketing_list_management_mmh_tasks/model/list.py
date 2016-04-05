# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv.orm import Model
from openerp.osv import fields
import logging
from datetime import date, timedelta
from ..utils import send_email
import xlwt
from cStringIO import StringIO
import re

_logger = logging.getLogger(__name__)
FUNNEL_MARKETING = {
    4: 'Book List',
    3: 'Catalog',
    2: 'BKSURVEY',
    1: 'PCBK',
}


class ListHeader(Model):

    _inherit = 'list.header'
    _columns = {
        'content_type': fields.selection([
            ('physical_books', 'Physical Books'),
            ('referral_programs', 'Referral Programs'),
        ], 'Content Type'),
    }

    def _partner_item_deliver(self, cr, uid, context=None):
        """ Generate list of partners that will be deliverd item """
        prod_code = 'BK0910'
        product_id = self.pool['product.product'].search(
            cr, uid, [('default_code', '=', prod_code)])
        if not product_id:
            _logger.error('Missing product ref: %s' % prod_code)
            return

        move_obj = self.pool['stock.move']
        move_ids = move_obj.search(
            cr, uid,
            [
                ('product_id', '=', product_id[0]),
                ('state', 'in', ('assigned', 'confirmed', 'waiting')),
            ],
            context=context)
        if move_ids:
            return [(m['partner_id'][0], m['id']) for m in move_obj.read(
                    cr, uid, move_ids, ['partner_id'])]
        return

    def _new_partners(self, cr, uid, from_date):
        return self.pool['res.partner'].search(
            cr, uid, [('create_date', '>=', from_date)])

    def physical_book_list(self, cr, uid, context=None):
        partners = {}

        week_ago = date.today() - timedelta(days=7)
        partner_ids = self._new_partners(cr, uid, week_ago)

        for p in partner_ids:
            partners[p] = {
                'partner_id': p,
                'stock_move_id': False,
                # We need to be able to discern new customers from others
                'marked': True
            }

        partner_item = self._partner_item_deliver(
            cr, uid, context=context)

        if not partner_item:
            return partners.values()

        for partner_id, move_id in partner_item:
            partners[partner_id] = {
                'partner_id': partner_id,
                'stock_move_id': move_id,
            }

        return partners.values()

    def _partner_invoices_period(self, cr, uid, date_from, date_to,
                                 context=None):
        discount_code = 'REF15'
        discount_id = self.pool['account.invoice.discount'].search(
            cr, uid, [('name', '=', discount_code)])
        if not discount_id:
            _logger.error('Missing discount ref: %s' % discount_code)
            return
        discount_id = discount_id[0]
        invoice_obj = self.pool['account.invoice']
        invoice_ids = invoice_obj.search(cr, uid, [
            ('date_invoice', '>', date_from),
            ('date_invoice', '<', date_to),
            ('amount_total', '>', 0.01),
            ('mmh_disc', '=', discount_id)
        ], context=context)
        if invoice_ids:
            return [(i['partner_id'][0], i['id']) for i in invoice_obj.read(
                    cr, uid, invoice_ids, ['partner_id'])]
        return

    def referral_program_list(self, cr, uid, context=None):
        partners = {}
        # Invoices between week ago and yesterday
        week_ago = date.today() - timedelta(days=7)
        day_ago = date.today() - timedelta(days=1)
        partner_invoices = self._partner_invoices_period(
            cr, uid, week_ago, day_ago, context=context)
        # Early return if not found
        if not partner_invoices:
            return partners.values()
        for partner_id, invoice_id in partner_invoices:
            partners[partner_id] = {
                'partner_id': partner_id,
                'invoice_id': invoice_id,
            }
        return partners.values()

    def list_management_mmh_cron(self, cr, uid, context=None):
        tasks = [
            {
                'name': 'Physical Books List',
                'func': self.physical_book_list,
                'interval_number': 1,
                'interval_type': 'weeks',
                'numbercall': len(FUNNEL_MARKETING),
                'content_type': 'physical_books',
            },
            {
                'name': 'Referral Program List',
                'func': self.referral_program_list,
                'interval_number': 1,
                'interval_type': 'weeks',
                'numbercall': 1,
                'content_type': 'referral_programs',
            },
        ]

        for task in tasks:
            partner_data = task['func'](cr, uid, context=context)
            items = [(0, 0, data) for data in partner_data]
            self.create(cr, uid, {
                'name': task['name'],
                'interval_number': task['interval_number'],
                'interval_type': task['interval_type'],
                'numbercall': task['numbercall'],
                'item_ids': items,
                'content_type': task['content_type'],
            }, context=context)

    def call_tasks(self, cr, uid, list_id, context=None):
        listr = self.browse(cr, uid, list_id, context=context)
        if listr.content_type == 'physical_books':
            marketing_name = FUNNEL_MARKETING.get(listr.numbercall, 'Unkown')
            data = self._create_book_sheet(cr, uid, listr, context=context)
            msg_id = send_email(
                self, cr, uid, list_id,
                'marketing_list_management_mmh_tasks',
                'generic_list', context=context)

            attachment_obj = self.pool['ir.attachment']
            attachment_id = attachment_obj.create(cr, uid, {
                'name': marketing_name,
                'datas_fname': ('_'.join(marketing_name.lower().split()) +
                                '.xls'),
                'datas': data,
                'res_model': self._name,
                'res_id': msg_id,
            }, context=context)

            mail_pool = self.pool['mail.mail']
            mail_pool.write(
                cr, uid, msg_id,
                {'attachment_ids': [(6, 0, [attachment_id])]},
                context=context)
        elif listr.content_type == 'referral_programs':
            data = self._create_referral_program_sheet(
                cr, uid, listr, context=context)
            msg_id = send_email(
                self, cr, uid, list_id,
                'marketing_list_management_mmh_tasks',
                'referral_program_list', context=context)
            attachment_obj = self.pool['ir.attachment']
            attachment_id = attachment_obj.create(cr, uid, {
                'name': "Referral Program List",
                'datas_fname': 'referral_program_list.xls',
                'datas': data,
                'res_model': self._name,
                'res_id': msg_id,
            }, context=context)

            mail_pool = self.pool['mail.mail']
            mail_pool.write(
                cr, uid, msg_id,
                {'attachment_ids': [(6, 0, [attachment_id])]},
                context=context)

    def _prepare_headers(self, worksheet, headers):
        """Writes a lsit of headers to the worksheet"""
        for i, fieldname in enumerate(headers):
            worksheet.write(0, i, fieldname)
            worksheet.col(i).width = 8000  # around 220 pixels

    def _write_row(self, worksheet, row_index, row, style):
        for cell_index, cell_value in enumerate(row):
            if isinstance(cell_value, basestring):
                cell_value = re.sub("\r", " ", cell_value)
            if cell_value is False:
                cell_value = None
            worksheet.write(row_index + 1, cell_index, cell_value, style)

    def _create_referral_program_sheet(self, cr, uid, listr, context=None):
        # TODO Check if x_referrer_id is still char
        # NON-INDEXED query... We do this expensive query because
        # x_referrer_id is actually a char not an id. Better solution would
        # probably be to convert the field in question to an actual link...
        query = """
        SELECT ai.id,
               rp.x_referrer_id,
               ai.amount_total,
               ai.internal_number,
               rp.id,
               refp.name,
               refp.street,
               refp.city,
               ref_state.name,
               refp.zip,
               ref_country.name
        FROM list_item li
            JOIN res_partner rp ON li.partner_id = rp.id
            JOIN account_invoice ai ON li.invoice_id = ai.id
            LEFT OUTER JOIN res_partner refp ON rp.x_referrer_id = refp.id::varchar
            LEFT OUTER JOIN res_country_state ref_state ON refp.state_id = ref_state.id
            LEFT OUTER JOIN res_country ref_country ON refp.country_id = ref_country.id
        WHERE list_id = %s
        """ % (listr.id)
        cr.execute(query)
        rows = cr.fetchall()
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')

        header = [
            'Invoice ID',
            'Referrer ID',
            'Amount Total',
            'Internal Number',
            'Partner ID',
            'Referrer Name',
            'Referrer Street',
            'Referrer City',
            'Referrer State',
            'Referrer Zip',
            'Referrer Country'
        ]
        self._prepare_headers(worksheet, header)

        style = xlwt.easyxf('align: wrap yes')

        for row_index, row in enumerate(rows):
            self._write_row(worksheet, row_index, row, style)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    def _create_book_sheet(self, cr, uid, listr, context=None):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')

        # Header
        header = [
            'Name',
            'Street',
            'Street 2',
            'City',
            'State',
            'Zip Code',
            'Country',
            'Customer Type',
            'Quantity',
            'Start Date',
            'Correct Address'
        ]
        self._prepare_headers(worksheet, header)

        style_normal = xlwt.easyxf('align: wrap yes')
        style_marked = xlwt.easyxf('align: wrap yes; pattern: pattern solid, '
                                   'fore_colour yellow;')

        # Content
        for row_index, item in enumerate(listr.item_ids):
            partner = item.partner_id
            row = [
                partner.name,
                partner.street,
                partner.street2,
                partner.city,
                partner.state_id and partner.state_id.name or None,
                partner.zip,
                partner.country_id and partner.country_id.name or None,
                partner.mmh_cust_type and partner.mmh_cust_type.name or None,
                (item.stock_move_id and item.stock_move_id.sale_line_id and
                    item.stock_move_id.sale_line_id.product_uom_qty or 0),
                partner.mmh_start_date,
                partner.correct_address or 0,
            ]
            if item.marked:
                style = style_marked
            else:
                style = style_normal
            self._write_row(worksheet, row_index, row, style)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        return data


class ListItem(Model):

    _inherit = 'list.item'
    _columns = {
        'stock_move_id': fields.many2one('stock.move', 'Stock Move'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice')
    }
