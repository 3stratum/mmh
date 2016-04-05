# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
import re
import math
import urllib
from urllib2 import Request, urlopen, URLError, quote
import xml.etree.ElementTree as etree
from xml.dom.minidom import parse, parseString
from openerp.osv import fields, osv
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

ups_service_type = {
    '01': 'Next Day Air',
    'ups_1DA': 'Next Day Air',
    '02': 'Second Day Air',
    'ups_2DA': 'Second Day Air',
    '03': 'Ground',
    'ups_GND': 'Ground',
    '07': 'Worldwide Express',
    '08': 'Worldwide Expedited',
    '11': 'Standard',
    '12': 'Three-Day Select',
    'ups_3DS': 'Three-Day Select',
    '13': 'Next Day Air Saver',
    'ups_1DP': 'Next Day Air Saver',
    '14': 'Next Day Air Early AM',
    'ups_1DM': 'Next Day Air Early AM',
    '54': 'Worldwide Express Plus',
    '59': 'Second Day Air AM',
    '65': 'Saver',
}

fedex_service_code={
    'EUROPE_FIRST_INTERNATIONAL_PRIORITY':'EUROPEFIRSTINTERNATIONALPRIORITY',
    'FEDEX_1_DAY_FREIGHT':'FEDEX1DAYFREIGHT',
    'FEDEX_2_DAY':'FEDEX2DAY',
    'FEDEX_2_DAY_FREIGHT':'FEDEX2DAYFREIGHT',
    'FEDEX_3_DAY_FREIGHT':'FEDEX3DAYFREIGHT',
    'FEDEX_EXPRESS_SAVER':'FEDEXEXPRESSSAVER',
    'STANDARD_OVERNIGHT':'STANDARDOVERNIGHT',
    'PRIORITY_OVERNIGHT':'PRIORITYOVERNIGHT',
    'FEDEX_GROUND':'FEDEXGROUND',
    'FIRST_OVERNIGHT':'FIRSTOVERNIGHT',
    'GROUND_HOME_DELIVERY':'GROUNDHOMEDELIVERY',
    'INTERNATIONAL_ECONOMY':'INTERNATIONALECONOMY',
    'INTERNATIONAL_ECONOMY_FREIGHT':'INTERNATIONALECONOMYFREIGHT',
    'INTERNATIONAL_FIRST':'INTERNATIONALFIRST',
    'INTERNATIONAL_PRIORITY':'INTERNATIONALPRIORITY',
    'INTERNATIONAL_PRIORITY_FREIGHT':'INTERNATIONALPRIORITYFREIGHT',
    'INTERNATIONAL_GROUND':'INTERNATIONALGROUND',
    }


class Error(object):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        _logger.info("%s", self.message)
        raise

class Shipping(object):
    def __init__(self, weight, shipper,receipient):
        self.weight = weight
        self.shipper = shipper
        self.receipient = receipient

class FedexShipping(Shipping):
    def __init__(self, weight, shipper,receipient):
        super(FedexShipping, self).__init__(weight,shipper,receipient)

    def send(self,):
        datas = self._get_data()
        data = datas[0]
        api_url = datas[1]
        request = Request(api_url, data)
        response_text = urlopen(request).read()
        response = self.__parse_response(response_text)
        return response

    def __parse_response(self, response_text):
        root = etree.fromstring(response_text)
        status_code = root.findtext('SoftError')
        response = self._parse_response_body(root)
        return response

class FedexRateRequest(FedexShipping):

    def __init__(self, ups_info,dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper,receipient,sys_default,cust_default,shipping_account,carrier_code):
        self.type = 'Fedex'
        self.ups_info = ups_info
        self.dropoff_type_fedex = dropoff_type_fedex
        self.service_type_fedex = service_type_fedex
        self.packaging_type_fedex = packaging_type_fedex
        self.package_detail_fedex = package_detail_fedex
        self.payment_type_fedex = payment_type_fedex
        self.physical_packaging_fedex = physical_packaging_fedex
        self.cust_default = cust_default
        self.sys_default = sys_default
        self.shipping_account= shipping_account
        self.carrier_code= carrier_code
        super(FedexRateRequest, self).__init__(weight,shipper,receipient)


    def _get_data(self):
        data = []
        if self.shipping_account=='customer_account':
             test=self.ups_info.fedex_test
        else:
             test=self.ups_info.test
        data.append("""<?xml version="1.0" encoding="UTF-8" ?>
<FDXRateAvailableServicesRequest xmlns:api="http://www.fedex.com/fsmapi" xmlns:xsi="http://www.w3.org/2001/XMLSchema-
instance" xsi:noNamespaceSchemaLocation="FDXRateAvailableServicesRequest.xsd">
<RequestHeader>
<CustomerTransactionIdentifier></CustomerTransactionIdentifier>
<AccountNumber>%s</AccountNumber>
<MeterNumber>%s</MeterNumber>
<CarrierCode>%s</CarrierCode>
</RequestHeader>
<ShipDate></ShipDate>
<DropoffType>%s</DropoffType>
<Packaging>YOURPACKAGING</Packaging>
<WeightUnits>LBS</WeightUnits>
<Weight>%s</Weight>
<ListRate>True</ListRate>
<OriginAddress>
<StateOrProvinceCode>%s</StateOrProvinceCode>
<PostalCode>%s</PostalCode>
<CountryCode>%s</CountryCode>
</OriginAddress>
<DestinationAddress>
<StateOrProvinceCode>%s</StateOrProvinceCode>
<PostalCode>%s</PostalCode>
<CountryCode>%s</CountryCode>
</DestinationAddress>
<Payment>
<PayorType>%s</PayorType>
</Payment>
<PackageCount>1</PackageCount>
</FDXRateAvailableServicesRequest>""" % (self.ups_info.account_no,self.ups_info.meter_no,self.carrier_code,self.dropoff_type_fedex,self.weight,self.shipper.state_code,self.shipper.zip,self.shipper.country_code,self.receipient.state_code,self.receipient.zip,self.receipient.country_code,self.payment_type_fedex))
        data.append('https://gatewaybeta.fedex.com/GatewayDC' if test else 'https://gateway.fedex.com/GatewayDC')
#        _logger.info("Response data %s", data)
        return data

    def _parse_response_body(self, root):
        return FedexRateResponse(root, self.weight, self.cust_default, self.sys_default)

class FedexRateResponse(object):

    def __init__(self, root, weight, cust_default, sys_default):
        self.root = root
        iter_array = root.getiterator('Entry')
        dict  = {}
        for i in iter_array:
            rate = i.findtext('EstimatedCharges/DiscountedCharges/NetCharge')
            negotiatedrate = i.findtext('EstimatedCharges/DiscountedCharges/BaseCharge')
            for key, value in fedex_service_code.items():
                if value == i.findtext('Service'):                    
                    service_type = key                    
                    dict[service_type] = {'code':key,'rate':rate,'negotiatedrates':negotiatedrate}
        self.rate = dict
        self.service_type = ''
        self.weight = ''
        self.sr_no = ''

    def __repr__(self):
        return (self.service_type, self.rate, self.weight, self.sr_no)

class UPSShipping(Shipping):
    def __init__(self, weight, shipper,receipient):
        super(UPSShipping, self).__init__(weight,shipper,receipient)

    def send(self,):
        datas = self._get_data()
        data = datas[0]
        api_url = datas[1]
        request = Request(api_url, data)        
        response_text = urlopen(request).read()
#        _logger.info("ups response_text: %s", response_text)
        response = self.__parse_response(response_text)
        return response

    def __parse_response(self, response_text):
        root = etree.fromstring(response_text)
        status_code = root.findtext('Response/ResponseStatusCode')
        if status_code != '1':
#            raise Exception('UPS: %s' % (root.findtext('Response/Error/ErrorDescription')))
            raise osv.except_osv(_('Warning !'),_('UPS: %s'% (root.findtext('Response/Error/ErrorDescription'))))
        else:
            response = self._parse_response_body(root)
        return response

class UPSRateRequest(UPSShipping):

    def __init__(self, ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper,receipient, cust_default, sys_default,shipping_account):
        self.type = 'UPS'
        self.ups_info = ups_info
        self.pickup_type_ups = pickup_type_ups
        self.service_type_ups = service_type_ups
        self.packaging_type_ups = packaging_type_ups
        self.cust_default = cust_default
        self.sys_default = sys_default
        self.shipping_account= shipping_account
        super(UPSRateRequest, self).__init__(weight,shipper,receipient)

    def _get_data(self):
        data = []
        if self.shipping_account=='customer_account':
            test=self.ups_info.ups_test
            user_id=self.ups_info.ups_user_id
            password=self.ups_info.ups_password
            self.shipper=self.receipient
            weight_unit=self.ups_info.weight_measure
        else:
            test=self.ups_info.test
            user_id=self.ups_info.user_id
            password=self.ups_info.password
            weight_unit='LBS'
        data.append("""<?xml version=\"1.0\"?>
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
                    <RequestOption>Shop</RequestOption>
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
                            <Code>%s</Code>
                        </UnitOfMeasurement>
                        <Weight>%s</Weight>
                    </PackageWeight>
                </Package>
            </Shipment>
            </RatingServiceSelectionRequest>""" % (self.ups_info.access_license_no,user_id,password,self.pickup_type_ups,self.shipper.zip,self.shipper.country_code,self.ups_info.shipper_no,self.receipient.zip,self.receipient.country_code,self.shipper.zip,self.shipper.country_code,'',self.packaging_type_ups,weight_unit,self.weight))
        data.append('https://wwwcie.ups.com/ups.app/xml/Rate' if test else 'https://onlinetools.ups.com/ups.app/xml/Rate')
        _logger.info("Response data %s", data)
        return data

    def _parse_response_body(self, root):
        return UPSRateResponse(root, self.weight, self.cust_default, self.sys_default)


class UPSRateResponse(object):
    def __init__(self, root, weight, cust_default, sys_default):
        self.root = root
        iter_array = root.getiterator('RatedShipment')
        dict  = {}
        for i in iter_array:
            rate = i.findtext('TotalCharges/MonetaryValue')
            negotiatedrate = i.findtext('NegotiatedRates/NetSummaryCharges/GrandTotal/MonetaryValue')
            service_type = ups_service_type[i.findtext('Service/Code')]
            dict[service_type] = {'code':i.findtext('Service/Code'),'rate':rate,'negotiatedrates':negotiatedrate}
        self.rate = dict
        self.service_type = ''
        self.weight = ''
        self.sr_no = ''

    def __repr__(self):
        return (self.service_type, self.rate, self.weight, self.sr_no)
        

class UPSShipmentConfirmRequest(UPSShipping):
    def __init__(self, ups_info, pickup_type_ups, service_type_ups, packaging_type_ups,weight, shipper,receipient,length_merge,width_merge,height_merge,pack_weight_merge=None,shipping_account=None,desc=None):
        self.type = 'UPS'
        self.ups_info = ups_info
        self.pickup_type_ups = pickup_type_ups
        self.service_type_ups = service_type_ups
        self.packaging_type_ups = packaging_type_ups
        self.length_ups = length_merge
        self.width_ups = width_merge
        self.height_ups = height_merge
        self.pack_weight_merge = pack_weight_merge
        self.shipping_account = shipping_account
        self.desc=desc
        super(UPSShipmentConfirmRequest, self).__init__(weight,shipper,receipient)

    def _get_data(self):
        data = []
        package_data=''
        pack_weight_merge=[]
        dim_len=len(self.length_ups)        
        if self.shipping_account=='customer_account':
            test=self.ups_info.ups_test
            user_id=self.ups_info.ups_user_id
            password=self.ups_info.ups_password
            self.shipper=self.receipient
            weight_unit=self.ups_info.weight_measure
        else:
            test=self.ups_info.test
            user_id=self.ups_info.user_id
            password=self.ups_info.password
            weight_unit='LBS'
        for i in range(0,dim_len):
            length_ups=self.length_ups[i]
            width_ups=self.width_ups[i]
            height_ups=self.height_ups[i]
            weight=self.pack_weight_merge[i]
            package_data += """<Package>
                        <PackagingType>
                            <Code>%s</Code>
                        </PackagingType>
                        <PackageWeight>
                            <Weight>%s</Weight>
                        </PackageWeight>
                        <Dimensions>
                            <UnitOfMeasurement>
                                <Code>IN</Code>
                            </UnitOfMeasurement>
                                <Length>%s</Length>
                                <Width>%s</Width>
                                <Height>%s</Height>
                        </Dimensions>
                    </Package>""" % (self.packaging_type_ups, weight, length_ups, width_ups, height_ups)########3(self.packaging_type_ups, weight, length_ups, width_ups, height_ups, self.ref1,self.ref2)
        xml_data="""<?xml version="1.0" ?>
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
                        <Description>%s</Description>
                     <Shipper>
                  <Name>%s</Name>
                  <AttentionName>%s</AttentionName>
                  <PhoneNumber>%s</PhoneNumber>
                  <ShipperNumber>%s</ShipperNumber>
                  <Address>
                       <AddressLine1>%s</AddressLine1>
                       <AddressLine2>%s</AddressLine2>
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
                       <AddressLine2>%s</AddressLine2>
                       <AddressLine1>%s</AddressLine1>
                       <City>%s</City>
                       <StateProvinceCode>%s</StateProvinceCode>
                       <CountryCode>%s</CountryCode>
                       <PostalCode>%s</PostalCode>
                       <ResidentialAddress />
                  </Address>
             </ShipTo>
             <Service>
                  <Code>%s</Code>
                  <Description>%s</Description>
             </Service>
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
             </PaymentInformation>"""% (self.ups_info.access_license_no,user_id,password,self.desc, self.shipper.company_name, self.shipper.name, self.shipper.phone, self.ups_info.shipper_no, self.shipper.address1,self.shipper.address2, self.shipper.city, self.shipper.state_code, self.shipper.country_code, self.shipper.zip, self.receipient.company_name, self.receipient.name, self.receipient.phone, self.receipient.address2, self.receipient.address1,self.receipient.city, self.receipient.state_code, self.receipient.country_code, self.receipient.zip,self.service_type_ups, ups_service_type[self.service_type_ups])
        label_data= """
            </Shipment>
            <LabelSpecification>
                <LabelPrintMethod>
                    <Code>GIF</Code>
                </LabelPrintMethod>
                <LabelImageFormat>
                    <Code>GIF</Code>
                </LabelImageFormat>
            </LabelSpecification>
        </ShipmentConfirmRequest>"""
        shipment_data=xml_data+package_data+label_data
#        _logger.info("Shipment data: %s", shipment_data)
        data.append(shipment_data)
        data.append('https://wwwcie.ups.com/ups.app/xml/ShipConfirm' if test else 'https://onlinetools.ups.com/ups.app/xml/ShipConfirm')
#        _logger.info("data: %s", data)
        return data

    def _parse_response_body(self, root):
        return UPSShipmentConfirmResponse(root)
        

class UPSShipmentConfirmResponse(object):
    def __init__(self, root):
        self.root = root
        self.shipment_digest = root.findtext('ShipmentDigest')

    def __repr__(self):
        return (self.shipment_digest)

class UPSShipmentAcceptRequest(UPSShipping):
    def __init__(self, ups_info, shipment_digest,shipping_account):        
        self.ups_info = ups_info
        self.shipment_digest = shipment_digest
        self.shipping_account = shipping_account

    def _get_data(self):
        data = []        
        if self.shipping_account=='customer_account':
            test=self.ups_info.ups_test
            user_id=self.ups_info.ups_user_id
            password=self.ups_info.ups_password
#            self.shipper=self.receipient
        else:
            test=self.ups_info.test
            user_id=self.ups_info.user_id
            password=self.ups_info.password
        data.append("""
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
</ShipmentAcceptRequest>""" % (self.ups_info.access_license_no,user_id,password,self.shipment_digest))

        data.append('https://wwwcie.ups.com/ups.app/xml/ShipAccept' if test else 'https://onlinetools.ups.com/ups.app/xml/ShipAccept')
        return data

    def _parse_response_body(self, root):
        return UPSShipmentAcceptResponse(root)

class UPSShipmentAcceptResponse(object):
    def __init__(self, root):
        self.root = root
        tracking_number_list =[]
        graphic_image_list=[]
        image=[]
        html_image_list=[]
        iter_array=root.getiterator('PackageResults')
        for i in iter_array:
            children = i.getchildren()
            tracking = children[0]
            image = children[2]
            tracking_number_list.append(tracking.text)
            graphic_image_list.append(image.getchildren()[1].text)
            html_image_list.append(image.getchildren()[2].text)
        image_format_list = root.findtext('ShipmentResults/PackageResults/LabelImage/LabelImageFormat/Code')
        self.image_format  = image_format_list
        self.tracking_number = tracking_number_list
        self.graphic_image = graphic_image_list
        self.html_image = html_image_list
        self.package_count = len(iter_array)

    def __repr__(self):
        return (self.tracking_number, self.image_format, self.graphic_image)

class USPSShipping(Shipping):
    def __init__(self, weight, shipper,receipient):        
        super(USPSShipping, self).__init__(weight,shipper,receipient)

    def send(self,):
        datas = self._get_data()
        print "dataaaaaaaaaaaaaaaaaaaaaa",datas
        data = datas[0]
        api_url = datas[1]
        values = {}
        values['XML'] = data
        api_url = api_url + urllib.urlencode(values)
        request = urlopen(api_url)
        response_text = request.read()
        response = self.__parse_response(response_text)
        return response

    def __parse_response(self, response_text):
        responseDOM = parseString(response_text)
        root = etree.fromstring(response_text)
        desc_error = ''
        for each in  responseDOM.getElementsByTagName('Error'):
            descp = each.getElementsByTagName('Description')[0].toxml()
            descData=descp.replace('<Description>','').replace('</Description>','')
            desc_error +=descData+' '
        response = self._parse_response_body(root)
        return response

class USPSRateRequest(USPSShipping):
    def __init__(self, usps_info, service_type_usps, first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default=False, sys_default=False,shipping_account=False):
        self.type = 'USPS'
        self.usps_info = usps_info
        self.service_type_usps = service_type_usps
        self.first_class_mail_type_usps = first_class_mail_type_usps
        self.container_usps = container_usps
        self.size_usps = size_usps
        self.width_usps = width_usps
        self.length_usps = length_usps
        self.height_usps = height_usps
        self.girth_usps = girth_usps
        self.cust_default = cust_default
        self.sys_default = sys_default
        self.shipping_account= shipping_account
        super(USPSRateRequest, self).__init__(weight,shipper,receipient)

    def _get_data(self):
        data = []
        if self.shipping_account=='customer_account':
            test=self.usps_info.usps_test
            user_id=self.usps_info.usps_user_id
        else:
            test=self.usps_info.test
            user_id=self.usps_info.user_id
        service_type = '<Service>' + self.service_type_usps + '</Service>'
        if self.service_type_usps == 'First Class':
            service_type += '<FirstClassMailType>' + self.first_class_mail_type_usps + '</FirstClassMailType>'
        shipper_zip=self.shipper.zip if self.shipper else ''
        recept_zip=self.receipient.zip if self.receipient else ''
        weight = math.modf(self.weight)
        pounds = int(weight[1])
        ounces = round(weight[0],2) * 16
        container = self.container_usps and '<Container>' + self.container_usps + '</Container>' or '<Container/>'
        size = '<Size>' + str(self.size_usps) + '</Size>'
        if self.size_usps == 'LARGE':
            size += '<Width>' + str(self.width_usps) + '</Width>'
            size += '<Length>' + str(self.length_usps) + '</Length>'
            size += '<Height>' + str(self.height_usps) + '</Height>'
            if self.container_usps == 'Non-Rectangular' or self.container_usps == 'Variable' or self.container_usps == '':
                size += '<Girth>' + str(self.girth_usps) + '</Girth>'
        data.append('<RateV4Request USERID="' + user_id + '"><Revision/><Package ID="1ST">' + service_type + '<ZipOrigination>' + shipper_zip + '</ZipOrigination><ZipDestination>' + recept_zip + '</ZipDestination><Pounds>' + str(pounds) + '</Pounds><Ounces>' + str(ounces) + '</Ounces>' + container + size + '<Machinable>true</Machinable></Package></RateV4Request>')
        data.append("http://production.shippingapis.com/ShippingAPI.dll?API=RateV4&")
        return data


    def _parse_response_body(self, root):
        return USPSRateResponse(root, self.weight, self.cust_default, self.sys_default)
    
class USPSRateResponse(object):
    def __init__(self, root, weight, cust_default, sys_default):
        self.root = root
        self.type = 'USPS'
        self.postage = []
        self.service_type = []
        postages = root.findall("Package/Postage")
        cust_default = "USPS/Priority Mail"
        if postages:
            for postage in postages:
                mail_service = postage.findtext('MailService').replace("&lt;sup&gt;&amp;reg;&lt;/sup&gt;","")
                sr_no = 1 if cust_default and cust_default.split('/')[0] == self.type and cust_default.split('/')[1] == mail_service else 9
                sr_no = 2 if sr_no == 9 and sys_default and sys_default.split('/')[0] == self.type and sys_default.split('/')[1] == mail_service else sr_no
                self.postage.append({'Rate':postage.findtext('Rate'), 'Service':mail_service, 'sr_no': sr_no})
        self.weight = weight

    def __repr__(self):
        return (self.service_type, self.rate, self.weight, self.sr_no)


class USPSDeliveryConfirmationRequest(USPSShipping):
    def __init__(self, usps_info, service_type_usps, weight, shipper, receipient,shipping_account):
        self.usps_info = usps_info
        self.service_type_usps = service_type_usps
        self.shipping_account = shipping_account
        self.weight = weight
        self.shipper = shipper
        self.receipient = receipient
        super(USPSDeliveryConfirmationRequest, self).__init__(weight,shipper,receipient)

    def _get_usps_servicename(self, service):
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

    def _get_data(self):
        data = []
        if self.shipping_account=='customer_account':
            test=self.usps_info.usps_test
            user_id=self.usps_info.usps_user_id
        else:
            test=self.usps_info.test
            user_id=self.usps_info.user_id
        data.append('<?xml version="1.0" encoding="UTF-8" ?><DeliveryConfirmationV3.0Request USERID="' + user_id + '"><Option>1</Option><ImageParameters></ImageParameters><FromName>' + self.shipper.name + '</FromName><FromFirm>' + self.shipper.company_name + '</FromFirm><FromAddress1>' + self.shipper.address2 + '</FromAddress1><FromAddress2>' + self.shipper.address1 + '</FromAddress2><FromCity>' + self.shipper.city + '</FromCity><FromState>' + self.shipper.state_code + '</FromState><FromZip5>' + self.shipper.zip + '</FromZip5><FromZip4></FromZip4><ToName>' + self.receipient.name + '</ToName><ToFirm>' + self.receipient.company_name + '</ToFirm><ToAddress1>' + self.receipient.address2 + '</ToAddress1><ToAddress2>' + self.receipient.address1 + '</ToAddress2><ToCity>' + self.receipient.city + '</ToCity><ToState>' + self.receipient.state_code + '</ToState><ToZip5>' + self.receipient.zip + '</ToZip5><ToZip4></ToZip4><WeightInOunces>' + str(self.weight*16) + '</WeightInOunces><ServiceType>' + self._get_usps_servicename(self.service_type_usps) + '</ServiceType><SeparateReceiptPage>True</SeparateReceiptPage><POZipCode></POZipCode><ImageType>TIF</ImageType><LabelDate></LabelDate><CustomerRefNo></CustomerRefNo><AddressServiceRequested></AddressServiceRequested><SenderName></SenderName><SenderEMail></SenderEMail><RecipientName></RecipientName><RecipientEMail></RecipientEMail></DeliveryConfirmationV3.0Request>')
        data.append("https://secure.shippingapis.com/ShippingAPITest.dll?API=DelivConfirmCertifyV3&" if test else "https://secure.shippingapis.com/ShippingAPI.dll?API=DeliveryConfirmationV3&")
        return data

    def _parse_response_body(self, root):
        return USPSDeliveryConfirmationResponse(root)

class USPSDeliveryConfirmationResponse(object):
    def __init__(self, root):
        self.root = root
        self.tracking_number = root.findtext('DeliveryConfirmationNumber')
        self.image_format = 'JPEG'
        self.graphic_image = root.findtext('DeliveryConfirmationLabel')

    def __repr__(self):
        return (self.tracking_number, self.image_format, self.graphic_image)