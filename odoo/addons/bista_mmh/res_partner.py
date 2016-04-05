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
from openerp.osv import osv, fields
from openerp import tools
from openerp import netsvc
from openerp.tools.translate import _
import suds
import sys
wsdl = "https://api.taxcloud.net/1.0/?wsdl"
usps_id = "930BISTA6109"
client = suds.client.Client(wsdl)


# Add Class and Origin to Customer Sales Order.
class res_partner(osv.osv):
    _inherit = "res.partner"
    def _credit_debit_mmh(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for partner in self.browse(cursor, user, ids, context=context):
            res[partner.id] = partner.credit

        return res


    _columns={

     ## replace field country_id to add new attribute required=True
        'country_id': fields.many2one('res.country', 'Country',required=True),

        'cust_bal_mmh': fields.function(_credit_debit_mmh, string='Customer Balance', type='float'),
        'address_valid_message': fields.char('Validation Message',size=256, help="Address is not verified"),
            #'valid_address':fields.boolean("Valid Address"),
    }

#    code to write payment_profile_id in to customer when import order from magento
    def cust_profile_payment(self,cr,uid,ids,profile_id,payment_profile_data,context={}):
        ids =int(ids)
        print'===============cust_profile_payment==================='
        cr.execute("UPDATE res_partner SET customer_profile_id='%s' where id=%d"%(profile_id,ids))
        payment_obj = self.pool.get('custmer.payment.profile')
        active_payment_profile_id = []
        for cc_number in payment_profile_data.iterkeys():
            each_profile = payment_profile_data[cc_number]
            search_payment_profile = payment_obj.search(cr,uid,[('profile_id','=',each_profile),('credit_card_no','=',cc_number)])
            if not search_payment_profile:
                create_payment = payment_obj.create(cr,uid,{'active_payment_profile':True,'profile_id':each_profile,'credit_card_no':cc_number,'customer_profile_id':profile_id})
                active_payment_profile_id.append(create_payment)
                cr.execute('INSERT INTO partner_profile_ids \
                        (partner_id,profile_id) values (%s,%s)', (ids, create_payment))
            else:
                active_payment_profile_id.append(search_payment_profile[0])
        if active_payment_profile_id:
            payment_obj.write(cr,uid,active_payment_profile_id,{'active_payment_profile':True})
            cr.execute("select profile_id from partner_profile_ids where partner_id=%s and profile_id not in %s",(ids,tuple(active_payment_profile_id),))
            in_active_payment_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if in_active_payment_ids:
                payment_obj.write(cr,uid,in_active_payment_ids,{'active_payment_profile':False})
        return True


    def update_customers(self ,cr ,uid ,ids  ,context= None):
	count=0
        for customer in self.browse(cr,uid,self.search(cr ,uid ,[('customer','=',True),('active','=',True)])):
            count=count+1
	    print 'count================',count
            zip_update=[]
            country_update=[]
            zip=customer.zip
            if zip and zip.find('-'):
            
                zip=zip.split('-')
                customer.write({'zip':zip[0]})
                zip_update.append(customer.id)
            if not customer.country_id:
                customer.write({'country_id':customer.state_id and customer.state_id.country_id and customer.state_id.country_id.id})
                
                country_update.append(customer.id)
        print'zip_update==============',zip_update
        print'country_update===========',country_update
        return True




    
    def get_customers(self ,cr ,uid ,ids  ,context= None):
        print "context...model......",context
        part_obj = self.pool.get('res.partner')
        #part_ids = context.get('active_ids',[])
        part_ids = part_obj.search(cr ,uid ,[('customer','=',True),('active','=',True)],limit=1)
        print "part_ids.........",part_ids
        sys.stdout.flush()
        return part_ids
    def view_sales(self, cr, uid, ids, context=None):
        '''This function returns an action that display existing Quotations and Sales corresponding to the customer.
        It can either be a in a list or in a form view, if there is only one invoice to show.
        '''


        model_data = self.pool.get('ir.model.data')
        # Select the view
        tree_view = model_data.get_object_reference(cr, uid, 'sale', 'view_order_tree')
        form_view = model_data.get_object_reference(cr, uid, 'sale', 'view_order_form')
        search_view = model_data.get_object_reference(cr, uid, 'sale', 'view_sales_order_filter')

        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view and tree_view[1] or False, 'tree'),(form_view and form_view[1] or False, 'form'), ],
            'target': 'current',
            'nodestroy': True,
            'context':{'default_partner_id': ids[0],},
            'domain':[('partner_id','in',ids)],
            'search_view_id': search_view and search_view[1] or False,

        }

#    def verify_address(self ,cr ,uid ,ids ,context=None):
#        try:
#            for partner in self.browse( cr ,uid ,ids ):
#                module_obj = self.pool.get('ir.module.module')
#                if module_obj.search(cr, 1, [['name', '=', 'bista_shipping'], ['state', 'in', ['installed', 'to upgrade']]], context=context):
#                    if self._name == "sale.order":
#                        usps_ids = self.pool.get('shipping.usps').search(cr ,uid ,('active','=',True))
#                result = client.service.VerifyAddress(usps_id,partner.street or "",partner.street2 or "",
#                           partner.city or "",partner.state_id and partner.state_id.code or "",partner.zip or "","")
#                print "result.........",result
#            return result
#        except Exception, e:
##             vals.update({'address_varified':False})
#            pass
    def get_state_id(self, cr, uid, code, context=None):
        """ Returns the id of the state from the code. """

        state_obj = self.pool.get('res.country.state')
        return state_obj.search(cr, uid, [('code', '=', code)], context=context)[0]

    def get_country_id(self, cr, uid, code, context=None):
        """ Returns the id of the country from the code. """

        country_obj = self.pool.get('res.country')
        return country_obj.search(cr, uid, [('code', '=', code)], context=context)[0]

    def get_state_code(self, cr, uid, state_id, context=None):
        """ Returns the code from the id of the state. """

        state_obj = self.pool.get('res.country.state')
        return state_id and state_obj.browse(cr, uid, state_id, context=context).code

    def get_country_code(self, cr, uid, country_id, context=None):
        """ Returns the code from the id of the country. """

        country_obj = self.pool.get('res.country')
        return country_id and country_obj.browse(cr, uid, country_id, context=context).code

    def _validate_address(self, cr, uid, address, usps_id=False, context=None):
        """ Returns the valid address from the TaxCloud Address Validation Service. """
        vals={}
        usps_ids =[]
        usps_id = False
        if context is None:
            context = {}
        module_obj = self.pool.get('ir.module.module')
        if module_obj.search(cr, 1, [['name', '=', 'bista_shipping'], ['state', 'in', ['installed', 'to upgrade']]], context=context):
            usps_ids = self.pool.get('shipping.usps').search(cr ,uid ,[('active','=',True)])
            print "usps_ids...........",usps_ids
        if usps_ids:
            usps_id = self.pool.get('shipping.usps').browse(cr ,uid ,usps_ids[0]).user_id
        if not usps_id:
            raise osv.except_osv(_('Warning'), _("USPS is not configured ,Please configure it first."))

        # Obtain the state code & country code and create a BaseAddress Object
        state_code = address.get('state_id') and self.get_state_code(cr, uid, address['state_id'], context=context)
        #country_code = address.get('country_id') and self.get_country_code(cr, uid, address['country_id'], context=context)
#        try:
        verifiedAddress = client.service.VerifyAddress(usps_id, address.get('street') or None, address.get('street2') or None,
                     address.get('city'),state_code, address.get('zip'))
#        print "verifiedAddress.............",verifiedAddress.Zip5,verifiedAddress.Zip4

        if verifiedAddress.ErrNumber!='0':
            vals.update({'address_valid_message':str(verifiedAddress.ErrDescription)})
#            raise osv.except_osv(_('Address Validation Error'), _(str(verifiedAddress.ErrDescription)))
        else:
            vals.update({
                    'street': verifiedAddress.Address1,
                    'street2': verifiedAddress.Address2 if verifiedAddress.__contains__('Address2') else '',
                    'city': verifiedAddress.City,
                    'state_id': self.get_state_id(cr, uid, verifiedAddress.State, context=context),
                    'zip': verifiedAddress.Zip5,
#                    'zip': verifiedAddress.Zip5+'-'+verifiedAddress.Zip4,
                    'address_valid_message': 'Valid Address',
                    'valid_address':True,
                     })

#        except Exception, e:
#            print "Exception E......",e.args
#            raise osv.except_osv(_('Address Validation Error'), _("Address is not Valid"))
#            pass
        #print "vals............",vals
        return vals

    def update_partner_address(self, cr, uid, vals, ids=None, from_write=False, context=None):
        """ Updates the vals dictionary with the valid address as returned from the TaxCloud Address Validation. """
        address = vals
        if vals:
            if (vals.get('street') or vals.get('street2') or vals.get('zip') or vals.get('city') or \
                vals.get('country_id') or vals.get('state_id')):
                print "getting called......"
                # It implies that there is TaxCloud configuration existing for the user company with
                # option 'Address Validation when a address is saved'
                # Check if the other conditions are met
#                 self.check_taxcloud_support(cr, uid, taxcloud_config, address.get('country_id'), context=context)

                # If this method is called from the 'write' method then we also need to pass
                # the previous address along with the modifications in the vals dictionary
                if from_write:
                    fields_to_read = filter(lambda x: x not in vals, ['street', 'street2', 'city', 'state_id', 'zip'])
                    address = fields_to_read and self.read(cr, uid, ids, fields_to_read, context=context)[0] or {}
                    address['state_id'] = address.get('state_id') and address['state_id'][0]
                    #address['country_id'] = address.get('country_id') and address['country_id'][0]
                    address.update(vals)
                #country_code = address.get('country_id') and self.get_country_code(cr, uid, address['country_id'], context=context)
                #if country_code == taxcloud_config.country_id.code :
                valid_address = self._validate_address(cr, uid, address,  context=context)
                vals.update(valid_address)
        return vals


    def create(self, cr, uid, vals, context=None):
        vals = self.update_partner_address(cr, uid, vals, context=context)
        return super(res_partner, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        vals = self.update_partner_address(cr, uid, vals, ids, True, context=context)
        return super(res_partner, self).write(cr, uid, ids, vals, context)

    def taxcloud_address_validate(self, cr, uid, ids, context=None):
        '''
           This function verifies address using taxcloud api.
           It checks for the valid address and updates existing address with the valid address returned from api.
        '''
        if context is None:
            context = {}
        vals ={}
        fields_to_read = ['street', 'street2', 'city', 'state_id', 'zip',]
        address = self.read(cr, uid, ids, fields_to_read, context=context)[0]
        address['state_id'] = address.get('state_id') and address['state_id'][0]
        #address['country_id'] = address.get('country_id') and address['country_id'][0]
        #vals.update(self.update_partner_address(cr, uid, address, ids,usps_id , context=context))
        #vals.update(self._validate_address(cr, uid, address, usps_id, context=context))
        vals.update(self.update_partner_address(cr, uid, address, ids, context=context))
        #print "final vals..........",vals
        self.write(cr, uid, ids, vals, context)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
#            'address_valid_message': '',
        })
        return super(res_partner, self).copy(cr, uid, id, default, context=context)
res_partner()
