# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields

class shipping_usps(osv.osv):
    _name = 'shipping.usps'

    def get_usps_info(self,cr,uid,context=None):
        ship_usps_id = self.search(cr,uid,[('active','=',True)])
        if not ship_usps_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites
            if error:
                raise osv.except_osv(_('Error'), _('Active USPS settings not defined'))
            else:
                return False
        else:
            ship_usps_id = ship_usps_id[0]
        return self.browse(cr,uid,ship_usps_id)

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'user_id': fields.char('UserID', size=64, required=True, translate=True),
#        'default' : fields.boolean('Is default?'),
        'test' : fields.boolean('Is test?'),
        'active' : fields.boolean('Active'),
    }
    _defaults = {
        'active' : True,
    }
shipping_usps()

class shipping_fedex(osv.osv):
    _name = 'shipping.fedex'
    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'account_no': fields.char('Account Number', size=64, required=True),
        'key': fields.char('Key', size=64, required=True),
        'password': fields.char('Password', size=64, required=True),
        'meter_no': fields.char('Meter Number', size=64, required=True),
        'integrator_id': fields.char('Integrator ID', size=64, required=True),
#        'default' : fields.boolean('Is default?'),
        'test' : fields.boolean('Is test?'),
        'active' : fields.boolean('Active'),
    }
    _defaults = {
        'active' : True,
    }
shipping_fedex()

class shipping_ups(osv.osv):
    _name = 'shipping.ups'

    def get_ups_info(self,cr,uid,context=None):
        ship_ups_id = self.search(cr,uid,[('active','=',True)])
        if not ship_ups_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites
            if error:
                raise osv.except_osv(_('Error'), _('Active UPS settings not defined'))
            else:
                return False
        else:
            ship_ups_id = ship_ups_id[0]
        return self.browse(cr,uid,ship_ups_id)

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'access_license_no': fields.char('Access License Number', size=64, required=True),
        'user_id': fields.char('UserID', size=64, required=True),
        'password': fields.char('Password', size=64, required=True),
        'shipper_no': fields.char('Shipper Number', size=64, required=True),
#        'default' : fields.boolean('Is default?'),
        'test' : fields.boolean('Is test?'),
        'active' : fields.boolean('Active'),
    }
    _defaults = {
        'active' : True,
    }
shipping_ups()

