# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import osv, fields
from openerp import tools
from openerp import netsvc
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

#class stock_picking_out(osv.osv):
#    _inherit = "stock.picking.out"
#    _columns={
#        'mmh_disc_code':fields.char('mmh_disc_code',size=64),
#        'mmh_class':fields.char('mmh_class',size=64),
#        'invoice_id' : fields.many2one('account.invoice','Pickings'),
#        'delivery_tracking_line': fields.many2many('delivery.tracking','picking_out_tracking','picking_id','tracking_id','Delivery Tracking Line'),
 #       'replace_address' : fields.boolean('Alternate Address For Delivery'),
 #       'alt_address':fields.many2one('res.partner','Shipping Address from Invoice',help="Address for delivery"),
#        'delivery_tracking_line': fields.one2many('delivery.tracking','order_id','Delivery Tracking Line')
#
#    
#    }

#
#stock_picking_out()'''

#wizard to manage scrapped products in the finished lines of mo

class stock_move_scrap(osv.osv_memory):
    _name = "stock.move.scrap"
    _description = "Scrap Products"
    _inherit = "stock.move.consume"
    _defaults = {
        'location_id': lambda *x: False
    }

    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for default value
        @param context: A standard dictionary
        @return: default values of fields
        """
        if context is None:
            context = {}
        res = super(stock_move_scrap, self).default_get(cr, uid, fields, context=context)
        move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
        location_obj = self.pool.get('stock.location')
        scrpaed_location_ids = location_obj.search(cr, uid, [('scrap_location','=',True)])

        if 'product_id' in fields:
            res.update({'product_id': move.product_id.id})
        if 'product_uom' in fields:
            res.update({'product_uom': move.product_uom.id})
        if 'product_qty' in fields:
            res.update({'product_qty': move.product_qty})
        if 'location_id' in fields:
            if scrpaed_location_ids:
                res.update({'location_id': scrpaed_location_ids[0]})
            else:
                res.update({'location_id': False})

        return res




    def move_scrap(self, cr, uid, ids, context=None):
        """ To move scrapped products
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        move_ids = context['active_ids']
        move_data = move_obj.browse(cr,uid,move_ids[0])
        print"move_ids",move_data.scrap_qty
        for data in self.browse(cr, uid, ids):
	    if data.product_qty< 1:
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity should be greater than 0 !'))
            if data.product_qty>(move_data.product_qty):
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity can not be greater than move quantity !'))
            if move_data.product_qty< (data.product_qty + move_data.scrap_qty):
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity can not be greater than move quantity !'))

            move_obj.action_scrap(cr, uid, move_ids,
                             data.product_qty, data.location_id.id, data.product_qty,
                             context=context)
        return {'type': 'ir.actions.act_window_close'}


stock_move_scrap()




## wizard class to manage scraped product in consumed line in MO
class mrp_move_scrap(osv.osv_memory):
    _name = "mrp.move.scrap"
    _description = "Scrap Products"

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
        'location_id': fields.many2one('stock.location', 'Location', required=True),
        'avail_qty':fields.float('Stock Available',digits=(16,3)),
        'virtual_qty':fields.float('Forecasted Qty',digits=(16,3))

    }

    _defaults = {
        'location_id': lambda *x: False
    }


    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for default value
        @param context: A standard dictionary
        @return: default values of fields
        """
        if context is None:
            context = {}
        res = super(mrp_move_scrap, self).default_get(cr, uid, fields, context=context)
        move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
        location_obj = self.pool.get('stock.location')
        scrpaed_location_ids = location_obj.search(cr, uid, [('scrap_location','=',True)])

        if 'product_id' in fields:
            res.update({'product_id': move.product_id.id})
        if 'product_uom' in fields:
            res.update({'product_uom': move.product_uom.id})
        if 'product_qty' in fields:
            res.update({'product_qty': move.product_qty})
        if 'location_id' in fields:
            if scrpaed_location_ids:
                res.update({'location_id': scrpaed_location_ids[0]})
            else:
                res.update({'location_id': False})
        if 'avail_qty' in fields:
            res.update({'avail_qty': move.product_id.qty_available})
        if 'virtual_qty' in fields:
            res.update({'virtual_qty': move.product_id.virtual_available})



        return res

    def move_unscrap(self, cr, uid, ids, context=None):
        """ To move scrapped products to manufacturing if scrap qty entered more by mistake.
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        move_ids = context['active_ids']
        move_data = move_obj.browse(cr,uid,move_ids[0])
        for data in self.browse(cr, uid, ids):
            if data.product_qty<1:
                raise osv.except_osv(_('Warning!'),
                            _('Unscrap Quantity should be greater than 0 !'))
            if data.product_qty>move_data.procure_qty:
                raise osv.except_osv(_('Warning!'),
                            _('Unscrap Quantity can not be greater than procure quantity !'))

            default_val = {
                'location_id': data.location_id.id,
                'product_qty': data.product_qty,
                'location_dest_id': move_data.location_id.id,
            }
            ## create move from scrap to production location and process it completely
            ## with the specified booked Journals
            unscrap_move = move_obj.copy(cr, uid, move_ids[0], default_val)
            move_obj.action_done(cr,uid,[unscrap_move])
            ## additional code to write off the origin
            move_obj.write(cr, uid, [unscrap_move],{'origin' : move_data.name + "/UnScrapped"})


            ### searching for the kitting move and create a reverse move for it
            dest_move_id = move_obj.search(cr,uid,[('move_dest_id','=',move_ids[0])])
            if dest_move_id:
                dest_move = move_obj.browse(cr,uid,dest_move_id[0])
                kit_move = move_obj.copy(cr,uid, dest_move_id[0],{
                    'product_qty' : data.product_qty,
                    'location_id' : dest_move.location_dest_id.id,
                    'location_dest_id' : dest_move.location_id.id,

                })

                ## marking the reversed kitting move as done
                move_obj.action_done(cr,uid,[kit_move])
                move_obj.write(cr, uid, [kit_move],{'origin' : move_data.name + '/Reverse Procure Move'})

                ## Update scrap qty and procure qty in stock move of MO
                move_data.write({'scrap_qty':move_data.scrap_qty-data.product_qty,'procure_qty':move_data.procure_qty-data.product_qty})

        return {'type': 'ir.actions.act_window_close'}

    def move_scrap_only(self, cr, uid, ids, context=None):
        """ To move scrapped products
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        move_ids = context['active_ids']
        move_data=move_obj.browse(cr,uid,move_ids[0])
        for data in self.browse(cr, uid, ids):
            if data.product_qty<1:
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity should be greater than 0 !'))
            if data.product_qty>(move_data.product_qty):
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity can not be greater than move quantity !'))
            if move_data.product_qty< (data.product_qty + move_data.scrap_qty):
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity can not be greater than move quantity !'))

            default_val = {
                'location_id': move_data.location_id.id,
                'product_qty': data.product_qty,
                'scrapped': True,
                'location_dest_id': data.location_id.id,
            }

#            print "default val",default_val
           ## create move from production to scrap location
            scrap_move=move_obj.copy(cr, uid, move_ids[0], default_val)
            move_obj.action_done(cr,uid,[scrap_move])
           ## additional code to write off the origin
            revese_move=move_obj.copy(cr, uid, move_ids[0],{
                'location_id': move_data.location_dest_id.id,
                'product_qty': data.product_qty,
                'scrapped': True,
                'location_dest_id': move_data.location_id.id
                })
            move_obj.action_done(cr,uid,[revese_move])

            move_obj.write(cr, uid, [scrap_move],{'origin' : move_data.name + "/Scrapped"})


#               ## Update scrap qty and procure qty in stock move of MO
            move_data.write({'scrap_qty':(move_data.scrap_qty+data.product_qty), 'product_qty':(move_data.product_qty-data.product_qty),'ref': move_data.name})

        return {'type': 'ir.actions.act_window_close'}




    def move_scrap(self, cr, uid, ids, context=None):
        """ To move scrapped products
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        move_ids = context['active_ids']
        move_data=move_obj.browse(cr,uid,move_ids[0])
        for data in self.browse(cr, uid, ids):
            if data.product_qty<1:
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity should be greater than 0 !'))
            if data.product_qty>(move_data.product_qty):
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity can not be greater than move quantity !'))
            if move_data.product_qty< (data.product_qty + move_data.scrap_qty):
                raise osv.except_osv(_('Warning!'),
                            _('Scrap Quantity can not be greater than move quantity !'))

            default_val = {
                'location_id': move_data.location_id.id,
                'product_qty': data.product_qty,
                'scrapped': True,
                'location_dest_id': data.location_id.id,
            }

#            print "default val",default_val
           ## create move from production to scrap location
            scrap_move=move_obj.copy(cr, uid, move_ids[0], default_val)
            move_obj.action_done(cr,uid,[scrap_move])
           ## additional code to write off the origin
            move_obj.write(cr, uid, [scrap_move],{'origin' : move_data.name + "/Scrapped"})

            ### searching the kitting move done earlier for this consumption move
            dest_move_id=move_obj.search(cr,uid,[('move_dest_id','=',move_ids[0])])

            ## if found only then do the copy of issual move
            if dest_move_id:
                new_move = move_obj.copy(cr,uid,dest_move_id[0],{
                    'product_qty':data.product_qty,
                    'move_dest_id':dest_move_id[0],
                    'origin' : move_data.name + "/Procure Move",
                })
                move_obj.action_done(cr,uid,[new_move])
                move_obj.write(cr, uid, [new_move],{'origin' : move_data.name + '/Procure Move'})

#               ## Update scrap qty and procure qty in stock move of MO
                move_data.write({'scrap_qty':move_data.scrap_qty+data.product_qty,'procure_qty':move_data.procure_qty+data.product_qty , 'ref': move_data.name})

        return {'type': 'ir.actions.act_window_close'}

# code to assign routings
#    def move_scrap(self, cr, uid, ids, context=None):
#        bom_obj = self.pool.get('mrp.bom')
#
#        bom_ids = bom_obj.search(cr,uid,[('bom_id','=',False)])
#        for each_bom in bom_obj.browse(cr,uid,bom_ids):
#            routing_id = each_bom.product_id.categ_id.routing_id
#            if routing_id:
#                bom_obj.write(cr,uid,each_bom.id,{'routing_id': routing_id.id})
#        return True



mrp_move_scrap()



class stock_move(osv.osv):
    '''
    Class inherit to define method for open scrap wizard
    '''
    _inherit='stock.move'

    _columns = {
        'scrap_qty': fields.float('Scrap Quantity', digits=(16,3),help='Store total scrap qty'),
        'procure_qty': fields.float('Procure Quantity', digits=(16,3),help='Store total procure quantity based on scrap qty'),
	'alternate_address': fields.related('picking_id','alt_address',type='many2one', relation="res.partner", string="Alternate Address",),
    }

    ## scrap function inherited to skip the state key in the dictionary line no.255

    def _create_product_valuation_moves(self, cr, uid, move, context=None):
        """
        Generate the appropriate accounting moves if the product being moves is subject
        to real_time valuation tracking, and the source or destination location is
        a transit location or is outside of the company.
        """
#        fdjslkfjslk
        if move.product_id.valuation == 'real_time': # FIXME: product valuation should perhaps be a property?
            if context is None:
                context = {}
            src_company_ctx = dict(context,force_company=move.location_id.company_id.id)
            dest_company_ctx = dict(context,force_company=move.location_dest_id.company_id.id)
            account_moves = []
            # Outgoing moves (or cross-company output part)
            if move.location_id.company_id \
                and (move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, src_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                #returning goods to supplier
                if move.location_dest_id.usage == 'supplier':
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_src, reference_amount, reference_currency_id, context))]
                else:
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_dest, reference_amount, reference_currency_id, context))]

            # Incoming moves (or cross-company input part)
            if move.location_dest_id.company_id \
                and (move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, dest_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                #goods return from customer
                if move.location_id.usage == 'customer':
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_dest, acc_valuation, reference_amount, reference_currency_id, context))]
                else:
                    account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_src, acc_valuation, reference_amount, reference_currency_id, context))]

            move_obj = self.pool.get('account.move')
            for j_id, move_lines in account_moves:
                move_obj.create(cr, uid,
                        {
                         'journal_id': j_id,
                         'line_id': move_lines,
                         'ref': move.picking_id and move.picking_id.name or move.name}, context=context)


    def action_scrap(self, cr, uid, ids, quantity, location_id, scrap_qty, context=None):
        """ Move the scrap/damaged product into scrap location
        @param cr: the database cursor
        @param uid: the user id
        @param ids: ids of stock move object to be scrapped
        @param quantity : specify scrap qty
        @param location_id : specify scrap location
        @param context: context arguments
        @return: Scraped lines
        """
        #quantity should in MOVE UOM
        if quantity <= 0:
            raise osv.except_osv(_('Warning!'), _('Please provide a positive quantity to scrap.'))
        res = []
        for move in self.browse(cr, uid, ids, context=context):
            source_location = move.location_id
            if move.state == 'done':
                source_location = move.location_dest_id
            if source_location.usage != 'internal':
                #restrict to scrap from a virtual location because it's meaningless and it may introduce errors in stock ('creating' new products from nowhere)
                raise osv.except_osv(_('Error!'), _('Forbidden operation: it is not allowed to scrap products from a virtual location.'))
            move_qty = move.product_qty
            uos_qty = quantity / move_qty * move.product_uos_qty

            ## commenting the state directly marked as done option to
            ## book journals against the parts moved to scrap.
            default_val = {
                'location_id': source_location.id,
                'product_qty': quantity,
                'product_uos_qty': uos_qty,
#                'state': move.state,
                'scrapped': True,
                'location_dest_id': location_id,
                'tracking_id': move.tracking_id.id,
                'prodlot_id': move.prodlot_id.id,
            }
            new_move = self.copy(cr, uid, move.id, default_val)

            res += [new_move]
            product_obj = self.pool.get('product.product')
            for product in product_obj.browse(cr, uid, [move.product_id.id], context=context):
                if move.picking_id:
                    uom = product.uom_id.name if product.uom_id else ''
                    message = _("%s %s %s has been <b>moved to</b> scrap.") % (quantity, uom, product.name)
                    move.picking_id.message_post(body=message)

        self.action_done(cr, uid, res, context=context)
        self.write(cr,uid,move.id,{'scrap_qty': (scrap_qty + move.scrap_qty)})
        return res

    def scrap_wizard(self,cr,uid,ids,context=None):
        stock_move=self.browse(cr,uid,ids[0])
        return {
            'name':_("Scrap Products"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'mrp.move.scrap',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }
stock_move()





class delivery_tracking(osv.osv):
    _name = "delivery.tracking"

    _columns={
#            'order_id': fields.many2one('stock.picking.out','Order Id',),
            'back_order_id': fields.many2one('stock.picking','Back Order Id',),
#            'back_order_id': fields.char('stock.picking.out','Back Order Id'),
#            'tracking_no': fields.char("Tracking No",size=64,),
            'tracking_no' : fields.related('back_order_id','carrier_tracking_ref',type='char', size=320, relation='stock.picking.out', string='Number'),
            'invoice_id': fields.many2one('account.invoice','Invoice Id'),

    }

delivery_tracking()

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _columns={
        'mmh_disc_code':fields.char('mmh_disc_code',size=64),
        'mmh_class':fields.char('mmh_class',size=64),
        'delivery_tracking_line': fields.many2many('delivery.tracking','picking_out_tracking','picking_id','tracking_id','Delivery Tracking Line'),
        'invoice_id' : fields.many2one('account.invoice','Pickings'),
        'alt_address':fields.many2one('res.partner','Shipping Address',help="Address for delivery"),
        'replace_address' : fields.boolean('Alternate Address For Delivery'),
	'state_partner_id': fields.related('partner_id','state_id',type = 'many2one',relation='res.country.state',string='State'),

    }
    def action_done(self, cr, uid, ids, context=None):
        invoice_obj=self.pool.get('account.invoice')
        res = super(stock_picking, self).action_done(cr, uid, ids, context=context)
        for val in self.browse(cr,uid,ids):
            if val.state=='done':
                invoive_ids=invoice_obj.search(cr,uid,[('origin','=',val.origin)])
                if invoive_ids:
                    invoice_obj.write(cr,uid,invoive_ids,{'invoice_cancel':True})
        return True
    # FIXME: needs refactoring, this code is partially duplicated in stock_move.do_partial()!
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, partner_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        wf_service = netsvc.LocalService("workflow")
        new_picking_name1 = False
        for pick in self.browse(cr, uid, ids, context=context):
            #print "pick............",pick,pick.name
            new_picking = None
            complete, too_many, too_few = [], [], []
            move_product_qty, prodlot_ids, product_avail, partial_qty, product_uoms = {}, {}, {}, {}, {}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s'%(move.id), {})
                product_qty = partial_data.get('product_qty',0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom',False)
                product_price = partial_data.get('product_price',0.0)
                product_currency = partial_data.get('product_currency',False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                product_uoms[move.id] = product_uom
                partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty, move.product_uom.id)
                if move.product_qty == partial_qty[move.id]:
                    complete.append(move)
                elif move.product_qty > partial_qty[move.id]:
                    too_few.append(move)
                else:
                    too_many.append(move)

                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
                    product = product_obj.browse(cr, uid, move.product_id.id)
                    move_currency_id = move.company_id.currency_id.id
                    context['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)

                    if product.id not in product_avail:
                        # keep track of stock on hand including processed lines not yet marked as done
                        product_avail[product.id] = product.qty_available

                    if qty > 0:
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                move_currency_id, product_price, round=False)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                product.uom_id.id)
                        if product_avail[product.id] <= 0:
                            product_avail[product.id] = 0
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.price_get('standard_price', context=context)[product.id]
                            new_std_price = ((amount_unit * product_avail[product.id])\
                                + (new_price * qty))/(product_avail[product.id] + qty)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})

                        # Record the values that were chosen in the wizard, so they can be
                        # used for inventory valuation if real-time valuation is enabled.
                        move_obj.write(cr, uid, [move.id],
                                {'price_unit': product_price,
                                 'price_currency_id': product_currency})

                        product_avail[product.id] += qty



            for move in too_few:
                product_qty = move_product_qty[move.id]
                if not new_picking:
                    new_picking_name = pick.name
                    new_picking_name1 = sequence_obj.get(cr, uid, 'stock.picking.%s'%(pick.type))
                    self.write(cr, uid, [pick.id],
                               {'name': new_picking_name1,
                               })
                    #print "pick.name....new_picking_name1.... ",pick.name,new_picking_name1
                    new_picking = self.copy(cr, uid, pick.id,
                            {
                                'name': new_picking_name,
                                'move_lines' : [],
                                'state':'draft',
                                'delivery_tracking_line' : [],
                            })
                    # to empty tracking no in the back Order
                    self.write(cr, uid, [pick.id],{'carrier_tracking_ref': False,})
                if product_qty != 0:
                    defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty, #TODO: put correct uos_qty
                            'picking_id' : new_picking,
                            'state': 'assigned',
                            'move_dest_id': False,
                            'price_unit': move.price_unit,
                            'product_uom': product_uoms[move.id]
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)
                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty': move.product_qty - partial_qty[move.id],
                            'product_uos_qty': move.product_qty - partial_qty[move.id], #TODO: put correct uos_qty
                            'prodlot_id': False,
                            'tracking_id': False,
                        })

            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                defaults = {'product_uom': product_uoms[move.id], 'product_qty': move_product_qty[move.id]}
                if prodlot_ids.get(move.id):
                    defaults.update({'prodlot_id': prodlot_ids[move.id]})
                move_obj.write(cr, uid, [move.id], defaults)
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty' : product_qty,
                    'product_uos_qty': product_qty, #TODO: put correct uos_qty
                    'product_uom': product_uoms[move.id]
                }
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)

            # At first we confirm the new picking (if necessary)
            if new_picking:
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                # Then we finish the good picking
                self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                self.action_move(cr, uid, [new_picking], context=context)
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                delivered_pack_id = pick.id
                back_order_name = self.browse(cr, uid, delivered_pack_id, context=context).name
                self.message_post(cr, uid, new_picking, body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name), context=context)
            else:
                self.action_move(cr, uid, [pick.id], context=context)
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id

            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}
            # if partially received its tracking history is written as a hierarchy

            invoice_ids = []
            if pick.sale_id:
                invoice_ids = self.pool.get('account.invoice').search(cr ,uid ,[('origin','=',pick.sale_id.name),('state','not in',['cancel'])])

            if new_picking:

                new_picking_obj = self.pool.get('stock.picking').browse(cr ,uid ,new_picking)
                
                vals = {
                        'back_order_id': pick.id or False,
                    }

                self.pool.get('stock.picking.out').write(cr, uid, [new_picking], {'delivery_tracking_line': [(0, False, vals)]}, context=context)

                backorder = pick.backorder_id
                
                while True:
                    vals.update({'back_order_id' : new_picking})
                    if not backorder:
                        break
                    self.pool.get('stock.picking.out').write(cr, uid, [backorder.id], {'delivery_tracking_line': [(0, False, vals)]}, context=context)
                    backorder = backorder.backorder_id or False

        return res

stock_picking()

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    _columns={
        'mmh_disc_code':fields.char('mmh_disc_code',size=64),
        'mmh_class':fields.char('mmh_class',size=64),
        'invoice_id' : fields.many2one('account.invoice','Pickings'),
        'delivery_tracking_line': fields.many2many('delivery.tracking','picking_out_tracking','picking_id','tracking_id','Delivery Tracking Line'),
        'replace_address' : fields.boolean('Alternate Address For Delivery'),
        'alt_address':fields.many2one('res.partner','Shipping Address from Invoice',help="Address for delivery"),
#        'delivery_tracking_line': fields.one2many('delivery.tracking','order_id','Delivery Tracking Line')
	'state_partner_id': fields.related('partner_id','state_id',type = 'many2one',relation='res.country.state',string='State'),
    }

stock_picking_out()



class mrp_bom(osv.osv):
    """
    Defines bills of material for a product.
    """
    _inherit = 'mrp.bom'
    _description = 'Bill of Material'

    def onchange_product_id(self, cr, uid, ids, product_id, name, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
	routing_id = False
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            if prod and prod.categ_id and prod.categ_id.routing_id:
                routing_id = prod.categ_id.routing_id.id
            return {'value': {'name': prod.name, 'product_uom': prod.uom_id.id, 'routing_id': routing_id}}
        return {}


mrp_bom()
