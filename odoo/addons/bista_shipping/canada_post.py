# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import osv, fields
from openerp.tools.translate import _
import connection_osv as connection

class shipping_method(osv.osv):
    _name = "shipping.method"
    _description = "Shipping Method"
    def get_service(self,cr,uid,ids,context={}):
        name =  self.browse(cr,uid,ids[0]).name
        passwd =  self.browse(cr,uid,ids[0]).passwd
        environment =  self.browse(cr,uid,ids[0]).environment
        result = connection.call(cr,uid,'GetService',name,passwd,environment)
        for each in result:
            if each.get('service-code',False) and each.get('service-name',False):
                service_code = each.get('service-code',False)
                service_nm = each.get('service-name',False)
                vals = {
                'name': 'Canada Post'+' '+service_nm,
                'service_code':service_code,
                }
                part_id = self.pool.get('res.partner').search(cr, uid, [('name','=', 'Canada Post')])
                prod_id = self.pool.get('product.product').search(cr, uid, [('name','=', 'Canada Service Product')])
                data_val = {
                'name': 'Canada Post'+' '+service_nm,
                'service_code':service_code,
                'active' : True,
                'partner_id' : part_id[0],
                'product_id' : prod_id[0],
                'is_canadapost' : True
                }
                search_val = self.pool.get('service.name').search(cr,uid,[('name','=',each.get('service-name',False))])

                if not search_val:
                    create_ship = self.pool.get('service.name').create(cr,uid,vals)
                service_nm='Canada Post'+' '+service_nm
                search_val = self.pool.get('delivery.carrier').search(cr,uid,[('name','=',service_nm)])
                
                if not search_val:
                    create_carrier = self.pool.get('delivery.carrier').create(cr,uid,data_val)
                    
        return True
    
    _columns = {
        'name': fields.char('User Name', size=64, required=True),
        'passwd': fields.char('Password', size=64, required=True),
        'customer_num': fields.char('Customer Number', size=64, required=True),
        'environment': fields.selection([('sandbox', 'Sandbox'), ('production', 'Production')], 'Environment',required=True),
        'address': fields.many2one('res.partner', 'Address', help="Address of partner", required=True),
    }
shipping_method()

class service_name(osv.osv):
    _name = "service.name"
    _description = "Service Method"
    _columns = {
        'name': fields.char('Service Name', size=64, required=True),
        'service_code': fields.char('Service Code', size=64, required=True),
        'link': fields.text('Link'),
    }
service_name()

