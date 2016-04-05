from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
from openerp.osv.orm import Model
from openerp.addons.account_statement_base_import.parser import new_bank_statement_parser
import sys
import traceback
from openerp.tools.config import config


class AccountStatementProfil(Model):

    _inherit = "account.statement.profile"

    def prepare_statement_lines_vals(
            self, cr, uid, parser_vals, account_payable, account_receivable,
            statement_id, context):

        values = super(AccountStatementProfil, self).prepare_statement_lines_vals(cr, uid, parser_vals, account_payable, account_receivable,
            statement_id, context)

        if values['amount'] >= 0.0:
            values['invoice_type'] = 'out_invoice'
            values['is_customer'] = True
        else:
            values['invoice_type'] = 'in_invoice'
            values['is_supplier'] = True
        
        return values


    def statement_import(self, cr, uid, ids, profile_id, file_stream, ftype="csv", context=None):
#        print "function calllllllllllllllllllllll"
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        attachment_obj = self.pool.get('ir.attachment')
        prof_obj = self.pool.get("account.statement.profile")
        account_obj = self.pool.get('account.account')
#        if not profile_id:
#            raise osv.except_osv(_("No Profile!"),
#                                 _("You must provide a valid profile to import a bank statement!"))
        prof = prof_obj.browse(cr, uid, profile_id, context=context)
#
        parser = new_bank_statement_parser(prof.import_type, ftype=ftype)
        result_row_list = parser.parse(file_stream)
        # Check all key are present in account.bank.statement.line!!
        if not result_row_list:
            raise osv.except_osv(_("Nothing to import"),
                                 _("The file is empty"))
        parsed_cols = parser.get_st_line_vals(result_row_list[0]).keys()
#        print "parsed_cols.......",parsed_cols
        for col in parsed_cols:
            if col not in statement_line_obj._columns:
                raise osv.except_osv(_("Missing column!"),
                                     _("Column %s you try to import is not "
                                       "present in the bank statement line!") % col)

        statement_vals = self.prepare_statement_vals(cr, uid, prof.id, result_row_list, parser, context)

        statement_id = statement_obj.create(cr, uid,
                                            statement_vals,
                                            context=context)

        if prof.receivable_account_id:
            account_receivable = account_payable = prof.receivable_account_id.id
        else:
            account_receivable, account_payable = statement_obj.get_default_pay_receiv_accounts(
                                                       cr, uid, context)
        try:
            # Record every line in the bank statement
            
            for line in result_row_list:
                statement_store = []
                parser_vals = parser.get_st_line_vals(line)

                if line.has_key('state'):
                    parser_vals['state']=line['state']
                else:
                    parser_vals['state']='draft'


                values = self.prepare_statement_lines_vals(
                    cr, uid, parser_vals, account_payable, account_receivable, statement_id,
                    context)



                ### code to check whether the csv has the account to register as the counterpart account
                ### while posting payments
                
                if line.has_key('account_id') and line['account_id']:
                    ac_ids = account_obj.search(cr, uid, [('code','=',line['account_id'].split(" ")[0])])
                    if ac_ids:
                        values.update({'account_id' : ac_ids[0]})
                ### code ends here
                
                statement_store.append(values)
                # Hack to bypass ORM poor perfomance. Sob...
#                print "statement_store.........",statement_store
                statement_line_obj._insert_lines(cr, uid, statement_store, context=context)
                self._write_extra_statement_lines(
                    cr, uid, parser, result_row_list, prof, statement_id, context)
                # Trigger store field computation if someone has better idea
                start_bal = statement_obj.read(
                    cr, uid, statement_id, ['balance_start'], context=context)
                start_bal = start_bal['balance_start']
                statement_obj.write(cr, uid, [statement_id], {'balance_start': start_bal})

#                attachment_data = {
#                    'name': 'statement file',
#                    'datas': file_stream,
#                    'res_model': 'account.bank.statement',
#                    'res_id': statement_id,
#                }
#                attachment_obj.create(cr, uid, attachment_data, context=context)
            # If user ask to launch completion at end of import, do it!

            if prof.launch_import_completion:
                statement_obj.button_auto_completion(cr, uid, [statement_id], context)

            # Write the needed log infos on profile
            self.write_logs_after_import(cr, uid, prof.id,
                                         statement_id,
                                         len(result_row_list),
                                         context)

        except Exception:
            error_type, error_value, trbk = sys.exc_info()
            st = "Error: %s\nDescription: %s\nTraceback:" % (error_type.__name__, error_value)
            st += ''.join(traceback.format_tb(trbk, 30))
            #TODO we should catch correctly the exception with a python
            #Exception and only re-catch some special exception.
            #For now we avoid re-catching error in debug mode
            if config['debug_mode']:
                raise
            raise osv.except_osv(_("Statement import error"),
                                 _("The statement cannot be created: %s") % st)

        return statement_id


#    _columns = {
#         'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null', track_visibility='onchange',
#            invisible=True, help="Linked partner (optional). Usually created when converting the lead."),
#    }

class account_bank_statement(osv.osv):

    _inherit = 'account.bank.statement'


    ### function inherited to check out the statement lines and check out some exceptions
    def create_move_from_st_line(self, cr, uid, st_line_id, company_currency_id, next_number, context=None):
        voucher_obj = self.pool.get('account.voucher')
        move_line_obj = self.pool.get('account.move.line')
        bank_st_line_obj = self.pool.get('account.bank.statement.line')
        st_line = bank_st_line_obj.browse(cr, uid, st_line_id, context=context)

        ### exceptions to be raised incase of an user mistakes

        if not st_line.voucher_id and st_line.account_id.type in ('receivable','payable') and \
            not st_line.partner_id:
                raise osv.except_osv(_("Missing Partner!"),
                                     _("Statement Line %s you\'re trying to book "
                                       "is not having a Partner Defined \n in the bank statement line"
                                       " as the accounts \n selected are receivable and payable") % st_line.id)

        return super(account_bank_statement, self).create_move_from_st_line(cr, uid, st_line.id, company_currency_id, next_number, context=context)


account_bank_statement()

class account_bank_statement_line(osv.osv):

    _inherit = 'account.bank.statement.line'

    _columns = {
        'invoice_type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type'),
        'is_customer' : fields.boolean('Is Customer'),
        'is_supplier' : fields.boolean('Is Supplier'),


    }

    def onchange_account_id(self, cr, uid, ids, account_id, context=None):

        res = {'value': {}}
        account_obj = self.pool.get('account.account')
        res['value']['is_customer'] = False
        res['value']['is_supplier'] = False
        if account_id:
            account = account_obj.browse(cr, uid, account_id)
            if account.type == 'receivable':
                res['value'].update({'is_customer': True,'is_supplier': False})
            elif account.type == 'payable':
                res['value'].update({'is_supplier': True,'is_customer': False})

        return res



    def open_invoice_tree(self, cr, uid, ids, context):

        return {
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }




account_bank_statement_line()



