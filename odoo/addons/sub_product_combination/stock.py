# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
class stock_move(osv.osv):
    _inherit = 'stock.move'
    def copy(self,cr,uid,id,default,context={}):
        default.update({'parent_stock_mv_id':False})
        return super(stock_move, self).copy(cr, uid, id, default, context=context)
    def get_parent_stock_mv_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        so_line_obj = self.pool.get('sale.order.line')
        stock_move_obj = self.pool.get('stock.move')
        for each_move in self.browse(cr, uid, ids, context=context):
            if each_move.sale_line_id:
                search_child_so_line_id = so_line_obj.search(cr,uid,[('parent_so_line_id','=',each_move.sale_line_id.id)])
                if search_child_so_line_id:
                    for each_line in search_child_so_line_id:
                        search_stock_move = stock_move_obj.search(cr,uid,[('sale_line_id','=',each_line),('state','in',('confirmed','assigned'))])
                        if search_stock_move and len(search_stock_move) == 1:
                            result[search_stock_move[0]] = each_move.id
                            result[each_move.id] = False
        return result
    _columns = {
    'parent_stock_mv_id': fields.function(get_parent_stock_mv_id, type='many2one', relation='stock.move', string='Parent Stock Move Id',store=True),
    }
stock_move()