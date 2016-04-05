# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
import openerp.addons.decimal_precision as dp
import urllib2
import urllib
from base64 import b64decode
import binascii
import socket
import shippingservice
from miscellaneous import Address
from fedex.services.rate_service import FedexRateServiceRequest
from fedex.services.ship_service import FedexProcessShipmentRequest
from fedex.config import FedexConfig
from openerp.addons.bista_shipping_endicia import endicia
import suds
from suds.client import Client
from openerp.tools.translate import _
import Image
from openerp.osv import fields, osv
import connection_osv as connection
import math
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)
from xml.dom.minidom import parse, parseString
from openerp import workflow

#added
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

def _get_shipping_type(self, cr, uid, context=None):
    return [
        ('Fedex','Fedex'),
        ('UPS','UPS'),
        ('USPS','USPS'),
        ('All','All'),
        ('Canada Post','Canada Post'),
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

def _get_fedex_carrier_code(self, cr, uid, context=None):
    return [
        ('FDXE', 'FDXE'),
        ('FDXG', 'FDXG'),]

def _get_first_class_mail_type_usps(self, cr, uid, context=None):
    return [
        ('Letter', 'Letter'),
        ('Flat', 'Flat'),
        ('Parcel', 'Parcel'),
        ('Postcard', 'Postcard'),
      ]

def _get_container_usps(self, cr, uid, context=None):
    return [
        ('Flat', 'Flat'),
        ('Parcel', 'Parcel'),
        ('Large Parcel', 'Large Parcel'),
        ('Irregular Parcel', 'Irregular Parcel'),
     ]

def _get_size_usps(self, cr, uid, context=None):
    return [
        ('REGULAR', 'Regular'),
        ('LARGE', 'Large'),
     ]


class sale_order(osv.osv):
    _inherit = "sale.order"

    def _default_journal(self, cr, uid, context={}):
        accountjournal_ids = self.pool.get('account.journal').search(cr, uid,[('name','=','Sales Journal')])
        if accountjournal_ids:
            return accountjournal_ids[0]
        else:
            return False

    # added to get the default package
    def _get_default_package_fedex(self, cr, uid, context={}):
        pack_id = self.pool.get('shipping.package.type.fedex').search(cr, uid, [('name','=','YOUR_PACKAGING')])
        if pack_id :
            return pack_id[0]
        else:
            return False

    def _get_default_package_ups(self, cr, uid, context={}):
        pack_id = self.pool.get('shipping.package.type.ups').search(cr, uid, [('name','=','Unknown')])
        if pack_id :
            return pack_id[0]
        else:
            return False


    def get_rates(self,cr,uid,ids,context={}):
        shipping_obj = self.pool.get('shipping.method')
        shipping_record = shipping_obj.search(cr,uid,[])
        if not shipping_record:
            raise osv.except_osv(_("Warning"), _("Shipping settings are not done. Go to Warehouse/Configuration/Canada Post/Configuration"))
        total = ''
        gst =0.00
        hst =0.00
        pst =0.00
        search_id = shipping_obj.search(cr,uid,[])
        if search_id:
            name =  shipping_obj.browse(cr,uid,search_id[0]).name
            passwd =  shipping_obj.browse(cr,uid,search_id[0]).passwd
            environment = shipping_obj.browse(cr,uid,search_id[0]).environment
            co_no = shipping_obj.browse(cr,uid,search_id[0]).customer_num
            cana_wt = self.browse(cr,uid,ids[0]).weight_package
            cana_ln = self.browse(cr,uid,ids[0]).cana_length
            cana_wdth = self.browse(cr,uid,ids[0]).cana_width
            cana_ht = self.browse(cr,uid,ids[0]).cana_height
            service_code = self.browse(cr,uid,ids[0]).services
            zip_code_customer = self.browse(cr, uid, ids[0]).partner_invoice_id.zip
            zip_code_supplier = shipping_obj.browse(cr,uid,search_id[0]).address.zip
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
        cr.execute("UPDATE sale_order SET rates='%s' where id=%d"%(shipping_rate,ids[0],))
        return True

    def prepare_shipping_response(self, cr, uid, order, context=None):
        shipping = self.pool.get('shipping.response')
        response = shipping.search(cr, uid, [('sale_order_id', '=', order.id)])
        return response

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
                raise osv.except_osv(_('Warning'), _('%s'%(e)))
            return False
        # This will show the reply to your rate_request being sent. You can access the
        # attributes through the response attribute on the request object. This is
        # good to un-comment to see the variables returned by the FedEx reply.
        # Here is the overall end result of the query.
#        for detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#            for surcharge in detail.ShipmentRateDetail.Surcharges:
#                if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
#                    _logger.info("ODA rate_request charge %s", surcharge.Amount.Amount)
#
#        for rate_detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#            _logger.info("Net FedEx Charge %s %s", rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount)

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
            'sale_order_id' : ids[0], #Change the ids[0] when switch to create
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
                'sale_order_id' : ids[0], #Change the ids[0] when switch to create
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
                    'res_model': 'sale.order',
                    'res_id': ids[0],
                }
            datas=data_attach['datas']
            pdf_attach.append(datas)
            attach_id = attachment_pool.create(cr, uid, data_attach)
        return attach_id


    ## This function is called when generate shipping quotes button is clicked
    def generate_shipping(self, cr, uid, ids, context={}):
        order_line_obj=self.pool.get('sale.order.line')
        res_partner_obj=self.pool.get('res.partner')
        stock_obj=self.pool.get('stock.picking')
        service_obj=self.pool.get('service.type')
        default_ship_object = self.pool.get('sys.default.shipping')
        if context is None:
            context = {}
        for id in ids:
            try:
                saleorder = self.browse(cr,uid,id)
                line_items=order_line_obj.search(cr,uid,[('order_id','=',id)])
                if len(line_items)==0:
                    raise osv.except_osv(_('Warning !'),_("Please Enter Line Item to Sale Order"))
                shipping_type = saleorder.shipping_type
                weight = saleorder.weight_package
                weight_unit='LB'
                if weight<=0.0:
                    raise osv.except_osv(_('Warning !'),_("Package Weight Invalid"))
                ###based on stock.picking type
                shipper_address = saleorder.shop_id and saleorder.shop_id.warehouse_id and saleorder.shop_id.warehouse_id.partner_id or False
                if not shipper_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise osv.except_osv(_('Warning !'),_("Shop Address not defined!"))
                    else:
                        return False
                if not (shipper_address.name or shipper_address.partner_id.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
                if not shipper_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
                if not shipper_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
                if not shipper_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
                shipper = Address(shipper_address.name, shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.name)
                cust_address = saleorder.partner_shipping_id
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
                shipping_res_obj = self.pool.get('shipping.response')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('sale_order_id','=',ids[0])])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)
                saleorderline_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',saleorder.id)])
                sys_default = default_ship_object._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                context['sys_default'] = sys_default
                cust_default= default_ship_object._get_cust_default_shipping(cr,uid,saleorder.carrier_id.id,context)
                context['cust_default'] = cust_default
                shipping_account=saleorder.shipping_account
                if not shipping_account:
                    raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
                #generating FeDex and UPS dimmension based on type of shipping
                if not saleorder.tracking_ids:
                    tracking_data = {}
                    if saleorder.shipping_type == 'Fedex' and saleorder.package_type_fedex :
                        package_type_data = saleorder.package_type_fedex
                        tracking_data.update({
                        'package_name':package_type_data.name,
                        'length_ups':package_type_data.length,
                        'width_ups':package_type_data.width,
                        'height_ups':package_type_data.height,
                        'saleorder_id':saleorder.id,
                        })
                    if saleorder.shipping_type == 'UPS' and saleorder.package_type_ups :
                        package_type_data = saleorder.package_type_ups
                        tracking_data.update({
                        'package_name':package_type_data.name,
                        'length_ups':package_type_data.length,
                        'width_ups':package_type_data.width,
                        'height_ups':package_type_data.height,
                        'saleorder_id':saleorder.id,
                        })
                    self.pool.get('package.tracking').create(cr, uid, tracking_data, context=context)
                if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
                    size_usps = saleorder.size_usps
                    if weight>70 and size_usps=='REGULAR':
                        raise osv.except_osv(_('Warning !'),_("Package weight exceed 70 so select size_usps as large"))
                    #enchancement for customer shipping account
                    if shipping_account=='my_account':
                        usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=saleorder.partner_id.id
                        usps_info=self.pool.get('res.partner').get_usps_info(cr,uid,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
                    ##########
                    first_class_mail_type_usps = saleorder.first_class_mail_type_usps or ''
                    container_usps = saleorder.container_usps or ''
                    width_usps = saleorder.width_usps
                    length_usps = saleorder.length_usps
                    height_usps = saleorder.height_usps
                    girth_usps = saleorder.girth_usps
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
                                usps = shippingservice.USPSRateRequest(usps_info, each_service[0], first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default, sys_default,shipping_account)
                                usps_response = usps.send()
                                context['type'] = 'USPS'
                                if usps_response==True:
                                    continue
                                self.create_quotes(cr,uid,ids,usps_response,context)
                if shipping_type == 'UPS' or shipping_type == 'All':
                    #enchancement for customer shipping account
                    pickup_type_ups = saleorder.pickup_type_ups
                    package_type_ups = saleorder.package_type_ups.ups_value
                    if shipping_account=='my_account':
                        ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=saleorder.partner_id.id
                        ups_info=res_partner_obj.get_ups_info(cr,uid,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
                    ###########
                    ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups,'' , package_type_ups, weight, shipper, receipient, cust_default, sys_default,shipping_account)
                    ups_response = ups.send()
                    context['type'] = 'UPS'
                    stock_obj.create_quotes_sales(cr,uid,ids,ups_response,context)
                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = saleorder.dropoff_type_fedex
                    service_type_fedex = saleorder.service_type_fedex
                    package_type_fedex = saleorder.package_type_fedex.name
                    package_detail_fedex = saleorder.package_detail_fedex
                    payment_type_fedex = saleorder.payment_type_fedex
                    physical_packaging_fedex = saleorder.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    fed_length = saleorder.pack_length
                    fed_width = saleorder.pack_width
                    fed_height = saleorder.pack_height
                    error_required = True
                    if shipping_account=='my_account':
                        shippingfedex_obj = self.pool.get('shipping.fedex')
                        shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
                        if not shippingfedex_id:
                            raise osv.except_osv(_('Error'), _('Default FedEx settings not defined'))
                        else:
                            shippingfedex_id = shippingfedex_id[0]
                            fedex_info = self.pool.get('shipping.fedex').browse(cr,uid,shippingfedex_id)
                            carrier_code = _get_fedex_carrier_code(cr,uid,ids,context)
                            for each_carrier_code in carrier_code:
                                fedex = shippingservice.FedexRateRequest(fedex_info,dropoff_type_fedex,service_type_fedex,package_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper,receipient,sys_default,cust_default,shipping_account,each_carrier_code[0])
                                fedex_response = fedex.send()
                                context['type'] = 'Fedex'
                                quotes = stock_obj.create_quotes_sales(cr,uid,ids,fedex_response,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=saleorder.partner_id.id
                        fedex_info=res_partner_obj.get_fedex_info(cr,uid,context)
                        carrier_code=_get_fedex_carrier_code(cr,uid,ids,context)
                        for each_carrier_code in carrier_code:
                            fedex = shippingservice.FedexRateRequest(fedex_info,dropoff_type_fedex,service_type_fedex,package_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper,receipient,sys_default,cust_default,shipping_account,each_carrier_code[0])
                            fedex_response = fedex.send()
                            context['type'] = 'Fedex'
                            stock_obj.create_quotes_sales(cr,uid,ids,fedex_response,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
            except Exception, exc:
                raise osv.except_osv(_('Error!'), _('%s' % (exc,)))
            return True

    def create(self, cr, uid, vals, context=None):
        default_ship_obj = self.pool.get('sys.default.shipping')
        if context is None:
            context={}
        if vals.get('type',False) and vals['type'] == 'out':
            try:
                vals['shipping_type'] = 'All'
                cust_default = False
                saleorder_lnk = self.pool.get('sale.order') .browse(cr,uid,vals['sale_id'])
                saleorderline_obj = self.pool.get('sale.order.line')
                saleorderline_ids = saleorderline_obj.search(cr,uid,[('order_id','=',vals['sale_id'])])
                weight = 0.0
                for saleorderline_id in saleorderline_ids:
                    saleorderline_lnk = saleorderline_obj.browse(cr,uid,saleorderline_id)
                    weight += (saleorderline_lnk.product_id.product_tmpl_id.weight_net * saleorderline_lnk.product_uom_qty)
                vals['weight_net'] = weight
                dropoff_type_fedex = vals['dropoff_type_fedex'] if vals.get('dropoff_type_fedex', False) else 'REGULAR_PICKUP'
                service_type_fedex = vals['service_type_fedex'] if vals.get('service_type_fedex', False) else 'FEDEX_GROUND'
                package_type_fedex = vals['package_type_fedex'] if vals.get('package_type_fedex', False) else 'YOUR_PACKAGING'
                package_detail_fedex = vals['package_detail_fedex'] if vals.get('package_detail_fedex', False) else 'INDIVIDUAL_PACKAGES'
                payment_type_fedex = vals['payment_type_fedex'] if vals.get('payment_type_fedex', False) else 'SENDER'
                physical_packaging_fedex = vals['physical_packaging_fedex'] if vals.get('physical_packaging_fedex', False) else 'BOX'
                vals['dropoff_type_fedex'] = dropoff_type_fedex
                vals['service_type_fedex'] = service_type_fedex
                vals['package_type_fedex'] = package_type_fedex
                vals['package_detail_fedex'] = package_detail_fedex
                vals['payment_type_fedex'] = payment_type_fedex
                vals['physical_packaging_fedex'] = physical_packaging_fedex
                pickup_type_ups = '01'
                service_type_ups = '03'
                package_type_ups = '02'
                vals['pickup_type_ups'] = pickup_type_ups
                vals['service_type_ups'] = service_type_ups
                vals['package_type_ups'] = package_type_ups
                carrier_id = saleorder_lnk.carrier_id and saleorder_lnk.carrier_id.id or False
                if carrier_id:
                    ## Find which carrier has been selected :- cust_default
                    vals['carrier_id'] = carrier_id
                    cust_default = default_ship_obj._get_cust_default_shipping(cr,uid,carrier_id,context)
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
                ## We consider the Gross Weight
                sys_default = default_ship_obj._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                if not (cust_default and cust_default.split("/")[0] == 'USPS') and sys_default and sys_default.split('/')[0] == 'USPS':
                    vals['service_type_usps'] = sys_default.split('/')[1] or ''
                    vals['container_usps'] = sys_default.split('/')[2] or ''
                    vals['size_usps'] = sys_default.split('/')[3] or ''
    #                ### Sys default applicable only for simple orders
    #                ## We consider the Gross Weight
                new_id = super(sale_order, self).create(cr, uid, vals, context)
                context['cust_default'] = cust_default
                context['sys_default'] = sys_default
                context['error'] = False
                res = self.generate_shipping(cr,uid,[new_id],context)
            except Exception, e:
                _logger.exception("Exception: %s", e)
        else:
            new_id = super(sale_order, self).create(cr, uid, vals, context=context)
            # added to calculate weight for sale order line product.
            if self.browse(cr, uid, new_id).use_shipping:
                self._cal_weight(cr, uid, [new_id], context)
        return new_id

    # added to calculate weight for sale order line product.
    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids,list):
            sale_id = ids[0]
        else:
            sale_id = ids
        if context is None:
            context={}
        #passing context to avoid maximum recursion depth exceeded while write
        context.update({'sale_write_called':'yes'})
        if self.browse(cr, uid, sale_id).use_shipping:
            self._cal_weight(cr, uid, [sale_id], context=context)
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)


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

    def dummy_fun(self, cr, uid, ids, context=None):
        res = self._cal_weight(cr, uid, ids, context)
        return True

    def _cal_weight(self, cr, uid, ids, context=None):
        for sale in self.browse(cr, uid, ids, context=context):
            order_line_obj=self.pool.get('sale.order.line')
            line_items=order_line_obj.search(cr, uid, [('order_id','=',sale.id)])
            total_weight = 0.00
            for move in line_items:
                weight=order_line_obj.browse(cr,uid,move).product_id.weight
                product_type=order_line_obj.browse(cr,uid,move).product_id.type
                if weight<=0.00 and product_type != 'service':
                    raise osv.except_osv(_('Warning'), _('Weight not defined for %s' % order_line_obj.browse(cr,uid,move).product_id.name))
                else:
                    total_weight += weight * order_line_obj.browse(cr,uid,move).product_uom_qty or 0.0
            # added if this function is called from sale_order write function(to avoid maximum recursion depth exceeded.)
            if context.get('sale_write_called',False):
                cr.execute("update sale_order set weight_package=%s where id=%s"%(total_weight,sale.id))
                cr.commit()
            else:
                self.write(cr,uid,sale.id,{'weight_package':total_weight})
        return total_weight

#    def _get_euro(self, cr, uid, context=None):
#        try:
#            return self.pool.get('res.currency').search(cr, uid, [('name','=','USD')])[0]
#        except:
#            return False



    _columns = {
        'use_shipping' : fields.boolean('Use Shipping',readonly=True, states={'draft': [('readonly', False)]}),
        'shipping_type' : fields.selection(_get_shipping_type,'Shipping Type',readonly=True, states={'draft': [('readonly', False)]}),
        'weight_package' : fields.float('Package Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds",readonly=True, states={'draft': [('readonly', False)]}),
        'service_type_usps' : fields.selection(_get_service_type_usps, 'Service Type', size=100,readonly=True, states={'draft': [('readonly', False)]}),
        'first_class_mail_type_usps' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50,readonly=True, states={'draft': [('readonly', False)]}),
        'container_usps' : fields.selection(_get_container_usps,'Container', size=100,readonly=True, states={'draft': [('readonly', False)]}),
        'size_usps' : fields.selection(_get_size_usps,'Size',readonly=True, states={'draft': [('readonly', False)]}),
        'width_usps' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
        'length_usps' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
        'height_usps' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
        'girth_usps' : fields.float('Girth', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
        'dropoff_type_fedex' : fields.selection([
                ('REGULAR_PICKUP','REGULAR PICKUP'),
                ('REQUEST_COURIER','REQUEST COURIER'),
                ('DROP_BOX','DROP BOX'),
                ('BUSINESS_SERVICE_CENTER','BUSINESS SERVICE CENTER'),
                ('STATION','STATION'),
            ],'Dropoff Type',readonly=True, states={'draft': [('readonly', False)]}),
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
           ],'Service Type',readonly=True, states={'draft': [('readonly', False)]}),
        'package_type_fedex':fields.many2one('shipping.package.type.fedex','Packaging Type',help="What kind of package this will be shipped in"),
        'package_detail_fedex' : fields.selection([
                ('INDIVIDUAL_PACKAGES','INDIVIDUAL_PACKAGES'),
                ('PACKAGE_GROUPS','PACKAGE_GROUPS'),
                ('PACKAGE_SUMMARY','PACKAGE_SUMMARY'),
            ],'Package Detail',readonly=True, states={'draft': [('readonly', False)]}),
        'payment_type_fedex' : fields.selection([
                ('RECIPIENT','RECIPIENT'),
                ('SENDER','SENDER'),
                ('THIRD_PARTY','THIRD_PARTY'),
            ],'Payment Type', help="Who pays for the rate_request?",readonly=True, states={'draft': [('readonly', False)]}),
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
            ],'Physical Packaging',readonly=True, states={'draft': [('readonly', False)]}),
        'pickup_type_ups' : fields.selection([
                ('01','Daily Pickup'),
                ('03','Customer Counter'),
                ('06','One Time Pickup'),
                ('07','On Call Air'),
                ('11','Suggested Retail Rates'),
                ('19','Letter Center'),
                ('20','Air Service Center'),
            ],'Pickup Type',readonly=True, states={'draft': [('readonly', False)]}),
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
            ],'Service Type',readonly=True, states={'draft': [('readonly', False)]}),
        'package_type_ups':fields.many2one('shipping.package.type.ups','Packaging Type'),
        'shipping_label' : fields.binary('Logo',readonly=True, states={'draft': [('readonly', False)]}),
        'shipping_rate': fields.float('Shipping Rate',readonly=True, states={'draft': [('readonly', False)]}),
        'response_usps_ids' : fields.one2many('shipping.response','sale_order_id','Order Response',readonly=True, states={'draft': [('readonly', False)]}),
        'tracking_ids' : fields.one2many('package.tracking','saleorder_id','Tracking Details'),
        #removed required from pack_width and pack_height and pack_length
        'pack_length': fields.integer('Length', readonly=True, states={'draft': [('readonly', False)]}),
        'pack_width': fields.integer('Width',readonly=True, states={'draft': [('readonly', False)]}),
        'pack_height': fields.integer('Height',readonly=True, states={'draft': [('readonly', False)]}),
        'services': fields.many2one('service.name', 'Services',readonly=True, states={'draft': [('readonly', False)]}),
        'cana_length': fields.float('Length', digits=(16,2),readonly=True, states={'draft': [('readonly', False)]}),
        'cana_width': fields.float('Width', digits=(16,2),readonly=True, states={'draft': [('readonly', False)]}),
        'cana_height': fields.float('Height', digits=(16,2),readonly=True, states={'draft': [('readonly', False)]}),
        'rates': fields.text('Rates', size=1000),
        'invalid_addr': fields.boolean('Invalid Address',readonly=True),
        'tracking_no': fields.char('Tracking Number', size=320,readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal',readonly=True),
        'customsvalue':fields.float('Amount',readonly=True, states={'draft': [('readonly', False)]}),
#        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True,states={'draft': [('readonly', False)]}),
        'ecom_order':fields.boolean('E-Commerce Order'),
        'shipping_account':fields.selection([('my_account','My Account'),('customer_account','Partner Account')],'Shipping Account'),   #enchancement for customer shipping account
        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits'),
    }

    _defaults = {
        'shipping_account':'my_account',
        'service_type_usps' : 'All',
        'container_usps':'Parcel',
        'size_usps' : 'REGULAR',
        'dropoff_type_fedex' : 'REGULAR_PICKUP',
        'service_type_fedex' : 'FEDEX_GROUND',
        'package_type_fedex' : _get_default_package_fedex,
        'package_detail_fedex' : 'INDIVIDUAL_PACKAGES',
        'payment_type_fedex' : 'SENDER',
        'physical_packaging_fedex' : 'BOX',
        'pickup_type_ups' : '01',
        'service_type_ups' : '03',
        'package_type_ups' : _get_default_package_ups,
        'journal_id': _default_journal,
#        'currency_id':_get_euro,
        'weight_unit':'LB',
    }

    def copy_data(self, cr, uid, ids, default, context=None):
        if context is None:
            context = {}
        default.update({'tracking_no': '','carrier_id':[],'shipping_type':False, 'weight_package':0.0, 'response_usps_ids': [],'picking_ids':[], 'shipping_rate':0.0})
        return super(sale_order, self).copy_data(cr, uid, ids, default,{})

    def _prepare_order_picking(self, cr, uid, order, context=None):

        res = super(sale_order, self)._prepare_order_picking(cr, uid, order, context)
        if res.has_key('check_super') and res['check_super']:
            res.update({
                'carrier_id':order.carrier_id.id,
                'carrier_tracking_ref':order.tracking_no,
                'service_type_usps' : order.service_type_usps,
                'first_class_mail_type_usps' : order.first_class_mail_type_usps,
                'width_usps' : order.width_usps,
                'length_usps' : order.length_usps,
                'height_usps' : order.height_usps,
                'girth_usps' : order.girth_usps,
                'shipping_rate':order.shipping_rate,
                'shipping_label':order.shipping_label,
                'services' : order.services.id,
                'cana_length' : order.cana_length,
                'cana_width' : order.cana_width,
                'cana_height' : order.cana_height,
                'dropoff_type_fedex' : order.dropoff_type_fedex,
                'service_type_fedex' : order.service_type_fedex,
                'package_type_fedex' : order.package_type_fedex.id,
                'package_detail_fedex' : order.package_detail_fedex,
                'payment_type_fedex' : order.payment_type_fedex,
                'physical_packaging_fedex' : order.physical_packaging_fedex,
                'pack_length' : order.pack_length,
                'pack_height' : order.pack_height,
                'pack_width' : order.pack_width,
                'rates' : order.rates,
                'pickup_type_ups' : order.pickup_type_ups,
                'service_type_ups' : order.service_type_ups,
                'package_type_ups' : order.package_type_ups.id,
                'sale_id':order.id,
                'customsvalue' : order.customsvalue,
                'response_usps_ids': [(6,0,self.prepare_shipping_response(cr, uid, order, context=context))],
            })

        else:
            res.update({
                'sale_id':order.id,		
                'carrier_id':order.carrier_id.id,
                'carrier_tracking_ref':order.tracking_no,
                'use_shipping' : order.use_shipping,
                'shipping_type' : order.shipping_type,
                'weight_package' : order.weight_package,
                'service_type_usps' : order.service_type_usps,
                'first_class_mail_type_usps' : order.first_class_mail_type_usps,
                'container_usps' : order.container_usps,
                'size_usps' : order.size_usps,
                'width_usps' : order.width_usps,
                'length_usps' : order.length_usps,
                'height_usps' : order.height_usps,
                'girth_usps' : order.girth_usps,
                'shipping_rate':order.shipping_rate,
                'shipping_label':order.shipping_label,
                'services' : order.services.id,
                'cana_length' : order.cana_length,
                'cana_width' : order.cana_width,
                'cana_height' : order.cana_height,
                'dropoff_type_fedex' : order.dropoff_type_fedex,
                'service_type_fedex' : order.service_type_fedex,
                'package_type_fedex' : order.package_type_fedex.id,
                'package_detail_fedex' : order.package_detail_fedex,
                'payment_type_fedex' : order.payment_type_fedex,
                'physical_packaging_fedex' : order.physical_packaging_fedex,
                'pack_length' : order.pack_length,
                'pack_height' : order.pack_height,
                'pack_width' : order.pack_width,
                'rates' : order.rates,
                'pickup_type_ups' : order.pickup_type_ups,
                'service_type_ups' : order.service_type_ups,
                'package_type_ups' : order.package_type_ups.id,
                'customsvalue' : order.customsvalue,
                'response_usps_ids': [(6,0,self.prepare_shipping_response(cr, uid, order, context=context))],
            })
        return res

    # inherited to add shipping functionality
    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False,context=None):
        move_obj = self.pool.get('stock.move')
        stock_picking=self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        stock_obj=self.pool.get('stock.picking.out')
        shipp_resp_obj=self.pool.get('shipping.response')
        picking_obj = self.pool.get('stock.picking')
        proc_ids,shipping_res_id = [],''
        default_loc=order.shop_id and order.shop_id.warehouse_id.lot_stock_id.id or False
        if default_loc == False :
             raise osv.except_osv(_('No Warehouse!'), _('There\'s no Warehouse or Location Stock:'))
        if picking_id and order.use_shipping :
            try:
                pick_bwr = stock_picking.browse(cr,uid,picking_id)
                if pick_bwr.sale_id.shop_id.warehouse_id.auto_label_generation==True:
                    shipping_response=shipp_resp_obj.search(cr,uid,[('sale_order_id','=',order.id)])
                    carrier=order.carrier_id.name
                    if carrier:
                        shipping_type=order.shipping_type
                        if shipping_type=='Fedex':
                            cr.execute("update pack_track set height_ups='%s', length_ups='%s', width_ups='%s'  where picking_id='%s'"%(1,1,1,int(picking_id)))
                            cr.commit()
                        carrier_name=carrier.split(shipping_type+' ')[1]
                        if len(shipping_response)>1:
                            for each in shipping_response:
                                ship_res_bw=shipp_resp_obj.browse(cr,uid,each)
                                if ship_res_bw.name==carrier_name:
                                    shipping_res_id=each
                        elif not shipping_response:
                            stock_obj.cana_generate_shipping(cr,uid,[picking_id],context)
                        elif shipping_response:
                             shipping_res_id=shipping_response[0]
                        if shipping_res_id:
                            shipp_resp_obj.generate_tracking_no(cr,uid,[shipping_res_id],context)
            except:
                pass
        return super(sale_order, self)._create_pickings_and_procurements(cr, uid, order=order, order_lines=order_lines, picking_id=picking_id,context=context)

    def onchange_shipping_rates(self, cr, uid, ids, service_type,response_usps_ids,shipping_type,context=None):
        width = 0
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
	vals = {'response_usps_ids' : delete_att_vals,
                'pack_length' : width,
                'pack_width' : width,
                'pack_height' : width,
                'carrier_tracking_ref': '',
                'carrier_id':carrier_ids and carrier_ids[0] or ''
                }
        return {'value':vals}
sale_order()

# added to have label generation facility on sale order also.
class package_tracking(osv.osv):
    _name = 'package.tracking'
    _columns = {
        'width_ups' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
        'length_ups' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
        'height_ups' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),
        'saleorder_id' : fields.many2one('sale.order','Sale', ondelete="cascade"),
        'package_id': fields.many2one('product.packaging','Package Name'),
        'package_name':fields.char('Package Name',size=256),
    }

package_tracking()

class shipping_response(osv.osv):
    _name = 'shipping.response'
    _inherit = "shipping.response"

    def generate_tracking_sale(self, cr, uid, ids, context={}, error=True):
        import os; _logger.info("server name: %s", os.uname()[1])
        try:
            saleorder_obj = self.pool.get('sale.order')
            shippingresp_lnk = self.browse(cr,uid,ids[0])
            res_partner_obj=self.pool.get('res.partner')
            #Notice :- This is only for sale order
            type='out'
            ### Shipper
            ### based on stock.pickings type
            # added 'rate_received' to avoid label generation , if it is already generated
            rate_received = shippingresp_lnk.sale_order_id.shipping_rate
            # added
            shipping_account=shippingresp_lnk.sale_order_id.shipping_account
            if not rate_received or shippingresp_lnk.type.lower() == 'usps':
                if type == 'out':
                    cust_address = shippingresp_lnk.sale_order_id.shop_id and shippingresp_lnk.sale_order_id.shop_id.warehouse_id.partner_id
                elif type == 'in':
                    cust_address = shippingresp_lnk.sale_order_id.partner_shipping_id
                if not cust_address:
                    if error:
                        raise osv.except_osv(_('Error'), _('Shop Address not defined!'),)
                    else:
                        return False
                if not (cust_address.name or cust_address.partner_id.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
                if not cust_address.street:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Street."))
                if not cust_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
                if not cust_address.state_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper State Code."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
                shipper = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
                ### Recipient
                if type == 'out':
                    cust_address = shippingresp_lnk.sale_order_id.partner_id
                elif type == 'in':
                    cust_address = shippingresp_lnk.sale_order_id.shop_id and shippingresp_lnk.sale_order_id.shop_id.warehouse_id.partner_id
                if not cust_address:
                    if error:
                        raise osv.except_osv(_('Error'), _('Shipper Address not defined!'),)
                    else:
                        return False
                if not (cust_address.name or cust_address.partner_id.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
                receipient = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
                weight = shippingresp_lnk.weight
                rate = shippingresp_lnk.rate

                if shippingresp_lnk.type.lower() == 'usps' and not ('usps_active' in context.keys()):
                    usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
                    usps = shippingservice.USPSDeliveryConfirmationRequest(usps_info, shippingresp_lnk.name,weight,shipper,receipient)
                    usps_response = usps.send()
                    context['attach_id'] = saleorder_obj.create_attachment(cr,uid,[shippingresp_lnk.sale_order_id.id],usps_response,context)
                    saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'tracking_no':usps_response.tracking_number, 'shipping_label':binascii.b2a_base64(str(b64decode(usps_response.graphic_image))), 'shipping_rate': rate})
                    context['track_success'] = True
                    context['tracking_no'] = usps_response.tracking_number

                elif shippingresp_lnk.type.lower() == 'fedex':
                    # added for customer account
                    if shipping_account=='my_account':
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
                    elif shipping_account=='customer_account':
                        partner_data = shippingresp_lnk.sale_order_id.partner_id
                        if not partner_data.fedex_active :
                            raise osv.except_osv(_('Error'), _('Default Fedex settings not defined'))
                        account_no = partner_data.account_no
                        key = partner_data.key
                        password = partner_data.fedex_password
                        meter_no = partner_data.meter_no
                        is_test = partner_data.fedex_test
                    #  added
                    if shippingresp_lnk.name in ('INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY'):
                            if not fedex_servicedetails.customsvalue and not fedex_servicedetails.currency_id:
                                raise osv.except_osv(_('Warning'), _('Please enter Amount and Currency values'))
                    CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)
                    # We're using the FedexConfig object from example_config.py in this dir.
                    shipment = FedexProcessShipmentRequest(CONFIG_OBJ)
                    # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
                    fedex_servicedetails = saleorder_obj.browse(cr,uid,shippingresp_lnk.sale_order_id.id)
                    shipment.RequestedShipment.DropoffType = fedex_servicedetails.dropoff_type_fedex #'REGULAR_PICKUP'
                    # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
                    # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
    #                shipment.RequestedShipment.ServiceType = fedex_servicedetails.service_type_fedex #'PRIORITY_OVERNIGHT'
                    shipment.RequestedShipment.ServiceType = shippingresp_lnk.name #'PRIORITY_OVERNIGHT'
                    # What kind of package this will be shipped in.
                    # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
                    shipment.RequestedShipment.PackagingType = fedex_servicedetails.package_type_fedex.name  #'FEDEX_PAK'
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
    #                package1_weight.Units = fedex_servicedetails.weight_unit
                    package1_weight.Units = "LB"
                    package1 = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                    package1.Weight = package1_weight
                    # added
                    move_lines = shippingresp_lnk.sale_order_id.order_line
                    pack_weight_merge={}
                    pack_id=[]
                    count=0
                    for each_move_lines in move_lines:
                        tracking_id=each_move_lines.product_packaging
                        if each_move_lines.th_weight <= 0.0:
                            raise osv.except_osv(_('Warning'), _('Please assign weight to each order lines'),)
                        else:
                            if tracking_id:
                                val=pack_weight_merge.get(tracking_id.id,False)
                                if val:
                                    val = float(each_move_lines.th_weight) + float(val)
                                    pack_weight_merge[tracking_id.id]=val
                                else:
                                    pack_weight_merge[tracking_id.id]=each_move_lines.th_weight
                                    pack_id.append(tracking_id)
                    tracking_lines = shippingresp_lnk.sale_order_id.tracking_ids
                    if not tracking_lines :
                        raise osv.except_osv(_('Warning!'), _('Please enter Fedex Dimmensions.'),)
                    if tracking_lines:
                        for each_tracking_lines in tracking_lines:
                            package1_dimension = shipment.create_wsdl_object_of_type('Dimensions')
                            package1_dimension.Length=int(each_tracking_lines.length_ups)
                            package1_dimension.Width=int(each_tracking_lines.width_ups)
                            package1_dimension.Height=int(each_tracking_lines.height_ups)
                            package1_dimension.Units='IN'
                            package1.Dimensions=package1_dimension
                    shipment.add_package(package1)
                    try:
                        shipment.send_request()
                    except Exception, e:
                        if error:
                            errormessage = e
                            raise osv.except_osv(_('Error'), _('%s' % (errormessage,)))
                    # This will show the reply to your shipment being sent. You can access the
                    # attributes through the response attribute on the request object. This is
                    # good to un-comment to see the variables returned by the Fedex reply.
                    # Here is the overall end result of the query.
                    # Getting the tracking number from the new shipment.
                    fedexTrackingNumber = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                    # Net shipping costs.
                    if fedex_servicedetails.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
                        fedexshippingrate = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount
                    else:
                        fedexshippingrate = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount
                    # Get the label image in ASCII format from the reply. Note the list indices
                    # we're using. You'll need to adjust or iterate through these if your shipment
                    # has multiple packages.
                    ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
                    # Convert the ASCII data to binary.
                    """
                    #This is an example of how to dump a label to a PNG file.
                    """
                    # This will be the file we write the label out to.
                    fedex_attachment_pool = self.pool.get('ir.attachment')
                    fedex_data_attach = {
                        'name': 'ShippingLabel.png',
                        'datas': binascii.b2a_base64(str(b64decode(ascii_label_data))),
                        'description': 'Packing List',
                        'res_name': shippingresp_lnk.sale_order_id.name,
                        'res_model': 'sale.order',
                        'res_id': shippingresp_lnk.sale_order_id.id,
                    }
                    fedex_attach_id = fedex_attachment_pool.search(cr,uid,[('res_id','=',shippingresp_lnk.sale_order_id.id),('res_name','=',shippingresp_lnk.sale_order_id.name)])
                    if not fedex_attach_id:
                        fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
                    else:
                        fedex_attach_result = fedex_attachment_pool.write(cr, uid, fedex_attach_id, fedex_data_attach)
                        fedex_attach_id = fedex_attach_id[0]
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
                    if fedexTrackingNumber:
                        saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'tracking_no':fedexTrackingNumber, 'shipping_label':binascii.b2a_base64(str(b64decode(ascii_label_data))), 'shipping_rate': fedexshippingrate})
                        context['track_success'] = True

                elif shippingresp_lnk.type.lower() == 'ups':
                    # added
                    move_lines = shippingresp_lnk.sale_order_id.order_line
                    pack_weight_merge = []
                    pack_id=[]
                    for each_move_lines in move_lines:
                        if each_move_lines.th_weight <= 0.0:
                            raise osv.except_osv(_('Warning'), _('Please assign weight to each order lines'),)
                        else:
                            pack_weight_merge.append(each_move_lines.th_weight)
                    shipping_account=shippingresp_lnk.sale_order_id.shipping_account
                    if shipping_account=='my_account':
                        ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                    elif shipping_account=='customer_account':
                        context['partner_id']=shippingresp_lnk.sale_order_id.partner_id.id
                        ups_info=res_partner_obj.get_ups_info(cr,uid,context)
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please select which shipping account type you want"))
                    ####################For Each UPS seperate dimension#################
                    tracking_lines = shippingresp_lnk.sale_order_id.tracking_ids
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
                    if len(tracking_lines) > len(shippingresp_lnk.sale_order_id.order_line):
                        raise osv.except_osv(_('Warning!'), _('No. of Package line should not be greater than sale order line'),)
                    pickup_type_ups = shippingresp_lnk.sale_order_id.pickup_type_ups
                    for key, value in ups_service_type.items():
                         if value == shippingresp_lnk.name:
                            service_code = key
                    service_type_ups = service_code
                    desc = shippingresp_lnk.sale_order_id.name
                    package_type_ups = shippingresp_lnk.sale_order_id.package_type_ups.ups_value
                    ups = shippingservice.UPSShipmentConfirmRequest(ups_info, pickup_type_ups, service_type_ups, package_type_ups, weight, shipper, receipient,length_merge,width_merge,height_merge,pack_weight_merge,shipping_account,desc)
                    ups_response = ups.send()
                    ups = shippingservice.UPSShipmentAcceptRequest(ups_info, ups_response.shipment_digest,shipping_account)
                    ups_response = ups.send()
                    saleorder_obj.create_attachment(cr,uid,[shippingresp_lnk.sale_order_id.id],ups_response,context)
                    tracking_number=''
                    all_tracking_number=''
                    for i in range(0,ups_response.package_count):
                        label_image = ups_response.graphic_image[i]
                        tracking_number=ups_response.tracking_number[i]
                        if i == 0:
                            all_tracking_number +=ups_response.tracking_number[i]
                        else:
                            all_tracking_number +=',' + ups_response.tracking_number[i]
                    saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'tracking_no':all_tracking_number, 'shipping_label':binascii.b2a_base64(str(b64decode(label_image))), 'shipping_rate': rate, 'label_recvd': True})
                    context['track_success'] = True
                    context['tracking_no'] = all_tracking_number
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
                    raise osv.except_osv(_('Warning!'), _('Delivery Method for this service type not defined'))
                return False
            saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'carrier_id':carrier_ids[0]})
            saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'tracking_no':context['tracking_no'], 'carrier_id':carrier_ids[0]})
            ### Write this shipping response is selected
            self.write(cr,uid,ids[0],{'selected':True})
            # code for creating product
            product_obj = self.pool.get('product.product')
            ship_prod_id = product_obj.search(cr, uid, [('name','=','Shipping Service')])
            ship_rate = shippingresp_lnk.rate
            if not ship_prod_id:
                product_val = {
                    'name':'Shipping Service',
                    'type':'service',
                    'list_price':ship_rate,
                    'standard_price':ship_rate,
                }
                shipping_prod_id = product_obj.create(cr, uid, product_val)
            else :
                shipping_prod_id = ship_prod_id[0]
                product_obj.write(cr, uid, ship_prod_id, {'list_price':ship_rate,'standard_price':ship_rate}, context=context)
            sale_line_data = {
                'product_id':shipping_prod_id,
                'name':'Shipping Service',
                'order_id':shippingresp_lnk.sale_order_id.id,
            }
            sale_line_id = self.pool.get('sale.order.line').create(cr, uid, sale_line_data)
            if context.get('batch_printing',False):
                return True
            return True
        else:
            return False

shipping_response()
