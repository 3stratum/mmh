# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from osv import fields, osv
from tools.translate import _
import netsvc
import math
import decimal_precision as dp

class charge_customer(osv.osv_memory):
    _name = "charge.customer"
    def cust_profile_id(self, cr, uid, context={}):
        act_model = context.get('active_model', False)
#        active_id = context.get('sale_id',False)
        active_id = context.get('active_id',False)
        if active_id:
            if act_model == 'sale.order':
                obj_all = self.pool.get('sale.order').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            elif act_model == 'account.invoice':
                obj_all = self.pool.get('account.invoice').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            elif act_model == 'account.voucher':
                obj_all = self.pool.get('account.voucher').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            if customer_id:
                profile_id = customer_id.customer_profile_id
                res = [(profile_id, profile_id)]
        return res
    
    def customer_payment_id(self, cr, uid, context={}):
        act_model = context.get('active_model', False)
        res = []
#        active_id = context.get('sale_id',False)
        active_id = context.get('active_id',False)
        if active_id:
            if act_model == 'sale.order':
                obj_all = self.pool.get('sale.order').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            elif act_model == 'account.invoice':
                obj_all = self.pool.get('account.invoice').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            elif act_model == 'account.voucher':
                obj_all = self.pool.get('account.voucher').browse(cr,uid,active_id)
                customer_id = obj_all.partner_id
            if customer_id:
                profile_ids = customer_id.profile_ids
                for each_profile in profile_ids:
                    cc_number = each_profile.credit_card_no
                    profile_id = each_profile.profile_id
                    res.append((profile_id, cc_number))
        return res

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        act_model = context.get('active_model',False)
        active_id = context.get('active_id',False)
        invoice_obj = self.pool.get('account.invoice')
        voucher_obj = self.pool.get('account.voucher')
        sale_obj = self.pool.get('sale.order')
        result = super(charge_customer, self).default_get(cr, uid, fields, context=context)
        if act_model == 'account.invoice':
#            active_id = context.get('sale_id',False)
            if active_id:
                cur_invoice_obj = invoice_obj.browse(cr,uid,active_id)
                if cur_invoice_obj.state == 'draft':
                    result['charge_amount'] = cur_invoice_obj.amount_total - cur_invoice_obj.amount_charged
                elif cur_invoice_obj.state == 'open':
                    result['charge_amount'] = cur_invoice_obj.residual - cur_invoice_obj.amount_charged
                else:
                    result['charge_amount'] = 0.0
        elif act_model == 'account.voucher':
            if active_id:
                voucher_cur = voucher_obj.browse(cr, uid, active_id)
                result['charge_amount'] = voucher_cur.amount
        return result

    def charge_customer(self,cr,uid,ids,context={}):
        if context is None:
            context = {}
        act_model = context.get('active_model',False)
#        active_id = context.get('sale_id',False)
        active_id = context.get('active_id',False)
        customer_profile_id,cc_number,obj_all,transaction_id,transaction_response = False,'',False,'',''
        authorize_net_config = self.pool.get('authorize.net.config')
        current_obj = self.browse(cr,uid,ids[0])
        invoice_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")

        if active_id:
            if act_model == 'sale.order':
#                active_id = context.get('sale_id',False)
                obj = self.pool.get('sale.order')
                obj_all = obj.browse(cr,uid,active_id)
                customer_profile_id = obj_all.partner_id.customer_profile_id
                amount = obj_all.amount_total
            elif act_model == 'account.invoice':
#                active_id = [context.get('active_id',False)]
                obj = self.pool.get('account.invoice')
                obj_all = obj.browse(cr,uid,active_id)
                print"obj_all--------",obj_all
                amount = obj_all.amount_total
                customer_profile_id = obj_all.partner_id.customer_profile_id
                if current_obj.charge_amount <=0 or round((current_obj.charge_amount + obj_all.amount_charged),2)  > obj_all.amount_total:
                    raise osv.except_osv(_('Warning!'), _('You\'re charging an invalid amount,the chargeable amount is either invalid or greater than the Invoice amount !'))
                else:
                    amount = current_obj.charge_amount
            ### additional code to check the active model from the customer voucher
            elif act_model == 'account.voucher':
                obj = self.pool.get('account.voucher')
                obj_all = obj.browse(cr,uid,active_id)

                amount = obj_all.amount
                customer_profile_id = obj_all.partner_id.customer_profile_id
                if round(current_obj.charge_amount,2) <> amount:
                    raise osv.except_osv(_('Warning!'), _('You\'re charging an invalid amount,the chargeable amount should be only the voucher amount !'))
            #### code ends here
            
#                cr.execute("SELECT order_id FROM sale_order_invoice_rel WHERE invoice_id=%s",(active_id[0],))
#                id1 = cr.fetchone()
#                if id1:
#                    cr.execute("SELECT auth_transaction_id,authorization_code,customer_payment_profile_id,auth_respmsg FROM sale_order WHERE id = %s",(id1,))
#                    result = cr.fetchall()
#                    if result[0][1]:
#                        cr.execute("UPDATE account_invoice SET auth_transaction_id='%s', authorization_code='%s', customer_payment_profile_id='%s',auth_respmsg='%s' where id=%s"%(result[0][0],result[0][1],result[0][2],result[0][3],active_id[0],))
#                        cr.commit()
#                        raise osv.except_osv(_('Warning!'), _('This record has already been authorize !'))
#            if not obj_all.auth_transaction_id:
            config_ids = authorize_net_config.search(cr,uid,[])
            if config_ids and customer_profile_id:
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                cust_payment_profile_id = current_obj.cust_payment_profile_id
                transaction_type = current_obj.transaction_type

                if act_model in ('account.invoice','sale.order'):
                    if obj_all.auth_transaction_id:
                        transaction_id = obj_all.auth_transaction_id
		print "charge %%%%%%%%%%%%%%%%%%%%%%%%%%"
                transaction_details =authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',active_id,transaction_type,amount,customer_profile_id,cust_payment_profile_id,transaction_id,act_model,'',context)
                cr.execute("select credit_card_no from custmer_payment_profile where profile_id='%s'"%(cust_payment_profile_id))
                cc_number = filter(None, map(lambda x:x[0], cr.fetchall()))
                if cc_number:
                    cc_number = cc_number[0]

                transaction_response = transaction_details
                if transaction_details and obj._name=='sale.order':
                    obj.api_response(cr,uid,active_id,transaction_response,customer_profile_id,cust_payment_profile_id,transaction_type,'XXXX'+cc_number,context)
                if transaction_details and obj._name=='account.invoice':
                    obj.api_response(cr,uid,active_id,transaction_response,cust_payment_profile_id,transaction_type,context)
                    print "transaction details.............////",transaction_details
                    split = transaction_details.split(',')
#                    if obj_all.state =='open' and transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
#                        invoice_obj.make_payment_of_invoice(cr, uid, [obj_all.id],context)

                    ### code to check the state of the Invoice and transaction type
                    print "obj all statre",obj_all.state
                    print "amount",(current_obj.charge_amount + obj_all.amount_charged)
                    print "obj_all.amount_total",obj_all.amount_total
                    #if obj_all.state == 'draft' and round((current_obj.charge_amount + obj_all.amount_charged),2) >= obj_all.amount_total  and  transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                    #    wf_service.trg_validate(uid, 'account.invoice', obj_all.id, 'invoice_open', cr)
                    #    invoice_obj.make_payment_of_invoice(cr, uid, [obj_all.id],context)
                    #    obj_all.write({'amount_charged' : current_obj.charge_amount + obj_all.amount_charged})
                    #elif obj_all.state == 'open' and round((current_obj.charge_amount + obj_all.amount_charged),2) >= obj_all.amount_total and  transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                    #    invoice_obj.make_payment_of_invoice(cr, uid, [obj_all.id],context)
                    #    obj_all.write({'amount_charged' : current_obj.charge_amount + obj_all.amount_charged})
                    if transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                        obj_all.write({'amount_charged' : current_obj.charge_amount + obj_all.amount_charged})
                    view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
                    view_id = view_ref and view_ref[1] or False,
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('Customer Invoices'),
                        'res_model': 'account.invoice',
                        'res_id': obj_all.id,
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': view_id,
                        'target': 'current',
                        'nodestroy': True,
                    }

                ### code to check for active model as account voucher and then validate the voucher
                if transaction_details and obj._name=='account.voucher':
                    obj.api_response(cr,uid,active_id,transaction_response,cust_payment_profile_id,transaction_type,context)
                    split = transaction_details.split(',')
                    
                    ### code to check the transaction details and voucher type of the transaction
                    if obj_all.state == 'draft' and transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                        wf_service.trg_validate(uid, 'account.voucher', obj_all.id, 'proforma_voucher', cr)
                        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_voucher_form')
                        view_id = view_ref and view_ref[1] or False,
                        return {
                            'type': 'ir.actions.act_window',
                            'name': _('Customer Payments'),
                            'res_model': 'account.voucher',
                            'res_id': obj_all.id,
                            'view_type': 'form',
                            'view_mode': 'form',
                            'view_id': view_id,
                            'target': 'current',
                            'nodestroy': True,
                        }

                    ### code ends here

                return transaction_details

#                    if context.get('recurring_billing'):
                
#                        wf_service = netsvc.LocalService("workflow")
#                        wf_service.trg_validate(uid, 'sale.order', active_id[0], 'order_confirm', cr)
#                        cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(active_id[0]))
#                        invoice_id=cr.fetchone()
#                        if invoice_id:
#                            self.pool.get('account.invoice').capture_payment(cr,uid,[invoice_id[0]],context)
            else:
                raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
        return {'type': 'ir.actions.act_window_close'}
    _columns={
#        'cust_profile_id':fields.selection(cust_profile_id, 'Customer Profile ID', help="Gives the state of the order", select=True,required=True),
        'cust_payment_profile_id':fields.selection(customer_payment_id, 'Credit Card Number', help="Credit Card Numer", select=True,required=True),
#        'transaction_type':fields.selection([('profileTransAuthCapture','Authorize and Capture')], 'Transaction Type'),
        'transaction_type':fields.selection([('profileTransAuthCapture','Authorize and Capture'),('profileTransPriorAuthCapture','Prior Auth Capture')], 'Transaction Type'),

        'charge_amount' : fields.float('Charge Amount',digits=(12,2),required=True),
#        'transaction_type':fields.selection([('profileTransAuthOnly','Authorize Only')], 'Transaction Type',readonly=True),
    }
    _defaults = {
        'transaction_type':'profileTransAuthCapture',
        }
charge_customer()
