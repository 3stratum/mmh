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
class customer_profile_payment(osv.osv_memory):
    _name = "customer.profile.payment"
    def onchange_cc_number(self,cr,uid,ids,cc_number,context={}):
        res,cc_number_filter = {},''
        if cc_number:
            cc_number_filter = cc_number.strip('%B')[:16]
            if cc_number_filter:
                res['auth_cc_number'] = cc_number_filter
            else:
                res['auth_cc_number'] = cc_number
#            if cc_number.find("?;")  != -1:
#                cc_number_filter = cc_number[cc_number.find(";")+1:cc_number.find("=")]
#            if cc_number_filter:
#                res['auth_cc_number'] = cc_number_filter
##            elif cc_number_filter_an:
##                res['auth_cc_number'] = cc_number_filter_an
#            else:
#                res['auth_cc_number'] = cc_number
        return {'value':res}
            
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        act_model = context.get('active_model',False)
        active_id = context.get('active_id',False)
        invoice_obj = self.pool.get('account.invoice')
        voucher_obj = self.pool.get('account.voucher')
        sale_obj = self.pool.get('sale.order')
        result = super(customer_profile_payment, self).default_get(cr, uid, fields, context=context)
        print "active model",act_model
        if act_model=='sale.order':
#            active_id = context.get('sale_id',False)
#            active_id = context.get('active_id',False)
            if active_id:
                customer_id = self.pool.get('sale.order').browse(cr,uid,active_id).partner_id
                if customer_id:
                    result['partner_id'] = customer_id.id
        elif act_model == 'account.invoice':
#            active_id = context.get('sale_id',False)
            if active_id:
                cur_invoice_obj = invoice_obj.browse(cr,uid,active_id)

                customer_id = cur_invoice_obj.partner_id

                if customer_id:
                    result['partner_id'] = customer_id.id
                    if cur_invoice_obj.state == 'draft':
                        result['charge_amount'] = cur_invoice_obj.amount_total - cur_invoice_obj.amount_charged
                    elif cur_invoice_obj.state == 'open':
                        result['charge_amount'] = cur_invoice_obj.residual - cur_invoice_obj.amount_charged
                    else:
                        result['charge_amount'] = 0.0
                        
        elif act_model == 'account.voucher':
#            active_id = context.get('sale_id',False)
            if active_id:
                voucher_cur = voucher_obj.browse(cr,uid,active_id)

                customer_id = voucher_cur.partner_id

                if customer_id:
                    result['partner_id'] = customer_id.id
                    result['charge_amount'] = voucher_cur.amount
        print "result",result
        return result

    def charge_customer(self,cr,uid,ids,context={}):
        if context is None:
            context = {}
#        active_id = context.get('sale_id',False)
        active_id = context.get('active_id',False)
        authorize_net_config = self.pool.get('authorize.net.config')
        wizard_obj = self.browse(cr, uid, ids[0])
        transaction_type = wizard_obj.transaction_type
        obj_all,transaction_details = False,''
        act_model = context.get('active_model',False)
        invoice_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        
        if act_model == 'sale.order':
            obj_all = self.pool.get('sale.order')
        elif act_model == 'account.invoice':
            obj_all = self.pool.get('account.invoice')
        elif act_model == 'account.voucher':
            obj_all = self.pool.get('account.voucher')
#            cr.execute("SELECT order_id from sale_order_invoice_rel WHERE invoice_id=%s",(active_id[0],))
#            id1 = cr.fetchone()
#            if id1:
#                cr.execute("SELECT auth_transaction_id,authorization_code,customer_payment_profile_id,auth_respmsg FROM sale_order WHERE id = %s",(id1,))
#                result = cr.fetchall()
#                if result:
#                    if result[0][1]:
#                        cr.execute("UPDATE account_invoice SET auth_transaction_id='%s', authorization_code='%s', customer_payment_profile_id='%s',auth_respmsg='%s' where id=%s"%(result[0][0],result[0][1],result[0][2],result[0][3],active_id[0],))
#                        cr.commit()
#                        raise osv.except_osv(_('Warning!'), _('This record has already been authorize !'))
        if active_id:
            id_obj = obj_all.browse(cr,uid,active_id)
            if id_obj:
                customer_id = obj_all.browse(cr,uid,active_id).partner_id
    #            email = customer_id.email
                email = customer_id.email
                cust_db_id = customer_id.id
                cust_profile_Id,numberstring=False,False
                current_obj = self.browse(cr,uid,ids[0])
                ccn = current_obj.auth_cc_number
                exp_date = current_obj.auth_cc_expiration_date
    #            exp_date = exp_date[:4] + '-' + exp_date[4:]
                exp_date = exp_date[-4:] + '-' + exp_date[:2]
                config_ids =authorize_net_config.search(cr,uid,[])
                if config_ids:
                    config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                    action_to_do = context.get('action_to_do',False)
                    if action_to_do == 'new_customer_profile':
                        response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileOnly',cust_db_id,email)
                        print "response",response
                        if response:
                            cust_profile_Id = response.get('cust_profile_id')
                            if cust_profile_Id:
                                if not response.get('sucess'):
                                    profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',cust_profile_Id)
                                    print "profile_info",profile_info
                                    if not profile_info.get('payment_profile'):
                                      response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id,False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                      numberstring = response.get('customerPaymentProfileId',False)
                                    else:
                                        profile_info = profile_info.get('payment_profile')
                                        if ccn[-4:] in profile_info.keys():
                                            numberstring =  profile_info[ccn[-4:]]
                                        else:
                                            response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id,False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                            numberstring = response.get('customerPaymentProfileId',False)
                                else:
                                    response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id,False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                    print"response",response
                                    numberstring = response.get('customerPaymentProfileId',False)
                    else:
                         cust_profile_Id = customer_id.customer_profile_id
                         if cust_profile_Id:
                            cr.execute("select profile_id from custmer_payment_profile where credit_card_no='%s' and customer_profile_id='%s'"%(str(ccn[-4:]),cust_profile_Id))
                            numberstring = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if numberstring:
                                numberstring = numberstring[0]
                         if not numberstring:
                            profile_info = authorize_net_config.call(cr,uid,config_obj,'GetCustomerProfile',cust_profile_Id)
                            print "profile_info",profile_info
                            if not profile_info.get('payment_profile'):
                              response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id,False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                              numberstring = response.get('customerPaymentProfileId',False)
                            else:
                                profile_info = profile_info.get('payment_profile')
                                if ccn[-4:] in profile_info.keys():
                                    numberstring =  profile_info[ccn[-4:]]
                                else:
                                    response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id,False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                                    numberstring = response.get('customerPaymentProfileId',False)
                         if not numberstring:
                            response = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerPaymentProfile',active_id,False,False,False,cust_profile_Id,ccn,exp_date,act_model)
                            numberstring = response.get('customerPaymentProfileId',False)
                    if cust_profile_Id and numberstring:
                        payment_profile_val = {ccn[-4:]: numberstring}
                        self.pool.get('res.partner').cust_profile_payment(cr,uid,customer_id.id,cust_profile_Id,payment_profile_val,context)

                        ### code to get the amount to be charged from the customer profile
                        voucher_cur = False
                        invoice_cur = False
                        if act_model == 'account.voucher':
                            voucher_cur = obj_all.browse(cr,uid,active_id)
                            amount = voucher_cur.amount
                            if round(current_obj.charge_amount,2) <> round(amount,2):
                                raise osv.except_osv(_('Warning!'), _('You\'re charging an invalid amount,the chargeable amount should be only the voucher amount !'))

                        else:
                            invoice_cur = obj_all.browse(cr,uid,active_id)
                            amount =  invoice_cur.amount_total
                            if current_obj.charge_amount <=0 or (current_obj.charge_amount + invoice_cur.amount_charged)  > invoice_cur.amount_total:
                                raise osv.except_osv(_('Warning!'), _('You\'re charging an invalid amount,the chargeable amount is either invalid or greater than the Invoice amount !'))
                            else:
                                amount = current_obj.charge_amount

                        ### code ends here
                        
                        transaction_res = authorize_net_config.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',active_id,transaction_type,amount,cust_profile_Id,numberstring,'',act_model,'',context)
                        if transaction_res:
                            if obj_all._name=='sale.order':
                                obj_all.api_response(cr,uid,active_id,transaction_res,cust_profile_Id,numberstring,transaction_type,'XXXX'+ccn[-4:],context)
                                return transaction_res
                            elif obj_all._name=='account.invoice':
                                obj_all.api_response(cr,uid,active_id,transaction_res,numberstring,transaction_type,context)


                                split = transaction_res.split(',')
#                                if invoice_cur.state =='open' and transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
#                                    invoice_obj.make_payment_of_invoice(cr, uid, [invoice_cur.id],context)

                                ### code to check the state of the Invoice and transaction type
                                #if invoice_cur.state == 'draft' and round((current_obj.charge_amount + invoice_cur.amount_charged),2) >= invoice_cur.amount_total  and  transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                                #    wf_service.trg_validate(uid, 'account.invoice', invoice_cur.id, 'invoice_open', cr)
                                #    invoice_obj.make_payment_of_invoice(cr, uid, [invoice_cur.id],context)
                                #    invoice_cur.write({'amount_charged' : current_obj.charge_amount + invoice_cur.amount_charged})
                                #elif invoice_cur.state == 'open' and round((current_obj.charge_amount + invoice_cur.amount_charged),2) >= invoice_cur.amount_total and  transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                                #    invoice_obj.make_payment_of_invoice(cr, uid, [invoice_cur.id],context)
                                #    invoice_cur.write({'amount_charged' : current_obj.charge_amount + invoice_cur.amount_charged})
                                if transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                                    invoice_cur.write({'amount_charged' : current_obj.charge_amount + invoice_cur.amount_charged})
                                view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
                                view_id = view_ref and view_ref[1] or False,
                                return {
                                    'type': 'ir.actions.act_window',
                                    'name': _('Customer Invoices'),
                                    'res_model': 'account.invoice',
                                    'res_id': invoice_cur.id,
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'view_id': view_id,
                                    'target': 'current',
                                    'nodestroy': True,
                                }
                            elif obj_all._name=='account.voucher':
                                obj_all.api_response(cr,uid,active_id,transaction_res,numberstring,transaction_type,context)


                                split = transaction_res.split(',')

                                ### code to check the state of the Voucher and transaction type
                                ### code to check the transaction details and voucher type of the transaction
                                if voucher_cur.state == 'draft' and transaction_type == 'profileTransAuthCapture' and int(split[0]) == 1:
                                    wf_service.trg_validate(uid, 'account.voucher', voucher_cur.id, 'proforma_voucher', cr)

                                ### code ends here
                                view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_voucher_form')
                                view_id = view_ref and view_ref[1] or False,
                                return {
                                    'type': 'ir.actions.act_window',
                                    'name': _('Customer Payments'),
                                    'res_model': 'account.voucher',
                                    'res_id': voucher_cur.id,
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'view_id': view_id,
                                    'target': 'current',
                                    'nodestroy': True,
                                }

#                                if context.get('recurring_billing'):
                                return transaction_res
#                                if transaction_res and obj_all._name=='sale.order':
#                                    wf_service = netsvc.LocalService("workflow")
#                                    wf_service.trg_validate(uid, 'sale.order', active_id[0], 'order_confirm', cr)
#                                    cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(active_id[0]))
#                                    invoice_id=cr.fetchone()
#                                    if invoice_id:
#                                        self.pool.get('account.invoice').capture_payment(cr,uid,[invoice_id[0]],context)
                else:
                    raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
        return {'type': 'ir.actions.act_window_close'}
    _columns = {
    'partner_id': fields.many2one('res.partner','Partner ID'),
    'auth_cc_number' :fields.char('Credit Card Number',size=256,help="Credit Card Number",required=True),
    'auth_cc_expiration_date' :fields.char('CC Exp Date [MMYYYY]',size=6,help="Credit Card Expiration Date",required=True),
    'transaction_type':fields.selection([('profileTransAuthCapture','Authorize and Capture')], 'Transaction Type'),
    'charge_amount' : fields.float('Charge Amount',digits=(12,2),required=True),
#    'transaction_type':fields.selection([('profileTransAuthOnly','Authorize Only')], 'Transaction Type',readonly=True),
    }
    _defaults = {
        'transaction_type':'profileTransAuthCapture',
        }
customer_profile_payment()
