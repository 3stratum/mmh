from openerp.osv import fields, osv
from openerp.tools.translate import _
import endicia
from endicia import Package
from miscellaneous import Address
import binascii
import types
from urllib2 import Request, urlopen, URLError, quote

class sale_order(osv.osv):
    _name = "sale.order"
    _inherit = "sale.order"
    def create_shipping_quotes(self,cr,uid,ids,response,weight,cust_default,sys_default,context=None):
        shipping_res_obj = self.pool.get('shipping.response')

        for resp in response['info']:
            sr_no = 1 if cust_default and cust_default.split('/')[0] == 'USPS' and cust_default.split('/')[1].split(' ')[0] in resp['service'] else 9
            sr_no = 2 if sr_no == 9 and sys_default and sys_default.split('/')[0] == 'USPS' and sys_default.split('/')[1].split(' ')[0] in resp['service'] else sr_no
            vals = {
                'name': resp['service'],
                'type': 'USPS',
                'rate': resp['cost'],
                'weight': weight,
                'sys_default': False,
                'cust_default': False,
                'sr_no': sr_no,
                'sale_order_id': ids[0]
            }
            res_id = shipping_res_obj.create(cr,uid,vals)
        return True

    def generate_usps_endicia_shipping(self, cr, uid, ids, weight, shipper, recipient, cust_default=False, sys_default=False, error=True, context=None):        
        if 'usps_endicia_active' in context.keys() and context['usps_endicia_active'] == False:
            return False
        if weight>70:
            raise osv.except_osv(_('Warning !'),_("Package weight exceed 70"))
        stockpicking_lnk = self.browse(cr,uid,ids[0])
        ship_endicia = self.pool.get('shipping.endicia').get_endicia_info(cr,uid,context)        
        credentials = {'partner_id':ship_endicia.requester_id,'account_id':ship_endicia.account_id,'passphrase':ship_endicia.passphrase}        
        en = endicia.Endicia(credentials,ship_endicia.test)        
        packages = [Package(stockpicking_lnk.service_type_usps, round(weight * 16,1),'' ,stockpicking_lnk.length_usps, stockpicking_lnk.width_usps, stockpicking_lnk.height_usps, value=1000, require_signature=3, reference='a12302b') ]        
        response = en.rate(packages, Package.shapes[stockpicking_lnk.container_usps], shipper, recipient)
        if response['status'] == 0:
            return self.create_shipping_quotes(cr,uid,ids,response,weight,cust_default,sys_default,context)


    def generate_shipping(self, cr, uid, ids, context={}):     
        default_ship_obj = self.pool.get('sys.default.shipping')
        if context is None:
            context = {}
        context['usps_active'] = False
        context['ups_active'] = False    
        super(sale_order, self).generate_shipping(cr, uid, ids, context)        
        for id in ids:
            try:
                saleorder = self.browse(cr,uid,id)
                shipping_type = saleorder.shipping_type
                if shipping_type == 'USPS' or shipping_type == 'All':
                    weight = saleorder.weight_package if saleorder.weight_package else saleorder.weight_net
                    if not weight:
                        if context.get('error',False):
                            raise osv.except_osv(_('Warning !'),_('Package Weight Invalid!'))
                        else:
                            return False
                    cust_address = saleorder.shop_id and saleorder.shop_id.warehouse_id.partner_id
                    if not cust_address:
                        if context.get('error',False):
                            raise osv.except_osv(_('Warning !'),_('Shop Address not defined!'))
                        else:
                            return False                    
                    shipper = Address(cust_address.name or cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
                    ### Recipient
                    cust_address = saleorder.partner_shipping_id#                   
                    receipient = Address(cust_address.name or '', cust_address.street and cust_address.street.rstrip(','), cust_address.city and cust_address.city.rstrip(','), cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 and (cust_address.street != cust_address.street2) and cust_address.street2.rstrip(',') or '', cust_address.phone or '', cust_address.email, (cust_address.name != cust_address.name) and cust_address.name or '')
                    saleorderline_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',saleorder.id)])
                    sys_default = default_ship_obj._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                    context['sys_default'] = sys_default
                    cust_default= default_ship_obj._get_cust_default_shipping(cr,uid,saleorder.carrier_id.id,context)
                    context['cust_default'] = cust_default
                    shipping_res = self.generate_usps_endicia_shipping(cr,uid,[id],weight,shipper,receipient,context.get('cust_default',False),context.get('sys_default',False),context.get('error',False),context)                    
            except Exception, exc:                
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
        return True

sale_order()

class shipping_response(osv.osv):
    _name = 'shipping.response'
    _inherit = 'shipping.response'

    def generate_tracking_sale(self, cr, uid, ids, context={}, error=True):
        endicia_response = self.browse(cr,uid,ids[0])
        line_obj=self.pool.get('sale.order.line')
        
        if endicia_response.type == 'USPS' and self.pool.get('shipping.endicia').search(cr,uid,[('active','=',True)]):
            context['usps_active'] = False
            #Endicia Quotes Selected
            sale_obj = self.pool.get('sale.order')
            order = endicia_response.sale_order_id
            if order.size_usps and order.size_usps == 'LARGE':
                if not order.width_usps or not order.length_usps or not order.height_usps and order.size_usps == 'LARGE' :
                    raise osv.except_osv(_('Warning !'),_("Please enter USPS dimmensions"))
            package = endicia.Package(endicia_response.name, round(endicia_response.weight*16 >= 1.0 and endicia_response.weight*16 or 1.0,1), endicia.Package.shapes[order.container_usps], order.length_usps, order.width_usps, order.height_usps,order.name,order.amount_total)
            cust_address = order.shop_id and order.shop_id.warehouse_id.partner_id
#            shipper = Address(cust_address.name or '', cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, (cust_address.name != cust_address.partner_id.name) and cust_address.partner_id.name or '')
            shipper = Address(cust_address.name or '', cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email or '')
            cust_address = order.partner_invoice_id
#	    receipient = Address(cust_address.name or '', cust_address.street and cust_address.street.rstrip(','), cust_address.city and cust_address.city.rstrip(','), cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 and (cust_address.street != cust_address.street2) and cust_address.street2.rstrip(',') or '', cust_address.phone or '', cust_address.email, (cust_address.name != cust_address.partner_id.name) and cust_address.partner_id.name or '')
            receipient = Address(cust_address.name or '', cust_address.street and cust_address.street.rstrip(','), cust_address.city and cust_address.city.rstrip(','), cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 and (cust_address.street != cust_address.street2) and cust_address.street2.rstrip(',') or '', cust_address.phone or '', cust_address.email or '')            
            international_label = False
            if receipient.country_code=='':
                raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
            if receipient.country_code.lower() != 'us' and receipient.country_code.lower() != 'usa' and receipient.country_code.lower() != 'pr':
                if context.get('no_international') and endicia_response.name != 'First Class Mail International':
                    sale_obj.write(cr,uid,order.id,{'is_international':True})
                    return False
#		package = endicia.Package(endicia_response.name, int(round(endicia_response.weight*16 >= 1.0 and endicia_response.weight*16 or 1.0)), endicia.Package.shapes[order.container_usps], order.length_usps, order.width_usps, order.height_usps,order.name,order.amount_total)
                package = endicia.Package(endicia_response.name, int(round(endicia_response.weight*16 >= 1.0 and endicia_response.weight*16 or 1.0)), endicia.Package.shapes[order.container_usps], order.length_ups, order.width_ups, order.height_ups,order.name,order.amount_total)
                receipient = Address(cust_address.name or '', cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, (cust_address.name != cust_address.partner_id.name) and cust_address.partner_id.name or '', cust_address.country_id.name)
                international_label = True
            customs = []
            move_lines=line_obj.search(cr,uid,[('order_id','=',order.id)])
            if international_label:
#                customs = [ endicia.Customs('Motorola Phone', 1, 1.0, 1.0, shipper.country_code), endicia.Customs('Samsung', 1, 1.0, 1.0, shipper.country_code), endicia.Customs('HTC Cases', 1, 1.0, 1.0, shipper.country_code), endicia.Customs('Blackberry cover', 1, 1.0, 1.0, shipper.country_code) ]
                for line_item in move_lines:
                    move_line=line_obj.browse(cr,uid,line_item)
##                    weight_net = move_line.product_id.product_tmpl_id.weight_net >= 1.0 and move_line.product_id.product_tmpl_id.weight_net or 1.0
		    weight_net = move_line.product_id.product_tmpl_id.weight_net and move_line.product_id.product_tmpl_id.weight_net*16 >= 1.0 and move_line.product_id.product_tmpl_id.weight_net*16*move_line.product_uom_qty or 1.0
                    customs.append(endicia.Customs(move_line.product_id.name, int(move_line.product_uom_qty), int(round(weight_net)), move_line.product_id.price_extra, shipper.country_code))                
            try:
                ship_endicia = self.pool.get('shipping.endicia').get_endicia_info(cr,uid,context)                
                request = endicia.LabelRequest(ship_endicia.requester_id, ship_endicia.account_id, ship_endicia.passphrase, ship_endicia.label_type if not international_label else 'International', ship_endicia.label_size, ship_endicia.image_format, ship_endicia.image_rotation,package, shipper, receipient, debug=ship_endicia.test, destination_confirm = True if endicia_response.name == 'First-Class Mail' and order.container_usps == 'Letter' else False,customs_info=customs)
                response = request.send()
                endicia_res = response._get_value()
            except Exception, e:
                if error:                    
                    raise osv.except_osv(_('Error'), _('%s' % (e,)))
                else:
                    return False

            attachment_pool = self.pool.get('ir.attachment')
            data_attach = {
                'name': 'ShippingLabel.' + ship_endicia.image_format.lower(),
                'datas': binascii.b2a_base64(str(endicia_res['label'])),
                'description': 'Packing List',
                'res_name': order.name,
                'res_model': 'sale.order',
                'res_id': order.id,
            }
            attach_id = attachment_pool.search(cr,uid,[('res_id','=',order.id),('res_name','=',order.name)])
            if not attach_id:
                attach_id = attachment_pool.create(cr, uid, data_attach)
            else:
                attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
                attach_id = attach_id[0]
            context['attach_id'] = attach_id

            if endicia_res['tracking']:
                rate = endicia_response.rate
		sale_obj.write(cr,uid,order.id,{'tracking_no':endicia_res['tracking'],'shipping_label':binascii.b2a_base64(str(endicia_res['label'])) ,'shipping_rate': rate})
                context['track_success'] = True
                context['tracking_no'] = endicia_res['tracking']

        return super(shipping_response,self).generate_tracking_sale(cr, uid, ids, context, error)

shipping_response()
