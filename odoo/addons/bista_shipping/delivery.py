# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import fields,osv

class delivery_carrier(osv.osv):
    _inherit = "delivery.carrier"
    _columns = {
        'service_code': fields.char('Service Code', size=100, help="Code used as input to API"),
        'service_output': fields.char('Service Output', size=100, help="Code returned as output by API"),
        'container_usps' : fields.char('Container', size=100),
        'size_usps' : fields.char('Size', size=100),
        'first_class_mail_type_usps' : fields.char('First Class Mail Type', size=100),
        'is_ups' : fields.boolean('Is UPS', help="If the field is set to True, it will consider it as UPS service type."),
        'is_usps' : fields.boolean('Is USPS', help="If the field is set to True, it will consider it as USPS service type."),
        'is_fedex' : fields.boolean('Is FedEx', help="If the field is set to True, it will consider it as FedEx service type."),
        'is_canadapost' : fields.boolean('Is Canada Post', help="If the field is set to True, it will consider it as Canada Post service type.")
    }
delivery_carrier()