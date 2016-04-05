# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import osv, fields
from openerp.tools.translate import _

default_type = ['4X6','4X5','4X4.5','DocTab','6X4']
certified_type = ['4X6','7X4','8X3','Booklet','EnvelopeSize10']
destconfirm_type = ['7X3','6X4','Dymo30384','Mailer7x5','EnvelopeSize10']

class shipping_endicia(osv.osv):
    _name = 'shipping.endicia'

    def get_endicia_info(self,cr,uid,context=None):
        ship_endicia_id = self.search(cr,uid,[('active','=',True)])                
        if not ship_endicia_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites            
            raise osv.except_osv(_('Warning!'), _('Active Endicia settings not defined'))
        else:
            ship_endicia_id = ship_endicia_id[0]        
        return self.browse(cr,uid,ship_endicia_id)

    def write_passphrase(self,cr,uid,new_passphrase,context=None):
        ship_endicia_id = self.search(cr,uid,[('active','=',True)])
        if not ship_endicia_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites
            if error:
                raise osv.except_osv(_('Error'), _('Active Endicia settings not defined'))
            else:
                return False
        else:
            ship_endicia_id = ship_endicia_id[0]
        return self.write(cr,uid,ship_endicia_id,{'passphrase':new_passphrase})

    def create(self, cr, uid, vals, context=None):
        if vals['label_type'] == 'Default' and vals['label_size'] not in default_type:
            raise osv.except_osv(_('Error'), _('Invalid label size for Default Label type'))
        elif vals['label_type'] == 'CertifiedMail' and vals['label_size'] not in certified_type:
            raise osv.except_osv(_('Error'), _('Invalid label size for Certified Mail Label type'))
        elif vals['label_type'] == 'DestinationConfirm' and vals['label_size'] not in destconfirm_type:
            raise osv.except_osv(_('Error'), _('Invalid label size for Destination Confirm Label type'))
        return super(shipping_endicia, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('label_type',False) and vals['label_type'] == 'Default' and vals['label_size'] not in default_type:
            raise osv.except_osv(_('Error'), _('Invalid label size for Default Label type'))
        elif vals.get('label_type',False) and vals['label_type'] == 'CertifiedMail' and vals['label_size'] not in certified_type:
            raise osv.except_osv(_('Error'), _('Invalid label size for Certified Mail Label type'))
        elif vals.get('label_type',False) and vals['label_type'] == 'DestinationConfirm' and vals['label_size'] not in destconfirm_type:
            raise osv.except_osv(_('Error'), _('Invalid label size for Destination Confirm Label type'))
        return super(shipping_endicia, self).write(cr, uid, ids, vals, context)

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'requester_id': fields.char('RequesterID', size=64, required=True),
        'account_id': fields.char('AccountID', size=64, required=True),
        'passphrase': fields.char('Passphrase', size=64, required=True),
        'test' : fields.boolean('Is test?'),
        'active' : fields.boolean('Active'),
        'label_type' : fields.selection([
                ('Default','Default'),
                ('CertifiedMail','Certified Mail'),
                ('DestinationConfirm','Destination Confirm'),
                ('Domestic','Domestic'),
                ('International','International'),
            ],'Label Type',size=64, required=True),
        'label_size' : fields.selection([
                ('4X6','4X6'),
                ('4X5','4X5'),
                ('4X4.5','4X4.5'),
                ('DocTab','DocTab'),
                ('6X4','6X4'),
                ('7X3','7X3'),
                ('7X4','7X4'),
                ('8X3','8X3'),
                ('Dymo30384','Dymo 30384'),
                ('Booklet','Booklet'),
                ('EnvelopeSize10','Envelope Size 10'),
                ('Mailer7x5','Mailer 7x5'),
            ],'Label Size',required=True),
        'image_format' : fields.selection([
                ('GIF','GIF'),
                ('JPEG','JPEG'),
                ('PDF','PDF'),
                ('PNG','PNG'),
            ],'Image Format',required=True),
        'image_rotation' : fields.selection([
                ('None','None'),
                ('Rotate90','Rotate 90'),
                ('Rotate180','Rotate 180'),
                ('Rotate270','Rotate 270'),
            ],'Image Rotation',required=True),
    }
    _defaults = {
        'active' : True,
    }
shipping_endicia()