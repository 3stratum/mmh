# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

import time
from lxml import etree
import decimal_precision as dp
import netsvc
import pooler
from osv import osv, fields
from tools.translate import _
from datetime import datetime, date
class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def copy(self,cr,uid,ids,vals,context):
        vals.update({
            'auth_transaction_type':'',
            'auth_transaction_id':'',
            'cc_number':'',
            'auth_respmsg': '',
            'authorization_code':'',
            'customer_payment_profile_id':'',
            'amount_charged' : 0.0,
            'invoice_original_id' : False,

        })
        return super(account_invoice, self).copy(cr, uid, ids, vals,context=context)

    def capture_payment(self,cr,uid,ids,context={}):
        if context is None:
            context={}
        (data,) = self.browse(cr,uid,ids)
        config_ids = self.pool.get('authorize.net.config').search(cr,uid,[])
#         model = 'sale.order'
        if config_ids:
            config_obj = self.pool.get('authorize.net.config').browse(cr,uid,config_ids[0])
            obj_all = self.browse(cr,uid,ids[0])
            model = 'account.invoice'
            amount_total = obj_all.amount_total
            customer_id = obj_all.partner_id
            approval_code = obj_all.auth_transaction_id
            customer_payment_profile_id = obj_all.customer_payment_profile_id
            customer_profile_id = customer_id.customer_profile_id
            context['captured_api'] = True
            transaction_details =self.pool.get('authorize.net.config').call(cr,uid,config_obj,'CreateCustomerProfileTransaction',ids[0],'profileTransPriorAuthCapture',amount_total,customer_profile_id,customer_payment_profile_id,approval_code,model,'',context)
            print "transaction_details",transaction_details

            if transaction_details:
                transaction_details=str(transaction_details)
                print transaction_details[0],type(transaction_details[0])
                print transaction_details[1],type(transaction_details[1])
                if transaction_details[0]=='1' and transaction_details[2]=='1':
#                     cr.execute("UPDATE account_invoice SET capture_status='captured' where id=%d"%(ids[0]))
#                 return transaction_details
#                     context.update({'captured':True})
                    wf_service = netsvc.LocalService("workflow")
                    print "invoice open and confirmation of invoices"
                    wf_service.trg_validate(uid, 'account.invoice', ids[0], 'invoice_open', cr)
                    returnval = self.make_payment_of_invoice(cr, uid, ids, context=context)
#                     inv_payment = super(account_invoice, self).invoice_pay_customer(cr, uid, ids, context=context)

        else:
            raise osv.except_osv('Define Authorize.Net Configuration!', 'Warning:Define Authorize.Net Configuration!')

        return True
    _columns = {
            'auth_transaction_id' :fields.char('Transaction ID', size=40,),
            'auth_transaction_type': fields.char('Transaction Type',size=156),
            'authorization_code': fields.char('Authorization Code',size=64,readonly=True),
            'customer_profile_id': fields.char('Customer Profile ID',size=64,readonly=True),
            'customer_payment_profile_id': fields.char('Payment Profile ID',size=64,readonly=True),
            'capture_status': fields.char('Capture Status',size=64),
            'auth_respmsg' :fields.text('Response Message',readonly=True),
            'cc_number' :fields.char('Credit Card Number', size=64),
            'invoice_original_id' : fields.many2one('account.invoice','Invoice Reference',help="Reference of the Original Invoice against which invoice is prepared"),
            'amount_charged' : fields.float('Authorized/Captured Amount',digits=(12,2),required=True),
	}

    def api_response(self,cr,uid,ids,response,payment_profile_id,transaction_type,context={}):
        split = response.split(',')
        vals = {}
        print"split",split
        transaction_id = split[6]
        transaction_message = split[3]
        authorize_code = split[4]
        invoice_cur = self.browse(cr, uid, ids)
        if transaction_id and transaction_message:
            if invoice_cur.auth_transaction_id:
                vals['auth_transaction_id'] = invoice_cur.auth_transaction_id + "/" + transaction_id
            else:
                vals['auth_transaction_id'] = transaction_id
            if invoice_cur.auth_respmsg:
                vals['auth_respmsg'] = invoice_cur.auth_respmsg + "/" + transaction_message
            else:
                vals['auth_respmsg'] = transaction_message
#            cr.execute("UPDATE account_invoice SET auth_transaction_id='%s', auth_respmsg='%s'where id=%d"%(transaction_id,transaction_message,ids))
        if authorize_code:
            if invoice_cur.authorization_code:
                vals['authorization_code'] = invoice_cur.authorization_code + "/" + authorize_code
            else:
                vals['authorization_code'] = authorize_code
#            cr.execute("UPDATE account_invoice SET authorization_code='%s' where id=%d"%(authorize_code,ids))
        if payment_profile_id:
            if invoice_cur.customer_payment_profile_id:
                vals['customer_payment_profile_id'] = invoice_cur.customer_payment_profile_id + "/" + payment_profile_id
            else:
                vals['customer_payment_profile_id'] = payment_profile_id
#            cr.execute("UPDATE account_invoice SET customer_payment_profile_id='%s' where id=%d"%(payment_profile_id,ids))
        if transaction_type:
            vals['auth_transaction_type'] = transaction_type
#            cr.execute("UPDATE account_invoice SET auth_transaction_type='%s' where id=%d"%(transaction_type,ids))
        if vals:
                self.write(cr,uid,ids,vals)
        self.log(cr,uid,ids,transaction_message)
        return True


    def make_payment_of_invoice(self, cr, uid, ids, context):
        logger = netsvc.Logger()
        if not context:
            context = {}
        inv_obj = self.browse(cr,uid,ids[0])
        voucher_id = False
        invoice_number = inv_obj.number
        voucher_pool = self.pool.get('account.voucher')
        journal_pool = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        bank_journal_ids = journal_pool.search(cr, uid, [('type', '=', 'bank')])
        if not len(bank_journal_ids):
            return True

        context.update({
                'default_partner_id': inv_obj.partner_id.id,
                'default_amount': inv_obj.amount_total,
                'default_name':inv_obj.name,
                'close_after_process': True,
                'invoice_type':inv_obj.type,
                'invoice_id':inv_obj.id,
#                'journal_id':bank_journal_ids[0],
                'journal_id': 12,
                'default_type': inv_obj.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
        })
        if inv_obj.type in ('out_refund','in_refund'):
            context.update({'default_amount':-inv_obj.amount_total})
        tax_id = self._get_tax(cr, uid, context)

        account_data = self.get_accounts(cr,uid,inv_obj.partner_id.id,bank_journal_ids[0])
        date = time.strftime('%Y-%m-%d')
        voucher_data = {
                'period_id': inv_obj.period_id.id,
                'account_id': account_data['value']['account_id'],
                'partner_id': inv_obj.partner_id.id,
#                'journal_id':bank_journal_ids[0],
                'journal_id': 12,
                'currency_id': inv_obj.currency_id.id,
                'reference': inv_obj.name or inv_obj.auth_transaction_id,   #payplan.name +':'+salesname
                #'narration': data[0]['narration'],
                'amount': inv_obj.amount_total,
                'type':account_data['value']['type'],
                'state': 'draft',
                'pay_now': 'pay_later',
                'name': '',
                'date': time.strftime('%Y-%m-%d'),
#                'date': inv_obj.date_invoice,
                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher',context=None),
                'tax_id': tax_id,
                'payment_option': 'without_writeoff',
                'comment': _('Write-Off'),
            }
        if inv_obj.type in ('out_refund','in_refund'):
            voucher_data.update({'amount':-inv_obj.amount_total})
        if not voucher_data['period_id']:
            period_ids = period_obj.find(cr, uid, inv_obj.date_invoice, context=context)
            period_id = period_ids and period_ids[0] or False
            voucher_data.update({'period_id':period_id})
        logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_data '%s'." % voucher_data)
        voucher_id = voucher_pool.create(cr,uid,voucher_data)
        logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_id '%s'." % voucher_id)

        if voucher_id:
            #Get all the Documents for a Partner
            if inv_obj.type in ('out_refund','in_refund'):
                amount=-inv_obj.amount_total
                res = voucher_pool.onchange_partner_id(cr, uid, [voucher_id], inv_obj.partner_id.id, bank_journal_ids[0], amount, inv_obj.currency_id.id, account_data['value']['type'], date, context=context)
            else:
                res = voucher_pool.onchange_partner_id(cr, uid, [voucher_id], inv_obj.partner_id.id, bank_journal_ids[0], inv_obj.amount_total, inv_obj.currency_id.id, account_data['value']['type'], date, context=context)
            #Loop through each document and Pay only selected documents and create a single receipt
            for line_data in res['value']['line_cr_ids']:
                logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data '%s'." % line_data)

                if not line_data['amount']:
                    continue
                name = line_data['name']
#                print "Name",name
                logger.notifyChannel("warning", netsvc.LOG_WARNING,"inv.number '%s'." % inv_obj.number)
                logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data['name'] '%s'." % line_data['name'])

                if line_data['name'] in [invoice_number]:
                    voucher_lines = {
                        'move_line_id': line_data['move_line_id'],
                        'amount': inv_obj.amount_total,
                        'name': line_data['name'],
                        'amount_unreconciled': line_data['amount_unreconciled'],
                        'type': line_data['type'],
                        'amount_original': line_data['amount_original'],
                        'account_id': line_data['account_id'],
                        'voucher_id': voucher_id,
                    }
                    print "cr voucher line create",voucher_lines
                    logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_lines '%s'." % voucher_lines)
                    voucher_line_id = self.pool.get('account.voucher.line').create(cr,uid,voucher_lines)
                    logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_line_id '%s'." % voucher_line_id)
            for line_data in res['value']['line_dr_ids']:
                logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data '%s'." % line_data)

                if not line_data['amount']:
                    continue
                name = line_data['name']
#                print "Name",name
                logger.notifyChannel("warning", netsvc.LOG_WARNING,"inv.number '%s'." % inv_obj.number)
                logger.notifyChannel("warning", netsvc.LOG_WARNING,"line_data['name'] '%s'." % line_data['name'])

                if line_data['name'] in [invoice_number]:
                    voucher_lines = {
                        'move_line_id': line_data['move_line_id'],
                        'amount': inv_obj.amount_total,
                        'name': line_data['name'],
                        'amount_unreconciled': line_data['amount_unreconciled'],
                        'type': line_data['type'],
                        'amount_original': line_data['amount_original'],
                        'account_id': line_data['account_id'],
                        'voucher_id': voucher_id,
                    }
                    print "dr voucher line create-------------drrrrrrrrrrr",voucher_lines
                    logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_lines '%s'." % voucher_lines)
                    voucher_line_id = self.pool.get('account.voucher.line').create(cr,uid,voucher_lines)
                    logger.notifyChannel("warning", netsvc.LOG_WARNING,"voucher_line_id '%s'." % voucher_line_id)

            #Add Journal Entries
            print "create lines",voucher_id
            voucher_pool.action_move_line_create(cr,uid,[voucher_id])

        return voucher_id

    def _get_tax(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if not journal_id:
            ttype = context.get('type', 'bank')
            res = journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)
            if not res:
                return False
            journal_id = res[0]

        if not journal_id:
            return False
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id
            return tax_id
        return False

    def get_accounts(self, cr, uid, partner_id=False, journal_id=False, context=None):
        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        default = {
            'value':{},
        }

        if not partner_id or not journal_id:
            return default

        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        account_id = False
        tr_type = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
            tr_type = 'sale'
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
            tr_type = 'purchase'
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            tr_type = 'receipt'

        default['value']['account_id'] = account_id
        default['value']['type'] = tr_type

        return default


    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
        print"view_id==============",view_id,context
        inv = self.browse(cr, uid, ids[0], context=context)
        cust_payment_profile_id=""
        auth_transaction_id=""
        cust_profile_id=""
        profile_values = {}
#        return_id = inv.return_id
#        invoice_id = return_id.linked_sale_order.invoice_ids if return_id and return_id.linked_sale_order else ""
        invoice_ref_obj = inv.invoice_original_id
        if invoice_ref_obj:
            cust_payment_profile_id = invoice_ref_obj.customer_payment_profile_id or ''
            auth_transaction_id = invoice_ref_obj.auth_transaction_id or ''
            cust_profile_id = invoice_ref_obj.partner_id.customer_profile_id or ''
            
#        cust_profile_id = return_id.linked_sale_order.partner_id.customer_profile_id if return_id and return_id.linked_sale_order and return_id.linked_sale_order.partner_id else ""
        
        profile_values['cust_payment_profile_id'] = cust_payment_profile_id
        profile_values['auth_transaction_id'] = auth_transaction_id
        profile_values['cust_profile_id'] = cust_profile_id


#        if inv.type=="out_invoice":
#
#            context['action_to_do'] = 'new_payment_profile'
#            context['active_id'] = ids[0]
#            context['active_model'] = 'account.invoice'
#            return {
#                'name': ('Register Payment Confirmation'),
#                'view_type': 'form',
#                'view_id': view_id,
#                'view_mode': 'form',
#                'res_model': 'register.payment.confirmation',
#                'view_id': False,
#                'type': 'ir.actions.act_window',
#                'target': 'new',
#                'context': context
#            }

        if cust_payment_profile_id and auth_transaction_id and inv.type=="out_refund":
            self.refund_customer(cr,uid,ids,profile_values,context)
        else:
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
                    'payment_expected_currency': inv.currency_id.id,
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                    'default_reference': inv.name,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
                }
            }


    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        """Prepare the dict of values to create the new refund from the invoice.
            This method may be overridden to implement custom
            refund generation (making sure to call super() to establish
            a clean extension chain).

            :param integer invoice_id: id of the invoice to refund
            :param dict invoice: read of the invoice to refund
            :param string date: refund creation date from the wizard
            :param integer period_id: force account.period from the wizard
            :param string description: description of the refund from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the refund
        """

        '''
        function inherited in authorize.net for MMH for also adding up the
        Invoice reference of the customer
        '''

        obj_journal = self.pool.get('account.journal')

        type_dict = {
            'out_invoice': 'out_refund', # Customer Invoice
            'in_invoice': 'in_refund',   # Supplier Invoice
            'out_refund': 'out_invoice', # Customer Refund
            'in_refund': 'in_invoice',   # Supplier Refund
        }
        invoice_data = {}
        ### invoice_original_id to be also added in the invoice
        ### code is modified below and an additional key is also
        ### added in the fields list
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id',
                'account_id', 'currency_id', 'payment_term', 'user_id', 'fiscal_position','invoice_original_id','mmh_class','mmh_disc']:
            if invoice._all_columns[field].column._type == 'many2one':
                if field == 'invoice_original_id':
                    invoice_data[field] = invoice.id
                else:
                    invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False

        invoice_lines = self._refund_cleanup_lines(cr, uid, invoice.invoice_line, context=context)

        tax_lines = filter(lambda l: l['manual'], invoice.tax_line)
        tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines, context=context)
        if journal_id:
            refund_journal_ids = [journal_id]
        elif invoice['type'] == 'in_invoice':
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')], context=context)
        else:
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')], context=context)

        if not date:
            date = time.strftime('%Y-%m-%d')
        invoice_data.update({
            'type': type_dict[invoice['type']],
            'date_invoice': date,
            'state': 'draft',
            'number': False,
            'invoice_line': invoice_lines,
            'tax_line': tax_lines,
            'journal_id': refund_journal_ids and refund_journal_ids[0] or False,
        })
        if period_id:
            invoice_data['period_id'] = period_id
        if description:
            invoice_data['name'] = description
        return invoice_data

    def refund_customer(self,cr,uid,ids,profile_values,context={}):
#        active_id = context.get('active_id',False)
        print"context-------*****",context,profile_values
        if ids:
            customer_profile_obj=""
            cc_number=""
            authorize_obj = self.pool.get('authorize.net.config')
            config_ids = authorize_obj.search(cr,uid,[])
            return_object = self.pool.get('return.order')
#            invoice_object = self.pool.get('return.order')
            if config_ids:
#                return_obj = return_object.browse(cr,uid,active_id)
                invoice_obj = self.browse(cr,uid,ids[0])
#                return_id = invoice_obj.return_id
                invoice_ref_obj = invoice_obj.invoice_original_id
#                invoice_id = return_id.linked_sale_order.invoice_ids

                total= invoice_obj.amount_total
#                cust_profile_id = return_id.linked_sale_order.partner_id.customer_profile_id
#                cust_payment_profile_id = invoice_id[0].customer_payment_profile_id
#                auth_transaction_id = invoice_id[0].auth_transaction_id
                cust_profile_id = profile_values.get("cust_profile_id",False)
                cust_payment_profile_id = profile_values.get("cust_payment_profile_id",False)
                auth_transaction_id = profile_values.get("auth_transaction_id",False)

                for customer_payment_profile in invoice_ref_obj.partner_id.profile_ids:
                    if customer_payment_profile.profile_id == cust_payment_profile_id:
                        customer_profile_obj = customer_payment_profile

                if customer_profile_obj:
                    cc_number = customer_profile_obj.credit_card_no
                    if cc_number and len(cc_number)==4:
                        cc_number='XXXX'+''+str(cc_number)
#                act_model = context.get('active_model',False)
                act_model = "account.invoice"
                config_obj = authorize_obj.browse(cr,uid,config_ids[0])
                print "ccc number",cc_number
                try:
                    print "before sending transaction request"
                    transaction_status = authorize_obj.call(cr,uid,config_obj,'getTransactionDetailsRequest',auth_transaction_id)
                    print "transaction status",transaction_status
                    if (transaction_status) and (transaction_status.get('transactionStatus') == 'settledSuccessfully'):
                        refund_tras_info =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',ids[0],'profileTransRefund',total,cust_profile_id,cust_payment_profile_id,auth_transaction_id,act_model,cc_number,context)
#                        refund_tras_info =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',return_obj.id,'profileTransRefund',total,'18120882','16964092','2192691900',act_model,'XXXX0027')
                        if refund_tras_info:
                            transaction=self.api_response(cr,uid,ids[0],refund_tras_info,cust_payment_profile_id,"profileTransRefund",context)
                            self.make_payment_of_invoice(cr, uid, ids, context=context)
                    else:
                        trasaction_details =authorize_obj.call(cr,uid,config_obj,'VoidTransaction',cust_profile_id,cust_payment_profile_id,auth_transaction_id)
                        if trasaction_details:
                            transaction=self.api_response(cr,uid,ids[0],trasaction_details,cust_payment_profile_id,"profileTransVoid",context)
                            self.make_payment_of_invoice(cr, uid, ids, context=context)

                except Exception, e:
#                    print "Error in URLLIB",str(e)
                    raise osv.except_osv(_('Error !'),_('%s')%(str(e)))
#                if return_id.receive:
#                    state = 'done'
#                else:
#                    state = 'progress'
#                return_object.write(cr,uid,[return_id.id],{'manual_invoice_invisible': True,'state':'done'})
#                self.write(cr,uid,ids,{'state':'paid'})
        return True




account_invoice()
