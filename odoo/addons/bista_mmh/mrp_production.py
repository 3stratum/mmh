from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.osv import fields, osv, orm
import time
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class mrp_production(osv.osv):
    _inherit='mrp.production'

#    making the stock moves done on Mark As Started

    def _make_production_line_procurement(self, cr, uid, production_line, shipment_move_id, context=None):
        wf_service = netsvc.LocalService("workflow")
        procurement_order = self.pool.get('procurement.order')
        production = production_line.production_id
        location_id = production.location_src_id.id
        date_planned = production.date_planned
        procurement_name = (production.origin or '').split(':')[0] + ':' + production.name
        procurement_id = procurement_order.create(cr, uid, {
                    'name': procurement_name,
                    'origin': procurement_name,
                    'date_planned': date_planned,
                    'product_id': production_line.product_id.id,
                    'product_qty': production_line.product_qty,
                    'product_uom': production_line.product_uom.id,
                    'product_uos_qty': production_line.product_uos and production_line.product_qty or False,
                    'product_uos': production_line.product_uos and production_line.product_uos.id or False,
                    'location_id': location_id,
                    'procure_method': production_line.product_id.procure_method,
                    'move_id': shipment_move_id,
                    'company_id': production.company_id.id,
                })
        self._hook_create_post_procurement(cr, uid, production, procurement_id, context=context)
        return procurement_id


    def _check_boolean(self, cr, uid, ids, field_name, args, context={}):
        '''
          This function checks if even a single product is consumed in MO ,
          then it sets consumed field and makes reference field readonly.
        '''
        res = {}
        for production in self.browse(cr, uid, ids, context=context):
            moves = [move for move in production.move_lines2]
            if len(moves) != 0 and production.state != 'draft':
                res[production.id] = True
            else:
                res[production.id] = False
        return res

#    updating the raw material location on change of product_id in MO
    def product_id_change(self, cr, uid, ids, product_id, context=None):

        product_obj=self.pool.get('product.product')

        ret_vals = super(mrp_production, self).product_id_change(cr, uid, ids,product_id, context=context)
        dest_loc = product_obj.browse(cr,uid,product_id).categ_id.location
        if dest_loc:
            ret_vals['value'].update({'location_dest_id' : dest_loc.id})
        return ret_vals

#    changing the raw material loaction as output
    def _src_id_default(self, cr, uid, ids, context=None):
        warehouse=self.pool.get('stock.warehouse')
        location_id=warehouse.browse(cr,uid,1).lot_stock_id
        return location_id.id

#    changing the final dest loaction as output
    def _dest_id_default(self, cr, uid, ids, context=None):
        warehouse=self.pool.get('stock.warehouse')
        location_id=warehouse.browse(cr,uid,1).lot_stock_id
        return location_id.id


    _columns={
        'name': fields.char('Reference', size=64, required=True, readonly=True),#states={'draft': [('readonly', False)],'ready': [('readonly', True)]}),
        'lot_number':fields.char('Lot number', size=64, required=True),
        'cnfm_date':fields.date('Date'),
        'consumed': fields.function(
            _check_boolean, string='consumed?',
            type='boolean',
            help="indicates if product to consume have been consumed\
                or canceled"),
       'location_src_id': fields.many2one('stock.location', 'Raw Materials Location', required=True,
            readonly=True, states={'draft':[('readonly',False)]},
            help="Location where the system will look for components."),
       'location_dest_id': fields.many2one('stock.location', 'Finished Products Location', required=True,
            readonly=True, states={'draft':[('readonly',False)]},
            help="Location where the system will stock the finished products."),
       'requested_by': fields.many2one('res.users','Requested By'),
    }
    _defaults={
            'consumed':False,
            'location_src_id': _src_id_default,
            'location_dest_id': _dest_id_default,
        }

    _order = "id desc"

    def _make_production_internal_shipment_line(self, cr, uid, production_line, shipment_id, parent_move_id, destination_location_id=False, context=None):
        stock_move = self.pool.get('stock.move')
        production = production_line.production_id
        date_planned = production.date_planned
        # Internal shipment is created for Stockable and Consumer Products
        if production_line.product_id.type not in ('product', 'consu'):
            return False

        ### code to replace the source location from the location mentioned in the category
        if production_line.product_id and production_line.product_id.categ_id and \
            production_line.product_id.categ_id.location:
            source_location_id = production_line.product_id.categ_id.location.id
        else:
            source_location_id = production.location_src_id.id

        ### code ends here
        if not destination_location_id:
            destination_location_id = source_location_id
        return stock_move.create(cr, uid, {
                        'name': production.name,
                        'picking_id': shipment_id,
                        'product_id': production_line.product_id.id,
                        'product_qty': production_line.product_qty,
                        'product_uom': production_line.product_uom.id,
                        'product_uos_qty': production_line.product_uos and production_line.product_uos_qty or False,
                        'product_uos': production_line.product_uos and production_line.product_uos.id or False,
                        'date': date_planned,
                        'move_dest_id': parent_move_id,
                        'location_id': source_location_id,
                        'location_dest_id': destination_location_id,
                        'state': 'waiting',
                        'company_id': production.company_id.id,
                })

#        Adding Confirmation Date on Confirmation of MO
    def action_confirm(self, cr, uid, ids, context=None):
        '''
         This function writes confirmation date in MO.
        '''

        ## code to assign source location in MO from product category location by default
        mo=self.browse(cr,uid,ids[0])
        location_id =mo.product_id.categ_id.location and mo.product_id.categ_id.location.id or False

#        if location_id:
#            self.write(cr,uid,ids,{'location_src_id': location_id})

        self.write(cr,uid,ids,{'cnfm_date': time.strftime(DEFAULT_SERVER_DATE_FORMAT)})
        ## main module code===========
        shipment_id = False
        wf_service = netsvc.LocalService("workflow")
        uncompute_ids = filter(lambda x:x, [not x.product_lines and x.id or False for x in self.browse(cr, uid, ids, context=context)])
        self.action_compute(cr, uid, uncompute_ids, context=context)
        for production in self.browse(cr, uid, ids, context=context):
            shipment_id = self._make_production_internal_shipment(cr, uid, production, context=context)
            produce_move_id = self._make_production_produce_line(cr, uid, production, context=context)

            # Take routing location as a Source Location.
            source_location_id = production.location_src_id.id
            if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
                source_location_id = production.bom_id.routing_id.location_id.id

            for line in production.product_lines:
                consume_move_id = self._make_production_consume_line(cr, uid, line, produce_move_id, source_location_id=source_location_id, context=context)
                if shipment_id:
                    shipment_move_id = self._make_production_internal_shipment_line(cr, uid, line, shipment_id, consume_move_id,\
                                 destination_location_id=source_location_id, context=context)
                    self._make_production_line_procurement(cr, uid, line, shipment_move_id, context=context)

            if shipment_id:
                wf_service.trg_validate(uid, 'stock.picking', shipment_id, 'button_confirm', cr)
                ## code add to call action assign of picking
                self.pool.get('stock.picking').action_assign(cr, uid, [shipment_id])
            production.write({'state':'confirmed'}, context=context)
        return shipment_id

#   creating an incoming shipment on cancel production

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels work order if production order is canceled.
        make return moves for consumed products in manufacturing order.
        @return: Super method
        """#action_cancel
        obj = self.browse(cr, uid, ids,context=context)[0]
        wf_service = netsvc.LocalService("workflow")
        picking_obj=self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        sequence_obj = self.pool.get('ir.sequence')

        pick_id=obj.picking_id
        curr_state=obj.state
        if curr_state in ('done'):
            raise osv.except_osv(_('Invalid Action!'), _('Cannot cancel a manufacturing order in state \'%s\'.') % curr_state)

        if pick_id:
            if curr_state in ('ready','in_production','done'):
                new_picking = picking_obj.copy(cr, uid, pick_id.id,{'name': sequence_obj.get(cr, uid,
                                                'stock.picking.in'),'type': 'in' ,'move_lines' : []})
    #            print "new_pickingnew_pickingnew_picking0",new_picking
                if new_picking:
                    for move in pick_id.move_lines:
                         defaults = {
                                    'picking_id' : new_picking,
                                    'location_id':move.location_dest_id.id,
                                    'location_dest_id':move.location_id.id,
                                    'move_dest_id':False,
                            }
                         move_obj.copy(cr, uid, move.id, defaults)
                    wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                    wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)

        ## Code taken from default action cancel
        if obj.move_created_ids:
            move_obj.action_cancel(cr, uid, [x.id for x in obj.move_created_ids])    
#        move_obj.action_cancel(cr, uid, [x.id for x in obj.move_lines2])

        ## code to make reverse move of consumed products
        for consume_move in obj.move_lines2:
             defaults = {
                        'location_id':consume_move.location_dest_id.id,
                        'location_dest_id':consume_move.location_id.id,
                }
             new_consume_move=move_obj.copy(cr, uid, consume_move.id, defaults)
             move_obj.action_done(cr,uid,[new_consume_move])
#             move_obj.action_cancel(cr,uid,[new_consume_move])

      ## code to make reverse move of final product in MO if MO is done

        for final_move in obj.move_created_ids2:
            if final_move.state=='done':
                defaults = {
                        'location_id':final_move.location_dest_id.id,
                        'location_dest_id':final_move.location_id.id,
                }
                new_final_move=move_obj.copy(cr, uid, final_move.id, defaults)
                move_obj.action_done(cr,uid,[new_final_move])


   ### code comment because create reverse move

#        for manuf in self.browse(cr, uid, ids, context=context):
#            #print "manuf.....",manuf
#            for move_line in obj.move_lines2:
#                #print "move_line..",move_line
#                dict ={}
#                dict={
#                'location_id':move_line.location_dest_id and move_line.location_dest_id.id or False,
#                'location_dest_id':move_line.location_id and move_line.location_id.id or False,
#                'origin':move_line.origin or False,
#                'state':'done',
#                }
#                res = move_obj.copy(cr ,uid , move_line.id , dict , context=context)
#                #print "res...........",res
#            self.pool.get('stock.move').action_cancel(cr, uid, [x.id for x in manuf.move_lines2], context=context)

        return super(mrp_production,self).action_cancel(cr,uid,ids,context=context)


mrp_production()



class mrp_routing(osv.osv):
    """
    For specifying the routings of Work Centers.
    """
    _inherit = 'mrp.routing'
    _description = 'Routing'
    _columns = {
        'categ_id' : fields.many2one('product.category', 'Product Category'),
    }

mrp_routing()

