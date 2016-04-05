# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from osv import fields, osv
from tools.translate import _
class profile_transaction(osv.osv_memory):
    _name = "profile.transaction"
   
    def get_selection_val(self,list):
        list1 =[]
        for each_list in list:
            list1.append(each_list)
        return list1
    def new_payment_profile(self,cr,uid,ids,context={}):
        context['sale_id'] = context.get('active_ids', False)
        context['action_to_do'] = 'new_payment_profile'
        active_model= context.get('active_model', False)
        print"active_model",active_model
        if active_model=="sale.order":
            context.update({
                'default_transaction_type': 'profileTransAuthOnly'
            })
        elif active_model=="account.invoice":
            context.update({
                'default_transaction_type': 'profileTransAuthCapture'
            })
        return {
            'name': ('New Payment Profile'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'customer.profile.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
             'context': context
            }
    def default_get(self, cr, uid, fields, context=None):
        result = super(profile_transaction, self).default_get(cr, uid, fields, context=context)
        result['auth_transaction_type'] = 'profileTransAuthCapture'
        sale_order_id = context.get('active_ids', False)
        customer_id = self.pool.get('sale.order').browse(cr,uid,sale_order_id[0]).partner_id
        cust_profile_id = customer_id.customer_profile_id
        if cust_profile_id:
            result['cust_profile_id'] = cust_profile_id
        return result
    def new_customer_profile(self,cr,uid,ids,context={}):
        ids = self.create(cr,uid,{},context)
        context['sale_id'] = context.get('active_ids', False)
        context['action_to_do'] = 'new_customer_profile'
        active_model= context.get('active_model', False)
        print"active_model",active_model
        if active_model=="sale.order":
            context.update({
                'default_transaction_type': 'profileTransAuthOnly'
            })
        elif active_model=="account.invoice":
            context.update({
                'default_transaction_type': 'profileTransAuthCapture'
            })
        return {
            'name': ('Payment Profile'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'customer.profile.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
             'context': context
            }
    def charge_customer(self,cr,uid,ids,context={}):
        sale_order_id = context.get('active_ids', False)
        context['sale_id'] = sale_order_id
        print"context------",context
        active_model= context.get('active_model', False)
        print"active_model",active_model
        if active_model=="sale.order":
            context.update({
                'default_transaction_type': 'profileTransAuthOnly'
            })
        elif active_model=="account.invoice":
            context.update({
                'default_transaction_type': 'profileTransAuthCapture'
            })
        return {
                'name': ('Charge Customer'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'charge.customer',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                 'context': context
            }
#        profile_ids_array = self.browse(cr,uid,ids[0]).profile_ids_array
#        if not profile_ids_array:
#            raise osv.except_osv('Please Select Payment Profile Id!', 'Warning:Please Select Payment Profile Id!')
##        value_true = {}
##        selected_chk_box = ''
##        for keys in self._columns.iterkeys():
##            val = self.read(cr,uid,ids[0],[keys])
##            key_val = val.get(keys,False)
##            if keys != 'auth_transaction_type':
##                value_true[keys] = key_val
##                if key_val:
##                    selected_chk_box= keys
##        true_vals = value_true.values()
##        count =true_vals.count(True)
##        if int(count) > 1:
##            raise osv.except_osv('Please Select Atleast One Payment Profile!', 'Warning:Please Select Atleast One Payment Profile!')
##        elif int(count) == 0:
##            raise osv.except_osv('Please Select Atleast One Payment Profile!', 'Warning:Please Select Atleast One Payment Profile!')
#        config_ids = self.pool.get('authorize.net.config').search(cr,uid,[])
#        sale_order_id = context.get('active_ids', False)
#        transaction_type = self.browse(cr,uid,ids[0]).auth_transaction_type
#        selected_chk_box = self.browse(cr,uid,ids[0]).profile_ids_array
#        if sale_order_id:
#            amount = self.pool.get('sale.order').browse(cr,uid,sale_order_id[0]).amount_total
#            if config_ids:
#                config_obj = self.pool.get('authorize.net.config').browse(cr,uid,config_ids[0])
#                customer_id = self.pool.get('sale.order').browse(cr,uid,sale_order_id[0]).partner_id
#                customer_profile_id = customer_id.customer_profile_id
#                transaction_details =self.pool.get('authorize.net.config').call(cr,uid,config_obj,'CreateCustomerProfileTransaction',sale_order_id[0],transaction_type,amount,customer_profile_id,selected_chk_box,'')
#                self.pool.get('sale.order').api_response(cr,uid,sale_order_id[0],transaction_details,selected_chk_box,transaction_type)
#            else:
#                raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
#        return {'type': 'ir.actions.act_window_close'}
     
#    def view_init(self, cr, uid, fields_list, context=None):
#        print"vewii init"
#        print"fields_list:",fields_list
#        print "profile transcation"
#        result = super(profile_transaction, self).view_init(cr, uid, fields_list, context=context)
#        print"result$$$$$$1111",result
#        sale_order_id = context.get('active_ids', False)
#        print"sale order id$$$$4",sale_order_id
#        if sale_order_id:
#            customer_id = self.pool.get('sale.order').browse(cr,uid,sale_order_id[0]).partner_id
#            if customer_id:
#                print"custmoer id",customer_id
#                profile_ids = customer_id.profile_ids
#                print"profile ids$$$$$",profile_ids
#                if 'auth_transaction_type' not in self._columns:
#                        self._columns['auth_transaction_type'] = fields.selection([('profileTransAuthCapture','Authorize and Capture'),('profileTransAuthOnly','Authorize Only')],'Transaction Type',help="Transaction Type")
#                cust_profile_id = customer_id.customer_profile_id
#                print"cust_profile_id $$$",cust_profile_id
#                if cust_profile_id:
#                    if 'cust_profile_id' not in self._columns:
#                        self._columns['cust_profile_id'] = fields.char(string='Customer Profile ID',size=64,readonly=True)
#                if cust_profile_id:
#                    if 'profile_ids_array' not in self._columns:
#                        self._columns['profile_ids_array'] = fields.selection([('profileTransAuthCapture','Authorize and Capture'),('profileTransAuthOnly','Authorize Only')],'Transaction Type',help="Transaction Type")
##                for each_profile in profile_ids:
##                    profile_id = each_profile.profile_id
##                    if '%s' % profile_id not in self._columns:
##                        self._columns['%s' % profile_id] = fields.boolean(string='%s'%profile_id)
#        print"result$$$$$$",result
#        return result
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(profile_transaction, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        fields_list = {}
        authorize_net_config = self.pool.get('authorize.net.config')
        if context is None:
            context = {}
        if view_type=='form':
            arch = """<form string="Authorize.Net Profiles">"""
#            sale_order_id = context.get('active_ids', False)
            active_id = context.get('active_id', False)
            act_model=context.get('active_model',False)
            if act_model == 'sale.order':
                obj_all = self.pool.get('sale.order')
            elif act_model == 'account.invoice':
                obj_all = self.pool.get('account.invoice')
            elif act_model == 'account.voucher':
                obj_all = self.pool.get('account.voucher')
            if active_id:
#                transaction_id = obj_all.browse(cr,uid,sale_order_id[0]).auth_transaction_id
#                if not transaction_id:
                    customer_id = obj_all.browse(cr,uid,active_id).partner_id
                    profile_ids = customer_id.profile_ids
                    if profile_ids:
                            arch+="""<separator string="EXISTING PAYMENT PROFILES" colspan="4"/>"""
                            for each_profile in profile_ids:
                                    if each_profile.credit_card_no:
                                        credit_card = "Credit Card Number "+each_profile.credit_card_no
                                        arch+="""<newline/><label string='%s' colspan="4"/><newline/>"""%(credit_card)
                            arch+="""<button name="charge_customer" string="Use Existing Card" type="object" icon="gtk-apply"/>"""
                    if customer_id.customer_profile_id:
                        config_ids =authorize_net_config.search(cr,uid,[])
                        if config_ids:
                            config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                            profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',customer_id.customer_profile_id)
                            if profile_info:
                                arch+="""<newline/><button name="new_payment_profile" string="New Payment Profile" type="object" icon="gtk-apply"/>"""
                            else:
                                arch+="""<button name="new_customer_profile" string="New Customer and Payment Profile" type="object" icon="gtk-apply"/>"""
                                    
                    else:
                        arch+="""<button name="new_customer_profile" string="New Customer and Payment Profile" type="object" icon="gtk-apply"/>"""
#                else:
#                    raise osv.except_osv('Transaction Completed!', 'Transaction for this sale order has been already completed!')
            arch += """</form>"""
            context['transaction_type'] = 'auth_transaction_type'
            result['arch'] = arch
            result['fields'] = fields_list
            result['context'] = context
#        return {
#            'name': 'Choose Your Configuration',
#            'type': 'form',
#            'fields': fields_list,
#            'model': 'profile.ransaction',
#            'arch': arch,
#            'field_parent': False,
#            'context': context}
        return result
profile_transaction()