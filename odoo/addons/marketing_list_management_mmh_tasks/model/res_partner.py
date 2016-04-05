# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.


from openerp.osv.orm import Model
from openerp.osv import fields


class ResPartner(Model):
    _inherit = 'res.partner'

    def _check_address(self, cr, uid, ids, field_name, arg=None, context=None):
        res = dict.fromkeys(ids, False)
        partner_obj = self.pool.get('res.partner')
        addresses = partner_obj.read(cr, uid, ids, [
            'street', 'street2', 'city', 'state_id', 'zip'
        ], context=context)
        # Modify state_id from (id, 'NAME) to id
        # Same as in bista_shipping
        for address in addresses:
            address['state_id'] = (address.get('state_id') and
                                   address.get('state_id')[0])
            # Calls wsdl service everytime, slow for long lists
            vals = partner_obj._validate_address(cr, uid, address,
                                                 context=context)
            valid_address = vals.get('valid_address')
            if valid_address:
                res[address.get('id')] = True
        return res

    _columns = {
        'correct_address': fields.function(_check_address, 'Correct Address',
                                           type='boolean'),
    }
