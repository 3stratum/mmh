# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields, osv
from fedex.config import FedexConfig
from fedex.services.rate_service import FedexRateServiceRequest
from fedex.services.ship_service import FedexProcessShipmentRequest
import logging
_logger = logging.getLogger(__name__)

class res_partner(osv.osv):
    _inherit = "res.partner"
    _columns = {
        'address_checked' : fields.boolean('Address Checked',readonly=True),
        'invalid_addr': fields.boolean('Invalid Address',readonly=True),
        #enchancement for customer shipping account done by saziya
        'ups_name': fields.char('UPS Name', size=64, translate=True),
        'account_no': fields.char('Account Number', size=64),
        'key': fields.char('Key', size=64 ),
        'ups_password': fields.char('Password', size=64),
        'meter_no': fields.char('Meter Number', size=64),
        'integrator_id': fields.char('Integrator ID', size=64),
        'ups_test' : fields.boolean('Is test?'),
        'ups_active' : fields.boolean('Active'),
        'fedex_name': fields.char('Fedex Name', size=64, translate=True),
        'access_license_no': fields.char('Access License Number', size=64),
        'ups_user_id': fields.char('UserID', size=64),
        'fedex_password': fields.char('Password', size=64),
        'shipper_no': fields.char('Shipper Number', size=64),
        'fedex_test' : fields.boolean('Is test?'),
        'fedex_active' : fields.boolean('Active'),
        'usps_name': fields.char('USPS Name', size=64, translate=True),
        'usps_user_id': fields.char('UserID', size=64, translate=True),
        'usps_test' : fields.boolean('Is test?'),
        'usps_active' : fields.boolean('Active'),
        'weight_measure':fields.selection([('LBS','LBS'),('KGS','KGS')],'Weight Measurement'),

    }

    #enhancement for customer shipping account done by saziya
    def get_ups_info(self,cr,uid,context=None):
        partner_obj = self.browse(cr, uid, context.get('partner_id'),context=context)
        ship_ups_id = self.search(cr,uid,[('ups_active','=',True),('id','=',context.get('partner_id'))])
        if not ship_ups_id:
            if 'error' not in context.keys() or context.get('error',False):
                raise osv.except_osv(_('Warning !'),_('Active UPS settings not defined for partner "%s" '% (partner_obj.name)))
            else:
                return False
        else:
            ship_ups_id = ship_ups_id[0]
        return self.browse(cr,uid,ship_ups_id)

    def get_usps_info(self,cr,uid,context=None):
        ship_usps_id = self.search(cr,uid,[('usps_active','=',True),('partner_id','=',context.get('partner_id'))])
        if not ship_usps_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites
            if 'error' not in context.keys() or context.get('error',False):
                raise osv.except_osv(_('Warning !'),_('Active USPS settings not defined'))
            else:
                return False
        else:
            ship_usps_id = ship_usps_id[0]
        return self.browse(cr,uid,ship_usps_id)

    def get_fedex_info(self,cr,uid,context=None):        
        partner_obj = self.browse(cr, uid, context.get('partner_id'),context=context)                
        shippingfedex_id = self.search(cr,uid,[('id','=',context.get('partner_id')),('fedex_active','=',True)])        
        if not shippingfedex_id:            
            raise osv.except_osv(_('Warning !'),_('Active Fedex settings not defined in Partner "%s"'%(partner_obj.name)))
        else:
            shippingfedex_id = shippingfedex_id[0]
        return self.browse(cr,uid,shippingfedex_id)

    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, sys_default=False,cust_default=False, error=True, context=None,fed_length=None,fed_width=None,fed_height=None,partner_id=None):
        if 'fedex_active' in context.keys() and context['fedex_active'] == False:
            return True
        res_partner_obj = self.pool.get('res.partner')
        shippingfedex_id = res_partner_obj.search(cr,uid,[('fedex_active','=',True),('id','=',partner_id)])
        if not shippingfedex_id:
            if error:                
                raise osv.except_osv(_('Warning !'),_('Active Fedex settings not defined!'))
            else:
                return False
        else:
            shippingfedex_id = shippingfedex_id[0]
        shippingfedex_ptr = res_partner_obj.browse(cr,uid,shippingfedex_id)
        account_no = shippingfedex_ptr.account_no
        key = shippingfedex_ptr.key
        password = shippingfedex_ptr.password
        meter_no = shippingfedex_ptr.meter_no
        is_test = shippingfedex_ptr.fedex_test
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
        package1_dimensions=rate_request.create_wsdl_object_of_type('Dimensions')
        package1_dimensions.Length=int(fed_length)
        package1_dimensions.Width=int(fed_width)
        package1_dimensions.Height=int(fed_height)
        package1_dimensions.Units="IN"
        _logger.info("Package Dimensions %s", package1_dimensions)
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
        #print 'response: ', rate_request.response

        # Here is the overall end result of the query.
#        _logger.info("Highest Severity %s", rate_request.response.HighestSeverity)
#
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


    ########
res_partner()