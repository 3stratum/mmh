import time
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"

    _columns = {

        'invoice_state' : fields.related('invoice_id','state',type = 'selection',
                    selection=[('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Paid'),
            ('cancel','Cancelled')]),
    	}
    _defaults = {
        'invoice_state': 'draft',}
    def write(self,cr,uid,ids,vals,context):
        sale_obj=self.pool.get('sale.order')
        sale_line_obj=self.pool.get('sale.order.line')
        res=super(account_invoice_line, self).write(cr, uid, ids, vals,context)
        
        for val in self.browse(cr,uid,ids):
            if val.invoice_id.invoice_cancel:# and val.invoice_id.origin:
                cr.execute("SELECT order_line_id FROM sale_order_line_invoice_rel WHERE invoice_id = %s ", (ids[0],))
                order_line_id = [r for r in cr.fetchall()]
                if 'price_unit' in vals and vals['price_unit']:
                    if order_line_id:
                        sale_line_obj.write(cr,uid,order_line_id[0][0],{'price_unit':val.price_unit})
        return res


class account_invoice(osv.osv):
    _inherit = "account.invoice"

    _columns = {
        'printed': fields.boolean('Printed',help='Inoice printed if checked .'),
        'rep_add' : fields.boolean('Alternate Address For Delivery', states={'draft': [('readonly', False)]}),
        'delivery_tracking_line': fields.one2many('delivery.tracking','invoice_id','Delivery Tracking Line'),
        'alt_add':fields.many2one('res.partner','Alternate Address',help="Alternate Address for delivery"),
        'picking_ids' : fields.one2many('stock.picking','invoice_id','Tracking Numbers'),
        'allocation_amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'invoice_cancel':fields.boolean('Invoice cancel',help='This field will true when delivery order done'),
        'invoice_line': fields.one2many('account.invoice.line', 'invoice_id','Invoice Lines', ),
	'state_partner_id': fields.related('partner_id','state_id',type = 'many2one',relation='res.country.state',string='State'),
        'line_account__id': fields.related('invoice_line','account_id',type = 'many2one',relation='account.account',string='Line Account'),
        }
    _defaults = {
        'printed': False,
        'rep_add': False,
        'invoice_cancel':False,
    }
#function to paid invoice wgen payment done in authorize.net but not update in openerp

    def paid_invioce(self, cr,uid,ids,context=None):
        wf_service = netsvc.LocalService("workflow")
        for obj_all in self.browse(cr,uid,ids):
            try:
                if obj_all.state == 'draft'   :
                    wf_service.trg_validate(uid, 'account.invoice', obj_all.id, 'invoice_open', cr)
                    self.make_payment_of_invoice(cr, uid, [obj_all.id],context)
                    obj_all.write({'amount_charged' :obj_all.amount_total})
                elif obj_all.state == 'open' :
                    self.make_payment_of_invoice(cr, uid, [obj_all.id],context)
                    obj_all.write({'amount_charged' :obj_all.amount_total})
            except:
                raise osv.except_osv(_('Warning!'), _('Unable to paid invoice'))
        return True



    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as printed'''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
#        for inv in self.browse(cr ,uid ,ids ):
#            if inv.printed:
#                raise osv.except_osv(_('Warning!'),
#                            _('Please uncheck "Printed" to print the invoice,as it has already printed.'))
        self.write(cr, uid, ids, {'printed': True}, context=context)
        res = super(account_invoice , self).invoice_print( cr, uid, ids, context=None)
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        picking_obj=self.pool.get('stock.picking')
        res = super(account_invoice , self).action_cancel( cr, uid, ids, context=None)
        for val in self.browse(cr,uid,ids):
            if not val.invoice_cancel:
                if val.origin:
                    pick_id=picking_obj.search(cr,uid,[('origin','=',val.origin),('type','=','out')])
                    if pick_id:
                        for picking in picking_obj.browse(cr,uid,pick_id):
                            if picking.state  in  ('done'):
                                raise osv.except_osv(_('Error!'), _('You cannot cancel invoice. You need to cancel delivery order first.'))
                            if picking.state not in  ('done','cancel'):
                                picking_obj.action_cancel(cr,uid,[picking.id])
        return True
account_invoice()
