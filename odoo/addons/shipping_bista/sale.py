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

from osv import fields, osv
import urllib
#import libxml2

import netsvc
logger = netsvc.Logger()

class sale_order(osv.osv):
    _inherit = "sale.order"

    def create(self, cr, uid, vals, context=None):
        #print "Shipping sale create called: ",vals
        partneraddr_obj = self.pool.get('res.partner.address')
        if partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).address_checked == True:
            vals['invalid_addr'] = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).invalid_addr
            id = super(sale_order, self).create(cr, uid, vals, context=context)
            return id

        ### Add shipping code here ####
        shippingups_obj = self.pool.get('shipping.ups')
        shippingups_id = shippingups_obj.search(cr,uid,[('active','=',True)])
        if not shippingups_id:
            vals['invalid_addr'] = True
        else:
            shippingups_id = shippingups_id[0]

            shippingups_ptr = shippingups_obj.browse(cr,uid,shippingups_id)
            access_license_no = shippingups_ptr.access_license_no
            user_id = shippingups_ptr.user_id
            password = shippingups_ptr.password
            shipper_no = shippingups_ptr.shipper_no

            ### Get Address from sale order
            
            street = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).street or ''
            #print "street: ",street

            street2 = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).street2 or ''
            #print "street2: ",street2

            city = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).city or ''
            #print "city: ",city

            state_code = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).state_id.code or ''
            #print "state_code: ",state_code

            country_code = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).country_id.code or ''
            #print "country_code: ",country_code

            postal_code = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).zip or ''
            #print "postal_code: ",postal_code

            data = """<?xml version=\"1.0\"?>
    <AccessRequest xml:lang=\"en-US\">
        <AccessLicenseNumber>%s</AccessLicenseNumber>
        <UserId>%s</UserId>
        <Password>%s</Password>
    </AccessRequest>
    <?xml version="1.0"?>
    <AddressValidationRequest xml:lang="en-US">
       <Request>
          <TransactionReference>
             <CustomerContext>Customer Data</CustomerContext>
             <XpciVersion>1.0001</XpciVersion>
          </TransactionReference>
          <RequestAction>AV</RequestAction>
       </Request>
       <Address>
          <City>%s</City>
          <StateProvinceCode>%s</StateProvinceCode>
          <CountryCode>%s</CountryCode>
          <PostalCode>%s</PostalCode>
       </Address>
    </AddressValidationRequest>
    """ % (access_license_no,user_id,password,city,state_code,country_code,postal_code)

            if shippingups_ptr.test:
                api_url = 'https://wwwcie.ups.com/ups.app/xml/AV'
            else:
                api_url = 'https://onlinetools.ups.com/ups.app/xml/AV'

            try:
                webf = urllib.urlopen(api_url, data)
                response = webf.read()
                #print "ups response: ",response

                sIndex = response.find('<ResponseStatusDescription>')
                eIndex = response.find('</ResponseStatusDescription>')
                status = response[sIndex+27:eIndex]
                #print "status: ",status

                if status != 'Success':
                    vals['invalid_addr'] = True
                    
                else:
                    sIndex = eIndex = i = 0

                    sIndex = response.find('<City>',i)
                    eIndex = response.find('</City>',i)
                    city_resp = response[sIndex+6:eIndex]
                    #print "city_resp: ",city_resp
                    i = eIndex + 7

                    sIndex = response.find('<StateProvinceCode>',i)
                    eIndex = response.find('</StateProvinceCode>',i)
                    state_code_resp = response[sIndex+19:eIndex]
                    #print "state_code_resp: ",state_code_resp
                    i = eIndex + 20

                    sIndex = response.find('<PostalCodeLowEnd>',i)
                    eIndex = response.find('</PostalCodeLowEnd>',i)
                    postal_code_lowend_resp = response[sIndex+18:eIndex]
                    #print "postal_code_lowend_resp: ",postal_code_lowend_resp
                    i = eIndex + 19

                    sIndex = response.find('<PostalCodeHighEnd>',i)
                    eIndex = response.find('</PostalCodeHighEnd>',i)
                    postal_code_highend_resp = response[sIndex+19:eIndex]
                    #print "postal_code_highend_resp: ",postal_code_highend_resp
                    i = eIndex + 20

                    vals['invalid_addr'] = True
                    while (sIndex != -1):
    #                    print "cond1: ",city.upper() == city_resp
    #                    print "cond2: ",state_code.upper() == state_code_resp
    #                    print "cond3: ",(int(postal_code) >= int(postal_code_lowend_resp) and int(postal_code) <= int(postal_code_highend_resp))
                        if city.upper() == city_resp and state_code.upper() == state_code_resp and (int(postal_code) >= int(postal_code_lowend_resp) and int(postal_code) <= int(postal_code_highend_resp)):
                            vals['invalid_addr'] = False
                            break

                        sIndex = response.find('<City>',i)
                        if sIndex == -1:
                            break
                        eIndex = response.find('</City>',i)
                        city_resp = response[sIndex+6:eIndex]
                        #print "city_resp: ",city_resp

                        sIndex = response.find('<StateProvinceCode>',i)
                        eIndex = response.find('</StateProvinceCode>',i)
                        state_code_resp = response[sIndex+19:eIndex]
                        #print "state_code_resp: ",state_code_resp

                        sIndex = response.find('<PostalCodeLowEnd>',i)
                        eIndex = response.find('</PostalCodeLowEnd>',i)
                        postal_code_lowend_resp = response[sIndex+18:eIndex]
                        #print "postal_code_lowend_resp: ",postal_code_lowend_resp

                        sIndex = response.find('<PostalCodeHighEnd>',i)
                        eIndex = response.find('</PostalCodeHighEnd>',i)
                        postal_code_highend_resp = response[sIndex+19:eIndex]
                        #print "postal_code_highend_resp: ",postal_code_highend_resp
                        i = eIndex + 20
            except:
                vals['invalid_addr'] = False
                pass

        print "address invalid status: ",vals['invalid_addr']
        id = super(sale_order, self).create(cr, uid, vals, context=context)
        partneraddr_obj.write(cr,uid,vals['partner_shipping_id'],{'address_checked':True,'invalid_addr':vals['invalid_addr']})
        return id

    def _default_journal(self, cr, uid, context={}):
        accountjournal_obj = self.pool.get('account.journal')
        accountjournal_ids = accountjournal_obj.search(cr,uid,[('name','=','Sales Journal')])
        if accountjournal_ids:
            return accountjournal_ids[0]
        else:
#            raise wizard.except_wizard(_('Error !'), _('Sales journal not defined.'))
            return False

    _columns = {
        #'partner_invoice_id': fields.many2one('res.partner.address', 'Invoice Address', readonly=True, required=False, states={'draft': [('readonly', False)]}, help="Invoice address for current sales order."),
        #'partner_order_id': fields.many2one('res.partner.address', 'Ordering Contact', readonly=True, required=False, states={'draft': [('readonly', False)]}, help="The name and address of the contact who requested the order or quotation."),
#        'ebay_shop_id': fields.many2one('ebay.sale.shop', 'Ebay Shop', reaonly=True, states={'draft': [('readonly', False)]}),
        'invalid_addr': fields.boolean('Invalid Address',readonly=True),
        'client_order_ref': fields.char('Tracking Number', size=64),
        'journal_id': fields.many2one('account.journal', 'Journal',readonly=True),
    }

    _defaults = {
        'journal_id': _default_journal,
    }

sale_order()

class sale_shop(osv.osv):
  _inherit = "sale.shop"
  _columns = {
      'suffix': fields.char('Suffix', size=64),
      'cust_address': fields.many2one('res.partner.address', 'Address'),

      }

sale_shop()
