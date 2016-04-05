from openerp import tools
from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw

class account_move(osv.osv):

    _inherit = 'account.move'


    _columns = {
          'product_id': fields.related('line_id','product_id', type='many2one',relation='product.product', string='Product'),
          'line_account__id': fields.related('line_id','account_id',type = 'many2one',relation='account.account',string='Line Account'),

    }

    def adjust_amount(self,cr,uid,ids,context=None):
        move_ids=self.search(cr,uid,[('journal_id','=',9),('state','=','posted'),('amount','=',0.0),('ref','ilike','OUT'),('date','>=','2014-10-01')])
        print'move_ids=====================', len(move_ids)
        for move in self.browse(cr,uid,move_ids):
            for line in move.line_id:
                if line.account_id.id in (1800,1044):
                    print'line=========================',line.account_id.id,line.quantity
                    if line.product_id.is_multi_variants:
                        cost=line.product_id.variant_cost_price
                    else:
                        cost=line.product_id.standard_price
                    print'cost===================',cost
                    if cost:
                        if line.account_id.id==1800:
                            credit=(line.quantity *cost)
                            line.write({'credit':credit})
                        if line.account_id.id ==1044:
                            debit=(line.quantity *cost)
                            line.write({'debit':debit})
        print'done==============================='
        return True
account_move()

class account_move_line(osv.osv):

    _inherit = 'account.move.line'

    _columns = {
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),

    }

    def on_write(self, cr, uid, id, context=None):
        if not id:
            return []
        ml = self.browse(cr, uid, id, context=context)
        return [id]

account_move_line()


