import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

class balance_receivable_payable(osv.osv_memory):

    _name = "balance.receivable.payable"
    _description = "Receivable and Payable Balances"

    _columns = {
        'invoice_type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type'),
        'partner_id' : fields.many2one('res.partner','Partner'),
        'invoice_ids' : fields.many2many('account.invoice','account_invoice_statement_line','balance_id','line_id','Invoices'),
     }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        act_model = context.get('active_model',False)
        active_id = context.get('active_id',False)
        line_obj = self.pool.get('account.bank.statement.line')
        partner_obj = self.pool.get('res.partner')
        line_cur_obj = line_obj.browse(cr, uid, active_id)
        result = super(balance_receivable_payable, self).default_get(cr, uid, fields, context=context)

        result['invoice_type'] = line_cur_obj.invoice_type
        result['partner_id'] = line_cur_obj.partner_id and line_cur_obj.partner_id.id or False

        return result

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(balance_receivable_payable, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if context.has_key('active_id'):
            active_id = context['active_id']
            line_obj = self.pool.get('account.bank.statement.line')
            invoice_obj = self.pool.get('account.invoice')
            line_cur_obj = line_obj.browse(cr, uid, active_id)
            if result['fields'].has_key('invoice_ids'):
                if line_cur_obj.partner_id:
                    result['fields']['invoice_ids']['domain'] = "[('partner_id','=',%s)]"%(line_cur_obj.partner_id.id)
                else:
                    type = line_cur_obj.invoice_type
                    invoice_ids = invoice_obj.search(cr, uid, [('type','=',type),('state','=','open')])
                    result['fields']['invoice_ids']['domain'] = "[('id','in',%s)]"%(invoice_ids)

        return result

    def assign_balances(self, cr, uid, ids, context=None):

        if context is None:
            context = {}
        data =  self.read(cr, uid, ids, context=context)[0]
        invoice_ids = data['invoice_ids']

#        if not invoice_ids:
#            return {'type': 'ir.actions.act_window_close'}

        invoice_obj = self.pool.get('account.invoice')
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        currency_obj = self.pool.get('res.currency')
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        line_date = time.strftime('%Y-%m-%d')

        st_line_obj = statement_line_obj.browse(cr, uid, context['active_id'])

        statement = statement_obj.browse(cr, uid, st_line_obj.statement_id.id, context=context)

        # for each selected move lines
        st_line_amount = abs(st_line_obj.amount)
        voucher_id = False
        dict_voucher_lines = []
        allocation_amt = 0.0

        if st_line_obj.voucher_id:
            voucher_obj.unlink(cr, uid, [st_line_obj.voucher_id.id],context)
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context=context):

            ### patch of code written to skip the rest of the pending transactions
            ### if the statement line amount reached zero or goes below that

            #### variable defined to set the allocation amount
            allocation_amt += invoice.allocation_amount
            if allocation_amt > st_line_amount or invoice.allocation_amount > invoice.residual or \
                invoice.allocation_amount == 0.0:
                raise osv.except_osv(_('Invalid Allocation Amt!'), _('Either total of Allocation amt is exceeding the Statement Line amount or the Allocation amt per line is more than the residual(balance) of the Invoice !'))

            ### variable code ends here
            
            voucher_res = {}
            ctx = context.copy()
            #  take the date for computation of currency => use payment date
            ctx['date'] = line_date
            amount = 0.0

            type = 'general'
            ttype = st_line_obj.amount <= 0.0 and 'payment' or 'receipt'
            sign = 1

            if invoice.journal_id.type in ('sale_refund', 'purchase_refund'):
                sign = -1

            if not voucher_id:
                voucher_res = { 'type': ttype,
                                'name': statement.name,
                                'partner_id': invoice.partner_id.id,
                                'journal_id': statement.journal_id.id,
                                'account_id': statement.journal_id.default_credit_account_id.id,
                                'company_id': statement.company_id.id,
                                'currency_id': statement.currency.id,
                                'date': statement.date,
                                'amount': st_line_amount * sign,
                                'period_id':statement.period_id.id}

                voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)


            voucher_line_dict =  {}

            amount_original = abs(invoice.amount_total)
            amount_unreconciled = abs(invoice.residual)

            move_line_id = False

            for item in invoice.move_id.line_id:

                if item.account_id.type in ('receivable','payable'):
                    move_line_id = item.id

            line_currency_id = invoice.currency_id and invoice.currency_id.id
            voucher_line_dict = {
                'name' : invoice.move_id.name,
                'type' : invoice.type in ('out_invoice','in_refund') and 'cr' or 'dr',
                'move_line_id' : move_line_id,
                'account_id' : invoice.account_id.id,
                'amount_original' : amount_original,
                'amount' : invoice.allocation_amount,
                'date_original': invoice.date_invoice,
                'date_due': invoice.date_due,
                'amount_unreconciled' : amount_unreconciled,
                'currency_id': line_currency_id,
                'voucher_id' : voucher_id,
            }
            

            print "voucher line dict",voucher_line_dict

            if voucher_line_dict['amount_unreconciled'] == voucher_line_dict['amount']:
                voucher_line_dict['reconcile'] = True

            if voucher_line_dict:
                voucher_line_dict.update({'voucher_id': voucher_id})
                voucher_line_obj.create(cr, uid, voucher_line_dict, context=context)
            st_line_obj.write({'voucher_id' : voucher_id})

        return True

#    def assign_balances(self, cr, uid, ids, context=None):
#
#        if context is None:
#            context = {}
#        data =  self.read(cr, uid, ids, context=context)[0]
#        line_ids = data['line_ids']
#        print "line ids",line_ids
#
#        if not line_ids:
#            return {'type': 'ir.actions.act_window_close'}
#
#        line_obj = self.pool.get('account.move.line')
#        statement_obj = self.pool.get('account.bank.statement')
#        statement_line_obj = self.pool.get('account.bank.statement.line')
#        currency_obj = self.pool.get('res.currency')
#        voucher_obj = self.pool.get('account.voucher')
#        voucher_line_obj = self.pool.get('account.voucher.line')
#        line_date = time.strftime('%Y-%m-%d')
#
#        st_line_obj = statement_line_obj.browse(cr, uid, context['active_id'])
#
#        statement = statement_obj.browse(cr, uid, st_line_obj.statement_id.id, context=context)
#
#        # for each selected move lines
#        st_line_amount = abs(st_line_obj.amount)
#        voucher_id = False
#        for line in line_obj.browse(cr, uid, line_ids, context=context):
#
#            ### patch of code written to skip the rest of the pending transactions
#            ### if the statement line amount reached zero or goes below that
#            print "st line amount",st_line_amount
#            if st_line_amount <= 0.0:
#                break
#
#            voucher_res = {}
#            ctx = context.copy()
#            #  take the date for computation of currency => use payment date
#            ctx['date'] = line_date
#            amount = 0.0
#
#            if line.debit > 0:
#                amount = line.debit
#            elif line.credit > 0:
#                amount = -line.credit
#
#            if line.amount_currency:
#                amount = currency_obj.compute(cr, uid, line.currency_id.id,
#                    statement.currency.id, line.amount_currency, context=ctx)
#            elif (line.invoice and line.invoice.currency_id.id <> statement.currency.id):
#                amount = currency_obj.compute(cr, uid, line.invoice.currency_id.id,
#                    statement.currency.id, amount, context=ctx)
#
#            context.update({'move_line_ids': [line.id],
#                            'invoice_id': line.invoice.id})
#            type = 'general'
#            ttype = amount < 0 and 'payment' or 'receipt'
#            sign = 1
#            if line.journal_id.type in ('sale', 'sale_refund'):
#                type = 'customer'
#                ttype = 'receipt'
#            elif line.journal_id.type in ('purchase', 'purhcase_refund'):
#                type = 'supplier'
#                ttype = 'payment'
#                sign = -1
#
#            if not voucher_id:
#                voucher_res = { 'type': ttype,
#                                'name': statement.name,
#                                'partner_id': line.partner_id.id,
#                                'journal_id': statement.journal_id.id,
#                                'account_id': statement.journal_id.default_credit_account_id.id,
#                                'company_id': statement.company_id.id,
#                                'currency_id': statement.currency.id,
#                                'date': statement.date,
#                                'amount': sign*st_line_obj.amount,
#        #                            'payment_rate': result['value']['payment_rate'],
#        #                            'payment_rate_currency_id': result['value']['payment_rate_currency_id'],
#                                'period_id':statement.period_id.id}
#
#                voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)
#
#
#            voucher_line_dict =  {}
#
#            amount_original = abs(line.amount_currency)
#            amount_unreconciled = abs(line.amount_residual_currency)
#
#            line_currency_id = line.currency_id and line.currency_id.id
#            voucher_line_dict = {
#                'name':line.move_id.name,
#                'type': line.credit and 'dr' or 'cr',
#                'move_line_id':line.id,
#                'account_id':line.account_id.id,
#                'amount_original': amount_original,
#                'amount' : st_line_amount >= amount_unreconciled and amount_unreconciled or st_line_amount,
##                'amount': line.amount,
#                'date_original':line.date,
#                'date_due':line.date_maturity,
#                'amount_unreconciled': amount_unreconciled,
#                'currency_id': line_currency_id,
#            }
#
#            st_line_amount -= amount_unreconciled
#
#            print "voucher line dict",voucher_line_dict
#
#            if voucher_line_dict['amount_unreconciled'] == voucher_line_dict['amount']:
#                voucher_line_dict['reconcile'] = True
#
#            if voucher_line_dict:
#                voucher_line_dict.update({'voucher_id': voucher_id})
#                voucher_line_obj.create(cr, uid, voucher_line_dict, context=context)
#            st_line_obj.write({'voucher_id' : voucher_id})
#        return {'type': 'ir.actions.act_window_close'}
#


balance_receivable_payable()



