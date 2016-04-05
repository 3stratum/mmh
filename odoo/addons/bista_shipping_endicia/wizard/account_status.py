# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields, osv
from openerp.tools.translate import _

import endicia

class account_status(osv.osv_memory):
    _name = "account.status"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(osv.osv_memory, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar=toolbar)
        if view_type == 'form':
            ship_endicia = self.pool.get('shipping.endicia').get_endicia_info(cr,uid,context)
            requester_id = ship_endicia.requester_id
            account_id = ship_endicia.account_id
            passphrase = ship_endicia.passphrase
            debug = ship_endicia.test

            try:
                request = endicia.AccountStatusRequest(requester_id, account_id, passphrase, debug=debug)
                response = request.send()
                account_status_res = response._get_value()
            except Exception, e:
                raise osv.except_osv(_('Error'), _('Error getting account status'))

            result['arch'] = '''<form string="Account Status">\n
                                <separator string="Account Status" colspan="4" />
                                <group colspan="4" col="2">
                                    <label string="Serial Number:" align="0.0" />
                                    <label string="%s" align="0.0" />
                                    <label string="Postage Balance:" align="0.0" />
                                    <label string="%s" align="0.0" />
                                    <label string="Ascending Balance:" align="0.0" />
                                    <label string="%s" align="0.0" />
                                    <label string="Account Status:" align="0.0" />
                                    <label string="%s" align="0.0" />
                                    <label string="Device ID:" align="0.0" />
                                    <label string="%s" align="0.0" />
                                </group>
                                <group colspan="4" col="1">
                                    <button special="cancel" string="_Close" icon="gtk-cancel"/>
                                </group>
                                </form>''' % (account_status_res['serial_number'], account_status_res['postage_balance'], account_status_res['postage_printed'], account_status_res['account_status'], account_status_res['device_id'])            
        return result

account_status()
