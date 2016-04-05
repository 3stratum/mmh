# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv.orm import Model
from openerp.osv import fields


class ListHeader(Model):

    _name = 'list.header'
    _columns = {
        'name': fields.char('List Name', required=True),
        'generated_date': fields.datetime('Generated', required=True),
        'item_ids': fields.one2many('list.item', 'list_id', 'Items'),
        'active': fields.boolean('Active'),
    }
    _order = 'generated_date desc, name'
    _defaults = {
        'generated_date': fields.datetime.now,
        'active': True,
    }


class ListItem(Model):

    _name = 'list.item'
    _columns = {
        'list_id': fields.many2one('list.header', 'List', required=True,
                                   ondelete="cascade"),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'marked': fields.boolean('Marked', help=("Mark this row in generated "
                                                 "excel sheet."))
    }
    _defaults = {
        'marked': False,
    }
