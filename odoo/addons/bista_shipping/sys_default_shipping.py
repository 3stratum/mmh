from openerp.osv import osv

class sys_default_shipping(osv.osv):
    _name = 'sys.default.shipping'

    def _get_sys_default_shipping(self,cr,uid,saleorderline_ids,weight,context={}):                
        sys_default = False
        product_obj = self.pool.get('product.product')
        saleorderline_obj = self.pool.get('sale.order.line')
        product_shipping_obj = self.pool.get('product.product.shipping')
        product_categ_shipping_obj = self.pool.get('product.category.shipping')

        if len(saleorderline_ids) <= 2:
            product_id = False
            ### Making sure product is not Shipping and Handling
            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
                if line.product_id.type == 'service':
                    continue
                product_id = line.product_id.id
            if not product_id:
                return False
        else:
            ### Get the product id of the heaviest product
            weight = 0.0
            product_id = False
            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
                if line.product_id.type == 'service':
                    continue
                if line.product_id and line.product_id.product_tmpl_id.weight_net > weight:
                    product_id = line.product_id.id
                    weight = line.product_id.product_tmpl_id.weight_net
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
        ### Format- USPS/First Class/Letter
        sys_default = res[0]['shipping_type'] + '/' + res[0]['service_type_usps'] + '/' + res[0]['container_usps'] + '/' + res[0]['size_usps']
        return sys_default

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
    
sys_default_shipping()