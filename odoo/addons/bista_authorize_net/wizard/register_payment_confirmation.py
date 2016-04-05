from osv import osv, fields
from openerp import netsvc
from openerp.tools.translate import _

class register_payment_confirmation(osv.osv_memory):
    _name="register.payment.confirmation"

    def accept_cash_money(self, cr, uid,ids,context):
        print ids,context
        invoice_id = False
        active_id=context.get('active_id',False)
        inv=self.pool.get("account.invoice").browse(cr,uid,active_id,context)
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
        active_model=context.get('active_model',False)
        print"active_model",active_model
        if active_model=='account.invoice':
            return {
                'name':_("Pay Invoice"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': {
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                    'default_reference': inv.name,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'active_model':active_model,
                    'active_ids':[active_id],
                    'active_id':active_id,
                }
            }

    def accept_authorizenet(self, cr, uid,ids,context):
        active_id=context.get('active_id',False)
        active_model=context.get('active_model',False)
        if active_model=='account.invoice' and active_id:
            context['action_to_do'] = 'new_payment_profile'
            return {
                'name': ('New Customer and Payment Profile'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'profile.transaction',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context
            }
# added function to call caputre payment method
    def call_capture_payment(self, cr, uid, ids, context):
        active_id=context.get('active_id',False)
        active_model=context.get('active_model',False)
        if active_model=='account.invoice' and active_id:
            self.pool.get("account.invoice").capture_payment(cr,uid,[active_id],context)
            return {'type': 'ir.actions.act_window_close'}

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        fields_list,categ_id,i = {},[],1
        inv_obj = self.pool.get('account.invoice')
        if context is None:
            context = {}
        result = super(register_payment_confirmation, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type=='form':
            arch = """<form string="Pre Order Confirmation">"""
            if context.get('active_id') and context.get('active_model') == 'account.invoice':
                inv_id_obj = inv_obj.browse(cr,uid,context.get('active_id'))
                if inv_id_obj.invoice_line and not inv_id_obj.authorization_code:
                    arch += """<separator string="Click on Payment Option"/>"""
                    arch += """<newline/>
                    <group col="2" colspan="4"> <button name="accept_cash_money" string="Payment by Check/Cash"
                         type="object" icon="gtk-go-forward" />
                        <button name="accept_authorizenet" string="Payment by Credit Card"
                         type="object" icon="gtk-go-forward" /></group></form>"""
#               added elif condition to show buttons based on authorize or not
                elif inv_id_obj.invoice_line and inv_id_obj.authorization_code or inv_id_obj.capture_status!="captured":
                    arch += """<separator string="Click on Payment Option"/>"""
                    arch += """<newline/>
                    <group col="2" colspan="4"> <button name="accept_cash_money" string="Payment by Check/Cash"
                         type="object" icon="gtk-go-forward" />
                        <button name="call_capture_payment" string="Capture Payment"
                         type="object" icon="gtk-go-forward" /></group></form>"""
                else:
                    raise osv.except_osv(_('Error!'),_('You cannot confirm a sales order which has no line.'))
            result['arch'] = arch
#            result['fields'] = fields_list
        return result

register_payment_confirmation()