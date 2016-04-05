# To change this template, choose Tools | Templates
# and open the template in the editor.
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import tempfile
import time

def _get_shipping_type(self, cr, uid, context=None):
    return [
        ('Fedex','Fedex'),
        ('UPS','UPS'),
        ('USPS','USPS'),
        ('All','All'),
        ('Canada Post','Canada Post'),]


class generate_packing_list(osv.osv_memory):
    _inherit = 'generate.packing.list'
    _columns={
        'shipping_type' : fields.selection(_get_shipping_type,'Shipping Type'),
    }
    
    def onchange_criteria(self, cr, uid, ids, carrier_id, start_date, end_date,shipping_type, context=None):
        value = {}
        pobj_search_array = []
        picking_ids_to_print= []
        picking_obj = self.pool.get('stock.picking')
        
        type_t = 'type','=','out'
        pobj_search_array.append(type_t)

        redo_t = 'shipping_process', 'in', ['draft','partial','backorder']
        pobj_search_array.append(redo_t)

        d_state = 'state', 'not in', ['done','cancel']
        pobj_search_array.append(d_state)
#        label_recv ='label_recvd', '=',True
#        pobj_search_array.append(label_recv)
        if carrier_id:
            carrier_t = 'carrier_id', '=', carrier_id
            pobj_search_array.append(carrier_t)
        if start_date:
            start_date_t = 'date', '>=',(start_date),
            pobj_search_array.append(start_date_t)
        if end_date:
            stop_date_t = 'date', '<=',(end_date),
            pobj_search_array.append(stop_date_t)
        if shipping_type:
            shipping_type_t='shipping_type', '=', shipping_type
            pobj_search_array.append(shipping_type_t)        
        picking_ids = picking_obj.search(cr, uid, pobj_search_array,order='date desc')
        
        if picking_ids:
            cr.execute('select product_id from stock_move where picking_id IN %s  group by product_id', (tuple(picking_ids),))
            product_ids = map(lambda x:x[0], cr.fetchall())
            stock_location_obj = self.pool.get('stock.location')
                #TODO: change the search of locations, take from stock_move instead
            location_ids = stock_location_obj.search(cr, uid, [('name', '=', 'Stock')])
            location_id = location_ids[0] if len(location_ids) else 12#since 12 is main stock location
                #Using product reserves and real stock check
            product_stock_value = stock_location_obj._product_get(cr, uid, location_id, product_ids, context={})
            for pick_id in picking_ids:
                add_this_picking = True
                #check availability for all orders together
                try:
                    picking_obj.action_assign(cr, uid, [pick_id])
                except:
                    pass
                cr.execute('select product_id,product_qty,state from stock_move where picking_id=%s'%(pick_id))
                #Validation if list should be picked or not
                for product_id,product_qty,state in cr.fetchall():
                    #if virtual (customized) is below zero dont allow printing for retail orders
                    if state != 'assigned':
                        add_this_picking = False
                    elif (state == 'assigned') and (product_qty > product_stock_value[product_id]):
                        add_this_picking = False
                        print "Picking id %s had assigned state and stock=%s was less than requested."%(pick_id, product_stock_value[product_id])
                if add_this_picking:
                    picking_ids_to_print.append(pick_id)        
        if len(picking_ids_to_print) > 0:
            value['count'] = len(picking_ids_to_print)
        else:
            value['count'] = 0
        return {'value': value}

    def generate_picking_list(self, cr, uid, ids, context=None):
        """This will generate a sorted list for selected orders"""
        picking_obj = self.pool.get('stock.picking')
        batch_obj = self.pool.get('batch.numbers')
        picking_ids_sorted = []
        vals = {}        
        if context is None:
            context = {}
        #do this only delivery orders only
        for this_obj in self.browse(cr, uid, ids):
            generate_new_pick = this_obj.generate_new_pick
            batch_number = this_obj.name.id
            limit = this_obj.limit
            confirm_order = this_obj.confirm_order
            if not limit:
                limit = 50
            if generate_new_pick:
                shipping_type=this_obj.shipping_type
                carrier_id = this_obj.carrier_id.id
#                shop_id = this_obj.shop_id.id
                start_date = this_obj.start_date
                end_date = this_obj.end_date
                if not batch_number:
                    vals['name'] = self.pool.get('ir.sequence').next_by_code(cr, uid, 'packing.list.batch')
                    batch_number = batch_obj.create(cr, uid,vals)
#                    print"batch_number",batch_number
                
                #check the availability for each and every confirmed sales order
                #create the search tuple as per the form values
                def create_search_array(carrier_id=None, start_date=False,end_date=False,shipping_type=False):
                    pobj_search_array = []
                    type_t = 'type','=','out'
                    pobj_search_array.append(type_t)

                    redo_t = 'shipping_process', 'in', ['draft','partial','backorder']
                    pobj_search_array.append(redo_t)
                    
                    d_state = 'state', 'not in', ['done','cancel']
                    pobj_search_array.append(d_state)
#                    label_recv ='label_recvd', '=',True
#                    pobj_search_array.append(label_recv)
                    if carrier_id:
                        carrier_t = 'carrier_id', '=', carrier_id
                        pobj_search_array.append(carrier_t)
                    if start_date:
                        start_date_t = 'date', '>=',(start_date),
                        pobj_search_array.append(start_date_t)
                    if end_date:
                        stop_date_t = 'date', '<=',(end_date),
                        pobj_search_array.append(stop_date_t)
                    if shipping_type:
                        shipping_type_t='shipping_type', '=', shipping_type
                        pobj_search_array.append(shipping_type_t)                    
                    return pobj_search_array
                #Need to bring the orders which are in available state and fulfil the above criteria
                #Also sort by date(As this the date when the sales order was confirmed)
                #check if this batch is printed, if yes, print again:
                picking_ids = picking_obj.search(cr, uid, create_search_array(carrier_id, start_date,end_date,shipping_type),order='date desc')                
                if not picking_ids:
                    raise osv.except_osv(_('Search Warning !'),_('No Dispatch Orders found for the entered criteria!'))
            else:
                cr.execute("select id from stock_picking where pl_batch_number='%s'"%(batch_number))
                picking_ids = map(lambda x:x[0], cr.fetchall())
                print picking_ids
                if not picking_ids:
                    raise osv.except_osv(_('Search Warning !'),_('No Dispatch Orders found for the entered criteria!'))
                #mark all this ids for packing list, to facilitate printing of packing lists
                #here get the details of products
            picking_ids_to_go_4_printing = []
            #based on availability of stock, the packing list should be printed
            #get all product_quantities to check if the product is really available- we need with reservation:            
            cr.execute('select product_id from stock_move where picking_id IN %s  group by product_id', (tuple(picking_ids),))
            # All Distinct Products that will be picked in current batch
            product_ids = map(lambda x:x[0], cr.fetchall())
            stock_location_obj = self.pool.get('stock.location')            
#            if this_obj.warehouse_id:
#                location_id = this_obj.warehouse_id.lot_stock_id.id
#            else:
                #TODO: change the search of locations, take from stock_move instead
            location_ids = stock_location_obj.search(cr, uid, [('name', '=', 'Stock')])
            location_id = location_ids[0] if len(location_ids) else 12#since 12 is main stock location
            #real stock will not work..we need stock with reservation
            #product_stock_value = stock_location_obj._product_get(cr, uid, location_id, product_ids, context={})
            #Taking product stock with reservation(customized).
            #Here, when the order is confirmed, the virtual(customized) stock goes down. so logic is, when the virtual(customized) stock
            #is greater than zero, that means printing should be allowed, else no
            #product_stock_with_reserve = self.pool.get('product.product').get_virtual_with_reservation(cr, uid, [location_id], product_ids)
            #Using product reserves and real stock check
            product_stock_value = stock_location_obj._product_get(cr, uid, location_id, product_ids, context={})
            for pick_id in picking_ids:
                add_this_picking = True
                #check availability for all orders together
                try:
                    picking_obj.action_assign(cr, uid, [pick_id])
                except:
                    pass
                cr.execute('select product_id,product_qty,state from stock_move where picking_id=%s'%(pick_id))
                #Validation if list should be picked or not
                for product_id,product_qty,state in cr.fetchall():
                    #if virtual (customized) is below zero dont allow printing for retail orders
                    if state != 'assigned':
                        add_this_picking = False
                    elif (state == 'assigned') and (product_qty > product_stock_value[product_id]):
                        add_this_picking = False
                        print "Picking id %s had assigned state and stock=%s was less than requested."%(pick_id, product_stock_value[product_id])
                if add_this_picking:
                    picking_ids_to_go_4_printing.append(pick_id)                
                if limit == len(picking_ids_to_go_4_printing):
                    break
                if add_this_picking == False:
                    picking_obj.write(cr, uid, [pick_id], {'shipping_process': 'partial'})            
            if len(picking_ids_to_go_4_printing) != 0:
                picking_ids_sorted = picking_ids_to_go_4_printing
#            if picking_ids_sorted:
#                if not batch_number:
#                    vals['name'] = self.pool.get('ir.sequence').next_by_code(cr, uid, 'packing.list.batch')
#                    batch_number = batch_obj.create(cr, uid,vals)
#                    print"batch_number",batch_number
            if context.get('generate_picking_list',False):
                dict,order_number={},''
                if len(picking_ids_sorted):
                    for each_id in picking_ids_sorted:
                        each_browse = picking_obj.browse(cr,uid,each_id)
                        comp = each_browse.move_lines
                        for each_comp in comp:
                            qty = each_comp.product_qty
                            if each_comp.product_id.id in dict.keys():
                                if each_comp.product_id.real_qty_available <= 0:
                                    raise osv.except_osv(_('Warning!'), _('Quantiy for product "%s" is not available in the stock "%s".') % (each_comp.product_id.name, each_comp.location_id.name,))
                                qty=dict[each_comp.product_id.id].get('qty')
                                order_number=dict[each_comp.product_id.id].get('order_number')
                                qty=qty+each_comp.product_qty
                                order_number=each_browse.name +" , "+order_number
                                dict[each_comp.product_id.id]={'qty':qty,'order_number':order_number,'prod_name':each_comp.product_id.name,'ids':picking_ids_sorted,'location':each_comp.location_id.name}
                            else:
                                dict[each_comp.product_id.id]={'qty':each_comp.product_qty,'order_number':each_browse.name,'prod_name':each_comp.product_id.name,'ids':picking_ids_sorted,'location':each_comp.location_id.name}
                        picking_obj.write(cr,uid,picking_ids_sorted,{'pl_batch_number':batch_number,'shipping_process':'marked'})
                        batch_obj.write(cr,uid,[batch_number],{'picked':True})
                datas = {'data': dict.values(),'batch':batch_obj.browse(cr, uid,batch_number).name,'print_date': time.strftime('%Y-%m-%d %H:%M:%S') }
                if len(picking_ids_sorted) > 0:
                    return {
                           'type': 'ir.actions.report.xml',
                           'report_name': 'stock.sorted.picking.list',
                           'datas': datas
                           }
                else:
                    raise osv.except_osv(_('Low Stock !'),_('Not Enough Stock'))
            elif context.get('generate_packing_lists',False):
                if len(picking_ids_sorted):
                    picking_obj.write(cr,uid,picking_ids_sorted,{'print_date': time.strftime('%Y-%m-%d %H:%M:%S'),'pl_batch_number':batch_number,'shipping_process':'printed'})
                    batch_obj.write(cr,uid,[batch_number],{'packed':True})
                    datas = {
                     'ids': picking_ids_sorted,
                     'model': 'stock.picking.out',
                     'form': {}
                    }
                    if confirm_order:
                        partial_obj = self.pool.get("stock.partial.picking")
                        for picking_id in picking_ids_sorted:
                            context['active_model']='ir.ui.menu'
                            context['active_ids'] = [picking_id]
                            context['active_id'] = picking_id
                            status = picking_obj.browse(cr,uid,picking_id).state
                            if status == 'draft':
                                 picking_obj.draft_validate(cr, uid, [picking_id], context=context)
                            picking_obj.action_process(cr, uid, [picking_id], context=context)
                            partial_id = partial_obj.create(cr, uid, {}, context=context)
                            partial_obj.do_partial(cr,uid,[partial_id],context=context)
                    return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'stock.picking.list',#'stock.packing.list',
                        'datas': datas,
                    }
#                        else:
#
#                            raise osv.except_osv(_('Low Stock !'),_('Not Enough Stock'))            
            elif context.get('print_labels',False):
                    print "shipping type ===============",this_obj.shipping_type                    
                    picking_obj.write(cr,uid,picking_ids_sorted,{'pl_batch_number':batch_number,'shipping_process':'labels_printed'})
                    batch_obj.write(cr,uid,[batch_number],{'labels_generated':True})                    
                    if len(picking_ids_sorted)>0:
                        dict={'ids':picking_ids_sorted}                        
                        datas = {'data': dict.values(),'batch':batch_obj.browse(cr, uid,batch_number).name,'print_date': time.strftime('%Y-%m-%d %H:%M:%S') }                        
#                        return {
#                           'type': 'ir.actions.report.xml',
#                           'report_name': 'ups.report.bista',
#                           'datas':datas
#                           }
                        if this_obj.shipping_type == 'UPS':
                            return {
                               'type': 'ir.actions.report.xml',
                               'report_name': 'ups.report.bista',
                               'datas':datas
                               }
                        if this_obj.shipping_type == 'Fedex':
                            return {
                               'type': 'ir.actions.report.xml',
                               'report_name': 'fedex.report.bista',
                               'datas':datas
                               }
                        if this_obj.shipping_type == 'USPS':
                            return {
                               'type': 'ir.actions.report.xml',
                               'report_name': 'usps.report.bista',
                               'datas':datas
                               }
                    else:
                        raise osv.except_osv(_('Low Stock !'),_('Not Enough Stock'))
            else:
                raise osv.except_osv(_('Search Warning !'),_('No Dispatch Orders found for the entered criteria!!!'))
generate_packing_list()

class print_each_packing_list(osv.osv_memory):
    _name = 'print.each.packing.list'
    _description = 'Print Packing Lists for each Delivery Order'

    def print_packing_lists(self, cr, uid, ids=None, context=None):
        """This will generate packing list for each order"""
        print 'print_packing_lists'
        picking_obj = self.pool.get('stock.picking')
            #Need to bring the orders which are marked for packing
        picking_ids = picking_obj.search(cr, uid, [('shipping_process', '=', 'marked')], order='date asc')
        if len(picking_ids):
            for picking_id in picking_ids:
                picking_obj.write(cr, uid, picking_id, {'shipping_process': 'printed'})
            datas = {
             'ids': picking_ids,
             'model': 'stock.picking',
             'form': {}
             }

            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'stock.packing.list',
                'datas': datas,
                }
        else:
            raise osv.except_osv(_('Search Warning !'),_('Delivery Orders are are not marked for picking. Please run Print Sorted Packing Lists!'))

print_each_packing_list()