from osv import fields, osv

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _description = "Stock Picking"
    _columns = {
    }
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        invoice_vals = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        order=picking.sale_id or False
        if order:
            invoice_vals['auth_transaction_id'] = order.auth_transaction_id
            invoice_vals['authorization_code'] = order.authorization_code
            invoice_vals['customer_payment_profile_id'] = order.customer_payment_profile_id
            invoice_vals['auth_respmsg'] = order.auth_respmsg
        return invoice_vals
stock_picking()
