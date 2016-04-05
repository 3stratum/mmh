from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import openerp.addons.decimal_precision as dp
import re
class product_product(osv.osv):

    _inherit = 'product.product'
    def _get_product_available_def_loc(self, cr, uid, ids,fields, arg=False, context=None):
        res ={}
        for id in ids:
            prod = self.browse(cr,uid,id)
            res[id] = {'default_loc_qty':0 ,
                        'value': 0}
            def_loc =prod.categ_id and prod.categ_id.location and prod.categ_id.location.id

            if def_loc:
                context.update({ 'states': ('done',), 'what': ('in', 'out'),'location':def_loc,'id_check':id})
                if context is None:
                    context = {}
                avail = self.get_product_available(cr, uid, [id],context=context)
                value = avail[id]*prod.standard_price
                if prod.is_multi_variants:
                    for variant in prod.dimension_value_ids:
                        value = avail[id]*variant.cost_price_extra
                res[id]['default_loc_qty']=avail[id]
                res[id]['value']= value
               
            else:
                res[id]['default_loc_qty']=0
                res[id]['value']= 0
        return res
    _columns = {
          'location': fields.many2one('stock.location', 'Raw Material Location'),
          'default_loc_qty':fields.function(_get_product_available_def_loc,multi='default_loc_qty',
                    type='float', string = "Quantity",digits_compute=dp.get_precision('Product Unit of Measure'),
                    help = "Quantity at Default Location of Product Category"),
          'value': fields.function(_get_product_available_def_loc , type = 'float', string = "Value",multi='default_loc_qty',
                    digits_compute=dp.get_precision('Product Unit of Measure'),
                    help = "Quantity X Cost"),
        'minimum_order_point':fields.related('orderpoint_ids','product_min_qty', type='float',relation='stock.warehouse.orderpoint', string='Minimum Orderpoint',readonly="1"),
        'variant_cost_price':fields.related('dimension_value_ids','cost_price_extra', type='float',relation='product.dimension.variant.value', string='Variant Cost Price',readonly="1")

    }

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context)
            if not ids:
                ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('default_code',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result


product_product()

class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
          'location': fields.many2one('stock.location', 'Default Location'),
          'routing_id' : fields.many2one('mrp.routing', 'Routing'),
    	}

product_category()


