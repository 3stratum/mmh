# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Enterprise Resource Planning and Management Solution
#
#    Copyright (c) 2014 - Present ITpedia Solutions LLC. All Rights Reserved
#    Author: Ramesh Solanki  <rasolanki@itpediasolutions.com>
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

class res_partner(osv.Model):
    _inherit = 'res.partner'
    
    def getData(self, cr, uid, *param):
        param = param[0]
        
        if param.get('getFields'):
            return[{
                    'id' : {'type':'integer'},
                    'name' : {'type' : 'string'},
                    'ref' : {'type' : 'string'},
                    'street' : {'type' : 'string'},
                    'street2' : {'type' : 'string'},
                    'city' : {'type' : 'string'},
                    'state' : {'type' : 'string'},
                    'zip' : {'type' : 'string'},
                    'country' : {'type' : 'string'},
                    'cust_type' : {'type' : 'string'},
            }]
        res={}

        is_set = param.get('is_set',[])
        is_not_set = param.get('is_not_set',[])
        both = param.get('both',[])
        cust_type = param.get('cust_type',[])
        if not is_set and is_not_set and both:
            return []
        result = []
        ids = []
        if is_set:
            ids = self.search(cr, uid, [('email','!=',False),('mmh_cust_type','=',cust_type)])
        elif is_not_set:
            ids = self.search(cr, uid, [('email','=',False),('mmh_cust_type','=',cust_type)])
        elif both:
             ids = self.search(cr, uid, [('mmh_cust_type','=',cust_type)])
        data = self.browse(cr, uid, ids)
        for i in data:
            res.update({
                        'id' : i.id, 
                        'name' : i.name or '',
                        'ref' : i.ref or '',
                        'street' : i.street or '',
                        'street2' : i.street2 or '',
                        'city' : i.city or '',
                        'state' : i.state_id.name or '',
                        'zip' : i.zip or '',
                        'country' : i.country_id.name or '',
                        'cust_type' : i.mmh_cust_type.name or '',
                         })
            result.append(res)
            res={}
        print result
        return result

            