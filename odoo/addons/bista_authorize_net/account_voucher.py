import time
from lxml import etree
import decimal_precision as dp
import netsvc
import pooler
from osv import osv, fields
from tools.translate import _
from datetime import datetime, date

class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    def api_response(self,cr,uid,ids,response,payment_profile_id,transaction_type,context={}):
        split = response.split(',')
        vals = {}
        transaction_id = split[6]
        transaction_message = split[3]
        authorize_code = split[4]
        voucher_cur = self.browse(cr, uid, ids)

        if transaction_id and transaction_message:
            
            vals['auth_transaction_id'] = transaction_id
            vals['auth_respmsg'] = transaction_message
        if authorize_code:
            vals['authorization_code'] = authorize_code
        if payment_profile_id:
            vals['customer_payment_profile_id'] = payment_profile_id
        if transaction_type:
            vals['auth_transaction_type'] = transaction_type

        if vals:
            ### code also to be written for updating the Invoices i.e transaction id fields
            self.write(cr,uid,ids,{'reference' : transaction_id})
        self.log(cr,uid,ids,transaction_message)
        return True

account_voucher()