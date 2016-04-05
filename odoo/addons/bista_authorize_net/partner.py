# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from osv import fields, osv
from openerp.tools.translate import _
class custmer_payment_profile(osv.osv):
    _name = "custmer.payment.profile"
    _rec_name ="profile_id"
    _columns = {
        'profile_id' : fields.char('PaymentProfile ID',size=64),
        'customer_profile_id' : fields.char('Customer Profile ID',size=64),
        'credit_card_no' : fields.char('Credit Card No.',size=64),
        'active_payment_profile': fields.boolean('Active Payment Profile')
    }
    def delete_record(self,cr,uid,ids,context=None):
        authorize_net_config = self.pool.get('authorize.net.config')
        cr.execute('select * from partner_profile_ids where profile_id=%s', (ids))
        partner_id = cr.fetchall()
        partner = partner_id[0][0]
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'bista_authorize_net', 'view_profile_ids')
        view_id = view_ref and view_ref[1] or False,
#code to delete payment profile on authorize.net
        for payment_profile in self.browse(cr,uid,ids):
            print 'payment_profile',payment_profile.id,payment_profile.profile_id
            customer_profile_id = payment_profile.customer_profile_id
            customer_payment_profile_id=payment_profile.profile_id
            config_ids =authorize_net_config.search(cr,uid,[])
            if config_ids:
                config_obj = authorize_net_config.browse(cr,uid,config_ids[0])
                response = authorize_net_config.call(cr,uid,config_obj,'DeleteCustomerPaymentProfileRequest',customer_profile_id,customer_payment_profile_id,'',context)
                if response=='Ok':
                    cr.execute('delete from partner_profile_ids where profile_id=%s', (ids))
                    self.unlink(cr,uid,ids[0])
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('Partners'),
                        'res_model': 'res.partner',
                        'res_id': partner,
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': view_id,
                        'target': 'current',
                        'nodestroy': True,
                    }
                else:
                    raise osv.except_osv(_('Error!'), _('%s')%(response))
        return False

custmer_payment_profile()
custmer_payment_profile()

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    def cust_profile_payment(self,cr,uid,ids,profile_id,payment_profile_data,context={}):
        ids =int(ids)
        cr.execute("UPDATE res_partner SET customer_profile_id='%s' where id=%d"%(profile_id,ids))
        payment_obj = self.pool.get('custmer.payment.profile')
        for cc_number in payment_profile_data.iterkeys():
            each_profile = payment_profile_data[cc_number]
            search_payment_profile = payment_obj.search(cr,uid,[('profile_id','=',each_profile),('credit_card_no','=',cc_number)])
            if not search_payment_profile:
                create_payment = payment_obj.create(cr,uid,{'profile_id':each_profile,'credit_card_no':cc_number,'customer_profile_id':profile_id})
                cr.execute('INSERT INTO partner_profile_ids \
                        (partner_id,profile_id) values (%s,%s)', (ids, create_payment))
                search_payment_profile = [create_payment]
            cr.execute("select profile_id from partner_profile_ids where partner_id=%s and profile_id=%s"%(ids,search_payment_profile[0]))
            exist_relation = cr.fetchall()

            if search_payment_profile  and not exist_relation:
                cr.execute('INSERT INTO partner_profile_ids \
                        (partner_id,profile_id) values (%s,%s)', (ids, search_payment_profile[0]))
        return True
    _columns = {
    'customer_profile_id': fields.char('Customer Profile ID',size=64),
        'profile_ids': fields.many2many('custmer.payment.profile','partner_profile_ids', 'partner_id', 'profile_id','Customer Profiles'),
    }
res_partner()
#class res_partner_address(osv.osv):
#    _inherit = "res.partner.address"
#    _columns = {
#    'email': fields.char('E-Mail', size=240,required=True),
#    'shipping_profile_id':fields.char('Shipping Profile ID',size=64)
#    }
#res_partner_address()
