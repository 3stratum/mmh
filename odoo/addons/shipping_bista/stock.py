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
from base64 import b64decode
import binascii
import decimal_precision as dp
import time
import webbrowser

import HTMLParser
h = HTMLParser.HTMLParser()
import httplib
import shippingservice
from miscellaneous import Address

from .xml_dict import dict_to_xml, xml_to_dict

from fedex.services.rate_service import FedexRateServiceRequest
from fedex.services.ship_service import FedexProcessShipmentRequest
from fedex.config import FedexConfig
import suds
from suds.client import Client

from tools.translate import _
import netsvc
logger = netsvc.Logger()
import math
import socket
import urllib2

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

    def generate_tracking_no(self, cr, uid, ids, context={}, error=True):
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
            real_stock  = move_line.product_id.qty_available
            print "real_stock: ",real_stock
            res = self.pool.get('stock.location')._product_reserve(cr, uid, [move_line.location_id.id], move_line.product_id.id, move_line.product_qty, {'uom': move_line.product_uom.id}, lock=True)
#            if not res:
#                saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'state':'shipping_except'})
#                if error:
#                    raise osv.except_osv(_('Error'), _('Not enough stock in inventory'))
#                return False
        partneradd_lnk = shippingresp_lnk.picking_id.sale_id.shop_id.cust_address
        if not partneradd_lnk:
           raise osv.except_osv(_('Error'), _('Shop Address not defined!'),)
        result_from = get_partner_details(shippingresp_lnk.picking_id.sale_id.shop_id.name,partneradd_lnk,context)

        partner_lnk = shippingresp_lnk.picking_id.partner_id
        address = self.pool.get('res.partner').address_get(cr,uid,[partner_lnk.id])
        partneradd_lnk = self.pool.get('res.partner.address').browse(cr,uid,address['default'])
        result_to = get_partner_details(partner_lnk.name,partneradd_lnk,context)
        ### Shipper
        cust_address = shippingresp_lnk.picking_id.sale_id.shop_id.cust_address
        if not cust_address:
            if error:
                raise osv.except_osv(_('Error'), _('Shop Address not defined!'),)
            else:
                return False
        shipper = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)

        ### Recipient
        cust_address = shippingresp_lnk.picking_id.address_id
        receipient = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)

        weight = shippingresp_lnk.weight
        rate = shippingresp_lnk.rate
        tracking_no = False

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
            context['attach_id'] = attach_id
            
            if tracking_no:
                stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':tracking_no, 'shipping_label':binascii.b2a_base64(str(b64decode(s_label))), 'shipping_rate': rate})
                context['track_success'] = True
        
        elif shippingresp_lnk.type.lower() == 'fedex':
            print "Inside Fedex Shipping"
            #raise osv.except_osv(_('Error'), _('FedEx shipment request under construction'))

            shippingfedex_obj = self.pool.get('shipping.fedex')
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
#            print "DROPOFF TYPE: ",shippingresp_lnk.dropoff_type_fedex
            fedex_servicedetails = stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id)
            
            shipment.RequestedShipment.DropoffType = fedex_servicedetails.dropoff_type_fedex #'REGULAR_PICKUP'
            print "DROP OFF TYPE: ",fedex_servicedetails.dropoff_type_fedex
            # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
            # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
            shipment.RequestedShipment.ServiceType = fedex_servicedetails.service_type_fedex #'PRIORITY_OVERNIGHT'

            # What kind of package this will be shipped in.
            # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
            shipment.RequestedShipment.PackagingType = fedex_servicedetails.packaging_type_fedex  #'FEDEX_PAK'

            # No idea what this is.
            # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
            shipment.RequestedShipment.PackageDetail = fedex_servicedetails.package_detail_fedex #'INDIVIDUAL_PACKAGES'

            # Shipper contact info.
            shipment.RequestedShipment.Shipper.Contact.PersonName = shipper.name #'Sender Name'
            shipment.RequestedShipment.Shipper.Contact.CompanyName = shipper.company_name #'Some Company'
            shipment.RequestedShipment.Shipper.Contact.PhoneNumber = shipper.phone #'9012638716'

            # Shipper address.
            shipment.RequestedShipment.Shipper.Address.StreetLines = shipper.address1 #['Address Line 1']
            shipment.RequestedShipment.Shipper.Address.City =  shipper.city #'Herndon'
            shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = shipper.state_code #'VA'
            shipment.RequestedShipment.Shipper.Address.PostalCode = shipper.zip #'20171'
            shipment.RequestedShipment.Shipper.Address.CountryCode = shipper.country_code #'US'
            shipment.RequestedShipment.Shipper.Address.Residential = False

            # Recipient contact info.
            shipment.RequestedShipment.Recipient.Contact.PersonName = receipient.name #'Recipient Name'
            shipment.RequestedShipment.Recipient.Contact.CompanyName = receipient.company_name #'Recipient Company'
            shipment.RequestedShipment.Recipient.Contact.PhoneNumber = receipient.phone #'9012637906'

            # Recipient address
            shipment.RequestedShipment.Recipient.Address.StreetLines = receipient.address1 #['Address Line 1']
            shipment.RequestedShipment.Recipient.Address.City = receipient.city #'Herndon'
            shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = receipient.state_code #'VA'
            shipment.RequestedShipment.Recipient.Address.PostalCode = receipient.zip #'20171'
            shipment.RequestedShipment.Recipient.Address.CountryCode = receipient.country_code #'US'
            # This is needed to ensure an accurate rate quote with the response.
            shipment.RequestedShipment.Recipient.Address.Residential = False

            # Who pays for the shipment?
            # RECIPIENT, SENDER or THIRD_PARTY
            shipment.RequestedShipment.ShippingChargesPayment.PaymentType = fedex_servicedetails.payment_type_fedex #'SENDER'

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
            package1_weight.Value = fedex_servicedetails.weight_package #1.0
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
            try:
                shipment.send_request()
            except Exception, e:
                if error:
                        if e.reason.strerror == 'Name or service not known':
                            errormessage = "Connection Error: Please check your internet connection!"
                        else:
                            errormessage = e
                    
                        print "EXception: ",errormessage        
                        raise osv.except_osv(_('Error'), _('%s' % (errormessage,)))                
                
            # This will show the reply to your shipment being sent. You can access the
            # attributes through the response attribute on the request object. This is
            # good to un-comment to see the variables returned by the Fedex reply.
            #print shipment.response
            
            # Here is the overall end result of the query.
            print "HighestSeverity:", shipment.response.HighestSeverity
            # Getting the tracking number from the new shipment.
            fedexTrackingNumber = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber 
            print "Fedex Tracking#:",fedexTrackingNumber 
            # Net shipping costs.
            fedexshippingrate = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount
            print "Net Shipping Cost (US$):",fedexshippingrate

            # Get the label image in ASCII format from the reply. Note the list indices
            # we're using. You'll need to adjust or iterate through these if your shipment
            # has multiple packages.
            ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
            # Convert the ASCII data to binary.
#            label_binary_data = binascii.a2b_base64(ascii_label_data)
#            print"LABEL: ",label_binary_data
            """
            #This is an example of how to dump a label to a PNG file.
            """
            # This will be the file we write the label out to.
#            png_file = open('example_shipment_label.png', 'wb')
#            png_file.write(b64decode(label_binary_data))
#            png_file.close()
            
            
            fedex_attachment_pool = self.pool.get('ir.attachment')
            fedex_data_attach = {
                'name': 'PackingList.png',
                'datas': binascii.b2a_base64(str(b64decode(ascii_label_data))),
                'description': 'Packing List',
                'res_name': shippingresp_lnk.picking_id.name,
                'res_model': 'stock.picking',
                'res_id': shippingresp_lnk.picking_id.id,
            }
            
            fedex_attach_id = fedex_attachment_pool.search(cr,uid,[('res_id','=',shippingresp_lnk.picking_id.id),('res_name','=',shippingresp_lnk.picking_id.name)])
            if not fedex_attach_id:
                fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
                print "attach_id: ",fedex_attach_id
            else:
                fedex_attach_result = fedex_attachment_pool.write(cr, uid, fedex_attach_id, fedex_data_attach)
                fedex_attach_id = fedex_attach_id[0]
                print "attach_result: ",fedex_attach_result
                
            context['attach_id'] = fedex_attach_id
            context['tracking_no'] = fedexTrackingNumber
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
#
#            if shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber:
#                track_success = True
            if fedexTrackingNumber:
                stockpickingwrite_result = stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':fedexTrackingNumber, 'shipping_label':binascii.b2a_base64(str(b64decode(ascii_label_data))), 'shipping_rate': fedexshippingrate})
                context['track_success'] = True    

        elif shippingresp_lnk.type.lower() == 'ups':
            ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)

            stockpicking_obj = self.pool.get('stock.picking')
            pickup_type_ups = shippingresp_lnk.picking_id.pickup_type_ups
            service_type_ups = shippingresp_lnk.picking_id.service_type_ups
            packaging_type_ups = shippingresp_lnk.picking_id.packaging_type_ups
            ups = shippingservice.UPSShipmentConfirmRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper, receipient)
            try:
                ups_response = ups.send()
            except Exception, e:
                if error:
                        if e.reason.strerror == 'Name or service not known':
                            errormessage = "Connection Error: Please check your internet connection!"
                        else:
                            errormessage = e
                    
                        print "EXception: ",errormessage        
                        raise osv.except_osv(_('Error'), _('%s' % (errormessage,)))
                        
            ups = shippingservice.UPSShipmentAcceptRequest(ups_info, ups_response.shipment_digest)
            ups_response = ups.send()
            
            context['attach_id'] = stockpicking_obj.create_attachment(cr,uid,[shippingresp_lnk.picking_id.id],ups_response,context)
            stockpickingwrite_result = stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':ups_response.tracking_number, 'shipping_label':binascii.b2a_base64(str(b64decode(ups_response.graphic_image))), 'shipping_rate': rate})
            context['track_success'] = True
            context['tracking_no'] = ups_response.tracking_number
        
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
            saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'client_order_ref':context['tracking_no'], 'carrier_id':carrier_ids[0]})

            ### Write this shipping respnse is selected
            self.write(cr,uid,ids[0],{'selected':True})

            if context.get('batch_printing',False):
                return True
            
            
            #serverip = socket.gethostbyname(socket.gethostname())
            try:
                serverip = urllib2.urlopen('http://whatismyip.org').read()
            except Exception, e:                
                if error:
                    raise osv.except_osv(_('Error'), _('%s' % (e))) 
                
            print "IP ADDRESS IS: ",serverip
            
            return {'type': 'ir.actions.act_url',
                'url': 'http://'+serverip+':8080/openerp/attachment/get?record=' + str(context['attach_id']),
                'target': 'new'}

#            datas = {'ids': [shippingresp_lnk.picking_id.id],
#                     'model': 'stock.picking'}

#            return {'type': 'ir.actions.report.xml',
#                    'report_name': 'webkitstock.picking.label',
#                    'datas': datas}
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

def _get_shipping_type(self, cr, uid, context=None):
    return [
        ('Fedex','Fedex'),
        ('UPS','UPS'),
        ('USPS','USPS'),
        ('All','All'),
    ]
def _get_service_type_usps(self, cr, uid, context=None):
    return [
        ('First Class', 'First Class'),
        ('First Class HFP Commercial', 'First Class HFP Commercial'),
        ('FirstClassMailInternational', 'First Class Mail International'),
        ('Priority', 'Priority'),
        ('Priority Commercial', 'Priority Commercial'),
        ('Priority HFP Commercial', 'Priority HFP Commercial'),
        ('PriorityMailInternational', 'Priority Mail International'),
        ('Express', 'Express'),
        ('Express Commercial', 'Express Commercial'),
        ('Express SH', 'Express SH'),
        ('Express SH Commercial', 'Express SH Commercial'),
        ('Express HFP', 'Express HFP'),
        ('Express HFP Commercial', 'Express HFP Commercial'),
        ('ExpressMailInternational', 'Express Mail International'),
        ('ParcelPost', 'Parcel Post'),
        ('ParcelSelect', 'Parcel Select'),
        ('StandardMail', 'Standard Mail'),
        ('CriticalMail', 'Critical Mail'),
        ('Media', 'Media'),
        ('Library', 'Library'),
        ('All', 'All'),
        ('Online', 'Online'),
    ]

def _get_first_class_mail_type_usps(self, cr, uid, context=None):
    return [
        ('Letter', 'Letter'),
        ('Flat', 'Flat'),
        ('Parcel', 'Parcel'),
        ('Postcard', 'Postcard'),
    ]

def _get_container_usps(self, cr, uid, context=None):
    return [
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
     ]

def _get_size_usps(self, cr, uid, context=None):
    return [
        ('REGULAR', 'Regular'),
        ('LARGE', 'Large'),
     ]

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
                raise Exception('%s' % (e))
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
            raise Exception('%s' % (e))
            return False


        if response.find('<Error>') != -1:
            sIndex = response.find('<Description>')
            eIndex = response.find('</Description>')
            if error:
                raise Exception('%s' % (response[int(sIndex)+13:int(eIndex)],))
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
#            mail_service = mail_service.replace("&amp;lt;sup&amp;gt;&amp;amp;reg;&amp;lt;/sup&amp;gt;",str(tm))
            mail_service = mail_service.replace("&amp;lt;sup&amp;gt;&amp;amp;reg;&amp;lt;/sup&amp;gt;","")
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

    def create_quotes(self, cr, uid, ids, vals, context={}):
        quotes_vals = {
            'name' : vals.service_type,
            'type' : context['type'],
            'rate' : vals.rate,
            'picking_id' : ids[0], #Change the ids[0] when switch to create
            'weight' : vals.weight,
            'sys_default' : False,
            'cust_default' : False,
            'sr_no' : vals.sr_no,
        }
        res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
        logger.notifyChannel('init', netsvc.LOG_WARNING, 'res_id is %s'%(res_id,))
        if res_id:
            return True
        else:
            return False

    def create_attachment(self, cr, uid, ids, vals, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        data_attach = {
            'name': 'PackingList.' + vals.image_format.lower() ,
            'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image))),
            'description': 'Packing List',
            'res_name': self.browse(cr,uid,ids[0]).name,
            'res_model': 'stock.picking',
            'res_id': ids[0],
        }
        attach_id = attachment_pool.search(cr,uid,[('res_id','=',ids[0]),('res_name','=',self.browse(cr,uid,ids[0]).name)])
        if not attach_id:
            attach_id = attachment_pool.create(cr, uid, data_attach)
            print "attach_id: ",attach_id
        else:
            attach_id = attach_id[0]
            attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
            print "attach_result: ",attach_result
        return attach_id


    ## This function is called when the button is clicked
    def generate_shipping(self, cr, uid, ids, context={}):
        print"IDS IS:",ids
        print"rajivcontext",context
        if context is None:
            context = {}
#        logger.notifyChannel('init', netsvc.LOG_WARNING, 'inside generate_shipping context: %s'%(context,))
        for id in ids:
            print"ID IS:",id
            try:
                stockpicking = self.browse(cr,uid,id)
                shipping_type = stockpicking.shipping_type
                print"shipping_type@@@",shipping_type

                weight = stockpicking.weight_package if stockpicking.weight_package else stockpicking.weight_net
                if not weight:
                    if context.get('error',False):
                        raise Exception('Package Weight Invalid!')
                    else:
                        return False
                shop_id = stockpicking.sale_id.shop_id
                print"shop_id@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",shop_id
                cust_address = stockpicking.sale_id.shop_id.cust_address
                print "CUST ADDRESS: ",cust_address
                if not cust_address:
                    if context.get('error',False):
                        raise Exception('Shop Address not defined!')
                    else:
                        return False

                shipper = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)
                
                ### Recipient
                cust_address = stockpicking.address_id
                cust_default=False
                sys_default=False
                stockpicking_lnk = self.browse(cr,uid,ids[0])
                receipient = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)

                # Deleting previous quotes
                shipping_res_obj = self.pool.get('shipping.response')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('picking_id','=',ids[0])])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)

                if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
                    print"Asif inside usps"
                    usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
                    service_type_usps = stockpicking.service_type_usps
                    first_class_mail_type_usps = stockpicking.first_class_mail_type_usps or ''
                    container_usps = stockpicking.container_usps or ''
                    size_usps = stockpicking.size_usps
                    width_usps = stockpicking.width_usps
                    length_usps = stockpicking.length_usps
                    height_usps = stockpicking.height_usps
                    girth_usps = stockpicking.girth_usps
                    usps = shippingservice.USPSRateRequest(usps_info, service_type_usps, first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default, sys_default)
                    usps_response = usps.send()
                    context['type'] = 'USPS'
                    self.create_quotes(cr,uid,ids,usps_response,context)
#                    shipping_res = self.generate_usps_shipping(cr,uid,[id],service_type_usps,first_class_mail_type_usps,container_usps,size_usps,weight,shipper_postal_code,customer_postal_code,sys_default,cust_default,error_required,context)

                if 'ups_active' not in context.keys() or (shipping_type == 'UPS' or shipping_type == 'All'):
                    print"Rajiv.S.Singh"
                    ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                    pickup_type_ups = stockpicking.pickup_type_ups
                    service_type_ups = stockpicking.service_type_ups
                    packaging_type_ups = stockpicking.packaging_type_ups
                    ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper, receipient, cust_default, sys_default)
                    ups_response = ups.send()
                    context['type'] = 'UPS'
                    self.create_quotes(cr,uid,ids,ups_response,context)
#                    shipping_res = self.generate_ups_shipping(cr,uid,[id],pickup_type_ups,service_type_ups,packaging_type_ups,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context)

                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = stockpicking.dropoff_type_fedex
                    service_type_fedex = stockpicking.service_type_fedex
                    packaging_type_fedex = stockpicking.packaging_type_fedex
                    package_detail_fedex = stockpicking.package_detail_fedex
                    payment_type_fedex = stockpicking.payment_type_fedex
                    physical_packaging_fedex = stockpicking.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    error_required = True
                    shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context)
            except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
            return True

    def _get_cust_default_shipping(self,cr,uid,carrier_id,context={}):
        if carrier_id:
            carrier_obj = self.pool.get('delivery.carrier')             
            carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
            cust_default = ''
            if carrier_lnk.is_ups:
                cust_default = 'UPS'
                service_type_ups = carrier_lnk.service_code or '03'
                cust_default += '/' + service_type_ups
            elif carrier_lnk.is_fedex:
                cust_default = 'FedEx'
                service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
                cust_default += '/' + service_type_fedex
            elif carrier_lnk.is_usps:
                cust_default = 'USPS'
                service_type_usps = carrier_lnk.service_code or 'All'
                cust_default += '/' + service_type_usps
        else:
            cust_default = False
        return cust_default

    def _get_sys_default_shipping(self,cr,uid,saleorderline_ids,weight,context={}):
        print "SIJO:inside _get_sys_default_shipping"
        sys_default = False
        if len(saleorderline_ids) <= 2:
            product_obj = self.pool.get('product.product')
            saleorderline_obj = self.pool.get('sale.order.line')
            product_shipping_obj = self.pool.get('product.product.shipping')
            product_categ_shipping_obj = self.pool.get('product.category.shipping')

            product_id = False
            ### Making sure product is not Shipping and Handling
            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
                if line.product_id.type == 'service':
                    continue
                product_id = line.product_id.id
                
            if not product_id:
                return False

            product_shipping_ids = product_shipping_obj.search(cr,uid,[('product_id','=',product_id)])

            if not product_shipping_ids:
                categ_id = product_obj.browse(cr,uid,product_id).product_tmpl_id.categ_id.id
                product_categ_shipping_ids = product_categ_shipping_obj.search(cr,uid,[('product_categ_id','=',categ_id)])
                if not product_categ_shipping_ids:
                    ### Assume the default
                    if (weight*16) > 14.0:
                        sys_default = 'USPS/Priority/Parcel/REGULAR'
                    else:
                        sys_default = 'USPS/First Class/Parcel/REGULAR'
                    return sys_default

            if product_shipping_ids:
                cr.execute(
                    'SELECT * '
                    'FROM product_product_shipping '
                    'WHERE weight <= %s ' +
                    'and product_id=%s ' +
                    'order by sequence desc limit 1',
                    (weight,product_id))
            else:
                cr.execute(
                    'SELECT * '
                    'FROM product_category_shipping '
                    'WHERE weight <= %s '+
                    'and product_categ_id=%s '+
                    'order by sequence desc limit 1',
                    (weight,categ_id))
            res = cr.dictfetchall()
            print "res: ",res
            ## res:  [{'create_uid': 1, 'create_date': '2011-06-28 01:43:49.017306', 'product_id': 187, 'weight': 3.0, 'sequence': 3, 'container_usps': u'Letter', 'service_type_usps': u'First Class', 'write_uid': None, 'first_class_mail_type_usps': u'Letter', 'size_usps': u'REGULAR', 'write_date': None, 'shipping_type': u'USPS', 'id': 14}]
            ### Format- USPS/First Class/Letter
            sys_default = res[0]['shipping_type'] + '/' + res[0]['service_type_usps'] + '/' + res[0]['container_usps'] + '/' + res[0]['size_usps']
        return sys_default


    def create(self, cr, uid, vals, context=None):
        #print "create vals: ",vals
        #create vals:  {'origin': u'SO009', 'note': False, 'state': 'auto', 'name': u'OUT/00007', 'sale_id': 9, 'move_type': u'direct', 'type': 'out', 'address_id': 3, 'invoice_state': 'none', 'company_id': 1}
        if context is None:
            context={}
        if vals.get('type',False) and vals['type'] == 'out':
            try:
                vals['shipping_type'] = 'All'
                cust_default = False
                saleorder_lnk = self.pool.get('sale.order') .browse(cr,uid,vals['sale_id'])
                saleorderline_obj = self.pool.get('sale.order.line')
                saleorderline_ids = saleorderline_obj.search(cr,uid,[('order_id','=',vals['sale_id'])])
                #logger.notifyChannel('init', netsvc.LOG_WARNING, 'saleorderline_ids is %s'%(saleorderline_ids),)
                weight = 0.0
                for saleorderline_id in saleorderline_ids:
                    saleorderline_lnk = saleorderline_obj.browse(cr,uid,saleorderline_id)
                    weight += (saleorderline_lnk.product_id.product_tmpl_id.weight_net * saleorderline_lnk.product_uom_qty)
                vals['weight_net'] = weight

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

                carrier_id = saleorder_lnk.carrier_id and saleorder_lnk.carrier_id.id or False
                if carrier_id:
                    ## Find which carrier has been selected :- cust_default
                    vals['carrier_id'] = carrier_id
                    cust_default = self._get_cust_default_shipping(cr,uid,carrier_id,context)
                    carrier_obj = self.pool.get('delivery.carrier')
                    carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
                    if carrier_lnk.is_ups:
                        service_type_ups = carrier_lnk.service_code or '03'
                        vals['service_type_ups'] = service_type_ups
                    elif carrier_lnk.is_fedex:
                        service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
                        vals['service_type_fedex'] = service_type_fedex
                    elif carrier_lnk.is_usps:
                        service_type_usps = carrier_lnk.service_code or 'All'
                        first_class_mail_type_usps = carrier_lnk.first_class_mail_type_usps or 'Parcel'
                        container_usps = carrier_lnk.container_usps or 'Parcel'
                        size_usps = carrier_lnk.size_usps or 'REGULAR'
                        vals['service_type_usps'] = service_type_usps
                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                        vals['container_usps'] = container_usps
                        vals['size_usps'] = size_usps
               
                ### Sys default applicable only for simple orders
                sys_default = False
#                if len(saleorderline_ids) <= 2:

                ## We consider the Gross Weight
                    
                sys_default = self._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                print "sys_default in create: ",sys_default
#                   Output: USPS/First Class/Letter/Reqular
#                   If the customer default is not there, ONLY then it goes for system default
                if not (cust_default and cust_default.split("/")[0] == 'USPS') and sys_default and sys_default.split('/')[0] == 'USPS':
                    vals['service_type_usps'] = sys_default.split('/')[1] or ''
#                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                    vals['container_usps'] = sys_default.split('/')[2] or ''
                    vals['size_usps'] = sys_default.split('/')[3] or ''

#                if not (cust_default or sys_default):
#                    if (weight*16) > 14.0:
#                        vals['service_type_usps'] = 'Priority'
#                        vals['first_class_mail_type_usps'] = 'Parcel'
#                        vals['container_usps'] = 'Parcel'
#                        vals['size_usps'] = 'REGULAR'
#                    else:
#                        vals['service_type_usps'] = 'First Class'
#                        vals['first_class_mail_type_usps'] = 'Parcel'
#                        vals['container_usps'] = 'Parcel'
#                        vals['size_usps'] = 'REGULAR'

                print "vals: ",vals
                new_id = super(stock_picking, self).create(cr, uid, vals, context)
                print "new_id: ",new_id
#                error_required = False
                
                context['cust_default'] = cust_default
                context['sys_default'] = sys_default
                context['error'] = False
                res = self.generate_shipping(cr,uid,[new_id],context)
                print "shipping response: ",res
#                print "error" + 1

            except Exception, e:
                print "Exception: ",e
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

    _columns = {
        'use_shipping' : fields.boolean('Use Shipping'),
        'shipping_type' : fields.selection(_get_shipping_type,'Shipping Type'),
        'weight_package' : fields.float('Package Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds"),
        'service_type_usps' : fields.selection(_get_service_type_usps, 'Service Type', size=100),
        'first_class_mail_type_usps' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
        'container_usps' : fields.selection(_get_container_usps,'Container', size=100),
        'size_usps' : fields.selection(_get_size_usps,'Size'),
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
