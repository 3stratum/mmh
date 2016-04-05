# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from osv import osv, fields
import time
from datetime import datetime, date
import socket
#try:
#    from quix.pay.gateway.authorizenet import AimGateway
#    from quix.pay.transaction import CreditCard
#except:
#    pass
class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
            'auth_transaction_type':fields.char('Transaction Type',size=256),
            'auth_transaction_id' :fields.char('Transaction ID', size=256,readonly=True),
            'customer_profile_id' :fields.char('Profile ID', size=256,readonly=True),
            'cc_number' :fields.char('Credit Card Number', size=256),
            'auth_respmsg' :fields.text('Response Message',readonly=True),
            'authorization_code': fields.char('Authorization Code',size=256,readonly=True),
            'customer_payment_profile_id': fields.char('Payment Profile ID',size=256,readonly=True),
            'cc_type': fields.char('Card Type',size=256,readonly=True)
	}
    def copy(self,cr,uid,ids,vals,context):
        vals.update({'auth_transaction_type':'','auth_transaction_id':'','cc_number':'',
        'auth_respmsg': '','authorization_code':'','customer_payment_profile_id':''})
        return super(sale_order, self).copy(cr, uid, ids, vals,context=context)
        
    def api_response(self,cr,uid,ids,response,customer_profile_id,payment_profile_id,transaction_type,cc_number,context={}):
        split = response.split(',')
        vals = {}
        if split:
            transaction_id = split[6]
            transaction_message = split[3]
            authorize_code = split[4]
            cc_type = split[51]
            if transaction_id and transaction_message:
                vals['auth_transaction_id'] = transaction_id
                vals['auth_respmsg'] = transaction_message
#                cr.execute("UPDATE sale_order SET auth_transaction_id='%s', auth_respmsg='%s'where id=%d"%(transaction_id,transaction_message,ids))
            if authorize_code:
                vals['authorization_code'] = authorize_code
#                cr.execute("UPDATE sale_order SET authorization_code='%s' where id=%d"%(authorize_code,ids))
            if payment_profile_id:
                vals['customer_payment_profile_id'] = payment_profile_id
#                cr.execute("UPDATE sale_order SET customer_payment_profile_id='%s' where id=%d"%(payment_profile_id,ids))
            if transaction_type:
                vals['auth_transaction_type'] = transaction_type
#                cr.execute("UPDATE sale_order SET auth_transaction_type='%s' where id=%d"%(transaction_type,ids))
            if customer_profile_id:
                vals['customer_profile_id'] = customer_profile_id
            if cc_number:
                vals['cc_number'] = cc_number
            if cc_type:
                if cc_type == 'Visa':
                    cc_type = 'VI'
                elif cc_type == 'MasterCard':
                    cc_type = 'MA'
                elif cc_type == 'American Express':
                    cc_type = 'AE'
                elif cc_type == 'Discover':
                    cc_type = 'DI'
                vals['cc_type'] = cc_type
            if vals:
                self.write(cr,uid,ids,vals)
            self.log(cr,uid,ids,transaction_message)
        return True
    """def submit(self,cr,uid,ids,context=None):
        (data,) = self.browse(cr,uid,ids)
        print 'data',data
        name_first = ''
        name_second = ''
        address = ''
        city = ''
        state = ''
        zip = ''
        country = ''
        email = ''
        phone = ''
        if data.client_order_ref:
            raise osv.except_osv('Order already authorized!', 'Warning:Order already authorized!')
        elif not data.auth_transaction_type:
            raise osv.except_osv('Select Transaction Type!', 'Warning:Select Transaction Type!')
        elif not data.auth_cc_expiration_date:
            raise osv.except_osv('Select Expiration Date!', 'Warning:Select Expiration Date!')
        elif not data.auth_cc_number:
            raise osv.except_osv('Enter Credit Card No!', 'Warning:Enter Credit Card No!')
        elif not data.partner_id.id:
            raise osv.except_osv('Select Customer!', 'Warning:Select Customer!')
        elif data.amount_total == 0.00:
            raise osv.except_osv('Please add Product into the Order!', 'Warning:Please add Product into the Order!')
        transaction_type = data.auth_transaction_type
        card_no = data.auth_cc_number
        expiration_date = data.auth_cc_expiration_date
        customer_information = data.customer_information
        if customer_information == True:
            name = data.partner_id.name
            name_split = name.split(' ')
            if name_split:
                name_first = name_split[0]
                if name_split[1]:
                    name_second = name_split[1]
            default_address_id = data.partner_order_id
            if default_address_id:
                street = default_address_id.street
                street2 = default_address_id.street2
                if street and street2:
                    address = street + street2
                elif street:
                    address = street
                elif street2:
                    address = street2
                city = default_address_id.city
                state_id = default_address_id.state_id
                if state_id:
                    state = state_id.name
                country_id = default_address_id.country_id
                if country_id:
                    country = country_id.name
                zip = default_address_id.zip
                phone = default_address_id.phone
                email = default_address_id.email
            shipping_address_id = data.partner_shipping_id
            if shipping_address_id:
                street = shipping_address_id.street
                street2 = shipping_address_id.street2
                if street and street2:
                    address = street + street2
                elif street:
                    address = street
                elif street2:
                    address = street2
                city = shipping_address_id.city
                state_id = shipping_address_id.state_id
                if state_id:
                    state = state_id.name
                country_id = shipping_address_id.country_id
                if country_id:
                    country = country_id.name
                zip = shipping_address_id.zip
        amount_total = data.amount_total
        config_ids = self.pool.get('authorize.net.config').search(cr,uid,[])
        if config_ids:
            login_id = self.pool.get('authorize.net.config').browse(cr,uid,config_ids[0]).api_username
            transaction_key = self.pool.get('authorize.net.config').browse(cr,uid,config_ids[0]).transaction_key
            payment = AIM(login_id, transaction_key, transaction_type,True,False)
            payment.setTransaction(card_no, expiration_date, amount_total)
            if customer_information == True:
                payment.customer_billing_address_fields(name_first, name_second, address,city,state,zip,country,phone,email)
            if shipping_address_id:
                payment.customer_shipping_address_fields(name_first, name_second, address,city,state,zip,country)
            if data.order_information == True:
                order_id = data.name
                order_line = data.order_line
                payment.order_info(order_id,order_line)
            payment.process()
            if payment.isApproved():
                print('Response Code: ', payment.getResponse('ResponseCode'))
                print('Response Text: ', payment.getResponse('ResponseText'))
                print('Response: ', payment.getResultResponseFull())
                print('Transaction ID: ', payment.getResponse('TransactionID'))
                print('CVV Result: ', payment.getResponse('CVVResponse'))
                print('Approval Code: ', payment.getResponse('AuthCode'))
                print('AVS Result: ', payment.getResponse('AVSResponse'))
                cr.execute("UPDATE sale_order SET auth_transaction_id='%s',auth_respmsg='%s',hidden_field='%s',authorization_code='%s' where id=%d"%(payment.getResponse('TransactionID'),payment.getResponse('ResponseText'),'approved',payment.getResponse('AuthCode'),data.id,))
            elif payment.isDeclined():
                print('Your credit card was declined by your bank')
            elif payment.isError():
                raise AuthnetAIMError('An uncaught error occurred')
        else:
            raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')
        return True"""

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals['auth_transaction_id'] = order.auth_transaction_id
        invoice_vals['authorization_code'] = order.authorization_code
        invoice_vals['customer_payment_profile_id'] = order.customer_payment_profile_id
        invoice_vals['auth_respmsg'] = order.auth_respmsg
        invoice_vals['cc_number'] = order.cc_number
        invoice_vals['customer_profile_id'] = order.customer_profile_id
        return invoice_vals
sale_order()

