# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from osv import osv, fields
import time


import authorize_osv
class authorize_net_config(authorize_osv.authorize_osv):
    _name = "authorize.net.config"
    _rec_name = "api_username"
    def get_customer_profile(self,cr,uid,ids,context={}):
        config_obj = self.browse(cr,uid,ids[0])
        email_ids = {}
        profile_ids_res = self.call(cr,uid,config_obj,'GetProfileIDS')
        if profile_ids_res.get('numericString',False):
           profile_ids = profile_ids_res.get('numericString',False)
           for each_id in profile_ids:
                profile_info = self.call(cr,uid,config_obj,'GetCustomerProfile',each_id)
                if profile_info.get('email',False):
                    email =profile_info.get('email',False)
                    email_ids[email] = {'customerProfileId':profile_info.get('customerProfileId',False),'payment_profile':profile_info.get('payment_profile',False)}
        return email_ids
                    
    def get_profile_ids(self,cr,uid,ids,context={}):
        config_obj = self.browse(cr,uid,ids[0])
        partner_obj = self.pool.get('res.partner')
        profile_ids_res = self.call(cr,uid,config_obj,'GetProfileIDS')
        if profile_ids_res.get('numericString',False):
           profile_ids = profile_ids_res.get('numericString',False)
           customerPaymentProfileId = []
           for each_id in profile_ids:
                profile_ids = self.call(cr,uid,config_obj,'GetCustomerProfile',each_id)
                print "profile_ids",profile_ids
                if profile_ids.get('email',False):
                    email = profile_ids.get('email',False)
                    search_partner = partner_obj.search(cr,uid,[('email','=',email)])
                    if search_partner:
                            if profile_ids.get('customerProfileId',False):
                                customerProfileId  = profile_ids.get('customerProfileId',False)
#                                customerPaymentProfileId  = profile_ids.get('customerPaymentProfileId',False)
                                customerPaymentProfile  = profile_ids.get('payment_profile',False)
                                if customerPaymentProfile:
                                    print"hiiiiiiiiiiiiiii"
#                                    cc_number = (customerPaymentProfile.keys()[0] if customerPaymentProfile.keys() else '')
#                                    customerPaymentProfileId = customerPaymentProfile.values()
                                    partner_obj.cust_profile_payment(cr,uid,search_partner[0],customerProfileId,customerPaymentProfile,context)

        return True
    def onchange_test_production(self,cr,uid,ids,test_production,context):
        if test_production:
            res = {}
            if test_production == 'test':
                res['server_url'] = 'https://apitest.authorize.net/xml/v1/request.api'
            else:
                res['server_url'] = 'https://api.authorize.net/xml/v1/request.api'
            return {'value':res}
    _columns = {
	'api_username' : fields.char('API Login ID', size=100, required=True),
	'transaction_key' : fields.char('Transaction Key', size=100, required=True),
	'server_url': fields.char('Server Url', size=264),
         'test_production': fields.selection([
            ('test', 'Test'),
            ('production', 'Production')
            ], 'Test/Production'),
    }
authorize_net_config()