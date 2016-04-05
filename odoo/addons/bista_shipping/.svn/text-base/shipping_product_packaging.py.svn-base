from openerp.osv import osv, fields
class shipping_package_type_fedex(osv.osv):
    _name = 'shipping.package.type.fedex'
    _columns = {
        'name': fields.char('Packaging Type',size=256),
        'length': fields.float('Length'),
        'width': fields.float('Width'),
        'height': fields.float('height'),
    }
shipping_package_type_fedex()

class shipping_package_type_ups(osv.osv):
    _name = 'shipping.package.type.ups'
    _columns = {
        'name': fields.char('Packaging Type',size=256),
        'length': fields.float('Length'),
        'width': fields.float('Width'),
        'height': fields.float('height'),
        'ups_value': fields.char('ups_value',size=64),        
    }
shipping_package_type_ups()