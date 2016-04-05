import pooler
from report import report_sxw
from tools.translate import _
from openerp.osv import fields, osv, orm

from openerp.addons.account_report_lib.account_report_base import accountReportbase

class cashFlowreport(accountReportbase):
    
    def __init__(self, cr, uid, name, context):      
        super(cashFlowreport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'cr': cr,
            'uid':uid,
            'pool': pooler,
            'get_data':self.get_data,
        })

    #1. Report parameters
    def get_report_parameters(self, cr, uid, data, context):
        
        filter_data = [] #contains the start and stop period or dates.
 
        #===================FILTER PARAMETERS =====================#       
        fiscal_year = self.get_fiscalyear(data)        
        filter_type = self.get_filter(data)
        target_move = self.get_target_move(data)
        chart_account_id = self.get_chart_account_id(data)
        print "dataaa",data
        #======================FILTER TIME ===============================#       
        if filter_type == 'filter_period':            
            #Build filter_data
            filter_data.append(self.get_start_period(data))
            filter_data.append(self.get_end_period(data))
            
        elif filter_type == 'filter_date':
            #Build filter_data
            filter_data.append(data['form']['date_from'])
            filter_data.append(data['form']['date_to'])

        else:
            filter_type = ''        
        
        return {
                'filter_data' : filter_data,
                'filter_type': filter_type,
                'fiscal_year': fiscal_year,
                'chart_account_id': chart_account_id,
                'target_move': target_move,
                
                }
    
    #2. Get all accounts that moves_cash
    def get_accounts_moves_cash(self, cr, uid, context):
        return self.pool.get('account.account').search(cr, uid, [('moves_cash','=',True)])
    
    #3. Get move_lines that match with filters.
    def get_move_lines(self, cr, uid, data, context):
        
        account_report_lib = self.pool.get('account.webkit.report.library')
        account_dict = {}
        
        #======================================================
        #Accounts
        account_ids = self.get_accounts_moves_cash(cr, uid, context)        
        #Parameters
        parameter_dict = self.get_report_parameters(cr, uid, data, context)

    
        
        #Get move_lines for each account.
        print "account moves cash",account_ids
        
        for account_id in account_ids:
            account_dict[account_id] = account_report_lib.get_move_lines(cr, uid,
                                                   account_ids=[account_id],
                                                   filter_type=parameter_dict['filter_type'],
                                                   filter_data=parameter_dict['filter_data'],
                                                   fiscalyear=parameter_dict['fiscal_year'],
                                                   target_move=parameter_dict['target_move'],
                                                   unreconcile=False,
                                                   historic_strict=False,
                                                   special_period=False,
                                                   context=context)
        
        #account_dict is a dictionary where key is account_id and it has all move_lines for each account.
        return account_dict
    
    #4. Build data for report
    def get_data(self, cr, uid, data,context):
        print "dataaa",data
        distribution_obj = self.pool.get('account.cash.flow.distribution')
        account_report_lib = self.pool.get('account.webkit.report.library')
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        cash_flow_amounts = {} # contains amounts for each cash_flow_types
        cash_flow_types = {}   # Groups by type    
        total_by_type = {}     # Return total amount by type
        cash_at_begin_period = {}
        cash_at_end_period = {}
        period_group = []
        period_names = []
        enable_comparison = False
        
        #===========================================================
        
        #Get move_lines
        account_dict = self.get_move_lines(cr, uid, data, context)
        parameter_dict = self.get_report_parameters(cr, uid, data, context)
        
        #Find if lines have a distribution_line
        print "account dict",account_dict

        ### aim code to get it serialized form in the menu

        if data['form'].has_key('enable_period_comp'):
            enable_comparison = data['form']['enable_period_comp']

            if enable_comparison:
                start_period = period_obj.browse(cr, uid, data['form']['period_from'])
                end_period = period_obj.browse(cr, uid, data['form']['period_to'])
                period_group = period_obj.get_interval_period(cr, uid, start_period, end_period,data['form']['fiscalyear_id'])
                for i in period_obj.browse(cr, uid, period_group):
                    initial_balance = 0.0
                    period_balance = 0.0
                    period_names.append(i.name)


                    #### aim code to find the cash at the begining of the period and the balance as well
                    accounts_initial_bal = account_report_lib.get_account_balance(cr, uid,
                                                                        account_ids= account_dict.keys(),
                                                                        field_names=['debit','credit','balance'],
                                                                        initial_balance=True,
                                                                        company_id = False,
                                                                        fiscal_year_id=parameter_dict['fiscal_year'].id,
                                                                        all_fiscal_years=False,
                                                                        state=data['form']['target_move'],
                                                                        start_date=data['form']['date_from'],
                                                                        end_date=data['form']['date_to'],
                                                                        start_period_id=i.id,
                                                                        end_period_id=i.id,
                                                                        period_ids=False,
                                                                        journal_ids=False,
                                                                        chart_account_id=False,
                                                                        filter_type=data['form']['filter'],
                                                                        context=context)

                    ### calculating the initial balance at the end of each period
                    for key,value in accounts_initial_bal.iteritems():
                        initial_balance += accounts_initial_bal[key]['balance']
                    cash_at_begin_period[i.id] = initial_balance

                    #### code ends here

                    #### aim code to find the cash balance at each period end
                    accounts_final_bal = account_report_lib.get_account_balance(cr, uid,
                                                                        account_ids= account_dict.keys(),
                                                                        field_names=['balance'],
                                                                        initial_balance=False,
                                                                        company_id = False,
                                                                        fiscal_year_id=parameter_dict['fiscal_year'].id,
                                                                        all_fiscal_years=False,
                                                                        state=data['form']['target_move'],
                                                                        start_date=data['form']['date_from'],
                                                                        end_date=data['form']['date_to'],
                                                                        start_period_id=i.id,
                                                                        end_period_id=i.id,
                                                                        period_ids=False,
                                                                        journal_ids=False,
                                                                        chart_account_id=False,
                                                                        filter_type=data['form']['filter'],
                                                                        context=context)

                    ### calculating the initial balance at the end of each period
                    for key,value in accounts_final_bal.iteritems():
                        period_balance += accounts_final_bal[key]['balance']
                    
                    cash_at_end_period[i.id] = period_balance + initial_balance

                    #### code ends here


        ### code ends here

        for account, move_lines in account_dict.iteritems():
            period_dict_account = []
            ac_obj = account_obj.browse(cr, uid, account)
            current_account = ac_obj
            amount_debit = 0.0
            amount_credit = 0.0
            balance = 0.0

            
            print "parameter dict",parameter_dict
            print "period from to",data['form']['period_from'],data['form']['period_to']
            
            list = []
            list.append(current_account.cash_flow_type.type)
            list.append(current_account.name+"("+current_account.code+")")

            if enable_comparison:
                for each_period in period_group:
                    account_bal = account_report_lib.get_account_balance(cr, uid,
                                                                        account_ids=[account],
                                                                        field_names=['debit','credit','balance'],
                                                                        initial_balance=False,
                                                                        company_id = False,
                                                                        fiscal_year_id=parameter_dict['fiscal_year'].id,
                                                                        all_fiscal_years=False,
                                                                        state=data['form']['target_move'],
                                                                        start_date=data['form']['date_from'],
                                                                        end_date=data['form']['date_to'],
                                                                        start_period_id=each_period,
                                                                        end_period_id=each_period,
                                                                        period_ids=False,
                                                                        journal_ids=False,
                                                                        chart_account_id=False,
                                                                        filter_type=data['form']['filter'],
                                                                        context=context)

                    list.append(account_bal[account]['balance'])

            else:
                account_bal = account_report_lib.get_account_balance(cr, uid,
                                                                    account_ids=[account],
                                                                    field_names=['debit','credit','balance'],
                                                                    initial_balance=False,
                                                                    company_id = False,
                                                                    fiscal_year_id=parameter_dict['fiscal_year'].id,
                                                                    all_fiscal_years=False,
                                                                    state=data['form']['target_move'],
                                                                    start_date=data['form']['date_from'],
                                                                    end_date=data['form']['date_to'],
                                                                    start_period_id=data['form']['period_from'],
                                                                    end_period_id=data['form']['period_to'],
                                                                    period_ids=False,
                                                                    journal_ids=False,
                                                                    chart_account_id=False,
                                                                    filter_type=data['form']['filter'],
                                                                    context=context)


            

                amount_debit = account_bal[account]['debit']
                amount_credit = account_bal[account]['credit']
                balance = account_bal[account]['balance']
                list.append(account_bal[account]['debit'])
                list.append(account_bal[account]['credit'])
                list.append(account_bal[account]['balance'])

            cash_flow_amounts[current_account.id] = list
                

        
        #========================================================================
        
        #Group in types (operational, investment, financing). Create list of each type (with id)
        #This connect dictionary with amounts (cash_flow_amounts) and dictionary with types.
        #example = {'operational': 1, 3, 4} -> cash_flow_id
        length_cash_flow_amt = 0
        for type_id, items in cash_flow_amounts.iteritems():

            length_cash_flow_amt = len(items)
            type_name = items[0]
            if type_name not in cash_flow_types.keys():
                cash_flow_types[type_name] = [type_id] #position 2 is id of cash_flow_type. Create a list with id of cash_flow_type.
            
            else:
                list = cash_flow_types[type_name] 
                list.append(type_id) #Add new id
                cash_flow_types[type_name] = list
                list = []
        
        
        #========================================================================
        amount = 0.0
        #Group totals by type, return a dictionary with totals.
        #Iterate in each id and sum, in cash_flow_amounts
        for type, list_ids in cash_flow_types.iteritems():
            ### code to calculate the subtotal in each periods
            total_by_type[type] = []
            subtotal_list = []
            subtotal_list.append("Total")
            if enable_comparison and length_cash_flow_amt > 2:
                
                for i in range(2,length_cash_flow_amt):
                    amount = 0.0
                    for item in list_ids:
                        if item in cash_flow_amounts.keys():
                            list_values = cash_flow_amounts[item]
                            amount += list_values[i]
                    subtotal_list.append(amount)
                total_by_type[type] = subtotal_list


            else:
                for item in list_ids:
                    if item in cash_flow_amounts.keys():
                        list_values = cash_flow_amounts[item] #extract info from cash_flow_amounts
                        amount += list_values[4] #amount for type.

                #for example
                #total_by_type['operational'] = 40 000
                total_by_type[type] = amount



        #=========================================================================
       
        #====RETURN THREE DICTIONARIES
        # 1. CASH_FLOW_AMOUNTS = Contains total amount, debit and credit for each cash_flow type
        # 2. CASH_FLOW_TYPES =  Return type_cash_flow as key (operational, investment and financing) and a list of ids of cash_flow_types that 
        # are associated of one of those types.
        # 3. TOTAL_BY_TYPE = Return a dictionary, where key is one type and it has total amount for each type.
        
        
        #If there not exist data, return empty dictionaries
        if not cash_flow_amounts:
            cash_flow_types = {
                               'operation': [],
                               'investment': [],
                               'financing': [],
                               }
            total_by_type = {
                               'operation':0.0,
                               'investment': 0.0,
                               'financing':0.0,
                               }


        print "cash flow amnount",cash_flow_amounts
        print "cash_flow_types",cash_flow_types
        print "total by type",total_by_type
        return cash_flow_amounts, cash_flow_types, total_by_type,enable_comparison,period_names,cash_at_begin_period,cash_at_end_period

report_sxw.report_sxw(
    'report.cash_flow_report',
    'cash.flow.type',
    'addons/cash_flow_report/report/cash_flow_report.mako',
    parser=cashFlowreport)
    