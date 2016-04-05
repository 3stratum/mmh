# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields, osv
from miscellaneous import Address
import shippingservice
from openerp.addons.bista_shipping_endicia import endicia
from base64 import b64decode
import binascii
import Image
import socket
import openerp.addons.decimal_precision as dp
import urllib2
import urllib
from base64 import b64decode
from fedex.services.rate_service import FedexRateServiceRequest
from fedex.services.ship_service import FedexProcessShipmentRequest
from fedex.config import FedexConfig
import urlparse
import connection_osv as connection
import math
import logging
_logger = logging.getLogger(__name__)
from openerp import netsvc
from openerp.tools.translate import _

ups_service_type = {
    '01': 'Next Day Air',
    '02': 'Second Day Air',
    '03': 'Ground',
    '07': 'Worldwide Express',
    '08': 'Worldwide Expedited',
    '11': 'Standard',
    '12': 'Three-Day Select',
    '13': 'Next Day Air Saver',
    '14': 'Next Day Air Early AM',
    '54': 'Worldwide Express Plus',
    '59': 'Second Day Air AM',
    '65': 'Saver',
}

def _get_fedex_carrier_code(self, cr, uid, context=None):
    return [
        ('FDXE', 'FDXE'),
        ('FDXG', 'FDXG'),]

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
        print "actuallllll calllllllllllllllllllllllll"
        if context is None:
            context = {}
        import os; _logger.info("server name: %s", os.uname()[1])
        try:
            saleorder_obj = self.pool.get('sale.order')
            stockmove_obj = self.pool.get('stock.move')
            stockpicking_obj = self.pool.get('stock.picking')
            res_partner_obj=self.pool.get('res.partner')
            shippingresp_lnk = self.browse(cr,uid,ids[0])
            type = shippingresp_lnk.picking_id.type
            print "typeeeeeeeeeeeeeeeeeeeeeeeee",type
            ### Shipper
            ### based on stock.pickings type
            tracking_ref=stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id).carrier_tracking_ref
            print "tracking_reftracking_reftracking_reftracking_reftracking_ref",tracking_ref
            
            if not tracking_ref:
                if type == 'out':
                    cust_address = shippingresp_lnk.picking_id.sale_id and shippingresp_lnk.picking_id.sale_id.shop_id and shippingresp_lnk.picking_id.sale_id.shop_id.warehouse_id.partner_id or shippingresp_lnk.picking_id.ware_id.partner_id
                    print "cust_addresscust_addresscust_addresscust_address",cust_address
                elif type == 'in':
                    cust_address = shippingresp_lnk.picking_id.address_id
                if not cust_address:
                    print "didnt gpt cust addresssss"
                  
                    if error:
                        raise osv.except_osv(_('Warning'), _('Shop Address not defined!'),)
                    else:
                        return False
                if not (cust_address.name):
                    print "didnt gpt cust name"
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
                if not cust_address.city:
                    print "didnt gpt cust city"
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
                if not cust_address.zip:
                    print "didnt gpt cust zip"
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
                if not cust_address.country_id.code:
                    print "didnt gpt cust contry code"
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
                if not cust_address.email:
                    print "didnt gpt cust email"
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper email."))
                shipper = Address(cust_address.name or cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)

                ### Recipient
                if type == 'out':
                    cust_address = shippingresp_lnk.picking_id.alt_address or shippingresp_lnk.picking_id.partner_id
                    print "customer adresssssssssssssssssss",cust_address
                elif type == 'in':
                    cust_address = shippingresp_lnk.picking_id.sale_id.shop_id and shippingresp_lnk.picking_id.sale_id.shop_id.warehouse_id.partner_id
                if not cust_address:
                    if error:
                        raise osv.except_osv(_('Warning'), _('Shipper Address not defined!'),)
                    else:
                        return False
                if not (cust_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
                receipient = Address(cust_address.name or cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
                weight = shippingresp_lnk.weight
                rate = shippingresp_lnk.rate
                tracking_numbers=''                
                if shippingresp_lnk.type.lower() == 'usps' and not ('usps_active' in context.keys()):
                    move_lines = shippingresp_lnk.picking_id.move_lines
                    count=0
                    for each_move_lines in move_lines:
                        tracking_id=each_move_lines.pack_track_id
                        weight=each_move_lines.weight
                        usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
                        shipping_account=shippingresp_lnk.picking_id.sale_id.shipping_account
                        usps = shippingservice.USPSDeliveryConfirmationRequest(usps_info, shippingresp_lnk.name,weight,shipper,receipient,shipping_account)
                        usps_response = usps.send()
                        count=count+1
                        tracking_no=stockpicking_obj.create_attachment_usps(cr,uid,[shippingresp_lnk.picking_id.id],usps_response,count,context)

                        if tracking_numbers:
                            tracking_numbers=str(tracking_numbers)+"/"+str(tracking_no)
                        else:
                            tracking_numbers=str(tracking_no)
                    stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':tracking_numbers, 'shipping_label':binascii.b2a_base64(str(b64decode(usps_response.graphic_image))), 'shipping_rate':rate,'label_recvd': True})
                    self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':tracking_numbers})
                    context['track_success'] = True
                    context['tracking_no'] = tracking_numbers

                if shippingresp_lnk.type.lower() == 'usps' and ('usps_active' in context.keys()):
                    endicia_active=self.pool.get('shipping.endicia').search(cr,uid,[('active','=',True)])
                    if endicia_active:
                        print "going here "
                        move_lines = shippingresp_lnk.picking_id.move_lines
                        count,attachment_id,tracking_nos=0,[],[]
                        international_label,tracking_numbers = False,''
                        #added
                        track_pack = []
                        available_trackings = shippingresp_lnk.picking_id.tracking_ids
                        picking_data = shippingresp_lnk.picking_id
                        for track_obj in available_trackings :
                            track_pack.append(track_obj.package_id)
                        if picking_data.size_usps and picking_data.size_usps == 'LARGE':
                           if not picking_data.width_usps or not picking_data.length_usps or not picking_data.height_usps and picking_data.size_usps == 'LARGE' :
                          	 raise osv.except_osv(_('Warning !'),_("Please enter USPS dimmensions"))
                        package = endicia.Package(shippingresp_lnk.name, shippingresp_lnk.picking_id.weight_package, endicia.Package.shapes[picking_data.container_usps], picking_data.length_usps, picking_data.width_usps, picking_data.height_usps,picking_data.name,250)
                            if receipient.country_code.lower() != 'us' and receipient.country_code.lower() != 'usa' and receipient.country_code.lower() != 'pr':
                                if context.get('no_international') and shippingresp_lnk.name != 'First Class Mail International':                    
                                    return False
                                package = endicia.Package(shippingresp_lnk.name, int(shippingresp_lnk.picking_id.weight_package), endicia.Package.shapes[picking_data.container_usps], picking_data.length_usps, picking_data.width_usps, picking_data.height_usps,picking_data.name,picking_data.sale_id.amount_total)
                               # package = endicia.Package(shippingresp_lnk.name, int(round(weight*16 >= 1.0 and weight*16 or 1.0)), endicia.Package.shapes[picking_data.container_usps], picking_data.length_usps, picking_data.width_usps, picking_data.height_usps,picking_data.name,picking_data.sale_id.amount_total)
                                international_label = True
                            customs = []
                            if international_label:
			    	for each_move_lines in move_lines:
                               	    weight_net = each_move_lines.product_id.product_tmpl_id.weight_net and each_move_lines.product_id.product_tmpl_id.weight_net*16 >= 1.0 and each_move_lines.product_id.product_tmpl_id.weight_net*16*each_move_lines.product_qty or 1.0
#                                weight_net = shippingresp_lnk.picking_id.weight_package
                                    customs.append(endicia.Customs(each_move_lines.product_id.name, int(each_move_lines.product_qty), int(round(weight_net)), move_line.product_id.product_tmpl_id.list_price, shipper.country_code))
                  
                               # customs.append(endicia.Customs(each_move_lines.product_id.name, int(each_move_lines.product_qty), int(round(weight_net)), each_move_lines.product_id.product_tmpl_id.list_price, shipper.country_code))
                            try:
                                print "customs"
                                ship_endicia = self.pool.get('shipping.endicia').get_endicia_info(cr,uid,context)
                                request = endicia.LabelRequest(ship_endicia.requester_id, ship_endicia.account_id, ship_endicia.passphrase, ship_endicia.label_type if not international_label else 'International', ship_endicia.label_size, ship_endicia.image_format, ship_endicia.image_rotation,package, shipper, receipient, debug=ship_endicia.test, destination_confirm = True if shippingresp_lnk.name == 'First-Class Mail' and shippingresp_lnk.picking_id.container_usps == 'Letter' else False,customs_info=customs)
                                response = request.send()
                                endicia_res = response._get_value()
                            except Exception, e:
                                if error:
                                    raise osv.except_osv(_('Error'), _('%s' % (e,)))
                                else:
                                    return False
                            tracking_no=stockpicking_obj.create_attachment_for_usps(cr,uid,[shippingresp_lnk.picking_id.id],ship_endicia,endicia_res,context)

                            if tracking_numbers:
                                    tracking_numbers=str(tracking_numbers)+" "+"/"+" "+str(tracking_no)
                            else:
                                    tracking_numbers=str(tracking_no)
                        if tracking_numbers:
                            rate = shippingresp_lnk.rate
                            stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':tracking_numbers, 'shipping_rate': rate, 'label_recvd': True})
                            self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':tracking_numbers})
                            ## code for MMH to write down the tracking number to the list
                            
                            ## code ends here

                            context['track_success'] = True
                            context['tracking_no'] = tracking_numbers
                elif shippingresp_lnk.type.lower() == 'fedex':                    
                    shippingfedex_obj = self.pool.get('shipping.fedex')
                    shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
                    if not shippingfedex_id:
                        raise osv.except_osv(_('Warning'), _('Default Fedex settings not defined'))
                    else:
                        shippingfedex_id = shippingfedex_id[0]
                    fedex_servicedetails = stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id)
                    if shippingresp_lnk.name in ('INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY'):
                        if not fedex_servicedetails.customsvalue and not fedex_servicedetails.currency_id:
                            raise osv.except_osv(_('Warning'), _('Please enter Amount and Currency values'))
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
                    # REGULAR_PICKUP, REQattachUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION                    
                    shipment.RequestedShipment.DropoffType = fedex_servicedetails.dropoff_type_fedex #'REGULAR_PICKUP'
                    # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
                    # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
                    #shipment.RequestedShipment.ServiceType = fedex_servicedetails.service_type_fedex #'PRIORITY_OVERNIGHT'
                    shipment.RequestedShipment.ServiceType = shippingresp_lnk.name #'PRIORITY_OVERNIGHT'
                    # What kind of package this will be shipped in.
                    # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
                    shipment.RequestedShipment.PackagingType = fedex_servicedetails.package_type_fedex.name
                    # No idea what this is.
                    # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
                    # shipment.RequestedShipment.PackageDetail = fedex_servicedetails.package_detail_fedex #'INDIVIDUAL_PACKAGES'
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
                    #This indicates number of packages
#                    shipment.RequestedShipment.PackageCount = int(number_of_packages) - 1
                    tracking_lines = shippingresp_lnk.picking_id.tracking_ids
                    if not tracking_lines :
                        raise osv.except_osv(_('Warning!'), _('Please enter Fedex Dimmensions.'),)
                    shipment.RequestedShipment.PackageCount = len(tracking_lines) - 1
                    package1 = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                    package1_weight = shipment.create_wsdl_object_of_type('Weight')
                    # Weight, in pounds.
                    package1_weight.Value = fedex_servicedetails.weight_package if fedex_servicedetails.weight_package else fedex_servicedetails.weight #1.0
                    package1_weight.Units = "LB"
                    package1.Weight = package1_weight
                    package1.PhysicalPackaging = fedex_servicedetails.physical_packaging_fedex
                    # Un-comment this to see the other variables you may set on a package.
                    # This adds the RequestedPackageLineItem WSDL object to the shipment. It
                    # increments the package count and total weight of the shipment for you.
                    shipment.add_package(package1)
                    # If you'd like to see some documentation on the ship service WSDL, un-comment
                    # this line. (Spammy).                    
                    move_lines = shippingresp_lnk.picking_id.move_lines
                    pack_weight_merge={}
                    pack_id=[]
                    count=0
                    for each_move_lines in move_lines:
                        tracking_id=each_move_lines.package_track_id
                        if each_move_lines.weight <= 0.0:
                            raise osv.except_osv(_('Warning'), _('Please assign weight to each order lines'),)
                        else:
                            if tracking_id:
                                val=pack_weight_merge.get(tracking_id.id,False)
                                if val:
                                    val = float(each_move_lines.weight) + float(val)
                                    pack_weight_merge[tracking_id.id]=val
                                else:
                                    pack_weight_merge[tracking_id.id]=each_move_lines.weight
                                    pack_id.append(tracking_id)
                    if tracking_lines:
                        if len(tracking_lines)>=1:
                            master_track_id=''
                            trcaking_numbers=''
                            count=0
                            for each_tracking_lines in tracking_lines:
                                package1_dimension = shipment.create_wsdl_object_of_type('Dimensions')
                                package1_dimension.Length=int(each_tracking_lines.length_ups)
                                package1_dimension.Width=int(each_tracking_lines.width_ups)
                                package1_dimension.Height=int(each_tracking_lines.height_ups)
                                package1_dimension.Units='IN'
                                package1.Dimensions=package1_dimension
                                if count<=0:
                                    count=count+1
                                    package1.SequenceNumber=count
                                    master_track_id = self.send_label_request(cr,uid,ids,shipment, len(tracking_lines),count, context)
                                    trcaking_numbers=master_track_id
                                else:
                                    count=count+1
                                    package1.SequenceNumber=count
                                    track_id_element = shipment.create_wsdl_object_of_type('TrackingId')
                                    track_id_element.TrackingNumber=master_track_id
                                    shipment.RequestedShipment.MasterTrackingId = track_id_element
                                    child_track_id = self.send_label_request(cr,uid,ids,shipment, len(tracking_lines),count, context)
                                    trcaking_numbers=trcaking_numbers+';'+child_track_id
                            stockpickingwrite_result = stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':str(trcaking_numbers),'label_recvd': True})
                            if shippingresp_lnk.picking_id.sale_id :
                                self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':trcaking_numbers})
                elif shippingresp_lnk.type.lower() == 'ups':
                    ####################Number of pack wise weight#################
                    move_lines = shippingresp_lnk.picking_id.move_lines
                    pack_weight_merge = []
                    pack_id=[]
                    for each_move_lines in move_lines:
                        if each_move_lines.weight <= 0.0:
                            raise osv.except_osv(_('Warning'), _('Please assign weight to each order lines'),)
                        else:
                            pack_weight_merge.append(each_move_lines.weight)
                    shipping_account=shippingresp_lnk.picking_id.sale_id.shipping_account
                    if shipping_account=='my_account':
                        ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=shippingresp_lnk.picking_id.partner_id.id
                        ups_info=res_partner_obj.get_ups_info(cr,uid,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
                    ####################For Each UPS seperate dimension#################                    
                    tracking_lines = shippingresp_lnk.picking_id.tracking_ids
                    length_merge=[]
                    width_merge=[]
                    height_merge=[]
                    if tracking_lines:
                        for each_tracking_lines in tracking_lines:
                            length_ups = each_tracking_lines.length_ups
                            length_merge.append(length_ups)
                            width_ups = each_tracking_lines.width_ups
                            width_merge.append(width_ups)
                            height_ups = each_tracking_lines.height_ups
                            height_merge.append(height_ups)
                    else:
                            raise osv.except_osv(_('Warning'), _('Please assign UPS Dimmensions!'),)                    
                    stockpicking_obj = self.pool.get('stock.picking')
                    pickup_type_ups = shippingresp_lnk.picking_id.pickup_type_ups                    
                    for key, value in ups_service_type.items():
                         if value == shippingresp_lnk.name:
                                service_code = key
                    service_type_ups = service_code
                    package_type_ups = shippingresp_lnk.picking_id.package_type_ups.ups_value                    
                    desc = shippingresp_lnk.picking_id.name                    
                    ups = shippingservice.UPSShipmentConfirmRequest(ups_info, pickup_type_ups, service_type_ups, package_type_ups, weight, shipper, receipient,length_merge,width_merge,height_merge,pack_weight_merge,shipping_account,desc)
                    ups_response = ups.send()                                                        
                    ups = shippingservice.UPSShipmentAcceptRequest(ups_info, ups_response.shipment_digest,shipping_account)
                    ups_response = ups.send()
                    stockpicking_obj.create_attachment(cr,uid,[shippingresp_lnk.picking_id.id],ups_response,context)
                    tracking_number=''
                    all_tracking_number=''
                    for i in range(0,ups_response.package_count):
                        label_image = ups_response.graphic_image[i]
                        tracking_number=ups_response.tracking_number[i]                        
                        if i == 0:
                            all_tracking_number +=ups_response.tracking_number[i]
                        else:
                            all_tracking_number +=',' + ups_response.tracking_number[i]                    
                    stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':all_tracking_number,'shipping_label':binascii.b2a_base64(str(b64decode(label_image))), 'shipping_rate': rate, 'label_recvd': True})                    
                    self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':all_tracking_number})
                    context['track_success'] = True
                    context['tracking_no'] = ups_response.tracking_number
            else:
                raise osv.except_osv(_('Warning !'),_("This shipping quotes has been already accepted"))

        except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
        ### Check Availability; Confirm; Validate : Automate Process Now step
        if context.get('track_success',False):
            ### Assign Carrier to Delivery carrier if user has not chosen
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
                    raise osv.except_osv(_('Warning'), _('Delivery Method for this service type not defined'))
                return False
            self.pool.get('stock.picking').write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_id':carrier_ids[0]})
            if shippingresp_lnk.picking_id.sale_id :
                saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{ 'carrier_id':carrier_ids[0]})
            ### Write this shipping respnse is selected
            self.write(cr,uid,ids[0],{'selected':True})            
            if context.get('batch_printing',False):
                return True
            return True
        else:
            return False

    def send_label_request(self,cr,uid,ids,shipment,pack_count, count='',context={}, error=True):
        shippingresp_lnk=self.browse(cr,uid,ids[0])
        saleorder_obj = self.pool.get('sale.order')
        stockpicking_obj = self.pool.get('stock.picking')
        try:
            shipment.send_request()
        except Exception, e:
            if error:
                raise osv.except_osv(_('Error'), _('%s' % (e,)))
        # This will show the reply to your shipment being sent. You can access the
        # attributes through the response attribute on the request object. This is
        # good to un-comment to see the variables returned by the Fedex reply.        
        # Here is the overall end result of the query.
        # Getting the tracking number from the new shipment.
        fedexTrackingNumber = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber        
        # Net shipping costs.
        fedexshippingrate = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount
        # Get the label image in ASCII format from the reply. Note the list indices
        # we're using. You'll need to adjust or iterate through these if your shipment
        # has multiple packages.
        ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
        """
        #This is an example of how to dump a label to a PNG file.
        """
        # This will be the file we write the label out to.
        if pack_count and pack_count > 0:
            label_name='Packing List'+' '+str(count)
        else:
            label_name='Packing List'
        fedex_attachment_pool = self.pool.get('ir.attachment')
        fedex_data_attach = {
            'name': label_name,
            'datas': binascii.b2a_base64(str(b64decode(ascii_label_data))),
            'description': 'Packing List',
            'res_name': shippingresp_lnk.picking_id.name,
            'res_model': 'stock.picking.out',
            'res_id': shippingresp_lnk.picking_id.id,
        }
        fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
        if fedexTrackingNumber:
            stockpickingwrite_result = stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':fedexTrackingNumber, 'shipping_label':binascii.b2a_base64(str(b64decode(ascii_label_data))), 'shipping_rate': fedexshippingrate, 'label_recvd': True})
            if shippingresp_lnk.picking_id.sale_id:
                self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':fedexTrackingNumber})
            context['track_success'] = True
        if context.get('track_success',False):
            type_fieldname = ''
            if shippingresp_lnk.type.lower() == 'fedex':
                type_fieldname = 'is_fedex'
            carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',shippingresp_lnk.name),(type_fieldname,'=',True)])
            if not carrier_ids:
                if error:
                    raise osv.except_osv(_('Warning!'), _('Delivery Method for this service type not defined'))
                return False
            self.pool.get('stock.picking').write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_id':carrier_ids[0]})
            if shippingresp_lnk.picking_id.sale_id:
                saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{ 'carrier_id':carrier_ids[0]})
            ### Write this shipping respnse is selected
            self.write(cr,uid,ids[0],{'selected':True})
        if pack_count and pack_count >= 0:
            return fedexTrackingNumber
        else:
            return True

        
    _order = 'sr_no'

    _columns = {
        'name': fields.char('Service Type', size=100, readonly=True),
        'type': fields.char('Shipping Type', size=64, readonly=True),
        'rate': fields.char('Rate', size=64, readonly=True),
        'weight' : fields.float('Weight'),
        'cust_default' : fields.boolean('Customer Default'),
        'sys_default' : fields.boolean('System Default'),
        'sr_no' : fields.integer('Sr. No'),
        'selected' : fields.boolean('Selected'),
        'picking_id' : fields.many2one('stock.picking','Picking'),
        'sale_order_id':fields.many2one('sale.order','Order')
    }
    _defaults = {
        'sr_no': 9,
        'selected': False
    }
shipping_response()

def _get_shipping_type(self, cr, uid, context=None):
    return [
        ('All','All'),
        ('Canada Post','Canada Post'),
        ('Fedex','Fedex'),
        ('UPS','UPS'),
        ('USPS','USPS'),

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


class pack_track(osv.osv):
    _name = 'pack.track'
    _columns = {
        'name':fields.char('Pack Name',size=120),
        'width_ups' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
        'length_ups' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
        'height_ups' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),
        'picking_id' : fields.many2one('stock.picking','Picking', ondelete="cascade"),
        'package_id': fields.many2one('product.packaging','Package Name'),
        'girth_usps':fields.float('Girth USPS',digits_compute= dp.get_precision('Stock Weight')),
        'shipping_type':fields.related('picking_id','shipping_type',type='char',string='Shipping Type')
    }


    def onchange_package_id(self, cr, uid, ids, package_id,context=None):
        if not package_id:
            value = {'height_ups':0,'width_ups':0,'length_ups':0}
        else:
            package_data = self.pool.get('product.packaging').browse(cr, uid, package_id, context=context)
            value = {
                'height_ups':package_data.height,
                'width_ups':package_data.width,
                'length_ups':package_data.length,
            }
        return {'value':value}
    
pack_track()

class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def get_rates(self,cr,uid,ids,context={}):        
        shipping_obj = self.pool.get('shipping.method')
        shipping_record = shipping_obj.search(cr,uid,[])
        if not shipping_record:
            raise osv.except_osv(_("Warning"), _("Shipping settings are not done. Go to Warehouse/Configuration/Canada Post/Configuration"))
        total = ''
        gst =0.00
        hst =0.00
        pst =0.00
        self_brw = self.browse(cr,uid,ids[0])
        search_id = shipping_obj.search(cr,uid,[])
        if search_id:
            shipping_brw = shipping_obj.browse(cr,uid,search_id[0])
            name =  shipping_brw.name
            passwd =  shipping_brw.passwd
            environment = shipping_brw.environment
            co_no = shipping_brw.customer_num
            cana_wt = self_brw.weight_package
            cana_ln = self_brw.cana_length
            cana_wdth = self_brw.cana_width
            cana_ht = self_brw.cana_height
            service_code = self_brw.services
            zip_code_customer = self_brw.address_id.zip
            zip_code_supplier = shipping_brw.address.zip
            serv_code = service_code.service_code
            xml_request = """<?xml version="1.0" encoding="utf-8"?>
    <mailing-scenario xmlns="http://www.canadapost.ca/ws/ship/rate">
    <customer-number>%s</customer-number>
    <parcel-characteristics>
    <weight>%s</weight>
    <dimensions>
    <length>%s</length>
    <width>%s</width>
    <height>%s</height>
    </dimensions>
    </parcel-characteristics>
    <origin-postal-code>%s</origin-postal-code>
    <destination><domestic>
    <postal-code>%s</postal-code>
    </domestic>
    </destination>
    <services>
    <service-code>%s</service-code>
    </services>
    </mailing-scenario>

            """%(co_no,cana_wt,cana_ln,cana_wdth,cana_ht,zip_code_supplier,zip_code_customer,serv_code)
            result = connection.call(cr, uid, 'GetRates', name, passwd, environment,xml_request)
            for each in result:
                if each.get('base',False):
                    base = each.get('base',False)
                if each.get('gst',False):
                    gst = each.get('gst',False)
                if each.get('pst',False):
                    pst = each.get('pst',False)
                if each.get('hst',False):
                    hst = each.get('hst',False)
                base = float(base)
                gst = float(gst)
                pst = float(pst)
                hst = float(hst)
                total = gst+pst+hst
                t1 = str(total)
                b1 = str(base)
                g1 = str(gst)
                p1 = str(pst)
                h1 = str(hst)
                shipping_rate = "Base Price : "+b1+"\n"+"Taxes : "+t1+"\n\t"+"gst : "+g1+"\n\t"+"pst : "+p1+"\n\t"+"hst : "+h1+"\n\t"
        cr.execute("UPDATE stock_picking SET rates='%s' where id=%d"%(shipping_rate,ids[0],))
        return True

    def cana_generate_shipping(self,cr,uid,ids,context={}):        
        shipping_obj = self.pool.get('shipping.method')
        shipping_record = shipping_obj.search(cr,uid,[])
        self_brw = self.browse(cr, uid, ids[0])
        if not shipping_record:
            raise osv.except_osv(_("Warning"), _("Shipping settings are not done. Go to Warehouse/Configuration/Canada Post/Configuration"))
        rt = self.browse(cr, uid, ids[0]).rates
        rt=(rt.split('\n')[0]).split(':')[1]        
        if not rt:
            raise osv.except_osv(_("Warning"), _("First Get Rates on clicking 'Get Rates' button"))
        shipping_obj = self.pool.get('shipping.method')
        search_id = shipping_obj.search(cr,uid,[])
        if search_id:
            shipping_brw = shipping_obj.browse(cr,uid,search_id[0])
            name =  shipping_brw.name
            passwd =  shipping_brw.passwd
            environment = shipping_brw.environment
            serv_code = self_brw.services.service_code
            comp_sender = shipping_brw.address.name
            phone_no = shipping_brw.address.phone
            street_name = shipping_brw.address.street
            city_name = shipping_brw.address.city
            supplier_zip = shipping_brw.address.zip
        comp_rec = self_brw.partner_id.name
        rec_name = self_brw.partner_id.name
        rec_street = self_brw.partner_id.street
        rec_city = self_brw.partner_id.city
        rec_zip = self_brw.partner_id.zip
        cana_wt = self_brw.weight_package
        cana_ln = self_brw.cana_length
        cana_wdth = self_brw.cana_width
        cana_ht = self_brw.cana_height
        xml_request = """<?xml version="1.0" encoding="utf-8"?>
<non-contract-shipment xmlns="http://www.canadapost.ca/ws/ncshipment">
<delivery-spec>
<service-code>%s</service-code>
<sender>
<company>%s</company>
<contact-phone>%s</contact-phone>
<address-details>
<address-line-1>%s</address-line-1>
<city>%s</city>
<prov-state>%s</prov-state>
<postal-zip-code>%s</postal-zip-code>
</address-details>
</sender>
<destination>
<name>%s</name>
<company>%s</company>
<address-details>
<address-line-1>%s</address-line-1>
<city>%s</city>
<prov-state>%s</prov-state>
<country-code>%s</country-code>
<postal-zip-code>%s</postal-zip-code>
</address-details>
</destination>
<parcel-characteristics>
<weight>%s</weight>
<dimensions>
<length>%s</length>
<width>%s</width>
<height>%s</height>
</dimensions>
</parcel-characteristics>
<preferences>
<show-packing-instructions>%s</show-packing-instructions>
</preferences>
</delivery-spec>
</non-contract-shipment>"""%(serv_code,comp_sender,phone_no,street_name,city_name,'ON',supplier_zip,rec_name,rec_name,rec_street,rec_city,'ON', 'CA',rec_zip,cana_wt,cana_ln,cana_wdth,cana_ht,'true',)
        result = connection.call(cr, uid, 'GetShipping', name, passwd, environment, xml_request)
        track_num=result.get('tracking_no',False)
        carrier_services = self_brw.services.name
        id1 = self.pool.get('delivery.carrier').search(cr, uid, [('name','=', 'Canada Post' + ' '+carrier_services)])
        stock_origin = self_brw.origin
        sale_id = self.pool.get('sale.order').search(cr, uid, [('name', '=', stock_origin)])
        if id1 and track_num:
            cr.execute("UPDATE stock_picking SET carrier_tracking_ref='%s',carrier_id=%d,label_recvd=True, shipping_rate='%s' where id=%d"%(track_num,id1[0],rt,ids[0],)) 
            if sale_id:
                cr.execute("UPDATE sale_order SET tracking_no=%s,carrier_id=%d where id = %s"%(track_num, id1[0],sale_id[0]))
        link=result.get('link',False)
        if link:
            urldat = urlparse.urlparse(link)
            if urldat:
                link = urldat[2]
            result_pdf = connection.call(cr, uid, 'Getartifact', name, passwd, environment, link)
            self.create_attachment_can(cr,uid,ids,result_pdf)
        return True
    
    def create_attachment_can(self, cr, uid, ids, vals, context={}):        
        attachment_pool = self.pool.get('ir.attachment')
        data_attach = {
            'name': 'PackingList1.pdf' ,
            'datas': binascii.b2a_base64(vals),
            'description': 'Packing1 List',
            'res_name': self.browse(cr,uid,ids[0]).name,
            'res_model': 'stock.picking.out',
            'res_id': ids[0],
        }
        attach_id = attachment_pool.search(cr,uid,[('res_id','=',ids[0]),('res_name','=',self.browse(cr,uid,ids[0]).name)])
        if not attach_id:
            attach_id = attachment_pool.create(cr, uid, data_attach)
        else:
            attach_id = attach_id[0]
            attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
        return attach_id

    def action_assign_new(self, cr, uid, ids, *args):
        """ Changes state of picking to available if all moves are confirmed.
        @return: True
        """        
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
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

    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, package_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, sys_default=False,cust_default=False, error=True, context=None,fed_length=None,fed_width=None,fed_height=None):
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
        # This is very generalized, top-level information.
        # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
        rate_request.RequestedShipment.DropoffType = dropoff_type_fedex
        # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
        # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
        rate_request.RequestedShipment.ServiceType = service_type_fedex
        # What kind of package this will be shipped in.
        # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
        rate_request.RequestedShipment.PackagingType = package_type_fedex
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
        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
        package1_weight = rate_request.create_wsdl_object_of_type('Weight')
        package1_weight.Value = weight
        package1_weight.Units = "LB"
        package1_dimensions=rate_request.create_wsdl_object_of_type('Dimensions')
        package1_dimensions.Length=int(fed_length)
        package1_dimensions.Width=int(fed_width)
        package1_dimensions.Height=int(fed_height)
        package1_dimensions.Units="IN"
        package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
        package1.Weight = package1_weight
        package1.Dimensions = package1_dimensions
        #can be other values this is probably the most common
        package1.PhysicalPackaging = physical_packaging_fedex
        # Un-comment this to see the other variables you may set on a package.        
        # This adds the RequestedPackageLineItem WSDL object to the rate_request. It
        # increments the package count and total weight of the rate_request for you.
        rate_request.add_package(package1)
        # If you'd like to see some documentation on the ship service WSDL, un-comment
        # this line. (Spammy).        
        # Un-comment this to see your complete, ready-to-send request as it stands
        # before it is actually sent. This is useful for seeing what values you can
        # change.        
        # Fires off the request, sets the 'response' attribute on the object.
        try:
            rate_request.send_request()
        except Exception, e:
            if error:
#                raise Exception('%s' % (e))
                raise osv.except_osv(_('Warning !'),_('%s'%(e)))
            return False
        # This will show the reply to your rate_request being sent. You can access the
        # attributes through the response attribute on the request object. This is
        # good to un-comment to see the variables returned by the FedEx reply.        
        # Here is the overall end result of the query.        
#        for detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#            for surcharge in detail.ShipmentRateDetail.Surcharges:
#                if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
##                    _logger.info("ODA rate_request charge: %s", surcharge.Amount.Amount)
#        for rate_detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#            _logger.info("Net FedEx Charge: %s %s", rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount)
        sr_no = 9
        sys_default_value = False
        cust_default_value = False
        if sys_default:
            sys_default_vals = sys_default.split('/')
            if sys_default_vals[0] == 'FedEx':
                sys_default_value = True
                sr_no = 2
        if cust_default:
            cust_default_vals = cust_default.split('/')
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
        if fedex_res_id:
            return True
        else:
            return False

    def create_quotes(self, cr, uid, ids, values, context={}):
        res_id = 0
        for vals in values.postage:
            vals['Service']=vals['Service'].split('&')[0]
            quotes_vals = {
                'name' : vals['Service'],
                'type' : context['type'],
                'rate' : vals['Rate'],
                'picking_id' : ids[0], #Change the ids[0] when switch to create
                'weight' : values.weight,
                'sys_default' : False,
                'cust_default' : False,
                'sr_no' : vals['sr_no'],
            }
            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
        if res_id:
            return True
        else:
            return False

    def create_attachment(self, cr, uid, ids, vals, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        pdf_attach=[]
        for i in range(0,vals.package_count):
            data_attach = {
                    'name': 'UpsLabel_'+str(i+1)+'.'+ vals.image_format.lower() ,
                    'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image[i]))),
                    'description': 'Packing List',
                    'res_name': self.browse(cr,uid,ids[0]).name,
                    'res_model': 'stock.picking.out',
                    'res_id': ids[0],
                }               
            datas=data_attach['datas']
            pdf_attach.append(datas)
            attach_id = attachment_pool.create(cr, uid, data_attach)
        return attach_id


    ## This function is called when the button is clicked
    def generate_shipping(self, cr, uid, ids, context={}):        
        default_ship_obj = self.pool.get('sys.default.shipping')
        if context is None:
            context = {}
        for id in ids:
            try:
                stockpicking = self.browse(cr,uid,id)
                shipping_type = stockpicking.shipping_type
                type = stockpicking.type
                weight = stockpicking.weight_package if stockpicking.weight_package else stockpicking.weight
                weight_unit='LB'
                if weight<=0.0:
                    raise osv.except_osv(_("Warning !"),_("Package Weight Invalid!"))
                ###based on stock.picking type
                if type == 'out':
                    shipper_address = stockpicking.sale_id and stockpicking.sale_id.shop_id and stockpicking.sale_id.shop_id.warehouse_id.partner_id or False
                elif type == 'in':
                    shipper_address = stockpicking.address_id
                if not shipper_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise osv.except_osv(_("Warning !"),_("Shop Address not defined!"))
                    else:
                        return False
                if not (shipper_address.name or shipper_address.partner_id.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
                if not shipper_address.street:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Street."))
                if not shipper_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
                if not shipper_address.state_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper State Code."))
                if not shipper_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
                if not shipper_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
                shipper = Address(shipper_address.name or shipper_address.partner_id.name, shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.partner_id.name)
                ### Recipient
                ###based on stock.picking type
                if type == 'out':
                    cust_address = stockpicking.alt_address or stockpicking.address_id
                elif type == 'in':
                    cust_address = stockpicking.sale_id and stockpicking.sale_id.shop_id and stockpicking.sale_id.shop_id.warehouse_id.partner_id or False
                if not cust_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise osv.except_osv(_('Warning !'),_("Reciepient Address not defined!"))
                    else:
                        return False
                if not (cust_address.name or cust_address.partner_id.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
                if not cust_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
                receipient = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)
                # Deleting previous quotes
                shipping_res_obj = self.pool.get('shipping.response')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('picking_id','=',ids[0])])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)
                saleorderline_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',stockpicking.sale_id.id)])
                sys_default = default_ship_obj._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                context['sys_default'] = sys_default
                cust_default = default_ship_obj._get_cust_default_shipping(cr,uid,stockpicking.carrier_id.id,context)
                context['cust_default'] = cust_default
                #generating FeDex and UPS dimmension based on type of shipping
                if not stockpicking.tracking_ids:
                    tracking_data = {}
                    if stockpicking.shipping_type == 'Fedex' and stockpicking.package_type_fedex :
                        package_type_data = stockpicking.package_type_fedex
                        tracking_data.update({
                        'package_name':package_type_data.name,
                        'length_ups':package_type_data.length,
                        'width_ups':package_type_data.width,
                        'height_ups':package_type_data.height,
                        'picking_id':stockpicking.id,
                        })
                    if stockpicking.shipping_type == 'UPS' and stockpicking.package_type_ups :
                        package_type_data = stockpicking.package_type_ups
                        tracking_data.update({
                        'package_name':package_type_data.name,
                        'length_ups':package_type_data.length,
                        'width_ups':package_type_data.width,
                        'height_ups':package_type_data.height,
                        'picking_id':stockpicking.id,
                        })
                    self.pool.get('pack.track').create(cr, uid, tracking_data, context=context)
                if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
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

                if shipping_type == 'UPS' or shipping_type == 'All':
                    ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)                    
                    pickup_type_ups = stockpicking.pickup_type_ups
                    service_type_ups = stockpicking.service_type_ups
                    package_type_ups = stockpicking.package_type_ups.ups_value                    
                    ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups, package_type_ups, weight, shipper, receipient, cust_default, sys_default)
                    ups_response = ups.send()                    
                    context['type'] = 'UPS'
                    self.create_quotes(cr,uid,ids,ups_response,context)

                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = stockpicking.dropoff_type_fedex
                    service_type_fedex = stockpicking.service_type_fedex
                    package_type_fedex = stockpicking.package_type_fedex
                    package_detail_fedex = stockpicking.package_detail_fedex
                    payment_type_fedex = stockpicking.payment_type_fedex
                    physical_packaging_fedex = stockpicking.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    fed_length = stockpicking.pack_length
                    fed_width = stockpicking.pack_width
                    fed_height = stockpicking.pack_height
                    error_required = True
                    shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,package_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context,fed_length,fed_width,fed_height)
            except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
            return True

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
    
    def _get_euro(self, cr, uid, context=None):        
        try:
            return self.pool.get('res.currency').search(cr, uid, [('name','=','USD')])[0]
        except:
            return False

    def create(self, cr, uid, vals, context=None):                        
        new_id = super(stock_picking, self).create(cr, uid, vals=vals, context=context)
        print "valsss",vals
        stock_data = self.browse(cr, uid, new_id, context=context)
        # added to calculate weight for sale order line product.        
        if vals.get('weight_package',False):
            weight = vals.get('weight_package',False)
            self.write(cr, uid, [new_id], {'weight_package':weight}, context=context)
        else:            
            self._cal_weight_stock(cr, uid, [new_id], context)
        # added to fill FedEx/UPS dimmension
        if stock_data.use_shipping :
            tracking_data = {}
            if stock_data.shipping_type == 'Fedex' and stock_data.package_type_fedex :
                package_type_data = stock_data.package_type_fedex
                tracking_data.update({
                'name':package_type_data.name,
                'length_ups':package_type_data.length,
                'width_ups':package_type_data.width,
                'height_ups':package_type_data.height,
                'picking_id':new_id,
                })
            if stock_data.shipping_type == 'UPS' and stock_data.package_type_ups :
                package_type_data = stock_data.package_type_ups
                tracking_data.update({
                'name':package_type_data.name,
                'length_ups':package_type_data.length,
                'width_ups':package_type_data.width,
                'height_ups':package_type_data.height,
                'picking_id':new_id,
                })
            self.pool.get('pack.track').create(cr, uid, tracking_data, context=context)
            # added to transfer label attachment from sale to delivery
            if stock_data.sale_id:
                sale_id = stock_data.sale_id.id
                attachment_pool = self.pool.get('ir.attachment')
                attachment_id = attachment_pool.search(cr, uid, [('res_model','=','sale.order'),('res_id','=',sale_id)])
                if attachment_id :
                    attachment_data = attachment_pool.browse(cr, uid, attachment_id[0])                    
                    data_attach = {
                        'name': attachment_data.name or '',
                        'datas': attachment_data.datas,
                        'description': 'Packing List',
                        'res_name': stock_data.name,
                        'res_model': 'stock.picking.out',
                        'res_id': new_id,
                    }
                    attachment_pool.create(cr, uid, data_attach)
        return new_id

    def _cal_weight_stock(self, cr, uid, ids, context=None):
        for each_picking in self.browse(cr, uid, ids, context=context):
            move_line_obj=self.pool.get('stock.move')
            line_items=move_line_obj.search(cr, uid, [('picking_id','=',each_picking.id)])
            total_weight = 0.00
            for move in line_items:
                weight=move_line_obj.browse(cr,uid,move).product_id.weight
                product_type=move_line_obj.browse(cr,uid,move).product_id.type
                if weight<=0.00 and product_type != 'service':
                    raise osv.except_osv(_('Warning'), _('Weight not defined for %s' % move_line_obj.browse(cr,uid,move).product_id.name))
                else:
                    total_weight += weight * move_line_obj.browse(cr,uid,move).product_qty or 0.0
            self.write(cr,uid,each_picking.id,{'weight_package':total_weight})
        return True

    _columns = {
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=320,readonly=True),
        'shipping_process': fields.selection([
                                ('draft', 'Open'),
                                ('marked', 'Marked for Packing'),
                                ('partial', 'Awaiting Goods'),
                                ('wait', 'Order on Hold'),
                                ('printed', 'Packing List Printed'),
                                ('barcode', 'Waiting for Scanning'),
                                ('labels_printed','Shipping Labels Printed'),
                                ('done', 'Done'),
                                ('cancel', 'Cancelled')
                                ], 'Shipping Process', readonly=True),
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
		('FIRST_OVERNIGHT','FIRST_OVERNIGHT'),
		('GROUND_HOME_DELIVERY','GROUND_HOME_DELIVERY'),
		('INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY'),
		('INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_ECONOMY_FREIGHT'),
		('INTERNATIONAL_FIRST','INTERNATIONAL_FIRST'),
		('INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY'),
		('INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_PRIORITY_FREIGHT'),
		('INTERNATIONAL_GROUND','INTERNATIONAL_GROUND'),
           ],'Service Type'),        
        'package_type_fedex':fields.many2one('shipping.package.type.fedex','Packaging Type',help="What kind of package this will be shipped in"),
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
                ('OTHER','OTHER'),
                ('BAG','BAG'),
                ('BARREL','BARREL'),
                ('BOX','BOX'),
                ('BUCKET','BUCKET'),
                ('BUNDLE','BUNDLE'),
                ('CARTON','CARTON'),
                ('TANK','TANK'),
                ('TUBE','TUBE'),
                ('BASKET','BASKET'),
                ('CASE','CASE'),
                ('CONTAINER','CONTAINER'),
                ('CRATE','CRATE'),
                ('CYLINDER','CYLINDER'),
                ('DRUM','DRUM'),
                ('ENVELOPE','ENVELOPE'),
                ('HAMPER','HAMPER'),
                ('PAIL','PAIL'),
                ('PALLET','PALLET'),
                ('PIECE','PIECE'),
                ('REEL','REEL'),
                ('ROLL','ROLL'),
                ('SKID','SKID'),
                ('TANK','TANK'),
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
        'package_type_ups':fields.many2one('shipping.package.type.ups','Packaging Type'),
        'shipping_label' : fields.binary('Logo'),
        'shipping_rate': fields.float('Shipping Rate',readonly=True),
        'response_usps_ids' : fields.one2many('shipping.response','picking_id','Shipping Response'),
        'label_recvd': fields.boolean('Shipping Label', readonly=True),
        'tracking_ids' : fields.one2many('pack.track','picking_id','Tracking Details'),
        'pack_length': fields.integer('Length', required=True),
        'pack_width': fields.integer('Width', required=True),
        'pack_height': fields.integer('Height', required=True),
        'checkbox': fields.boolean('Canada Post'),
        'services': fields.many2one('service.name', 'Services'),
        'cana_length': fields.float('Length', digits=(16,2)),
        'cana_width': fields.float('Width', digits=(16,2)),
        'cana_height': fields.float('Height', digits=(16,2)),
        'rates': fields.text('Rates', size=1000),
        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits'),
        'customsvalue':fields.float('Custom Values'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'ware_id' : fields.many2one('stock.warehouse','Warehouse'),
#        'shipping_account':fields.selection([('my_account','My Account')],'Shipping Account'),
        'shipping_account':fields.selection([('my_account','My Account'),('customer_account','Partner Account')],'Shipping Account'),   #enchancement for customer shipping account
   }



    _defaults = {
        'use_shipping' : True,
        'service_type_usps' : 'All',
        'size_usps' : 'REGULAR',
        'dropoff_type_fedex' : 'REGULAR_PICKUP',
        'service_type_fedex' : 'FEDEX_GROUND',
        'package_detail_fedex' : 'INDIVIDUAL_PACKAGES',
        'payment_type_fedex' : 'SENDER',
        'physical_packaging_fedex' : 'BOX',
        'pickup_type_ups' : '01',
        'service_type_ups' : '03',
        'pack_length' : 0,
        'pack_width' : 0,
        'pack_height' : 0,
        'weight_unit':'LB',
        'currency_id':_get_euro,
        'shipping_account':'my_account',

    }
    
    # over-rided to avoid delivery grid warning
    def _prepare_shipping_invoice_line(self, cr, uid, picking, invoice, context=None):
        """Prepare the invoice line to add to the shipping costs to the shipping's
           invoice.

            :param browse_record picking: the stock picking being invoiced
            :param browse_record invoice: the stock picking's invoice
            :return: dict containing the values to create the invoice line,
                     or None to create nothing
        """        
        return {}
    
    def copy_data(self, cr, uid, ids, default, context=None):
        if context is None:
            context = {}
        print "////////////////////////////"
#        default.update({'carrier_id':'','shipping_type':False, 'weight_package':'', 'response_usps_ids': '','shipping_rate':'', 'pl_batch_number':'', 'shipping_process':'draft','sale_id':'' ,'label_recvd':False, 'print_date':False})
        return super(stock_picking, self).copy_data(cr, uid, ids, default,context=context)

    def create_attachment_usps(self, cr, uid, ids, vals, count,context={}):
        attachment_pool = self.pool.get('ir.attachment')
        stockpicking_obj = self.pool.get('stock.picking')
        shippingresp_lnk = self.browse(cr,uid,ids[0])
        label_name='PackingList' + str(count)
        data_attach = {
            'name': label_name + '.'+vals.image_format.lower() ,   ##changes done for multilabels
            'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image))),
            'description': label_name,
            'res_name': self.browse(cr,uid,ids[0]).name,
            'res_model': 'stock.picking.out',
            'res_id': ids[0],
        }
        attach_id = attachment_pool.create(cr, uid, data_attach)        
        if vals.tracking_number:
            return vals.tracking_number
        else:
            return True

    def create_attachment_for_usps(self,cr,uid,ids,ship_endicia,endicia_res,count):
        attachment_pool = self.pool.get('ir.attachment')
        shippingresp_lnk = self.browse(cr,uid,ids[0])
        data_attach = {
            'name': 'PackingList.' + ship_endicia.image_format.lower(),
            'datas': binascii.b2a_base64(str(endicia_res['label'])),
            'description': 'Packing List',
            'res_name': shippingresp_lnk.name,
            'res_model': 'stock.picking.out',
            'res_id': shippingresp_lnk.id,
        }
        attach_id = attachment_pool.create(cr, uid, data_attach)
        if endicia_res['tracking']:
            return endicia_res['tracking']
        else:
            return True
        return True

    def create_quotes_sales(self, cr, uid, ids, vals, context={}):              
        dict = vals.rate
        res_id=0
        for i in dict.iterkeys():            
            val_dict = dict[i]
            quotes_vals = {
                'name' : i,
                'type' : context['type'],
                'rate' :val_dict.get('rate'),
                'sale_order_id' : ids[0], #Change the ids[0] when switch to create
                'weight' :'',
                'sys_default' : False,
                'cust_default' : False,
                'sr_no' : '',
            }
            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
        if res_id:
            return True
        else:
            return False

    def create_quotes_stock(self, cr, uid, ids, vals, context={}):
        dict = vals.rate
        res_id=0
        for i in dict.iterkeys():
            val_dict = dict[i]
            quotes_vals = {
                'name' : i,
                'type' : context['type'],
                'rate' :val_dict.get('rate'),
                'picking_id' : ids[0], #Change the ids[0] when switch to create
                'weight' :'',
                'sys_default' : False,
                'cust_default' : False,
                'sr_no' : '',
            }
            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
        if res_id:
            return True
        else:
            return False

    def onchange_shipping_rates(self, cr, uid, ids, service_type,response_usps_ids,shipping_type,context=None):        
        if ids:
            width = self.browse(cr,uid,ids[0]).pack_width
            delete_att_vals = []
            if response_usps_ids != []:
                for res_id in response_usps_ids:
                    cr.execute('delete from shipping_response where id=%s',(res_id[1],))
                    cr.commit()

            ### Assign Carrier to Delivery carrier if user has not selected
            carrier_ids=''
            if shipping_type:
                if shipping_type.lower() == 'usps':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',service_type),('is_usps','=',True)])
                elif shipping_type.lower() == 'ups':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_code','=',service_type),('is_ups','=',True)])
                elif shipping_type.lower() == 'fedex':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',service_type),('is_fedex','=',True)])
                elif shipping_type.lower() == 'canada post':
                    canada_service_type=self.pool.get('service.name').browse(cr,uid,service_type).name
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('name','=',canada_service_type),('is_canadapost','=',True)])
                elif shipping_type.lower() == 'all':
                    canada_service_type=self.pool.get('service.name').browse(cr,uid,service_type).name
                    if canada_service_type:
                        service_type=canada_service_type
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,['|','|',('service_output','=',service_type),('name','=',service_type),('service_code','=',service_type)])
                if not carrier_ids:
                    raise osv.except_osv(_('Error'), _('Delivery Method is not defined for selected service type'))

                ### Write this shipping respnse is selected
            vals = {'response_usps_ids' : delete_att_vals,
                    'pack_length' : width,
                    'pack_width' : width,
                    'pack_height' : width,
                    'carrier_id':carrier_ids and carrier_ids[0] or ''
                    }
            return {'value':vals}
        return {'value':{}}

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
        'pack_track_id':fields.many2one('pack.track','Pack Assign'),
        'package_track_id':fields.many2one('product.packaging','Pack Assign'),
        }

    # inherited to pass pack_track_id within stock move
    def create(self, cr, uid, vals, context=None):
        if vals :
            pack_assign = vals.get('product_packaging',False)
            if pack_assign :
                vals.update({'package_track_id':pack_assign})
        move_id = super(stock_move, self).create(cr, uid, vals, context=context)
        stock_picking_obj = self.browse(cr, uid, move_id, context=context).picking_id
        return move_id
    #

stock_move()


class stock_picking_out(osv.osv):    
    _inherit = "stock.picking.out"
    def _get_shipping_type(self, cr, uid, context=None):
        return [
            ('All','All'),
            ('Canada Post','Canada Post'),
            ('Fedex','Fedex'),
            ('UPS','UPS'),
            ('USPS','USPS'),
        ]
    
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
		('FIRST_OVERNIGHT','FIRST_OVERNIGHT'),
		('GROUND_HOME_DELIVERY','GROUND_HOME_DELIVERY'),
		('INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY'),
		('INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_ECONOMY_FREIGHT'),
		('INTERNATIONAL_FIRST','INTERNATIONAL_FIRST'),
		('INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY'),
		('INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_PRIORITY_FREIGHT'),
		('INTERNATIONAL_GROUND','INTERNATIONAL_GROUND'),
           ],'Service Type'),        
        'package_type_fedex':fields.many2one('shipping.package.type.fedex','Packaging Type',help="What kind of package this will be shipped in"),
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
                ('OTHER','OTHER'),
                ('BAG','BAG'),
                ('BARREL','BARREL'),
                ('BOX','BOX'),
                ('BUCKET','BUCKET'),
                ('BUNDLE','BUNDLE'),
                ('CARTON','CARTON'),
                ('TANK','TANK'),
                ('TUBE','TUBE'),
                ('BASKET','BASKET'),
                ('CASE','CASE'),
                ('CONTAINER','CONTAINER'),
                ('CRATE','CRATE'),
                ('CYLINDER','CYLINDER'),
                ('DRUM','DRUM'),
                ('ENVELOPE','ENVELOPE'),
                ('HAMPER','HAMPER'),
                ('PAIL','PAIL'),
                ('PALLET','PALLET'),
                ('PIECE','PIECE'),
                ('REEL','REEL'),
                ('ROLL','ROLL'),
                ('SKID','SKID'),
                ('TANK','TANK'),
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
        'package_type_ups':fields.many2one('shipping.package.type.ups','Packaging Type'),
        'shipping_label' : fields.binary('Logo'),
        'shipping_rate': fields.float('Shipping Rate',readonly=True),
        'response_usps_ids' : fields.one2many('shipping.response','picking_id','Shipping Response'),
        'label_recvd': fields.boolean('Shipping Label', readonly=True),
        'tracking_ids' : fields.one2many('pack.track','picking_id','Tracking Details'),
        'pack_length': fields.integer('Length', required=True),
        'pack_width': fields.integer('Width', required=True),
        'pack_height': fields.integer('Height', required=True),
        'checkbox': fields.boolean('Canada Post'),
        'services': fields.many2one('service.name', 'Services'),
        'cana_length': fields.float('Length', digits=(16,2)),
        'cana_width': fields.float('Width', digits=(16,2)),
        'cana_height': fields.float('Height', digits=(16,2)),
        'rates': fields.text('Rates', size=1000),
        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits'),
        'customsvalue':fields.float('Custom Values'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'carrier_id':fields.many2one("delivery.carrier","Carrier"),
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=320,readonly=True),
        'shipping_process': fields.selection([
                                ('draft', 'Open'),
                                ('marked', 'Marked for Packing'),
                                ('partial', 'Awaiting Goods'),
                                ('wait', 'Order on Hold'),
                                ('printed', 'Packing List Printed'),
                                ('barcode', 'Waiting for Scanning'),
                                ('labels_printed','Shipping Labels Printed'),
                                ('done', 'Done'),
                                ('cancel', 'Cancelled')
                                ], 'Shipping Process', readonly=True),
        'ware_id' : fields.many2one('stock.warehouse','Warehouse'),
        'shipping_account':fields.selection([('my_account','My Account'),('customer_account','Partner Account')],'Shipping Account'),   #enchancement for customer shipping account
    }

    def create(self, cr, uid, vals, context=None):                                
        new_id = super(stock_picking_out, self).create(cr, uid, vals, context=context)
        stock_data = self.browse(cr, uid, new_id, context=context)
        # added to calculate weight for sale order line product.
        self._cal_weight_stock(cr, uid, [new_id], context)
        return new_id
    
    def copy_data(self, cr, uid, ids, default, context=None):
        if context is None:
            context = {}
#        default.update({'carrier_id':'','shipping_type':False, 'weight_package':'', 'response_usps_ids': '','shipping_rate':'', 'pl_batch_number':'', 'shipping_process':'draft','sale_id':'' ,'label_recvd':False, 'print_date':False})
        return super(stock_picking_out, self).copy_data(cr, uid, ids, default,context=context)

    def dummy_fun(self, cr, uid, ids, context=None):
        res = self._cal_weight_stock(cr, uid, ids, context)
        return True

    def _cal_weight_stock(self, cr, uid, ids, context=None):
        for each_picking in self.browse(cr, uid, ids, context=context):
            move_line_obj=self.pool.get('stock.move')
            line_items=move_line_obj.search(cr, uid, [('picking_id','=',each_picking.id)])
            total_weight = 0.00
            for move in line_items:
                weight=move_line_obj.browse(cr,uid,move).product_id.weight
                product_type=move_line_obj.browse(cr,uid,move).product_id.type
                if weight<=0.00 and product_type != 'service':
                    raise osv.except_osv(_('Warning'), _('Weight not defined for %s' % move_line_obj.browse(cr,uid,move).product_id.name))
                else:
                    total_weight += weight * move_line_obj.browse(cr,uid,move).product_qty or 0.0
            self.write(cr,uid,each_picking.id,{'weight_package':total_weight})
        return True

    def create_quotes(self, cr, uid, ids, values, context={}):
        res_id = 0
        for vals in values.postage:
            vals['Service']=vals['Service'].split('&')[0]
            quotes_vals = {
                'name' : vals['Service'],
                'type' : context['type'],
                'rate' : vals['Rate'],
                'picking_id' : ids[0], #Change the ids[0] when switch to create
                'weight' : values.weight,
                'sys_default' : False,
                'cust_default' : False,
                'sr_no' : vals['sr_no'],
            }
            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
        if res_id:
            return True
        else:
            return False
 
    def onchange_shipping_rates(self, cr, uid, ids, service_type,response_usps_ids,shipping_type,context=None):
        if ids:
            width = self.browse(cr,uid,ids[0]).pack_width
            delete_att_vals = []
            if response_usps_ids != []:
                for res_id in response_usps_ids:
                    cr.execute('delete from shipping_response where id=%s',(res_id[1],))
                    cr.commit()
            ### Assign Carrier to Delivery carrier if user has not selected
            carrier_ids=''
            if shipping_type:
                if shipping_type.lower() == 'usps':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',service_type),('is_usps','=',True)])
                elif shipping_type.lower() == 'ups':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_code','=',service_type),('is_ups','=',True)])
                elif shipping_type.lower() == 'fedex':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',service_type),('is_fedex','=',True)])
                elif shipping_type.lower() == 'canada post':
                    canada_service_type=self.pool.get('service.name').browse(cr,uid,service_type).name
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('name','=',canada_service_type),('is_canadapost','=',True)])
                elif shipping_type.lower() == 'all':
                    canada_service_type=self.pool.get('service.name').browse(cr,uid,service_type).name
                    if canada_service_type:
                        service_type=canada_service_type
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,['|','|',('service_output','=',service_type),('name','=',service_type),('service_code','=',service_type)])
                if not carrier_ids:
                    raise osv.except_osv(_('Error'), _('Delivery Method is not defined for selected service type'))
                ### Write this shipping respnse is selected
            vals = {'response_usps_ids' : delete_att_vals,
                    'pack_length' : width,
                    'pack_width' : width,
                    'pack_height' : width,
                    'carrier_id':carrier_ids and carrier_ids[0] or ''
                    }
            return {'value':vals}
        return {'value':{}}

    def generate_shipping(self, cr, uid, ids,context=None):        
        stock_obj = self.pool.get('stock.picking')
        res_partner_obj = self.pool.get('res.partner')
        default_ship_obj = self.pool.get('sys.default.shipping')
        if context is None:
            context = {}
        for id in ids:
            try:
                stockpicking = self.browse(cr,uid,id)
                shipping_type = stockpicking.shipping_type
                type = stockpicking.type
                weight = stockpicking.weight_package
                weight_unit='LB'               
                if weight<=0.0:                    
                    raise osv.except_osv(_('Warning !'),_("Package Weight Invalid!"))
                ###based on stock.picking type
                if type == 'out':
#                    shipper_address = stockpicking.sale_id and stockpicking.sale_id.shop_id.cust_address or False
                    if stockpicking.sale_id :
                        shipper_address = stockpicking.sale_id.shop_id and stockpicking.sale_id.shop_id.warehouse_id.partner_id
                    else:
                        shipper_address = stockpicking.ware_id.partner_id
                    if not shipper_address :
                        raise osv.except_osv(_('Warning !'),_("Please Select Warehouse"))
#                    shipper_address = stockpicking.sale_id and stockpicking.sale_id.warehouse_id.partner_id or False                
                elif type == 'in':
                    shipper_address = stockpicking.partner_id.name                                
                if not shipper_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise osv.except_osv(_('Warning !'),_("Shop Address not defined!"))
                    else:
                        return False
                if not (shipper_address.name or shipper_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
                if not shipper_address.street:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Street."))
                if not shipper_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
                if not shipper_address.state_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper State Code."))
                if not shipper_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
                if not shipper_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
                shipper = Address(shipper_address.name or shipper_address.name, shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.name)

                ### Recipient
                ###based on stock.picking type
                if type == 'out':
                    cust_address = stockpicking.partner_id
                elif type == 'in':
                    cust_address = stockpicking.sale_id and stockpicking.sale_id.shop_id and stockpicking.sale_id.shop_id.warehouse_id.partner_id or False
                if not cust_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise osv.except_osv(_('Warning !'),_("Reciepient Address not defined!"))
                    else:
                        return False
                if not (cust_address.name or cust_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
                if not cust_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
                receipient = Address(cust_address.name or cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
                # Deleting previous quotes
                shipping_res_obj = self.pool.get('shipping.response')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('picking_id','=',ids[0])])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)
                saleorderline_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',stockpicking.sale_id.id)])
                sys_default = default_ship_obj._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                context['sys_default'] = sys_default
                cust_default= default_ship_obj._get_cust_default_shipping(cr,uid,stockpicking.carrier_id.id,context)
                context['cust_default'] = cust_default                
                if not stockpicking.tracking_ids:
                    tracking_data = {}
                    if stockpicking.shipping_type == 'Fedex' and stockpicking.package_type_fedex :
                        package_type_data = stockpicking.package_type_fedex
                        tracking_data.update({
                        'name':package_type_data.name,
                        'length_ups':package_type_data.length,
                        'width_ups':package_type_data.width,
                        'height_ups':package_type_data.height,
                        'picking_id':stockpicking.id,
                        })
                    if stockpicking.shipping_type == 'UPS' and stockpicking.package_type_ups :
                        package_type_data = stockpicking.package_type_ups
                        tracking_data.update({
                        'name':package_type_data.name,
                        'length_ups':package_type_data.length,
                        'width_ups':package_type_data.width,
                        'height_ups':package_type_data.height,
                        'picking_id':stockpicking.id,
                        })
                    self.pool.get('pack.track').create(cr, uid, tracking_data, context=context)
                if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
                    usps_obj = self.pool.get('shipping.usps')
                    usps_info = usps_obj.get_usps_info(cr,uid,context)
                    first_class_mail_type_usps = stockpicking.first_class_mail_type_usps or ''
                    container_usps = stockpicking.container_usps or ''
                    size_usps = stockpicking.size_usps
                    width_usps = stockpicking.width_usps
                    length_usps = stockpicking.length_usps
                    height_usps = stockpicking.height_usps
                    girth_usps = stockpicking.girth_usps
                    shipping_account = stockpicking.sale_id and stockpicking.sale_id.shipping_account or stockpicking.shipping_account
                    if shipping_account=='my_account':
                        usps_info = usps_obj.get_usps_info(cr,uid,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=stockpicking.sale_id.partner_id.id
                        usps_info=self.pool.get('res.partner').get_usps_info(cr,uid,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
                    service_type_usps=_get_service_type_usps(cr,uid,ids,context)
                    for each_service in service_type_usps:
                        if 'First Class' in each_service[0]:
                                first_class_usps=_get_first_class_mail_type_usps(cr,uid,ids,context)
                                for each_first_class_mail in first_class_usps:
                                    usps = shippingservice.USPSRateRequest(usps_info, each_service[0], each_first_class_mail[0], container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default, sys_default,shipping_account)
                                    usps_response = usps.send()
                                    context['type'] = 'USPS'
                                    if usps_response==True:
                                        continue
                                    self.create_quotes(cr,uid,ids,usps_response,context)
                        else:
                            usps = shippingservice.USPSRateRequest(usps_info,each_service[0] , first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default, sys_default,shipping_account)
                            usps_response = usps.send()
                            context['type'] = 'USPS'
                            if usps_response==True:
                                continue
                            self.create_quotes(cr,uid,ids,usps_response,context)
                if shipping_type == 'UPS' or shipping_type == 'All':
                    shipping_account = stockpicking.sale_id and stockpicking.sale_id.shipping_account or stockpicking.shipping_account
                    if shipping_account=='my_account':
                        ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=stockpicking.partner_id.id
                        ups_info=res_partner_obj.get_ups_info(cr,uid,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
                    pickup_type_ups = stockpicking.pickup_type_ups
                    service_type_ups = stockpicking.service_type_ups
                    package_type_ups = stockpicking.package_type_ups.ups_value                    
                    ###########
                    ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, '', package_type_ups, weight, shipper, receipient, cust_default, sys_default,shipping_account)
                    ups_response = ups.send()
                    context['type'] = 'UPS'
                    stock_obj.create_quotes_stock(cr,uid,ids,ups_response,context)
                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = stockpicking.dropoff_type_fedex
                    service_type_fedex = stockpicking.service_type_fedex
                    package_type_fedex = stockpicking.package_type_fedex
                    package_detail_fedex = stockpicking.package_detail_fedex
                    payment_type_fedex = stockpicking.payment_type_fedex
                    physical_packaging_fedex = stockpicking.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    shipping_account = stockpicking.sale_id and stockpicking.sale_id.shipping_account or stockpicking.shipping_account

                    if shipping_account=='my_account':
                        shippingfedex_obj = self.pool.get('shipping.fedex')
                        shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
                        if not shippingfedex_id:
                                raise osv.except_osv(_('Error'), _('Default FedEx settings not defined'))
                        else:
                            shippingfedex_id = shippingfedex_id[0]
                            fedex_info=shippingfedex_obj.browse(cr,uid,shippingfedex_id)
                            carrier_code=_get_fedex_carrier_code(cr,uid,ids,context)
                            for each_carrier_code in carrier_code:
                                fedex = shippingservice.FedexRateRequest(fedex_info,dropoff_type_fedex,service_type_fedex,package_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper,receipient,sys_default,cust_default,shipping_account,each_carrier_code[0])
                                fedex_response = fedex.send()
                                context['type'] = 'Fedex'
                                stock_obj.create_quotes_stock(cr,uid,ids,fedex_response,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=stockpicking.partner_id.id
                        fedex_info=res_partner_obj.get_fedex_info(cr,uid,context)
                        carrier_code=_get_fedex_carrier_code(cr,uid,ids,context)
                        for each_carrier_code in carrier_code:
                            fedex = shippingservice.FedexRateRequest(fedex_info,dropoff_type_fedex,service_type_fedex,package_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper,receipient,sys_default,cust_default,shipping_account,each_carrier_code[0])
                            fedex_response = fedex.send()
                            context['type'] = 'Fedex'
                            stock_obj.create_quotes_stock(cr,uid,ids,fedex_response,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
            except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
        return True


    def create_quotes_sales(self, cr, uid, ids, vals, context={}):        
        dict = vals.rate
        res_id=0
        for i in dict.iterkeys():            
            val_dict = dict[i]
            quotes_vals = {
                'name' : i,
                'type' : context['type'],
                'rate' :val_dict.get('rate'),
                'sale_order_id' : ids[0], #Change the ids[0] when switch to create
                'weight' :'',
                'sys_default' : False,
                'cust_default' : False,
                'sr_no' : '',
            }
            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
        if res_id:
            return True
        else:
            return False

    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, package_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, sys_default=False,cust_default=False, error=True, context=None):
        try:
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
            # This is very generalized, top-level information.
            # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
            rate_request.RequestedShipment.DropoffType = dropoff_type_fedex
            # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
            # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
            rate_request.RequestedShipment.ServiceType = service_type_fedex
            # What kind of package this will be shipped in.
            # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
            rate_request.RequestedShipment.PackagingType = package_type_fedex
            # No idea what this is.
            # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
            rate_request.RequestedShipment.PackageDetail = package_detail_fedex
            rate_request.RequestedShipment.Shipper.Address.PostalCode = shipper_postal_code
            rate_request.RequestedShipment.Shipper.Address.CountryCode = shipper_country_code
            rate_request.RequestedShipment.Shipper.Address.Residential = False
            rate_request.RequestedShipment.Recipient.Address.PostalCode = customer_postal_code
            rate_request.RequestedShipment.Recipient.Address.CountryCode = customer_country_code
            if service_type_fedex=='GROUND_HOME_DELIVERY':
                rate_request.RequestedShipment.Recipient.Address.Residential = True
            else:
                rate_request.RequestedShipment.Recipient.Address.Residential = False
            # This is needed to ensure an accurate rate quote with the response.
            #rate_request.RequestedShipment.Recipient.Address.Residential = True
            #include estimated duties and taxes in rate quote, can be ALL or NONE
            rate_request.RequestedShipment.EdtRequestType = 'NONE'
            # Who pays for the rate_request?
            # RECIPIENT, SENDER or THIRD_PARTY
            rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex    
            rate_request.RequestedShipment.PackageCount = 1
            package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
            package1_weight = rate_request.create_wsdl_object_of_type('Weight')            
            package1_weight.Value = weight
            package1_weight.Units = "LB"
            package1.Weight = package1_weight
            #can be other values this is probably the most common
            package1.PhysicalPackaging = physical_packaging_fedex
            # Un-comment this to see the other variables you may set on a package.
            # This adds the RequestedPackageLineItem WSDL object to the rate_request. It
            # increments the package count and total weight of the rate_request for you.
            rate_request.add_package(package1)
            # If you'd like to see some documentation on the ship service WSDL, un-comment
            # this line. (Spammy).
            # Un-comment this to see your complete, ready-to-send request as it stands
            # before it is actually sent. This is useful for seeing what values you can
            # change.
            # Fires off the request, sets the 'response' attribute on the object.
            try:
                rate_request.send_request()
            except Exception, e:
                if error:
#                    raise Exception('%s' % (e))
                    raise osv.except_osv(_('Warning !'),_('%s'% (e)))
                return False
            # This will show the reply to your rate_request being sent. You can access the
            # attributes through the response attribute on the request object. This is
            # good to un-comment to see the variables returned by the FedEx reply.
            # Here is the overall end result of the query.
#            for detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#                for surcharge in detail.ShipmentRateDetail.Surcharges:
#                    if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
#                        _logger.info("ODA rate_request charge: %s", surcharge.Amount.Amount)
#            for rate_detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#                _logger.info("Net FedEx Charge: %s %s", rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount)
            sr_no = 9
            sys_default_value = False
            cust_default_value = False
            if sys_default:
                sys_default_vals = sys_default.split('/')
                if sys_default_vals[0] == 'FedEx':
                    sys_default_value = True
                    sr_no = 2

            if cust_default:
                cust_default_vals = cust_default.split('/')
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
            if fedex_res_id:
                return True
            else:
                return False
        except Exception, e:
#            raise Exception('%s' % (e))
            raise osv.except_osv(_('Warning'), _('%s'% (e)))
        
    def get_rates(self,cr,uid,ids,context={}):
        shipping_obj = self.pool.get('shipping.method')
        shipping_record = shipping_obj.search(cr,uid,[])
        if not shipping_record:
            raise osv.except_osv(_("Warning"), _("Shipping settings are not done. Go to Warehouse/Configuration/Canada Post/Configuration"))
        total = ''
        gst =0.00
        hst =0.00
        pst =0.00
        self_brw = self.browse(cr,uid,ids[0])
        search_id = shipping_obj.search(cr,uid,[])
        if search_id:
            shipping_brw = shipping_obj.browse(cr,uid,search_id[0])
            name =  shipping_brw.name
            passwd =  shipping_brw.passwd
            environment = shipping_brw.environment
            co_no = shipping_brw.customer_num
            cana_wt = self_brw.weight_package
            cana_ln = self_brw.cana_length
            cana_wdth = self_brw.cana_width
            cana_ht = self_brw.cana_height
            service_code = self_brw.services
            zip_code_customer = self_brw.partner_id.zip
            zip_code_supplier = shipping_brw.address.zip
            serv_code = service_code.service_code
            xml_request = """<?xml version="1.0" encoding="utf-8"?>
    <mailing-scenario xmlns="http://www.canadapost.ca/ws/ship/rate">
    <customer-number>%s</customer-number>
    <parcel-characteristics>
    <weight>%s</weight>
    <dimensions>
    <length>%s</length>
    <width>%s</width>
    <height>%s</height>
    </dimensions>
    </parcel-characteristics>
    <origin-postal-code>%s</origin-postal-code>
    <destination><domestic>
    <postal-code>%s</postal-code>
    </domestic>
    </destination>
    <services>
    <service-code>%s</service-code>
    </services>
    </mailing-scenario>

            """%(co_no,cana_wt,cana_ln,cana_wdth,cana_ht,zip_code_supplier,zip_code_customer,serv_code)            
            result = connection.call(cr, uid, 'GetRates', name, passwd, environment,xml_request)            
            for each in result:
                if each.get('base',False):
                    base = each.get('base',False)                    
                if each.get('gst',False):
                    gst = each.get('gst',False)                    
                if each.get('pst',False):
                    pst = each.get('pst',False)                    
                if each.get('hst',False):
                    hst = each.get('hst',False)                    
                base = float(base)
                gst = float(gst)
                pst = float(pst)
                hst = float(hst)
                total = gst+pst+hst
                t1 = str(total)
                b1 = str(base)
                g1 = str(gst)
                p1 = str(pst)
                h1 = str(hst)
                shipping_rate = "Base Price : "+b1+"\n"+"Taxes : "+t1+"\n\t"+"gst : "+g1+"\n\t"+"pst : "+p1+"\n\t"+"hst : "+h1+"\n\t"               
        cr.execute("UPDATE stock_picking SET rates='%s' where id=%d"%(shipping_rate,ids[0],))
        return True

    def cana_generate_shipping(self,cr,uid,ids,context={}):
        shipping_obj = self.pool.get('shipping.method')
        stock_obj=self.pool.get('stock.picking')
        shipping_record = shipping_obj.search(cr,uid,[])
        self_brw = self.browse(cr, uid, ids[0])
        if not shipping_record:
            raise osv.except_osv(_("Warning"), _("Shipping settings are not done. Go to Warehouse/Configuration/Canada Post/Configuration"))
        rt = self.browse(cr, uid, ids[0]).rates
        rt=(rt.split('\n')[0]).split(':')[1]
        if not rt:
            raise osv.except_osv(_("Warning"), _("First Get Rates on clicking 'Get Rates' button"))
        shipping_obj = self.pool.get('shipping.method')
        search_id = shipping_obj.search(cr,uid,[])
        if search_id:
            shipping_brw = shipping_obj.browse(cr,uid,search_id[0])
            name =  shipping_brw.name
            passwd =  shipping_brw.passwd
            environment = shipping_brw.environment
            serv_code = self_brw.services.service_code
            comp_sender = shipping_brw.address.name
            phone_no = shipping_brw.address.phone
            street_name = shipping_brw.address.street
            city_name = shipping_brw.address.city
            supplier_zip = shipping_brw.address.zip
        comp_rec = self_brw.partner_id.name
        rec_name = self_brw.partner_id.name
        rec_street = self_brw.partner_id.street
        rec_city = self_brw.partner_id.city
        rec_zip = self_brw.partner_id.zip
        cana_wt = self_brw.weight_package
        cana_ln = self_brw.cana_length
        cana_wdth = self_brw.cana_width
        cana_ht = self_brw.cana_height
        xml_request = """<?xml version="1.0" encoding="utf-8"?>
<non-contract-shipment xmlns="http://www.canadapost.ca/ws/ncshipment">
<delivery-spec>
<service-code>%s</service-code>
<sender>
<company>%s</company>
<contact-phone>%s</contact-phone>
<address-details>
<address-line-1>%s</address-line-1>
<city>%s</city>
<prov-state>%s</prov-state>
<postal-zip-code>%s</postal-zip-code>
</address-details>
</sender>
<destination>
<name>%s</name>
<company>%s</company>
<address-details>
<address-line-1>%s</address-line-1>
<city>%s</city>
<prov-state>%s</prov-state>
<country-code>%s</country-code>
<postal-zip-code>%s</postal-zip-code>
</address-details>
</destination>
<parcel-characteristics>
<weight>%s</weight>
<dimensions>
<length>%s</length>
<width>%s</width>
<height>%s</height>
</dimensions>
</parcel-characteristics>
<preferences>
<show-packing-instructions>%s</show-packing-instructions>
</preferences>
</delivery-spec>
</non-contract-shipment>"""%(serv_code,comp_sender,phone_no,street_name,city_name,'ON',supplier_zip,rec_name,rec_name,rec_street,rec_city,'ON', 'CA',rec_zip,cana_wt,cana_ln,cana_wdth,cana_ht,'true',)
        result = connection.call(cr, uid, 'GetShipping', name, passwd, environment, xml_request)
        track_num=result.get('tracking_no',False)
        carrier_services = self_brw.services.name
        id1 = self.pool.get('delivery.carrier').search(cr, uid, [('name','=', 'Canada Post' + ' '+carrier_services)])
        stock_origin = self_brw.origin
        sale_id = self.pool.get('sale.order').search(cr, uid, [('name', '=', stock_origin)])
        if id1 and track_num:
            cr.execute("UPDATE stock_picking SET carrier_tracking_ref='%s',carrier_id=%d,label_recvd=True, shipping_rate='%s' where id=%d"%(track_num,id1[0],rt,ids[0],))
            if sale_id:
                cr.execute("UPDATE sale_order SET tracking_no=%s,carrier_id=%d where id = %s"%(track_num, id1[0],sale_id[0]))
        link=result.get('link',False)
        if link:
            urldat = urlparse.urlparse(link)
            if urldat:
                link = urldat[2]
            result_pdf = connection.call(cr, uid, 'Getartifact', name, passwd, environment, link)
            self.create_attachment_can(cr,uid,ids,result_pdf)
        return True

    def create_attachment_can(self, cr, uid, ids, vals, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        data_attach = {
            'name': 'PackingList1.pdf' ,
            'datas': binascii.b2a_base64(vals),
            'description': 'Packing1 List',
            'res_name': self.browse(cr,uid,ids[0]).name,
            'res_model': 'stock.picking.out',
            'res_id': ids[0],
        }
        attach_id = attachment_pool.search(cr,uid,[('res_id','=',ids[0]),('res_name','=',self.browse(cr,uid,ids[0]).name)])
        if not attach_id:
            attach_id = attachment_pool.create(cr, uid, data_attach)
        else:
            attach_id = attach_id[0]
            attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
        return attach_id
stock_picking_out()

class stock_picking_in(osv.osv):    
    _inherit = "stock.picking.in"
    _columns = {
        'carrier_id':fields.many2one("delivery.carrier","Carrier"),
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=32),
    }
stock_picking_in()

class stock_warehouse(osv.osv):
    _inherit='stock.warehouse'
    _columns={
        'auto_label_generation':fields.boolean('Auto Label Generation')
    }
stock_warehouse()
