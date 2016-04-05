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

import decimal_precision as dp
import urllib2
import urllib
import math
from base64 import b64decode
import binascii
import decimal_precision as dp
import time
import webbrowser

import HTMLParser
h = HTMLParser.HTMLParser()
import httplib

from .xml_dict import dict_to_xml, xml_to_dict

#from fedex.services.rater_service import FedexRateServiceRequest
#from fedex.services.ship_service import FedexProcessShipmentRequest
#from fedex.config import FedexConfig
#import suds
#from suds.client import Client

from tools.translate import _
import netsvc
logger = netsvc.Logger()


def get_partner_details(firm_name, partneradd_lnk, context=None):
        result = {}
        if partneradd_lnk:
            result['name'] = partneradd_lnk.name
            result['firm'] = firm_name or partneradd_lnk.name
            result['add1'] = partneradd_lnk.street or ''
            result['add2'] = partneradd_lnk.street2 or ''
            result['city'] = partneradd_lnk.city or ''
            result['state_code'] = partneradd_lnk.state_id.code or ''
            result['zip5'] = ''
            result['zip4'] = ''
            print "zip: ",partneradd_lnk.zip
            if len(partneradd_lnk.zip.strip()) == 5:
                result['zip5'] = partneradd_lnk.zip
                result['zip4'] = ''
            elif len(partneradd_lnk.zip.strip()) == 4:
                result['zip4'] = partneradd_lnk.zip
                result['zip5'] = ''
            elif str(partneradd_lnk.zip).find('-'):
                zips = str(partneradd_lnk.zip).split('-')
                if len(zips[0]) == 5 and len(zips[1]) == 4:
                    result['zip5'] = zips[0]
                    result['zip4'] = zips[1]
                elif len(zips[0]) == 4 and len(zips[1]) == 5:
                    result['zip4'] = zips[0]
                    result['zip5'] = zips[1]
            else:
                result['zip4'] = result['zip5'] = ''
                
            result['email'] = partneradd_lnk.email or ''
            result['country_code'] = partneradd_lnk.country_id.code or ''
            result['phone'] = partneradd_lnk.phone or ''
        return result

class shipping_response(osv.osv):
    _name = 'shipping.response'

    def generate_tracking_no(self, cr, uid, ids, error=True, context={}):
        print "generate_tracking_no ids: ",ids
#        import subprocess as sp
#        url = 'http://www.python.org'
#        child = sp.Popen("firefox %s" % url, shell=True)

        def get_usps_servicename(service):
            if 'First-Class' in service:
                return 'First Class'
            elif 'Express Mail' in service:
                return 'Express Mail'
            elif 'Priority Mail' in service:
                return 'Priority Mail'
            elif 'Library Mail' in service:
                return 'Library Mail'
            elif 'Parcel Post' in service:
                return 'Parcel Post'
            elif 'Media Mail' in service:
                return 'Media Mail'
            
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'generate_tracking_no called')
        saleorder_obj = self.pool.get('sale.order')
        stockmove_obj = self.pool.get('stock.move')
        stockpicking_obj = self.pool.get('stock.picking')
        shippingresp_lnk = self.browse(cr,uid,ids[0])
        
        move_ids = stockmove_obj.search(cr,uid,[('picking_id','=',shippingresp_lnk.picking_id.id)])

        move_lines = stockmove_obj.browse(cr,uid,move_ids)
        for move_line in move_lines:
            res = self.pool.get('stock.location')._product_reserve(cr, uid, [move_line.location_id.id], move_line.product_id.id, move_line.product_qty, {'uom': move_line.product_uom.id}, lock=True)
            if not res:
                saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'state':'shipping_except'})
                if error:
                    raise osv.except_osv(_('Error'), _('Not enough stock in inventory'))
                return False

        
        #print "shippingresp_lnk.type: ",shippingresp_lnk.type

        ### From Details
#        cr.execute('select user_id,cid from res_company_users_rel where user_id = %s',(uid,))
#        res = cr.fetchall()
#        adr = dict(res)

#        partner_lnk = self.pool.get('res.company').browse(cr,uid,adr[uid]).partner_id
#        address = self.pool.get('res.partner').address_get(cr,uid,[partner_lnk.id])
        #logger.notifyChannel('init', netsvc.LOG_WARNING, 'address %s' % (address,))
#        partneradd_lnk = self.pool.get('res.partner.address').browse(cr,uid,address['default'])
        partneradd_lnk = shippingresp_lnk.picking_id.sale_id.shop_id.cust_address
        if not partneradd_lnk:
            raise osv.except_osv(_('Error'), _('Shop Address not defined!'),)
        result_from = get_partner_details(shippingresp_lnk.picking_id.sale_id.shop_id.name,partneradd_lnk,context)
#        print "result_from: ",result_from
        ### End From

        ### To Details
#        shippingresp_lnk = self.browse(cr,uid,ids[0])
        partner_lnk = shippingresp_lnk.picking_id.partner_id
        address = self.pool.get('res.partner').address_get(cr,uid,[partner_lnk.id])
        partneradd_lnk = self.pool.get('res.partner.address').browse(cr,uid,address['default'])
        result_to = get_partner_details(partner_lnk.name,partneradd_lnk,context)
        #print "result_to: ",result_to
        ### End To

        weight = shippingresp_lnk.weight
        rate = shippingresp_lnk.rate
        
        track_success = False
        tracking_no = False
#        usps_active = 'usps_active' in context.keys() a

        print "usps cond: ", 'usps_active' in context.keys() and context.get('usps_active')
#        print "error" + 1
        if shippingresp_lnk.type.lower() == 'usps' and ('usps_active' in context.keys() and context.get('usps_active')):

            shippingusps_obj = self.pool.get('shipping.usps')
            shippingusps_id = shippingusps_obj.search(cr,uid,[('active','=',True)])
            if not shippingusps_id:
                if error:
                    raise osv.except_osv(_('Error'), _('Default USPS settings not defined'))
                return False
            else:
                shippingusps_id = shippingusps_id[0]
            shippingusps_ptr = shippingusps_obj.browse(cr,uid,shippingusps_id)
            user_id = shippingusps_ptr.user_id

            
            url = "https://testing.shippingapis.com/ShippingAPITest.dll?API=DeliveryConfirmationV3&" if shippingusps_ptr.test else "https://secure.shippingapis.com/ShippingAPI.dll?API=DeliveryConfirmationV3&"
            
            weight = math.modf(weight)
            pounds = int(weight[1])
            ounces = round(weight[0],4) * 16
            final_weight = pounds*16 + ounces
            print "usps weight pounds: ",pounds
            print "usps weight ounces: ",ounces
            
            service_type = get_usps_servicename(shippingresp_lnk.name)
            print "service_type: ",service_type
            
            values = {}
            values['XML'] = '<DeliveryConfirmationV3.0Request USERID="' + user_id + '"><Option>1</Option><ImageParameters></ImageParameters><FromName>' + result_from['name'] + '</FromName><FromFirm>' + result_from['firm'] + '</FromFirm><FromAddress1>' + result_from['add2'] + '</FromAddress1><FromAddress2>' + result_from['add1'] + '</FromAddress2><FromCity>' + result_from['city'] + '</FromCity><FromState>' + result_from['state_code'] + '</FromState><FromZip5>' + result_from['zip5'] + '</FromZip5><FromZip4>' + result_from['zip4'] + '</FromZip4><ToName>' + result_to['name'] + '</ToName><ToFirm>' + result_to['firm'] + '</ToFirm><ToAddress1>' + result_to['add2'] + '</ToAddress1><ToAddress2>' + result_to['add1'] + '</ToAddress2><ToCity>' + result_to['city'] + '</ToCity><ToState>' + result_to['state_code'] + '</ToState><ToZip5>' + result_to['zip5'] + '</ToZip5><ToZip4>' + result_to['zip4'] + '</ToZip4><WeightInOunces>' + str(final_weight) + '</WeightInOunces><ServiceType>' + service_type + '</ServiceType><SeparateReceiptPage>TRUE</SeparateReceiptPage><POZipCode></POZipCode><ImageType>TIF</ImageType><LabelDate></LabelDate><CustomerRefNo></CustomerRefNo><AddressServiceRequested></AddressServiceRequested><SenderName></SenderName><SenderEMail></SenderEMail><RecipientName></RecipientName><RecipientEMail></RecipientEMail></DeliveryConfirmationV3.0Request>'
            url = url + urllib.urlencode(values)
            print "usps url: ",url
            #logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipping url is %s'%(url,))
            #req = urllib2.Request(url)
            #opener = urllib2.build_opener()
            #f = opener.open(req)
            #response = f.read()
            
            try:
                f = urllib2.urlopen(url)
                response = f.read()
                print "usps response: ",response
            except Exception, e:
                #print e
                if error:
                    raise osv.except_osv(_('Error'), _('%s' % (e)))
                return False
            #print "after exception"
            
            if response.find('<Error>') != -1:
                sIndex = response.find('<Description>')
                eIndex = response.find('</Description>')
                if error:
                    raise osv.except_osv(_('Error'), _('%s') % (response[int(sIndex)+13:int(eIndex)],))
                return False

            i = sIndex = eIndex = 0
            sIndex = response.find('<DeliveryConfirmationNumber>',i)
            eIndex = response.find('</DeliveryConfirmationNumber>',i)
            tracking_no = response[int(sIndex) + 36:int(eIndex)]

            sIndex = response.find('<DeliveryConfirmationLabel>',i)
            eIndex = response.find('</DeliveryConfirmationLabel>',i)
            s_label = response[int(sIndex) + 27:int(eIndex)]

            s_label = s_label.replace('\n','')
            s_label = s_label.replace('\r','')
            #shipping_label = b64decode(s_label).encode('UTF-8')
            #logger.notifyChannel('init', netsvc.LOG_WARNING, '!!!!!!shipping_label is %s'%(s_label,))

            """filename = "Label1.tif"
            FILE = open(filename,"w")
            FILE.write(b64decode(s_label))"""

            attachment_pool = self.pool.get('ir.attachment')
            data_attach = {
                'name': 'PackingList.tif',
                'datas': binascii.b2a_base64(str(b64decode(s_label))),
                'description': 'Packing List',
                'res_name': shippingresp_lnk.picking_id.name,
                'res_model': 'stock.picking',
                'res_id': shippingresp_lnk.picking_id.id,
            }
            attach_id = attachment_pool.search(cr,uid,[('res_id','=',shippingresp_lnk.picking_id.id),('res_name','=',shippingresp_lnk.picking_id.name)])
            if not attach_id:
                attach_id = attachment_pool.create(cr, uid, data_attach)
                print "attach_id: ",attach_id
            else:
                attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
                attach_id = attach_id[0]
                print "attach_result: ",attach_result

            
            if tracking_no:
                stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':tracking_no, 'shipping_label':binascii.b2a_base64(str(b64decode(s_label))), 'shipping_rate': rate})
                context['track_success'] = True
        
        elif shippingresp_lnk.type.lower() == 'fedex':
            #print "Inside Fedex Shipping"
            raise osv.except_osv(_('Error'), _('FedEx shipment request under construction'))

            """shippingfedex_obj = self.pool.get('shipping.fedex')
            shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
            if not shippingfedex_id:
                raise osv.except_osv(_('Error'), _('Default Fedex settings not defined'))
            else:
                shippingfedex_id = shippingfedex_id[0]
                
            shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
            account_no = shippingfedex_ptr.account_no
            key = shippingfedex_ptr.key
            password = shippingfedex_ptr.password
            meter_no = shippingfedex_ptr.meter_no
            is_test = shippingfedex_ptr.test
            CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)
       
            # This is the object that will be handling our tracking request.
            # We're using the FedexConfig object from example_config.py in this dir.
            shipment = FedexProcessShipmentRequest(CONFIG_OBJ)

            # This is very generalized, top-level information.
            # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
            shipment.RequestedShipment.DropoffType = 'REGULAR_PICKUP'

            # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
            # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
            shipment.RequestedShipment.ServiceType = 'PRIORITY_OVERNIGHT'

            # What kind of package this will be shipped in.
            # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
            shipment.RequestedShipment.PackagingType = 'FEDEX_PAK'

            # No idea what this is.
            # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
            shipment.RequestedShipment.PackageDetail = 'INDIVIDUAL_PACKAGES'

            # Shipper contact info.
            shipment.RequestedShipment.Shipper.Contact.PersonName = 'Sender Name'
            shipment.RequestedShipment.Shipper.Contact.CompanyName = 'Some Company'
            shipment.RequestedShipment.Shipper.Contact.PhoneNumber = '9012638716'

            # Shipper address.
            shipment.RequestedShipment.Shipper.Address.StreetLines = ['Address Line 1']
            shipment.RequestedShipment.Shipper.Address.City = 'Herndon'
            shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = 'VA'
            shipment.RequestedShipment.Shipper.Address.PostalCode = '20171'
            shipment.RequestedShipment.Shipper.Address.CountryCode = 'US'
            shipment.RequestedShipment.Shipper.Address.Residential = True

            # Recipient contact info.
            shipment.RequestedShipment.Recipient.Contact.PersonName = 'Recipient Name'
            shipment.RequestedShipment.Recipient.Contact.CompanyName = 'Recipient Company'
            shipment.RequestedShipment.Recipient.Contact.PhoneNumber = '9012637906'

            # Recipient address
            shipment.RequestedShipment.Recipient.Address.StreetLines = ['Address Line 1']
            shipment.RequestedShipment.Recipient.Address.City = 'Herndon'
            shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = 'VA'
            shipment.RequestedShipment.Recipient.Address.PostalCode = '20171'
            shipment.RequestedShipment.Recipient.Address.CountryCode = 'US'
            # This is needed to ensure an accurate rate quote with the response.
            shipment.RequestedShipment.Recipient.Address.Residential = True

            # Who pays for the shipment?
            # RECIPIENT, SENDER or THIRD_PARTY
            shipment.RequestedShipment.ShippingChargesPayment.PaymentType = 'SENDER'

            # Specifies the label type to be returned.
            # LABEL_DATA_ONLY or COMMON2D
            shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'

            # Specifies which format the label file will be sent to you in.
            # DPL, EPL2, PDF, PNG, ZPLII
            shipment.RequestedShipment.LabelSpecification.ImageType = 'PNG'

            # To use doctab stocks, you must change ImageType above to one of the
            # label printer formats (ZPLII, EPL2, DPL).
            # See documentation for paper types, there quite a few.
            shipment.RequestedShipment.LabelSpecification.LabelStockType = 'PAPER_4X6'

            # This indicates if the top or bottom of the label comes out of the
            # printer first.
            # BOTTOM_EDGE_OF_TEXT_FIRST or TOP_EDGE_OF_TEXT_FIRST
            shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = 'BOTTOM_EDGE_OF_TEXT_FIRST'

            package1_weight = shipment.create_wsdl_object_of_type('Weight')
            # Weight, in pounds.
            package1_weight.Value = 1.0
            package1_weight.Units = "LB"

            package1 = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
            package1.Weight = package1_weight
            # Un-comment this to see the other variables you may set on a package.
            #print package1

            # This adds the RequestedPackageLineItem WSDL object to the shipment. It
            # increments the package count and total weight of the shipment for you.
            shipment.add_package(package1)

            # If you'd like to see some documentation on the ship service WSDL, un-comment
            # this line. (Spammy).
            #print shipment.client

            # Un-comment this to see your complete, ready-to-send request as it stands
            # before it is actually sent. This is useful for seeing what values you can
            # change.
            #print shipment.RequestedShipment

            # If you want to make sure that all of your entered details are valid, you
            # can call this and parse it just like you would via send_request(). If
            # shipment.response.HighestSeverity == "SUCCESS", your shipment is valid.
            #shipment.send_validation_request()

            # Fires off the request, sets the 'response' attribute on the object.
            shipment.send_request()

            # This will show the reply to your shipment being sent. You can access the
            # attributes through the response attribute on the request object. This is
            # good to un-comment to see the variables returned by the Fedex reply.
            print shipment.response

            # Here is the overall end result of the query.
            print "HighestSeverity:", shipment.response.HighestSeverity
            # Getting the tracking number from the new shipment.
            print "Tracking #:", shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
            # Net shipping costs.
            print "Net Shipping Cost (US$):", shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount

            # Get the label image in ASCII format from the reply. Note the list indices
            # we're using. You'll need to adjust or iterate through these if your shipment
            # has multiple packages.
            ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
            # Convert the ASCII data to binary.
            label_binary_data = binascii.a2b_base64(ascii_label_data)

            """
            #This is an example of how to dump a label to a PNG file.
            """
            # This will be the file we write the label out to.
            png_file = open('example_shipment_label.png', 'wb')
            png_file.write(label_binary_data)
            png_file.close()

            """
            #This is an example of how to print the label to a serial printer. This will not
            #work for all label printers, consult your printer's documentation for more
            #details on what formats it can accept.
            """
            # Pipe the binary directly to the label printer. Works under Linux
            # without requiring PySerial. This WILL NOT work on other platforms.
            #label_printer = open("/dev/ttyS0", "w")
            #label_printer.write(label_binary_data)
            #label_printer.close()

            """
            #This is a potential cross-platform solution using pySerial. This has not been
            #tested in a long time and may or may not work. For Windows, Mac, and other
            #platforms, you may want to go this route.
            """
            #import serial
            #label_printer = serial.Serial(0)
            #print "SELECTED SERIAL PORT: "+ label_printer.portstr
            #label_printer.write(label_binary_data)
            #label_printer.close()

            if shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber:
                track_success = True"""

        elif shippingresp_lnk.type.lower() == 'ups':
            shippingups_obj = self.pool.get('shipping.ups')
            shippingups_id = shippingups_obj.search(cr,uid,[('active','=',True)])
            if not shippingups_id:
                if error:
                    raise osv.except_osv(_('Error'), _('Default UPS settings not defined'))
                return False
            else:
                shippingups_id = shippingups_id[0]

            shippingups_ptr = shippingups_obj.browse(cr,uid,shippingups_id)
            access_license_no = shippingups_ptr.access_license_no
            user_id = shippingups_ptr.user_id
            password = shippingups_ptr.password
            shipper_no = shippingups_ptr.shipper_no
            #print "shipper_no: ",shipper_no

            stockpicking_obj = self.pool.get('stock.picking')
            service_code = shippingresp_lnk.picking_id.service_type_ups
            service_desc = stockpicking_obj.get_ups_servicetype_name(cr,uid,shippingresp_lnk.picking_id.id,shippingresp_lnk.picking_id.service_type_ups)
            packagingtype_code = shippingresp_lnk.picking_id.packaging_type_ups


            data = """
<?xml version="1.0" ?>
<AccessRequest xml:lang='en-US'>
    <AccessLicenseNumber>%s</AccessLicenseNumber>
    <UserId>%s</UserId>
    <Password>%s</Password>
</AccessRequest>
<?xml version="1.0" ?>
<ShipmentConfirmRequest>
    <Request>
         <TransactionReference>
              <CustomerContext>guidlikesubstance</CustomerContext>
              <XpciVersion>1.0001</XpciVersion>
         </TransactionReference>
         <RequestAction>ShipConfirm</RequestAction>
         <RequestOption>nonvalidate</RequestOption>
    </Request>
    <Shipment>
         <Shipper>
              <Name>%s</Name>
              <AttentionName>%s</AttentionName>
              <PhoneNumber>%s</PhoneNumber>
              <ShipperNumber>%s</ShipperNumber>
              <Address>
                   <AddressLine1>%s</AddressLine1>
                   <City>%s</City>
                   <StateProvinceCode>%s</StateProvinceCode>
                   <CountryCode>%s</CountryCode>
                   <PostalCode>%s</PostalCode>
              </Address>
         </Shipper>
         <ShipTo>
              <CompanyName>%s</CompanyName>
              <AttentionName>%s</AttentionName>
              <PhoneNumber>%s</PhoneNumber>
              <Address>
                   <AddressLine1>%s</AddressLine1>
                   <City>%s</City>
                   <StateProvinceCode>%s</StateProvinceCode>
                   <CountryCode>%s</CountryCode>
                   <PostalCode>%s</PostalCode>
                   <ResidentialAddress />
              </Address>
         </ShipTo>
         <PaymentInformation>
                <Prepaid>
                <BillShipper>
                     <CreditCard>
                         <Type>06</Type>
                         <Number>4111111111111111</Number>
                         <ExpirationDate>121999</ExpirationDate>
                     </CreditCard>
                </BillShipper>
            </Prepaid>
         </PaymentInformation>
         <Service>
              <Code>%s</Code>
              <Description>%s</Description>
         </Service>
        <Package>
            <PackagingType>
                <Code>%s</Code>
            </PackagingType>
            <PackageWeight>
                <Weight>%s</Weight>
            </PackageWeight>
        </Package>
    </Shipment>
    <LabelSpecification>
        <LabelPrintMethod>
            <Code>GIF</Code>
        </LabelPrintMethod>
        <LabelImageFormat>
            <Code>GIF</Code>
        </LabelImageFormat>
    </LabelSpecification>
</ShipmentConfirmRequest>""" % (access_license_no,user_id,password,result_from['firm'],result_from['name'],result_from['phone'],shipper_no,result_from['add1'],result_from['city'],result_from['state_code'],result_from['country_code'],result_from['zip5'],result_to['firm'],result_to['name'],result_to['phone'],result_to['add1'],result_to['city'],result_to['state_code'],result_to['country_code'],result_to['zip5'],service_code,service_desc,packagingtype_code,weight)
            #.notifyChannel('init', netsvc.LOG_WARNING, 'shipconfirm request: %s' % (data,))
            #print "shipconfirm request: ",data
            
            api_url = 'https://wwwcie.ups.com/ups.app/xml/ShipConfirm' if shippingups_ptr.test else 'https://onlinetools.ups.com/ups.app/xml/ShipConfirm'
            
            webf = urllib.urlopen(api_url, data)
            response = webf.read()
            #print "shipconfirm response: ",response
            #logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipconfirm response: %s' % (response,))

            sIndex = response.find('<ResponseStatusDescription>')
            eIndex = response.find('</ResponseStatusDescription>')
            status = response[sIndex+27:eIndex]
            #print "status: ",status

            if status != 'Success':
                sIndex = response.find('<ErrorDescription>')
                eIndex = response.find('</ErrorDescription>')
                if sIndex != -1:
                    error_desc = response[sIndex+18:eIndex]
                    if error:
                        raise osv.except_osv(_('Error'), _('%s' % (error_desc,)))
                return False

            sIndex = response.find('<ShipmentDigest>')
            eIndex = response.find('</ShipmentDigest>')
            shipment_digest = response[sIndex+16:eIndex]
            
            data = """
<?xml version="1.0" ?>
<AccessRequest xml:lang='en-US'>
    <AccessLicenseNumber>%s</AccessLicenseNumber>
    <UserId>%s</UserId>
    <Password>%s</Password>
</AccessRequest>
<?xml version="1.0" ?>
<ShipmentAcceptRequest>
    <Request>
        <RequestAction>ShipAccept</RequestAction>
    </Request>
    <ShipmentDigest>%s</ShipmentDigest>
</ShipmentAcceptRequest>""" % (access_license_no,user_id,password,shipment_digest)
            #print "shipaccept request: ",data
            #logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipaccept request: %s' % (data,))
            
            api_url = 'https://wwwcie.ups.com/ups.app/xml/ShipAccept' if shippingups_ptr.test else 'https://onlinetools.ups.com/ups.app/xml/ShipAccept'
            
            try:
                webf = urllib.urlopen(api_url, data)
                response = webf.read()
                print "ups tracking no response: ",response
            except Exception, e:
                if error:
                    raise osv.except_osv(_('Error'), _('%s' % (e)))
                return False
            #print "shipaccept response: ",response
            #logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipaccept response: %s' % (response,))

            sIndex = response.find('<ResponseStatusDescription>')
            eIndex = response.find('</ResponseStatusDescription>')
            status = response[sIndex+27:eIndex]
            #print "status: ",status

            if status != 'Success':
                sIndex = response.find('<ErrorDescription>')
                eIndex = response.find('</ErrorDescription>')
                if sIndex != -1:
                    error_desc = response[sIndex+18:eIndex]
                    if error:
                        raise osv.except_osv(_('Error'), _('%s' % (error_desc,)))
                return False

            sIndex = response.find('<TrackingNumber>')
            eIndex = response.find('</TrackingNumber>')
            tracking_no = response[sIndex+16:eIndex]
            context['track_success'] = True
            
            sIndex = response.find('<HTMLImage>')
            eIndex = response.find('</HTMLImage>')
            html_image = response[sIndex+11:eIndex]
            
            sIndex = response.find('<GraphicImage>')
            eIndex = response.find('</GraphicImage>')
            graphic_image = response[sIndex+14:eIndex]

#            filename = "Label.gif"
#            FILE = open(filename,"r")
#            test_data = FILE.read()
            
#            filename = "Label.gif"
#            FILE = open(filename,"w")
#            FILE.write(binascii.b2a_base64(str(b64decode(graphic_image))))

            attachment_pool = self.pool.get('ir.attachment')
            data_attach = {
                'name': 'PackingList.gif',
                'datas': binascii.b2a_base64(str(b64decode(graphic_image))),
                'description': 'Packing List',
                'res_name': shippingresp_lnk.picking_id.name,
                'res_model': 'stock.picking',
                'res_id': shippingresp_lnk.picking_id.id,
            }
            attach_id = attachment_pool.search(cr,uid,[('res_id','=',shippingresp_lnk.picking_id.id),('res_name','=',shippingresp_lnk.picking_id.name)])
            if not attach_id:
                attach_id = attachment_pool.create(cr, uid, data_attach)
                print "attach_id: ",attach_id
            else:
                attach_id = attach_id[0]
                attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
                print "attach_result: ",attach_result

            stockpickingwrite_result = stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':tracking_no, 'shipping_label':binascii.b2a_base64(str(b64decode(graphic_image))), 'shipping_rate': rate})
#            print "stockpickingwrite_result: ",stockpickingwrite_result

            """datas = {
             'ids': [shippingresp_lnk.picking_id.id],
             'model': 'stock.picking',
             }"""
        
        ### Check Availability; Confirm; Validate : Automate Process Now step
        if context.get('track_success',False):
            ### Assign Carrier to Delivery carrier if user has not chosen
#            carrier_lnk = stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id).carrier_id
#            if not carrier_lnk:
            type_fieldname = ''
            if shippingresp_lnk.type.lower() == 'usps':
                type_fieldname = 'is_usps'
            elif shippingresp_lnk.type.lower() == 'ups':
                type_fieldname = 'is_ups'
            elif shippingresp_lnk.type.lower() == 'fedex':
                type_fieldname = 'is_fedex'
            carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',shippingresp_lnk.name),(type_fieldname,'=',True)])
            if not carrier_ids:
                if error:
                    raise osv.except_osv(_('Error'), _('Shipping service output settings not defined'))
                return False
#            print "selected carrier ids: ",carrier_ids
            self.pool.get('stock.picking').write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_id':carrier_ids[0]})
            
            ### Check Availabiity
            actionassign_result = stockpicking_obj.action_assign_new(cr,uid,[shippingresp_lnk.picking_id.id])
            print "actionassign_result: ",actionassign_result
            if not actionassign_result:
                ### Force Availability
#                forceassign_result = stockpicking_obj.force_assign(cr,uid,[shippingresp_lnk.picking_id.id])
                saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'state':'shipping_except'})
                return False
            
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            partial_datas = {
                'delivery_date' : current_time
            }

            for move in move_lines:
                if move.state in ('done', 'cancel'):
                    continue

                partial_datas['move%s' % (move.id)] = {
                    'product_id' : move.product_id.id,
                    'product_qty' : move.product_qty,
                    'product_uom' :move.product_uom.id,
                    'prodlot_id' : move.prodlot_id.id,
                }

            #print "partial_datas: ",partial_datas
            res = stockpicking_obj.do_partial(cr,uid,[shippingresp_lnk.picking_id.id],partial_datas,context)

            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_write(uid, 'stock.picking', shippingresp_lnk.picking_id.id, cr)
            wf_service.trg_write(uid, 'sale.order', shippingresp_lnk.picking_id.sale_id.id, cr)
            saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'client_order_ref':tracking_no, 'carrier_id':carrier_ids[0]})

            ### Write this shipping respnse is selected
            self.write(cr,uid,ids[0],{'selected':True})
            
            datas = {'ids': [shippingresp_lnk.picking_id.id],
                     'model': 'stock.picking'}

            return {'type': 'ir.actions.report.xml',
                    'report_name': 'webkitstock.picking.label',
                    'datas': datas}
#            return True
        else:
            return False 
    _order = 'sr_no'

    _columns = {
        'name': fields.char('Service Type', size=100, readonly=True),
        'type': fields.char('Shipping Type', size=64, readonly=True),
        'rate': fields.char('Rate', size=64, readonly=True),
        #'tracking_no' : fields.char('Tracking No.', size=100),
        'weight' : fields.float('Weight'),
        'cust_default' : fields.boolean('Customer Default'),
        'sys_default' : fields.boolean('System Default'),
        'sr_no' : fields.integer('Sr. No'),
        'selected' : fields.boolean('Selected'),
        'picking_id' : fields.many2one('stock.picking','Picking')
    }
    _defaults = {
        'sr_no': 9,
        'selected': False
    }
shipping_response()

class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"

    def action_assign_new(self, cr, uid, ids, *args):
        """ Changes state of picking to available if all moves are confirmed.
        @return: True
        """
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
            print "move_ids in action_assign_new: ",move_ids
            if not move_ids:
                return False
            self.pool.get('stock.move').action_assign(cr, uid, move_ids)
        return True

    def get_ups_servicetype_name(self, cr, uid, ids, code, mag_code=False):
        if code:
            if code == '01':
                return 'Next Day Air'
            elif code == '02':
                return 'Second Day Air'
            elif code == '03':
                return 'Ground'
            elif code == '07':
                return 'Worldwide Express'
            elif code == '08':
                return 'Worldwide Expedited'
            elif code == '11':
                return 'Standard'
            elif code == '12':
                return 'Three-Day Select'
            elif code == '13':
                return 'Next Day Air Saver'
            elif code == '14':
                return 'Next Day Air Early AM'
            elif code == '54':
                return 'Worldwide Express Plus'
            elif code == '59':
                return 'Second Day Air AM'
            elif code == '65':
                return 'Saver'
            else:
                return False
        elif mag_code:
            if mag_code == 'ups_3DS':
                return 'Three-Day Select'
            elif mag_code == 'ups_GND':
                return 'Ground'
            elif mag_code == 'ups_2DA':
                return 'Second Day Air'
            elif mag_code == 'ups_1DP':
                return 'Next Day Air Saver'
            elif mag_code == 'ups_1DA':
                return 'Next Day Air'
            elif mag_code == 'ups_1DM':
                return 'Next Day Air Early AM'
        else:
            return False

    def generate_ups_shipping(self, cr, uid, ids, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default=False,cust_default=False,error=True,context=None):
        if 'ups_active' in context.keys() and context['ups_active'] == False:
            return True
        shippingups_obj = self.pool.get('shipping.ups')
        shippingups_id = shippingups_obj.search(cr,uid,[('active','=',True)])
        if not shippingups_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites
            if error:
                raise osv.except_osv(_('Error'), _('Default UPS settings not defined'))
            else:
                return False
        else:
            shippingups_id = shippingups_id[0]

        shippingups_ptr = shippingups_obj.browse(cr,uid,shippingups_id)
        access_license_no = shippingups_ptr.access_license_no
        user_id = shippingups_ptr.user_id
        password = shippingups_ptr.password
        shipper_no = shippingups_ptr.shipper_no

#        stockpicking_lnk = self.browse(cr,uid,ids[0])

        data = """<?xml version=\"1.0\"?>
        <AccessRequest xml:lang=\"en-US\">
            <AccessLicenseNumber>%s</AccessLicenseNumber>
            <UserId>%s</UserId>
            <Password>%s</Password>
        </AccessRequest>
        <?xml version=\"1.0\"?>
        <RatingServiceSelectionRequest xml:lang=\"en-US\">
            <Request>
                <TransactionReference>
                    <CustomerContext>Rating and Service</CustomerContext>
                    <XpciVersion>1.0001</XpciVersion>
                </TransactionReference>
                <RequestAction>Rate</RequestAction>
                <RequestOption>Rate</RequestOption>
            </Request>
        <PickupType>
            <Code>%s</Code>
        </PickupType>
        <Shipment>
            <Shipper>
                <Address>
                    <PostalCode>%s</PostalCode>
                    <CountryCode>%s</CountryCode>
                </Address>
            <ShipperNumber>%s</ShipperNumber>
            </Shipper>
            <ShipTo>
                <Address>
                    <PostalCode>%s</PostalCode>
                    <CountryCode>%s</CountryCode>
                <ResidentialAddressIndicator/>
                </Address>
            </ShipTo>
            <ShipFrom>
                <Address>
                    <PostalCode>%s</PostalCode>
                    <CountryCode>%s</CountryCode>
                </Address>
            </ShipFrom>
            <Service>
                <Code>%s</Code>
            </Service>
            <Package>
                <PackagingType>
                    <Code>%s</Code>
                </PackagingType>
                <PackageWeight>
                    <UnitOfMeasurement>
                        <Code>LBS</Code>
                    </UnitOfMeasurement>
                    <Weight>%s</Weight>
                </PackageWeight>
            </Package>
        </Shipment>
        </RatingServiceSelectionRequest>""" % (access_license_no,user_id,password,pickup_type_ups,shipper_postal_code,shipper_country_code,shipper_no,customer_postal_code,customer_country_code,shipper_postal_code,shipper_country_code,service_type_ups,packaging_type_ups,weight)

        
        api_url = 'https://wwwcie.ups.com/ups.app/xml/Rate' if shippingups_ptr.test else 'https://onlinetools.ups.com/ups.app/xml/Rate'
        
        webf = urllib.urlopen(api_url, data)
        response = webf.read()
        #print "ups response: ",response

        if response.find('<Error>') != -1:
            sIndex = response.find('<ErrorDescription>')
            eIndex = response.find('</ErrorDescription>')
            if error:
                raise osv.except_osv(_('Error'), _('%s') % (response[int(sIndex)+18:int(eIndex)],))
            else:
                return False

        i = sIndex = eIndex = 0
        sTCIndex = response.find('<TotalCharges>',i)
        eTCIndex = response.find('</TotalCharges>',i)

        sIndex = response.find('<MonetaryValue>',sTCIndex)
        eIndex = response.find('</MonetaryValue>',sTCIndex)
        rate = response[sIndex+15:eIndex]
        #print "rate: ",rate

        sr_no = 9
        sys_default_value = False
        cust_default_value = False

        if cust_default and cust_default.split('/')[0] == 'UPS':
            cust_default_value = True
            sr_no = 1

        elif sys_default and sys_default.split('/')[0] == 'UPS':
            sys_default_value = True
            sr_no = 2

        ups_res_vals = {
            'name' : self.get_ups_servicetype_name(cr,uid,ids,service_type_ups),
            'type' : 'UPS',
            'rate' : rate,
            'picking_id' : ids[0], #Change the ids[0] when switch to create
            'weight' : weight,
            'sys_default' : sys_default_value,
            'cust_default' : cust_default_value,
            'sr_no' : sr_no
        }
        ups_res_id = self.pool.get('shipping.response').create(cr,uid,ups_res_vals)
        if ups_res_id:
            return True
        else:
            return False


    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, sys_default=False,cust_default=False, error=True, context=None):
        if 'fedex_active' in context.keys() and context['fedex_active'] == False:
            return True
        shippingfedex_obj = self.pool.get('shipping.fedex')
        shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
        if not shippingfedex_id:
            if error:
                raise osv.except_osv(_('Error'), _('Default FedEx settings not defined'))
            else:
                return False
        else:
            shippingfedex_id = shippingfedex_id[0]

        shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
        account_no = shippingfedex_ptr.account_no
        key = shippingfedex_ptr.key
        password = shippingfedex_ptr.password
        meter_no = shippingfedex_ptr.meter_no
        is_test = shippingfedex_ptr.test
        CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)
        rate_request = FedexRateServiceRequest(CONFIG_OBJ)

        stockpicking_lnk = self.browse(cr,uid,ids[0])

        #print "dropoff_type_fedex: ",dropoff_type_fedex
        #print "service_type_fedex: ",service_type_fedex
        #print "packaging_type_fedex: ",packaging_type_fedex
        # This is very generalized, top-level information.
        # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
        rate_request.RequestedShipment.DropoffType = dropoff_type_fedex

        # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
        # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
        rate_request.RequestedShipment.ServiceType = service_type_fedex

        # What kind of package this will be shipped in.
        # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
        rate_request.RequestedShipment.PackagingType = packaging_type_fedex

        # No idea what this is.
        # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
        rate_request.RequestedShipment.PackageDetail = package_detail_fedex

        rate_request.RequestedShipment.Shipper.Address.PostalCode = shipper_postal_code
        rate_request.RequestedShipment.Shipper.Address.CountryCode = shipper_country_code
        rate_request.RequestedShipment.Shipper.Address.Residential = False

        rate_request.RequestedShipment.Recipient.Address.PostalCode = customer_postal_code
        rate_request.RequestedShipment.Recipient.Address.CountryCode = customer_country_code
        # This is needed to ensure an accurate rate quote with the response.
        #rate_request.RequestedShipment.Recipient.Address.Residential = True
        #include estimated duties and taxes in rate quote, can be ALL or NONE
        rate_request.RequestedShipment.EdtRequestType = 'NONE'

        # Who pays for the rate_request?
        # RECIPIENT, SENDER or THIRD_PARTY
        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex

        package1_weight = rate_request.create_wsdl_object_of_type('Weight')
        package1_weight.Value = weight
        package1_weight.Units = "LB"

        package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
        package1.Weight = package1_weight
        #can be other values this is probably the most common
        package1.PhysicalPackaging = physical_packaging_fedex
        # Un-comment this to see the other variables you may set on a package.
        #print package1

        # This adds the RequestedPackageLineItem WSDL object to the rate_request. It
        # increments the package count and total weight of the rate_request for you.
        rate_request.add_package(package1)

        # If you'd like to see some documentation on the ship service WSDL, un-comment
        # this line. (Spammy).
        #print rate_request.client

        # Un-comment this to see your complete, ready-to-send request as it stands
        # before it is actually sent. This is useful for seeing what values you can
        # change.
        #print rate_request.RequestedShipment

        # Fires off the request, sets the 'response' attribute on the object.
        try:
            rate_request.send_request()

        except Exception, e:
            if error:
                raise osv.except_osv(_('Error'), _('%s' % (e)))
            return False

        # This will show the reply to your rate_request being sent. You can access the
        # attributes through the response attribute on the request object. This is
        # good to un-comment to see the variables returned by the FedEx reply.
        #print 'response: ', rate_request.response

        # Here is the overall end result of the query.
        #print "HighestSeverity:", rate_request.response.HighestSeverity

        for detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
            for surcharge in detail.ShipmentRateDetail.Surcharges:
                if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
                    print "ODA rate_request charge %s" % surcharge.Amount.Amount

        for rate_detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
            print "Net FedEx Charge %s %s" % (rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount)

        sr_no = 9
        sys_default_value = False
        cust_default_value = False
        if sys_default:
            sys_default_vals = sys_default.split('/')
            #print "sys_default_vals: ",sys_default_vals
            if sys_default_vals[0] == 'FedEx':
                sys_default_value = True
                sr_no = 2

        if cust_default:
            cust_default_vals = cust_default.split('/')
            #print "sys_default_vals: ",sys_default_vals
            if cust_default_vals[0] == 'FedEx':
                cust_default_value = True
                sr_no = 1

        fedex_res_vals = {
            'name' : service_type_fedex,
            'type' : 'FedEx',
            'rate' : rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount,
            'picking_id' : ids[0], #Change the ids[0] when switch to create
            'weight' : weight,
            'sys_default' : sys_default_value,
            'cust_default' : cust_default_value,
            'sr_no' : sr_no
        }
        fedex_res_id = self.pool.get('shipping.response').create(cr,uid,fedex_res_vals)
        #print "fedex_res_id: ",fedex_res_id
        if fedex_res_id:
            return True
        else:
            return False


    def generate_usps_shipping(self, cr, uid, ids,service_type_usps,first_class_mail_type_usps,container,size_usps,weight,zip_origination,zip_destination,sys_default=False,cust_default=False,error=True,context=None):
        #service_type = {}
        ### Shift the code to def create
        ### Check if it is in delivery orders - Done
        ### Deleting all that exist if user is generating shipping again - Done
        ### Defaults values of types
        ### New link to do Generate Shipping

        
        #logger.notifyChannel('init', netsvc.LOG_WARNING, 'service_type_usps is %s'%(urllib.urlencode(service_type),))
        if 'usps_active' in context.keys() and context['usps_active'] == False:
            return True

        stockpicking_lnk = self.browse(cr,uid,ids[0])
        usps_res_id = False
        
        shippingusps_obj = self.pool.get('shipping.usps')
        shippingusps_id = shippingusps_obj.search(cr,uid,[('active','=',True)])
        if not shippingusps_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites
            if error:
                raise osv.except_osv(_('Error'), _('Active USPS settings not defined'))
            else:
                return False
        else:
            shippingusps_id = shippingusps_id[0]
        shippingusps_ptr = shippingusps_obj.browse(cr,uid,shippingusps_id)
        user_id = shippingusps_ptr.user_id

        url = "http://testing.shippingapis.com/ShippingAPITest.dll?API=RateV4&" if shippingusps_ptr.test else "http://production.shippingapis.com/ShippingAPI.dll?API=RateV4&"

        ## <Service></Service>
        service_type = '<Service>' + service_type_usps + '</Service>'

        if service_type_usps == 'First Class':
            service_type += '<FirstClassMailType>' + first_class_mail_type_usps + '</FirstClassMailType>'
        #logger.notifyChannel('init', netsvc.LOG_WARNING, 'service_type is %s'%(service_type,))
        ### <Container />
        container = container and '<Container>' + container + '</Container>' or '<Container/>'
        #logger.notifyChannel('init', netsvc.LOG_WARNING, 'container is %s'%(container,))
        ### <Size />
        size = '<Size>' + size_usps + '</Size>'
        if size_usps == 'LARGE':
            size += '<Width>' + str(stockpicking_lnk.width_usps) + '</Width>'
            size += '<Length>' + str(stockpicking_lnk.length_usps) + '</Length>'
            size += '<Height>' + str(stockpicking_lnk.height_usps) + '</Height>'

            if stockpicking_lnk.container_usps == 'Non-Rectangular' or stockpicking_lnk.container_usps == 'Variable' or stockpicking_lnk.container_usps == '':
                size += '<Girth>' + str(stockpicking_lnk.height_usps) + '</Girth>'
        #logger.notifyChannel('init', netsvc.LOG_WARNING, 'size is %s'%(size,))

        weight_org = weight
        weight = math.modf(weight)
        pounds = int(weight[1])
        ounces = round(weight[0],2) * 16

        #logger.notifyChannel('init', netsvc.LOG_WARNING, 'pounds is %s'%(pounds,))
        #logger.notifyChannel('init', netsvc.LOG_WARNING, 'ounces is %s'%(ounces,))

        values = {}
        values['XML'] = '<RateV4Request USERID="' + user_id + '"><Revision/><Package ID="1ST">' + service_type + '<ZipOrigination>' + zip_origination + '</ZipOrigination><ZipDestination>' + zip_destination + '</ZipDestination><Pounds>' + str(pounds) + '</Pounds><Ounces>' + str(ounces) + '</Ounces>' + container + size + '<Machinable>true</Machinable></Package></RateV4Request>'
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'values is %s'%(urllib.urlencode(values),))
        url = url + urllib.urlencode(values)
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipping url is %s'%(url,))
        try:
            f = urllib2.urlopen(url)
            response = f.read()
            logger.notifyChannel('init', netsvc.LOG_WARNING, '!!!!!!shipping response is %s'%(response,))
        except Exception, e:
            raise osv.except_osv(_('Error'), _('%s' % (e)))
            return False


        if response.find('<Error>') != -1:
            sIndex = response.find('<Description>')
            eIndex = response.find('</Description>')
            if error:
                raise osv.except_osv(_('Error'), _('%s') % (response[int(sIndex)+13:int(eIndex)],))
            else:
                return False

        

        i = sIndex = eIndex = 0
        sIndex = response.find('<MailService>',i)
        eIndex = response.find('</MailService>',i)
        rsIndex = response.find('<Rate>',i)
        reIndex = response.find('</Rate>',i)
        while (sIndex != -1):
            i = reIndex + 7
            mail_service = response[int(sIndex) + 13:int(eIndex)]
            tm = chr(174)
            mail_service = mail_service.replace("&amp;lt;sup&amp;gt;&amp;amp;reg;&amp;lt;/sup&amp;gt;",str(tm))
            rate = response[int(rsIndex)+6:int(reIndex)]
            sIndex = response.find('<MailService>',i)
            eIndex = response.find('</MailService>',i)
            rsIndex = response.find('<Rate>',i)
            reIndex = response.find('</Rate>',i)
            #logger.notifyChannel('init', netsvc.LOG_WARNING, 'sIndex is %s'%(sIndex,))
            #logger.notifyChannel('init', netsvc.LOG_WARNING, 'eIndex is %s'%(eIndex,))
            #logger.notifyChannel('init', netsvc.LOG_WARNING, '!!!!!!shipping mail_service is %s'%(mail_service,))
            #logger.notifyChannel('init', netsvc.LOG_WARNING, '!!!!!!shipping rate is %s'%(h.unescape(rate),))

            
            """if sys_default:
                if mail_service.lower().find(def_service_type.lower()) != -1:
                    #print "Testng condition: ",mail_service.lower().find(def_service_type.lower())
                    if mail_service.lower().find(def_firstclass_type.lower()) != -1:
                        if def_container:
                            if mail_service.lower().find(def_container.lower()) != -1:
                                sys_default_value = True
                                sr_no = 1
                        else:
                            sys_default_value = True
                            sr_no = 1"""

            sys_default_value = False
            cust_default_value = False
            sr_no = 9
            print "sys_default: ",sys_default

            if cust_default and cust_default.split('/')[0] == 'USPS':
                cust_default_value = True
                sr_no = 1
                    
            elif sys_default and sys_default.split('/')[0] == 'USPS':
                sys_default_value = True
                sr_no = 2
                    
            usps_res_vals = {
                'name' : mail_service,
                'type' : 'USPS',
                'rate' : rate,
                'picking_id' : ids[0], #Change the ids[0] when switch to create
                'weight' : weight_org,
                'sys_default' : sys_default_value,
                'cust_default' : cust_default_value,
                'sr_no' : sr_no,
            }
            usps_res_id = self.pool.get('shipping.response').create(cr,uid,usps_res_vals)
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'usps_res_id is %s'%(usps_res_id,))
        if usps_res_id:
            return True
        else:
            return False

    ## This function is called when the button is clicked
    def generate_shipping(self, cr, uid, ids, context=None):
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'inside generate_shipping %s'%(ids,))
        for id in ids:
            try:
                stockpicking_lnk = self.browse(cr,uid,id)
                shipping_type = stockpicking_lnk.shipping_type

                weight = 0.0
                if not stockpicking_lnk.weight_package:
                    weight = stockpicking_lnk.weight_net
                else:
                    weight = stockpicking_lnk.weight_package

                if not weight:
                    raise Exception('Package Weight Invalid!')
                #print "weight: ",weight
                ### Shipper
                cr.execute('select user_id,cid from res_company_users_rel where user_id = %s',(uid,))
                res = cr.fetchall()
                adr = dict(res)

    #            partner_lnk = self.pool.get('res.company').browse(cr,uid,adr[uid]).partner_id
    #            address = self.pool.get('res.partner').address_get(cr,uid,[partner_lnk.id])
                #logger.notifyChannel('init', netsvc.LOG_WARNING, 'address %s' % (address,))
    #            partneradd_lnk = self.pool.get('res.partner.address').browse(cr,uid,address['default'])
                partneradd_lnk = stockpicking_lnk.sale_id.shop_id.cust_address
                if not partneradd_lnk:
                    raise Exception('Shop Address not defined!')
                result = get_partner_details(stockpicking_lnk.sale_id.shop_id.name,partneradd_lnk,context)
                print "result: ",result
                shipper_postal_code = result['zip5']
                shipper_country_code = result['country_code']
                #print "shipper_postal_code: ",shipper_postal_code
                #print "shipper_country_code: ",shipper_country_code

                ### Recipient
                address = self.pool.get('res.partner').address_get(cr,uid,[stockpicking_lnk.partner_id.id])
                #logger.notifyChannel('init', netsvc.LOG_WARNING, 'address %s' % (address,))
                partneradd_lnk = self.pool.get('res.partner.address').browse(cr,uid,address['default'])
                result = get_partner_details(stockpicking_lnk.partner_id.name,partneradd_lnk,context)
                customer_postal_code = result['zip5']
                customer_country_code = result['country_code']

                # Deleting previous quotes
                shipping_res_obj = self.pool.get('shipping.response')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('picking_id','=',ids[0])])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)

                sys_default=False
                cust_default=False

                error_required = True

                if shipping_type == 'USPS' or shipping_type == 'All':
                    service_type_usps = stockpicking_lnk.service_type_usps
                    first_class_mail_type_usps = stockpicking_lnk.first_class_mail_type_usps or ''
                    container_usps = stockpicking_lnk.container_usps or ''
                    size_usps = stockpicking_lnk.size_usps
                    shipping_res = self.generate_usps_shipping(cr,uid,[id],service_type_usps,first_class_mail_type_usps,container_usps,size_usps,weight,shipper_postal_code,customer_postal_code,sys_default,cust_default,error_required,context)

                if shipping_type == 'UPS' or shipping_type == 'All':
                    pickup_type_ups = stockpicking_lnk.pickup_type_ups
                    service_type_ups = stockpicking_lnk.service_type_ups
                    packaging_type_ups = stockpicking_lnk.packaging_type_ups
                    shipping_res = self.generate_ups_shipping(cr,uid,[id],pickup_type_ups,service_type_ups,packaging_type_ups,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context)

    #            if shipping_type == 'Fedex' or shipping_type == 'All':
    #                dropoff_type_fedex = stockpicking_lnk.dropoff_type_fedex
    #                service_type_fedex = stockpicking_lnk.service_type_fedex
    #                packaging_type_fedex = stockpicking_lnk.packaging_type_fedex
    #                package_detail_fedex = stockpicking_lnk.package_detail_fedex
    #                payment_type_fedex = stockpicking_lnk.payment_type_fedex
    #                physical_packaging_fedex = stockpicking_lnk.physical_packaging_fedex
    #                shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context)
            except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
            return True
#

    def create(self, cr, uid, vals, context=None):
        #print "create vals: ",vals
        #create vals:  {'origin': u'SO009', 'note': False, 'state': 'auto', 'name': u'OUT/00007', 'sale_id': 9, 'move_type': u'direct', 'type': 'out', 'address_id': 3, 'invoice_state': 'none', 'company_id': 1}
       
        if vals.get('type',False) and vals['type'] == 'out':
            try:
                vals['shipping_type'] = 'All'
                cust_default = False
                saleorder_lnk = self.pool.get('sale.order') .browse(cr,uid,vals['sale_id'])
                carrier_id = saleorder_lnk.carrier_id and saleorder_lnk.carrier_id.id or False

                service_type_usps = 'All'
                first_class_mail_type_usps = False
                container_usps = False
                size_usps = 'REGULAR'
                vals['service_type_usps'] = service_type_usps
                vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                vals['container_usps'] = container_usps
                vals['size_usps'] = size_usps

                dropoff_type_fedex = 'REGULAR_PICKUP'
                service_type_fedex = 'FEDEX_GROUND'
                packaging_type_fedex = 'YOUR_PACKAGING'
                package_detail_fedex = 'INDIVIDUAL_PACKAGES'
                payment_type_fedex = 'SENDER'
                physical_packaging_fedex = 'BOX'
                vals['dropoff_type_fedex'] = dropoff_type_fedex
                vals['service_type_fedex'] = service_type_fedex
                vals['packaging_type_fedex'] = packaging_type_fedex
                vals['package_detail_fedex'] = package_detail_fedex
                vals['payment_type_fedex'] = payment_type_fedex
                vals['physical_packaging_fedex'] = physical_packaging_fedex

                pickup_type_ups = '01'
                service_type_ups = '03'
                packaging_type_ups = '02'
                vals['pickup_type_ups'] = pickup_type_ups
                vals['service_type_ups'] = service_type_ups
                vals['packaging_type_ups'] = packaging_type_ups

                if carrier_id:
                    ## Find which carrier has been selected :- cust_default
                    carrier_obj = self.pool.get('delivery.carrier')
                    carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
                    if carrier_lnk.is_ups:
                        cust_default = 'UPS'
                        service_type_ups = carrier_lnk.service_code or '03'
                        vals['service_type_ups'] = service_type_ups
                        cust_default += '/' + service_type_ups
                    elif carrier_lnk.is_fedex:
                        cust_default = 'FedEx'
                        service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
                        vals['service_type_fedex'] = service_type_fedex
                        cust_default += '/' + service_type_fedex
                    elif carrier_lnk.is_usps:
                        cust_default = 'USPS'
                        service_type_usps = carrier_lnk.service_code or 'All'
                        first_class_mail_type_usps = carrier_lnk.first_class_mail_type_usps or 'Letter'
                        container_usps = carrier_lnk.container_usps or ''
                        size_usps = carrier_lnk.size_usps or 'REGULAR'
                        vals['service_type_usps'] = service_type_usps
                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                        vals['container_usps'] = container_usps
                        vals['size_usps'] = size_usps
                        cust_default += '/' + service_type_usps

                saleorderline_obj = self.pool.get('sale.order.line')
                saleorderline_ids = saleorderline_obj.search(cr,uid,[('order_id','=',vals['sale_id'])])
                #logger.notifyChannel('init', netsvc.LOG_WARNING, 'saleorderline_ids is %s'%(saleorderline_ids),)

                ## We consider the Gross Weight
                weight = 0.0
                for saleorderline_id in saleorderline_ids:
                    saleorderline_lnk = saleorderline_obj.browse(cr,uid,saleorderline_id)
                    weight += saleorderline_lnk.product_id.product_tmpl_id.weight_net


                usps_fc_letter = True
                usps_fc_nrect_parcel = True
                for saleorderline_id in saleorderline_ids:
                    saleorderline_lnk = saleorderline_obj.browse(cr,uid,saleorderline_id)

                    prod_categ = saleorderline_lnk.product_id.product_tmpl_id.categ_id.name or ''
                    list_price = saleorderline_lnk.product_id.product_tmpl_id.list_price or 0.0

    #                logger.notifyChannel('init', netsvc.LOG_WARNING, 'cond1 is %s'%(prod_categ.lower() not in ('cell phone') and list_price > 50)
    #                logger.notifyChannel('init', netsvc.LOG_WARNING, 'cond2 is %s'%(list_price > 50)
    #                logger.notifyChannel('init', netsvc.LOG_WARNING, 'cond3 is %s'%(list_price < 200)
    #                logger.notifyChannel('init', netsvc.LOG_WARNING, 'cond4 is %s'%((weight < 1.0)
    #                    print "cond1: ",prod_categ.lower() not in ('cell phone') and list_price > 50
    #                    print "cond2: ",list_price < 200
    #                    print "cond3: ",(weight < 1.0)
    #                    print "cond4: ",not(((True) or (False)) and (False))

                    if not (prod_categ.lower() in ('battery','battery doors','gel skin','screen protector','memory','wired headsets','usb cables') and weight < 3.0 / 16.0 and list_price <=20):
                        usps_fc_letter = False
                    if not(((prod_categ.lower() not in ('cell phone') and list_price > 50) or (list_price < 200)) and (weight < 1.0)):
                        usps_fc_nrect_parcel = False

    #                print "usps_fc_letter: ",usps_fc_letter
    #                print "usps_fc_nrect_parcel: ",usps_fc_nrect_parcel

                sys_default = False
                if saleorderline_ids:
                    if usps_fc_letter:
                        if not (cust_default and cust_default.split("/")[0] == 'USPS'):
                            sys_default = "USPS/First-Class/Letter"
                            service_type_usps = 'First Class'
                            first_class_mail_type_usps = 'Letter'
                            container_usps = ''
                            size_usps = 'REGULAR'
                            vals['service_type_usps'] = service_type_usps
                            vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                            vals['container_usps'] = container_usps
                            vals['size_usps'] = 'REGULAR'
                    elif usps_fc_nrect_parcel:
                        if not (cust_default and cust_default.split("/")[0] == 'USPS'):
                            sys_default = "USPS/First-Class/Parcel/Non-Rectangular"
                            service_type_usps = 'First Class'
                            first_class_mail_type_usps = 'Parcel'
                            container_usps = 'Non-Rectangular'
                            size_usps = 'REGULAR'
                            vals['service_type_usps'] = service_type_usps
                            vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                            vals['container_usps'] = container_usps
                            vals['size_usps'] = size_usps
                    else:
                        if not (cust_default and cust_default.split("/")[0] == 'UPS'):
                            sys_default = "UPS/03"
                            service_type_ups = '03'
                            vals['service_type_ups'] = service_type_ups
                print "sys_default in create: ",sys_default

                ## Zip soruce and Zip Destination
    #            cr.execute('select user_id, cid from res_company_users_rel where user_id = %s',(uid,))
    #            res = cr.fetchall()
    #            adr = dict(res)

    #            partner_lnk = self.pool.get('res.company').browse(cr,uid,adr[uid]).partner_id
    #            address = self.pool.get('res.partner').address_get(cr,uid,[partner_lnk.id])
                #logger.notifyChannel('init', netsvc.LOG_WARNING, 'address %s' % (address,))
                #partneradd_lnk = self.pool.get('res.partner.address').browse(cr,uid,address['default'])
                partneradd_lnk = saleorder_lnk.shop_id.cust_address
                result = get_partner_details(saleorder_lnk.shop_id.name,partneradd_lnk,context)
                print "zip5: ",result.get('zip5',False)
                shipper_postal_code = result['zip5']
                shipper_country_code = result['country_code']

                partner_lnk = self.pool.get('sale.order').browse(cr,uid,vals['sale_id']).partner_id
                address = self.pool.get('res.partner').address_get(cr,uid,[partner_lnk.id])
                #logger.notifyChannel('init', netsvc.LOG_WARNING, 'address %s' % (address,))
                partneradd_lnk = self.pool.get('res.partner.address').browse(cr,uid,address['default'])
                result = get_partner_details(partner_lnk.name,partneradd_lnk,context)
                customer_postal_code = result['zip5']
                customer_country_code = result['country_code']

                new_id = super(stock_picking, self).create(cr, uid, vals, context)

                error_required = False

                shipping_usps_res = self.generate_usps_shipping(cr,uid,[new_id],service_type_usps,first_class_mail_type_usps,container_usps,size_usps,weight,shipper_postal_code,customer_postal_code,sys_default,cust_default,error_required,context)
                logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipping_usps_res is %s'%(shipping_usps_res,))

                shipping_ups_res = self.generate_ups_shipping(cr,uid,[new_id],pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context)
                logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipping_ups_res is %s'%(shipping_ups_res,))

    #            shipping_fedex_res = self.generate_fedex_shipping(cr,uid,[new_id],dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context=None)
    #            logger.notifyChannel('init', netsvc.LOG_WARNING, 'shipping_fedex_res is %s'%(shipping_fedex_res,))
            except:
                new_id = super(stock_picking, self).create(cr, uid, vals, context)
        else:
            new_id = super(stock_picking, self).create(cr, uid, vals, context)
        #print "new_id: ",new_id
#        print "error" + 1
        return new_id


    def _cal_weight_usps(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for picking in self.browse(cr, uid, ids, context=context):
            weight_net = picking.weight_net or 0.00
            weight_net_usps = weight_net / 2.2


            res[picking.id] = {
                                'weight_net_usps': weight_net_usps,
                              }
        return res

    def _get_picking_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()

    def _get_service_type_usps(self, cr, uid, context=None):
        logger.notifyChannel('init', netsvc.LOG_WARNING, '_get_service_type_usps context is %s'%(context,))
        return 'First Class'

    _columns = {
        'use_shipping' : fields.boolean('Use Shipping'),
        'shipping_type' : fields.selection([
                ('Fedex','Fedex'),
                ('UPS','UPS'),
                ('USPS','USPS'),
                ('All','All'),
            ],'Shipping Type'),
        #'weight_net_usps': fields.function(_cal_weight_usps, method=True, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight_usps',
                  #store={
                 #'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                 #'stock.move': (_get_picking_line, ['product_id','product_qty','product_uom','product_uos_qty'], 20),
                 #}, help="Total weight of products in pounds"),"""
        'weight_package' : fields.float('Package Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds"),
        'service_type_usps' : fields.selection([
                ('First Class', 'First Class'),
                ('First Class HFP Commercial', 'First Class HFP Commercial'),
                ('Priority', 'Priority'),
                ('Priority Commercial', 'Priority Commercial'),
                ('Priority HFP Commercial', 'Priority HFP Commercial'),
                ('Express', 'Express'),
                ('Express Commercial', 'Express Commercial'),
                ('Express SH', 'Express SH'),
                ('Express SH Commercial', 'Express SH Commercial'),
                ('Express HFP', 'Express HFP'),
                ('Express HFP Commercial', 'Express HFP Commercial'),
                ('Parcel', 'Parcel'),
                ('Media', 'Media'),
                ('Library', 'Library'),
                ('All', 'All'),
                ('Online', 'Online'),
            ], 'Service Type', size=100),
        'first_class_mail_type_usps' : fields.selection([
                ('Letter', 'Letter'),
                ('Flat', 'Flat'),
                ('Parcel', 'Parcel'),
                ('Postcard', 'Postcard'),
            ], 'First Class Mail Type', size=50),
         'container_usps' : fields.selection([
                ('Variable', 'Variable'),
                ('Card', 'Card'),
                ('Letter', 'Letter'),
                ('Flat', 'Flat'),
                ('Parcel', 'Parcel'),
                ('Large Parcel', 'Large Parcel'),
                ('Irregular Parcel', 'Irregular Parcel'),
                ('Oversized Parcel', 'Oversized Parcel'),
                ('Flat Rate Envelope', 'Flat Rate Envelope'),
                ('Padded Flat Rate Envelope', 'Padded Flat Rate Envelope'),
                ('Legal Flat Rate Envelope', 'Legal Flat Rate Envelope'),
                ('SM Flat Rate Envelope', 'SM Flat Rate Envelope'),
                ('Window Flat Rate Envelope', 'Window Flat Rate Envelope'),
                ('Gift Card Flat Rate Envelope', 'Gift Card Flat Rate Envelope'),
                ('Cardboard Flat Rate Envelope', 'Cardboard Flat Rate Envelope'),
                ('Flat Rate Box', 'Flat Rate Box'),
                ('SM Flat Rate Box', 'SM Flat Rate Box'),
                ('MD Flat Rate Box', 'MD Flat Rate Box'),
                ('LG Flat Rate Box', 'LG Flat Rate Box'),
                ('RegionalRateBoxA', 'RegionalRateBoxA'),
                ('RegionalRateBoxB', 'RegionalRateBoxB'),
                ('Rectangular', 'Rectangular'),
                ('Non-Rectangular', 'Non-Rectangular'),
             ],'Container', size=100),
         'size_usps' : fields.selection([
                ('REGULAR', 'Regular'),
                ('LARGE', 'Large'),
             ],'Size'),
         'width_usps' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
         'length_usps' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
         'height_usps' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),
         'girth_usps' : fields.float('Girth', digits_compute= dp.get_precision('Stock Weight')),
         #'machinable_usps' : fields.boolean('Machinable', domain=[('service_type_usps', 'in', ('first_class','parcel','all','online')), '|', ('first_class_mail_type_usps', 'in', ('letter','flat'))]),
         #'ship_date_usps' : fields.date('Ship Date', help="Date Package Will Be Mailed. Ship date may be today plus 0 to 3 days in advance."),
         'dropoff_type_fedex' : fields.selection([
                ('REGULAR_PICKUP','REGULAR PICKUP'),
                ('REQUEST_COURIER','REQUEST COURIER'),
                ('DROP_BOX','DROP BOX'),
                ('BUSINESS_SERVICE_CENTER','BUSINESS SERVICE CENTER'),
                ('STATION','STATION'),
            ],'Dropoff Type'),
         'service_type_fedex' : fields.selection([
                ('EUROPE_FIRST_INTERNATIONAL_PRIORITY','EUROPE_FIRST_INTERNATIONAL_PRIORITY'),
                ('FEDEX_1_DAY_FREIGHT','FEDEX_1_DAY_FREIGHT'),
                ('FEDEX_2_DAY','FEDEX_2_DAY'),
                ('FEDEX_2_DAY_FREIGHT','FEDEX_2_DAY_FREIGHT'),
                ('FEDEX_3_DAY_FREIGHT','FEDEX_3_DAY_FREIGHT'),
                ('FEDEX_EXPRESS_SAVER','FEDEX_EXPRESS_SAVER'),
                ('STANDARD_OVERNIGHT','STANDARD_OVERNIGHT'),
                ('PRIORITY_OVERNIGHT','PRIORITY_OVERNIGHT'),
                ('FEDEX_GROUND','FEDEX_GROUND'),
           ],'Service Type'),
         'packaging_type_fedex' : fields.selection([
                ('FEDEX_BOX','FEDEX BOX'),
                ('FEDEX_PAK','FEDEX PAK'),
                ('FEDEX_TUBE','FEDEX_TUBE'),
                ('YOUR_PACKAGING','YOUR_PACKAGING'),
            ],'Packaging Type', help="What kind of package this will be shipped in"),
         'package_detail_fedex' : fields.selection([
                ('INDIVIDUAL_PACKAGES','INDIVIDUAL_PACKAGES'),
                ('PACKAGE_GROUPS','PACKAGE_GROUPS'),
                ('PACKAGE_SUMMARY','PACKAGE_SUMMARY'),
            ],'Package Detail'),
         'payment_type_fedex' : fields.selection([
                ('RECIPIENT','RECIPIENT'),
                ('SENDER','SENDER'),
                ('THIRD_PARTY','THIRD_PARTY'),
            ],'Payment Type', help="Who pays for the rate_request?"),
         'physical_packaging_fedex' : fields.selection([
                ('BAG','BAG'),
                ('BARREL','BARREL'),
                ('BOX','BOX'),
                ('BUCKET','BUCKET'),
                ('BUNDLE','BUNDLE'),
                ('CARTON','CARTON'),
                ('TANK','TANK'),
                ('TUBE','TUBE'),
            ],'Physical Packaging'),
         'pickup_type_ups' : fields.selection([
                ('01','Daily Pickup'),
                ('03','Customer Counter'),
                ('06','One Time Pickup'),
                ('07','On Call Air'),
                ('11','Suggested Retail Rates'),
                ('19','Letter Center'),
                ('20','Air Service Center'),
            ],'Pickup Type'),
         'service_type_ups' : fields.selection([
                ('01','Next Day Air'),
                ('02','Second Day Air'),
                ('03','Ground'),
                ('07','Worldwide Express'),
                ('08','Worldwide Expedited'),
                ('11','Standard'),
                ('12','Three-Day Select'),
                ('13','Next Day Air Saver'),
                ('14','Next Day Air Early AM'),
                ('54','Worldwide Express Plus'),
                ('59','Second Day Air AM'),
                ('65','Saver'),
            ],'Service Type'),
         'packaging_type_ups' : fields.selection([
                ('00','Unknown'),
                ('01','Letter'),
                ('02','Package'),
                ('03','Tube'),
                ('04','Pack'),
                ('21','Express Box'),
                ('24','25Kg Box'),
                ('25','10Kg Box'),
                ('30','Pallet'),
                ('2a','Small Express Box'),
                ('2b','Medium Express Box'),
                ('2c','Large Express Box'),
            ],'Packaging Type'),
         'shipping_label' : fields.binary('Logo'),
         'shipping_rate': fields.float('Shipping Rate'),
         'response_usps_ids' : fields.one2many('shipping.response','picking_id','Shipping Response')
    }

    _defaults = {
        'use_shipping' : True,
        'shipping_type' : 'All',
        'service_type_usps' : 'All',
        'size_usps' : 'REGULAR',
        'dropoff_type_fedex' : 'REGULAR_PICKUP',
        'service_type_fedex' : 'FEDEX_GROUND',
        'packaging_type_fedex' : 'YOUR_PACKAGING',
        'package_detail_fedex' : 'INDIVIDUAL_PACKAGES',
        'payment_type_fedex' : 'SENDER',
        'physical_packaging_fedex' : 'BOX',
        'pickup_type_ups' : '01',
        'service_type_ups' : '03',
        'packaging_type_ups' : '02'
    }

stock_picking()

class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _cal_move_weight_new(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for move in self.browse(cr, uid, ids, context=context):
            weight = weight_net = 0.00
            
            converted_qty = move.product_qty
            if move.product_uom.id <> move.product_id.uom_id.id:
                converted_qty = uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, move.product_id.uom_id.id)

            if move.product_id.weight > 0.00:
                weight = (converted_qty * move.product_id.weight)

            if move.product_id.weight_net > 0.00:
                    weight_net = (converted_qty * move.product_id.weight_net)

            res[move.id] =  {
                            'weight': weight,
                            'weight_net': weight_net,
                            }
        return res

    _columns = {
        'weight': fields.function(_cal_move_weight_new, method=True, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_move_weight',
                  store={
                 'stock.move': (lambda self, cr, uid, ids, c=None: ids, ['product_id', 'product_qty', 'product_uom'], 20),
                 }),
        'weight_net': fields.function(_cal_move_weight_new, method=True, type='float', string='Net weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_move_weight',
                  store={
                 'stock.move': (lambda self, cr, uid, ids, c=None: ids, ['product_id', 'product_qty', 'product_uom'], 20),
                 }),
        }

stock_move()

class scan_batch(osv.osv):
    _name ="scan.batch"
    _columns = {
        'name'  :fields.char ('Batch No',required="1",size=128 ),
        'order_no' :fields.char ('Order No',size=64),
    }
    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get_last(cr, uid, 'print.packing.slip'),
    }

    def open_order(self, cr, uid, ids, context=None):
        print "inside action_packing_slip"
        (data,) = self.browse(cr, uid, ids , context=context)
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr, uid, [('model','=','ir.ui.view'),('name','=','view_shipping_picking_out_form')], context=context)
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name':_("Outgoing Order for Shipping"),
            'view_mode': 'form',
            'view_id': False,
            'views': [(resource_id,'form')],
            'view_type': 'form',
            'res_id' : data.order_no,
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
    
scan_batch()


