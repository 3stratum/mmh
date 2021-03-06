# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from osv import fields, osv
from tools.translate import _
class customer_profile_payment_profile(osv.osv_memory):
    _name = "customer.profile.payment.profile"
    def default_get(self, cr, uid, fields, context=None):
        result = super(customer_profile_payment_profile, self).default_get(cr, uid, fields, context=context)
        partner_id = context.get('active_ids',False)
        if partner_id:
            address_get = self.pool.get('res.partner').address_get(cr,uid,partner_id,['default','invoice','delivery'])
            result['billing_addr'] = address_get.get('invoice',False) or address_get.get('contact',False)
            result['shipping_addr'] = address_get.get('delivery',False) or address_get.get('contact',False)
#            result['shipping_add_info'] = 'no_shipping'
        return result

    def customer_profile(self,cr,uid,ids,context={}):
        partner_id = context.get('active_ids',False)
        numberstring,cust_profile_Id = '',''
        current_obj = self.browse(cr,uid,ids[0])
        authorize_net_config = self.pool.get('authorize.net.config')
        act_model = context.get('active_model',False)

        if partner_id:
            partner_id_obj = self.pool.get('res.partner').browse(cr,uid,partner_id[0])
            billing_address = current_obj.billing_addr
            shipping_address = current_obj.shipping_addr
            check_box = self.browse(cr,uid,ids[0]).customer_profile
            if check_box == True:
                shipping_address = billing_address
#            if billing_address:
#                email = billing_address.email
            email = partner_id_obj.email
            ccn = current_obj.auth_cc_number
            exp_date = current_obj.auth_cc_expiration_date
#            exp_date = exp_date[:4] + '-' + exp_date[4:]
            exp_date = exp_date[-4:] + '-' + exp_date[:2]
            config_ids =authorize_net_config.search(cr,uid,[])
            if config_ids:
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                cust_profile_Id = partner_id_obj.customer_profile_id
                if not cust_profile_Id:
                    response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfile',False,partner_id[0],billing_address,shipping_address,email,ccn,exp_date)
                    cust_profile_Id = response.get('customerProfileId',False)
                    cust_payment_profile_Id = response.get('customerPaymentProfileIdList',False)
                    numberstring = cust_payment_profile_Id.get('numericString',False)
                else:
                    if cust_profile_Id:
                        response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',False,partner_id[0],billing_address,shipping_address,cust_profile_Id,ccn,exp_date,act_model)
                        numberstring = response.get('customerPaymentProfileId',False)
                if response:
                    if numberstring:
                        payment_profile = {ccn[-4:]: numberstring}
                        self.pool.get('res.partner').cust_profile_payment(cr,uid,partner_id[0],cust_profile_Id,payment_profile,context)
            else:
                raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'auth_cc_number' :fields.char('Credit Card Number',size=16,help="Credit Card Number",required=True),
        'auth_cc_expiration_date' :fields.char('CC Exp Date [MMYYYY]',size=6,help="Credit Card Expiration Date",required=True),
        'billing_addr': fields.many2one('res.partner','Billing Address',required=True),
        'shipping_addr': fields.many2one('res.partner','Shipping Address'),
        'customer_profile': fields.boolean('Customer Profile'),
    #    'shipping_add_info':fields.selection([('shipping_add_as_billing','Create a Shipping Profile same as Billing Address'),('new_shipping_profile','New Shipping Profile')], 'Shipping Option',required=True),
    
    }

customer_profile_payment_profile()