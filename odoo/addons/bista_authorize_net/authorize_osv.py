# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
###############################################################################

from osv import osv, fields
import time
import netsvc
logger = netsvc.Logger()
from tools.translate import _
import pooler
import httplib, ConfigParser, urlparse
from xml.dom.minidom import parse, parseString
import unicodedata
class Session:
    def Initialize(self, api_login_id, transaction_key,ServerURL):
        self.api_login_id = api_login_id
        self.transaction_key = transaction_key
        self.ServerURL = ServerURL
        urldat = urlparse.urlparse(self.ServerURL)
        self.Serverhost = urldat[1]
        self.Path = urldat[2]
########## Call
class Call:
    RequestData = "<xml />"  # just a stub
    def MakeCall(self):
        conn = httplib.HTTPSConnection(self.Session.Serverhost)
        length  = len(self.RequestData)
        conn.request("POST", self.Session.Path, self.RequestData, self.GenerateHeaders(length))
        response = conn.getresponse()
        data = response.read()
        conn.close()
        responseDOM = parseString(data)
        # check for any <Error> tags and print
        # TODO: Return a real exception and log when this happens
        tag = responseDOM.getElementsByTagName('Error')
        if (tag.count!=0):
            for error in tag:
                print "\n",error.toprettyxml("  ")
        return responseDOM

    def GenerateHeaders(self,length):
        headers = {"Content-Type":"text/xml",
                    "Content-Length":str(length)}
        return headers

class GetProfileIDS:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info
    def get_profile_ids(self,nodelist):
       profile_ids = []
       final_info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'numericString':
                   if cNode.childNodes:
                         profile_ids.append(cNode.childNodes[0].data)
       final_info['numericString'] = profile_ids
       return final_info

    def Get(self):
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
            <getCustomerProfileIdsRequest xmlns='AnetApi/xml/v1/schema/AnetApiSchema.xsd'>
            <merchantAuthentication>
            <name>%s</name>
            <transactionKey>%s</transactionKey>
                </merchantAuthentication>
            </getCustomerProfileIdsRequest>"""% (self.Session.api_login_id,self.Session.transaction_key)
#        print" api.RequestData", api.RequestData
        responseDOM = api.MakeCall()
        response_ids = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        if response_ok.get('resultCode',False) == 'Ok':
            response_ids = self.get_profile_ids(responseDOM.getElementsByTagName('ids'))
        else:
            text = response_ok.get('message',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        print"xml########",responseDOM.toprettyxml()
        responseDOM.unlink()
        return response_ids

class GetCustomerProfile:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info
    def get_profile_info(self,nodelist):
       info = {}
       profile_info = {}
       payment_profile_ids = []
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'email':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'customerProfileId':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'paymentProfiles':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'customerPaymentProfileId':
                                payment_profile_id = cNode.getElementsByTagName('customerPaymentProfileId')[0].childNodes[0].data
                                cc_number = str(cNode.getElementsByTagName('cardNumber')[0].childNodes[0].data)[-4:]
                                profile_info[cc_number] = payment_profile_id
                                payment_profile_ids.append(gcNode.childNodes[0].data)
       if payment_profile_ids:
           info['customerPaymentProfileId'] = payment_profile_ids
       if profile_info:
           info['payment_profile'] = profile_info
       return info
    def Get(self,profile_id):
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
<getCustomerProfileRequest xmlns='AnetApi/xml/v1/schema/AnetApiSchema.xsd'>
<merchantAuthentication>
<name>%s</name>
<transactionKey>%s</transactionKey>
</merchantAuthentication>
<customerProfileId>%s</customerProfileId>
</getCustomerProfileRequest>"""% (self.Session.api_login_id,self.Session.transaction_key,profile_id)
        responseDOM = api.MakeCall()
        profile_info =''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        print"xml*********",responseDOM.toprettyxml()
        if response_ok.get('resultCode',False) == 'Ok':
            profile_info = self.get_profile_info(responseDOM.getElementsByTagName('profile'))
        else:
            text = response_ok.get('message',False)
            if text:
#                 raise osv.except_osv(_('Error!'), _('%s')%(text))
                profile_info = {}
        responseDOM.unlink()
        return profile_info

class CreateCustomerProfileTransaction:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info

    def Get(self,cr,uid,sale_order_id,transaction_type,amount,profile_id,payment_profile_id,approval_code,active_model,cc_number,context):
        lineitem,tax = '',''
        tax_obj = pooler.get_pool(cr.dbname).get('account.tax')
        order_details = ''
        if (active_model=='sale.order') or (active_model=='return.order') or (active_model=='credit.service'):
            obj1 = pooler.get_pool(cr.dbname).get(active_model).browse(cr,uid,sale_order_id)
            desc =obj1.note
            inv_number =obj1.name
            if not desc:
                description = ''
            else:
                description =desc
            order_details = """<order>
                            <invoiceNumber>%s</invoiceNumber>
                            <description>%s</description>
                       </order>"""%(inv_number,description)
            sale_order_line = obj1.order_line
            if obj1.amount_tax > 0.0:
                tax = "<tax><amount>%s</amount></tax>"%(obj1.amount_tax)
            for each_line in sale_order_line:
                taxable = 'false'
                product_id = each_line.product_id
                default_code = product_id.default_code or product_id.name
                product_name = (str(product_id.name)[:31].replace('&','&amp;') if product_id.name else '')
                description = (str(each_line.name)[:255].replace('&','&amp;') if each_line.name else '')
                quantity = (each_line.product_uom_qty if each_line.product_uom_qty else 0.0)
                unit_price  =  (each_line.price_unit if each_line.price_unit else 0.0)
                price = each_line.price_unit * (1 - (each_line.discount or 0.0) / 100.0)
                taxes = tax_obj.compute_all(cr, uid, each_line.tax_id, price, each_line.product_uom_qty, each_line.order_id.partner_invoice_id.id, each_line.product_id, each_line.order_id.partner_id)
                if taxes:
                    subtotal = taxes.get('total')
                    if subtotal > 0.0:
                        if taxes.get('taxes'):
                            tax_amount = taxes.get('taxes')[0].get('amount')
                            if tax_amount > 0.0:
                                taxable = 'true'
                lineitem += """<lineItems>
                                    <itemId>%s</itemId>
                                    <name>%s</name>
                                    <description>%s</description>
                                    <quantity>%s</quantity>
                                    <unitPrice>%s</unitPrice>
                                    <taxable>%s</taxable>
                                </lineItems>"""% (default_code,product_name,description,quantity,unit_price,taxable)


        elif active_model == 'account.invoice':
            obj1 = pooler.get_pool(cr.dbname).get('account.invoice').browse(cr,uid,sale_order_id)
            desc = obj1.comment
            inv_number = (obj1.number if obj1.number else obj1.origin)

            ###code to check whether the invoice has some info either in the Origin
            ### or no

            if not inv_number:
                raise osv.except_osv(_('Error!'), _('Please provide some Info in the Source Document field in the Other Info Tab of the Invoice to register the Transaction with proper ID'))
#            if not desc:
#                description = ''
#            else:
#   my code to check invoice is validated or not means invoice number is exist or not
            ## commenting the below to remove the validation
#            if not obj1.number:
#                raise osv.except_osv(_('Error!'), _('Please validate invoice first'))
#            if not inv_number:
#                raise osv.except_osv(_('Error!'), _('Please validate invoice first'))
#   my code ends
            description =inv_number
            order_details = """<order>
                            <invoiceNumber>%s</invoiceNumber>
                            <description>%s</description>
                       </order>"""%(inv_number[:20],description)
            sale_order_line = obj1.invoice_line
            if obj1.amount_tax > 0.0:
                tax = "<tax><amount>%s</amount></tax>"%(obj1.amount_tax)
            for each_line in sale_order_line:
                ### code to check whether the order line is a negative one or zero
                if each_line.quantity <= 0.0 or each_line.price_unit <=0.0:
                    continue

                ### code ends here
                taxable = 'false'
                product_id = each_line.product_id
                default_code = product_id and product_id.default_code or product_id and product_id.name[:6]
		if default_code:
                    default_code = default_code.replace('&','&amp;')
                product_name = (product_id.name)[:31].replace('&','&amp;') if product_id.name else ''
                product_name = unicode(product_name)
                #product_name = (str(product_id.name)[:31].replace('&','&amp;') if product_id.name else '')
                if product_name:
                    product_name = unicode(product_name)
                    product_name = unicodedata.normalize('NFKD', product_name).encode('ascii','ignore')
                description = ((each_line.name)[:255].replace('&','&amp;') if each_line.name else '')
                if description:
                    description = description.encode('ascii', 'ignore')
                quantity = (each_line.quantity if each_line.quantity else 0.0)
                unit_price  =  (each_line.price_unit if each_line.price_unit else 0.0)
                cr.execute('select tax_id from account_invoice_line_tax where invoice_line_id=%d'%(each_line.id))
                result = filter(None, map(lambda x:x[0], cr.fetchall()))
                if result:
                    taxable = 'true'
                lineitem += """<lineItems>
                                    <itemId>%s</itemId>
                                    <name>%s</name>
                                    <description>%s</description>
                                    <quantity>%s</quantity>
                                    <unitPrice>%s</unitPrice>
                                    <taxable>%s</taxable>
                                </lineItems>"""% (default_code,product_name,description,quantity,unit_price,taxable)
        if transaction_type == 'profileTransPriorAuthCapture':
            approval_code_str = "<transId>%s</transId>"%(approval_code)
            order_details = ''
        elif transaction_type == 'profileTransRefund':
            approval_code_str = "<transId>%s</transId>"%(approval_code)
            cc_number = "<creditCardNumberMasked>%s</creditCardNumberMasked>"%(cc_number)
        elif transaction_type == 'profileTransVoid':
            approval_code_str = "<transId>%s</transId>"%(approval_code)
        else:
            approval_code_str =''
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
    <createCustomerProfileTransactionRequest xmlns='AnetApi/xml/v1/schema/AnetApiSchema.xsd'>
    <merchantAuthentication>
    <name>"""+str(self.Session.api_login_id)+"""</name>
    <transactionKey>"""+str(self.Session.transaction_key)+"""</transactionKey>
    </merchantAuthentication>
    <transaction>
    <""" + transaction_type.encode('utf-8') + """>
    <amount>"""+str(amount)+"""</amount>
    """ + tax.encode('utf-8') + """
    """ + lineitem.encode('utf-8') + """
    <customerProfileId>"""+str(profile_id)+"""</customerProfileId>
    <customerPaymentProfileId>"""+str(payment_profile_id)+"""</customerPaymentProfileId>
    """ + cc_number.encode('utf-8') + """
    """ + order_details.encode('utf-8') + """
    """ + approval_code_str.encode('utf-8') + """
     </""" + transaction_type.encode('utf-8') + """>
    </transaction>
    <extraOptions><![CDATA[x_duplicate_window=300]]></extraOptions>
    </createCustomerProfileTransactionRequest>"""
        responseDOM = api.MakeCall()
        print" responseDOM", responseDOM.toprettyxml()
        print"api.RequestData", api.RequestData
        directResponse = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        if response_ok.get('resultCode',False) == 'Ok':
            directResponse = responseDOM.getElementsByTagName('directResponse')[0].childNodes[0].data
#            if (context.get('recurring_billing',False)) or (context.get('captured_api',False)):
#                response = {'resultCode':response_ok.get('resultCode',False),'response':directResponse}
#            return response
        else:
            text = response_ok.get('message',False)
#            if responseDOM.getElementsByTagName('directResponse'):
#                directResponse = responseDOM.getElementsByTagName('directResponse')[0].childNodes[0].data
            if text:
#                if directResponse:
#                    if (context.get('recurring_billing',False)) or (context.get('captured_api',False)):
#                        response = {'resultCode':response_ok.get('resultCode',False),'response':directResponse,'message':text}
#                        return response
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        responseDOM.unlink()
        return directResponse

class CreateCustomerProfile:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info
    def get_profile_ids(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'numericString':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data

       return info
    def Get(self,sale_order_id,part_id,billing_addr,shippping_addr,email,cc,ext_date,cr,uid,model=False,active_model=False):
        str_billto,address,str_shipto,mode = '','','',''
        if sale_order_id:
            if model:
                customer_id = pooler.get_pool(cr.dbname).get('return.order').browse(cr,uid,sale_order_id).partner_id
                billing_add_id = pooler.get_pool(cr.dbname).get('return.order').browse(cr,uid,sale_order_id).partner_invoice_id
                shipping_add_id = pooler.get_pool(cr.dbname).get('return.order').browse(cr,uid,sale_order_id).partner_shipping_id
            else:
                if active_model=='sale.order':
                    obj_all = pooler.get_pool(cr.dbname).get('sale.order')
                    customer_id = obj_all.browse(cr,uid,sale_order_id).partner_id
                    billing_add_id = obj_all.browse(cr,uid,sale_order_id).partner_invoice_id
                    shipping_add_id = obj_all.browse(cr,uid,sale_order_id).partner_shipping_id
                elif active_model =='account.invoice':
                    obj_all = pooler.get_pool(cr.dbname).get('account.invoice')
                    customer_id = obj_all.browse(cr,uid,sale_order_id).partner_id
                    billing_add_id = obj_all.browse(cr,uid,sale_order_id).address_invoice_id
                    shipping_add_id = obj_all.browse(cr,uid,sale_order_id).address_invoice_id
        else:
            customer_id = pooler.get_pool(cr.dbname).get('res.partner').browse(cr,uid,part_id)
            billing_add_id = billing_addr
            shipping_add_id = shippping_addr
        name = customer_id.name
        ## code to replace any & operator from the name in order to split it out properly
        name = name.replace('&','&amp;')
        ### code ends here
        name= name.split(' ')
        first_name = "<firstName>%s</firstName>"
        second_name = "<lastName>%s</lastName>"
        address_str = "<address>%s</address>"
        city_str = "<city>%s</city>"
        state_str = "<state>%s</state>"
        country_str = "<country>%s</country>"
        zip_str =  "<zip>%s</zip>"
        phone_str = "<phoneNumber>%s</phoneNumber>"
        fax_str = "<faxNumber>%s</faxNumber>"
##############billing address##
        str_billto += "<billTo>"
        str_billto += first_name%(name[0])
        try:
            str_billto += second_name%(name[1])
        except Exception, e:
            str_billto += second_name%('')
#        str_billto += "<company></company>"
        street = billing_add_id.street
        street2 = billing_add_id.street2
        if street and street2:
            address = street + street2
        elif street:
            address = street
        elif street2:
            address = street2
        if address:
            str_billto += address_str%(address)
        city = billing_add_id.city
        if city:
            str_billto += city_str%(city)
        state_id = billing_add_id.state_id
        if state_id:
            state = state_id.code
            if state:
                str_billto += state_str%(state)
        zip = billing_add_id.zip
        if zip:
            str_billto +=zip_str%(zip)
        country_id = billing_add_id.country_id
        if country_id:
            country = country_id.code
            if country:
                str_billto += country_str%(country)
        phone = billing_add_id.phone
        if phone:
            str_billto += phone_str%(phone)
        fax = billing_add_id.fax
        if fax:
            str_billto += fax_str%(fax)
        else:
            str_billto +=fax_str%('')
        str_billto +="</billTo>"
#################shipping address
        str_shipto += "<shipToList>"
        str_shipto += first_name%(name[0])
        try:
            str_shipto += second_name%(name[1])
        except Exception, e:
            str_shipto += second_name%('')
        str_shipto += "<company></company>"
        street = shipping_add_id.street
        street2 = shipping_add_id.street2
        if street and street2:
            address = street + street2
        elif street:
            address = street
        elif street2:
            address = street2
        if address:
            str_shipto += address_str%(address)
        city = shipping_add_id.city
        if city:
            str_shipto += city_str%(city)
        state_id = shipping_add_id.state_id
        if state_id:
            state = state_id.code
            if state:
                str_shipto += state_str%(state)
        zip = shipping_add_id.zip
        if zip:
            str_shipto +=zip_str%(zip)
        country_id = shipping_add_id.country_id
        if country_id:
            country = country_id.code

            if country:
                str_shipto += country_str%(country)
        phone = shipping_add_id.phone
        if phone:
            str_shipto += phone_str%(phone)
        fax = phone = shipping_add_id.fax
        if fax:
            str_shipto += fax_str%(fax)
        str_shipto +="</shipToList>"
        api = Call()
        api.Session = self.Session
        authorize_config_obj = pooler.get_pool(cr.dbname).get('authorize.net.config')
        search_authorize_config = authorize_config_obj.search(cr, uid, [('api_username','=',self.Session.api_login_id),('transaction_key','=',self.Session.transaction_key)])
        if search_authorize_config:
            test_production = authorize_config_obj.browse(cr,uid,search_authorize_config[0]).test_production
            if test_production == 'test':
                mode = "<validationMode>testMode</validationMode>"
            else:
                mode = "<validationMode>liveMode</validationMode>"
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
    <createCustomerProfileRequest xmlns='AnetApi/xml/v1/schema/AnetApiSchema.xsd'>
    <merchantAuthentication>
    <name>%(login_id)s</name>
    <transactionKey>%(trans_key)s</transactionKey>
    </merchantAuthentication>
    <profile>
    <merchantCustomerId>%(part_id)s</merchantCustomerId>
    <email>%(email)s</email>
    <paymentProfiles>
    <customerType>individual</customerType>
     """ + str_billto.encode('utf-8') + """
    <payment>
    <creditCard>
    <cardNumber>%(cc)s</cardNumber>
    <expirationDate>%(ext_date)s</expirationDate>
    </creditCard>
    </payment>
    </paymentProfiles>
    """ + str_shipto.encode('utf-8') + """
    </profile>
    """ + mode.encode('utf-8') + """
    </createCustomerProfileRequest>"""
        api.RequestData = api.RequestData % { 'login_id': self.Session.api_login_id,
                                              'trans_key': self.Session.transaction_key,
                                              'email': email,
                                              'cc': cc,
                                              'ext_date': ext_date,
                                              'part_id' : part_id}
        print"api.RequestData", api.RequestData
        responseDOM = api.MakeCall()
#        print"response",responseDOM.toprettyxml()
        Dictionary ={}
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        if response_ok.get('resultCode',False) == 'Ok':
            cust_profile_id = responseDOM.getElementsByTagName('customerProfileId')[0].childNodes[0].data
            if cust_profile_id:
                Dictionary.update({'customerProfileId': cust_profile_id})
            cust_profile_payment_id = self.get_profile_ids(responseDOM.getElementsByTagName('customerPaymentProfileIdList'))
            if cust_profile_payment_id:
                Dictionary.update({'customerPaymentProfileIdList': cust_profile_payment_id})
        else:
            text = response_ok.get('message',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        print"xml",responseDOM.toprettyxml()
        responseDOM.unlink()
        return Dictionary

class CreateCustomerPaymentProfile:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info

    def Get(self,cr,uid,sale_order_id,part_id,billing_addr,shipping_addr,cust_profile_id,cc,ext_date,active_model=False):
        str_billto,str_shipto,address,mode = '','','',''
        if sale_order_id:
            if active_model=='sale.order':
                obj_all = pooler.get_pool(cr.dbname).get('sale.order')
                customer_id = obj_all.browse(cr,uid,sale_order_id).partner_id
                billing_add_id = obj_all.browse(cr,uid,sale_order_id).partner_invoice_id
                shipping_add_id = obj_all.browse(cr,uid,sale_order_id).partner_shipping_id
            elif active_model =='account.invoice':
                obj_all = pooler.get_pool(cr.dbname).get('account.invoice')
                customer_id = obj_all.browse(cr,uid,sale_order_id).partner_id
                billing_add_id = obj_all.browse(cr,uid,sale_order_id).partner_id
                shipping_add_id = obj_all.browse(cr,uid,sale_order_id).partner_id
            elif active_model == 'account.voucher':
                obj_all = pooler.get_pool(cr.dbname).get('account.voucher')
                customer_id = obj_all.browse(cr,uid,sale_order_id).partner_id
                billing_add_id = obj_all.browse(cr,uid,sale_order_id).partner_id
                shipping_add_id = obj_all.browse(cr,uid,sale_order_id).partner_id

        else:
            customer_id = pooler.get_pool(cr.dbname).get('res.partner').browse(cr,uid,part_id)
            billing_add_id = billing_addr
            shipping_add_id = shipping_addr
        name = customer_id.name
        ## code to replace any & operator from the name in order to split it out properly
        name = name.replace('&','&amp;')
        ### code ends here
        name= name.split(' ')
        first_name = "<firstName>%s</firstName>"
        second_name = "<lastName>%s</lastName>"
        address_str = "<address>%s</address>"
        city_str = "<city>%s</city>"
        state_str = "<state>%s</state>"
        country_str = "<country>%s</country>"
        zip_str =  "<zip>%s</zip>"
        phone_str = "<phoneNumber>%s</phoneNumber>"
        fax_str = "<faxNumber>%s</faxNumber>"
##############billing address##
        str_billto += "<billTo>"
        str_billto += first_name%(name[0])
        try:
            str_billto += second_name%(name[1])
        except Exception, e:
            str_billto += second_name%('')
        str_billto += "<company></company>"
        street = billing_add_id.street
        street2 = billing_add_id.street2
        if street and street2:
            address = street + street2
        elif street:
            address = street
        elif street2:
            address = street2
        if address:
            str_billto += address_str%(address)
        city = billing_add_id.city
        if city:
            str_billto += city_str%(city)
        state_id = billing_add_id.state_id
        if state_id:
            state = state_id.code
            if state:
                str_billto += state_str%(state)
        zip = billing_add_id.zip
        if zip:
            str_billto +=zip_str%(zip)
        country_id = billing_add_id.country_id
        if country_id:
            country = country_id.code
            if country:
                str_billto += country_str%(country)
        phone = billing_add_id.phone
        if phone:
            str_billto += phone_str%(phone)
        fax = billing_add_id.fax
        if fax:
            str_billto += fax_str%(fax)
        else:
            str_billto +=fax_str%('')
        str_billto +="</billTo>"
#################shipping address
        str_shipto += "<shipToList>"
        str_shipto += first_name%(name[0])
        try:
            str_shipto += second_name%(name[1])
        except Exception, e:
            str_shipto += second_name%('')
        str_shipto += "<company></company>"
        street = shipping_add_id.street
        street2 = shipping_add_id.street2
        if street and street2:
            address = street + street2
        elif street:
            address = street
        elif street2:
            address = street2
        if address:
            str_shipto += address_str%(address)
        city = shipping_add_id.city
        if city:
            str_shipto += city_str%(city)
        state_id = shipping_add_id.state_id
        if state_id:
            state = state_id.code
            if state:
                str_shipto += state_str%(state)
        zip = shipping_add_id.zip
        if zip:
            str_shipto +=zip_str%(zip)
        country_id = shipping_add_id.country_id
        if country_id:
            country = country_id.code
            if country:
                str_shipto += country_str%(country)
        phone = shipping_add_id.phone
        if phone:
            str_shipto += phone_str%(phone)
        fax = shipping_add_id.fax
        if fax:
            str_shipto += fax_str%(fax)
        str_shipto +="</shipToList>"
        api = Call()
        api.Session = self.Session
        authorize_config_obj = pooler.get_pool(cr.dbname).get('authorize.net.config')
        search_authorize_config = authorize_config_obj.search(cr, uid, [('api_username','=',self.Session.api_login_id),('transaction_key','=',self.Session.transaction_key)])
        if search_authorize_config:
            test_production = authorize_config_obj.browse(cr,uid,search_authorize_config[0]).test_production
            if test_production == 'test':
                mode = "<validationMode>testMode</validationMode>"
            else:
                mode = "<validationMode>liveMode</validationMode>"
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
    <createCustomerPaymentProfileRequest xmlns='AnetApi/xml/v1/schema/AnetApiSchema.xsd'>
    <merchantAuthentication>
    <name>%(login_id)s</name>
    <transactionKey>%(trans_key)s</transactionKey>
    </merchantAuthentication>
    <customerProfileId>%(cust_profile_id)s</customerProfileId>
    <paymentProfile>
     """ + str_billto.encode('utf-8') + """
    <payment>
    <creditCard>
    <cardNumber>%(cc)s</cardNumber>
    <expirationDate>%(ext_date)s</expirationDate>
    </creditCard>
    </payment>
    </paymentProfile>
    """ + mode.encode('utf-8') + """
    </createCustomerPaymentProfileRequest>"""
        api.RequestData = api.RequestData % { 'login_id': self.Session.api_login_id,
                                              'trans_key': self.Session.transaction_key,
                                              'cust_profile_id': cust_profile_id,
                                              'cc': cc,
                                              'ext_date': ext_date}
        print" api.RequestData", api.RequestData
        responseDOM = api.MakeCall()
        print"response",responseDOM.toprettyxml()
        Dictionary ={}
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        if response_ok.get('resultCode',False) == 'Ok':
            cust_payment_profile_id = responseDOM.getElementsByTagName('customerPaymentProfileId')[0].childNodes[0].data
            if cust_payment_profile_id:
                Dictionary.update({'customerPaymentProfileId': cust_payment_profile_id})
        else:
            text = response_ok.get('message',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        responseDOM.unlink()
        return Dictionary

class ValidateCustomerPaymentProfile:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info

    def Get(self,customer_profile_id,payment_profile_id,shipping_address_id):
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
            <validateCustomerPaymentProfileRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
            <merchantAuthentication>
            <name>%(login_id)s</name>
            <transactionKey>%(trans_key)s</transactionKey>
            </merchantAuthentication>
            <customerProfileId>%(cust_profile_id)s</customerProfileId>
            <customerPaymentProfileId>%(payment_profile_id)s</customerPaymentProfileId>
            <customerShippingAddressId>%(shipping_address_id)s</customerShippingAddressId>
            <validationMode>liveMode</validationMode>
            </validateCustomerPaymentProfileRequest>"""
        api.RequestData = api.RequestData % { 'login_id': self.Session.api_login_id,
                                              'trans_key': self.Session.transaction_key,
                                              'cust_profile_id': customer_profile_id,
                                              'payment_profile_id': payment_profile_id,
                                              'shipping_address_id': shipping_address_id}
        print" api.RequestData", api.RequestData
        responseDOM = api.MakeCall()
        response_ids = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        if response_ok.get('resultCode',False) == 'Ok':
            response_ids = self.get_profile_ids(responseDOM.getElementsByTagName('ids'))
        else:
            text = response_ok.get('message',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        print"xml",responseDOM.toprettyxml()
        responseDOM.unlink()
        return response_ids

class getTransactionDetailsRequest:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info

    def get_transaction_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'transactionStatus':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'authAmount':
                   info[cNode.nodeName] = cNode.childNodes[0].data
       return info

    def Get(self,trans_id):
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
            <getTransactionDetailsRequest xmlns='AnetApi/xml/v1/schema/AnetApiSchema.xsd'>
            <merchantAuthentication>
            <name>%s</name>
            <transactionKey>%s</transactionKey>
                </merchantAuthentication>
                <transId>%s</transId>
            </getTransactionDetailsRequest>"""% (self.Session.api_login_id,self.Session.transaction_key,trans_id)
        print" api.RequestData", api.RequestData
        responseDOM = api.MakeCall()
        response = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        if response_ok.get('resultCode',False) == 'Ok':
            response = self.get_transaction_response(responseDOM.getElementsByTagName('transaction'))
        else:
            text = response_ok.get('message',False)
            if text:
                raise osv.except_osv(_('Error!'), _('%s')%(text))
        print"xml########",responseDOM.toprettyxml()
        responseDOM.unlink()
        return response



class VoidTransaction:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[cNode.nodeName] = gcNode.childNodes[0].data
       return info

    def Get(self,profile_id,payment_profile_id,trans_id):
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
            <createCustomerProfileTransactionRequest xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
            <merchantAuthentication>
            <name>%s</name>
            <transactionKey>%s</transactionKey>
            </merchantAuthentication>
            <transaction>
            <profileTransVoid>
            <customerProfileId>%s</customerProfileId>
            <customerPaymentProfileId>%s</customerPaymentProfileId>
            <transId>%s</transId>
            </profileTransVoid>
            </transaction>
            </createCustomerProfileTransactionRequest>"""% (self.Session.api_login_id,self.Session.transaction_key,profile_id,payment_profile_id,trans_id)
        print" api.RequestData", api.RequestData
        responseDOM = api.MakeCall()
        response = ''
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        if response_ok.get('resultCode',False) == 'Ok':
            response = responseDOM.getElementsByTagName('directResponse')[0].childNodes[0].data
        print"xml########",responseDOM.toprettyxml()
        responseDOM.unlink()
        return response

class CreateCustomerProfileOnly:
    Session = Session()
    def __init__(self, api_login_id, transaction_key, ServerURL):
        self.Session.Initialize(api_login_id, transaction_key, ServerURL)
    def get_response(self,nodelist):
       info = {}
       for node in nodelist:
           for cNode in node.childNodes:
               if cNode.nodeName == 'resultCode':
                   if cNode.childNodes:
                        info[cNode.nodeName] = cNode.childNodes[0].data
               elif cNode.nodeName == 'message':
                   for gcNode in cNode.childNodes:
                        if gcNode.nodeName == 'text':
                            info[gcNode.nodeName] = gcNode.childNodes[0].data
                        elif gcNode.nodeName == 'code':
                            info[gcNode.nodeName] = gcNode.childNodes[0].data
       return info

    def Get(self,cust_db_id,email_id):
        api = Call()
        api.Session = self.Session
        api.RequestData = """<?xml version='1.0' encoding='utf-8'?>
    <createCustomerProfileRequest xmlns='AnetApi/xml/v1/schema/AnetApiSchema.xsd'>
    <merchantAuthentication>
    <name>%s</name>
    <transactionKey>%s</transactionKey>
    </merchantAuthentication>
    <profile>
    <merchantCustomerId>%s</merchantCustomerId>
    <email>%s</email>
    </profile></createCustomerProfileRequest>"""% (self.Session.api_login_id,self.Session.transaction_key,cust_db_id,email_id)
        print" api.RequestData", api.RequestData
        responseDOM = api.MakeCall()
        print "responseDOM",responseDOM.toprettyxml()
        custmer_profile_data = {}
        response_ok = self.get_response(responseDOM.getElementsByTagName('messages'))
        print "response_ok",response_ok
        if response_ok.get('resultCode',False) == 'Ok':
            cust_profile_id = responseDOM.getElementsByTagName('customerProfileId')[0].childNodes[0].data
            custmer_profile_data['cust_profile_id'] = cust_profile_id
            custmer_profile_data['sucess'] = True
        else:
            code = response_ok.get('code',False)
            if code == 'E00039':
                myString = response_ok.get('text',False)
#                val = text[text.find("ID")+1:text.find("already")]
                val = myString[myString.find("ID")+2:myString.find("already")]
                cust_profile_id = val.strip()
                custmer_profile_data['cust_profile_id'] = cust_profile_id
                custmer_profile_data['sucess'] = False
        responseDOM.unlink()
        return custmer_profile_data


class authorize_osv(osv.osv):
    _name = 'authorize_osv'
    def call(self, cr, uid, obj, method, *arguments):
        if method == 'GetProfileIDS':
            gp = GetProfileIDS(obj.api_username, obj.transaction_key,obj.server_url)
            result = gp.Get()
            return result
#            print"result",result
        elif method == 'GetCustomerProfile':
            gcp = GetCustomerProfile(obj.api_username, obj.transaction_key,obj.server_url)
            result = gcp.Get(arguments[0])
            return result
#            print"result",result
        elif method == 'CreateCustomerProfileTransaction':
            gcpt = CreateCustomerProfileTransaction(obj.api_username, obj.transaction_key,obj.server_url)
            result = gcpt.Get(cr,uid,arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5],arguments[6],arguments[7],arguments[8])
            return result
#            print"result",result
        elif method == 'CreateCustomerProfile':
#            print "create customer profile"
            ccp = CreateCustomerProfile(obj.api_username, obj.transaction_key,obj.server_url)
            if len(arguments)>7:
                result = ccp.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5],arguments[6],cr,uid,None,arguments[7])
            else:
                result = ccp.Get(arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5],arguments[6],cr,uid)
#            print"result",result
            return result
        elif method == 'CreateCustomerPaymentProfile':
            ccpp = CreateCustomerPaymentProfile(obj.api_username, obj.transaction_key,obj.server_url)
            print "arguments testtttt",arguments
            result = ccpp.Get(cr,uid,arguments[0],arguments[1],arguments[2],arguments[3],arguments[4],arguments[5],arguments[6],arguments[7])
#            print"result",result
            return result
        elif method == 'ValidateCustomerPaymentProfile':
            vcpp = ValidateCustomerPaymentProfile(obj.api_username, obj.transaction_key,obj.server_url)
            result = vcpp.Get(arguments[0],arguments[1],arguments[2],cr,uid)
#            print"result",result
            return result
        elif method == 'getTransactionDetailsRequest':
            vcpp = getTransactionDetailsRequest(obj.api_username, obj.transaction_key,obj.server_url)
            result = vcpp.Get(arguments[0])
#            print"result",result
            return result
        elif method == 'VoidTransaction':
            vcpp = VoidTransaction(obj.api_username, obj.transaction_key,obj.server_url)
            result = vcpp.Get(arguments[0],arguments[1],arguments[2])
#            print"result",result
            return result
        elif method == 'CreateCustomerProfileOnly':
            vcpp = CreateCustomerProfileOnly(obj.api_username, obj.transaction_key,obj.server_url)
            result = vcpp.Get(arguments[0],arguments[1])
#            print"result",result
            return result
#        elif method == 'getTransactionListRequest':
#            vcpp = getUnsettledTransactionListRequest(obj.api_username, obj.transaction_key,obj.server_url)
#            result = vcpp.Get()
#            print"result",result
#            return result
