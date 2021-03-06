# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Addons modules by CLEARCORP S.A.
#    Copyright (C) 2009-TODAY CLEARCORP S.A. (<http://clearcorp.co.cr>).
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

import time
import pooler
from report import report_sxw
import locale
from openerp.tools.translate import _

class accountReportbase(report_sxw.rml_parse):
    
    """
        This class is the base for the reports. Contains all the basic functions
        to extract info that the reports needs
    """
    def __init__(self, cr, uid, name, context):
        super(accountReportbase, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr' : cr,
            'uid': uid,
            'get_start_period': self.get_start_period,
            'get_end_period':self.get_end_period,
            'get_fiscal_year':self.get_fiscalyear,
            'get_chart_account_id': self.get_chart_account_id,
            'get_filter': self.get_filter,
            'get_target_move': self.get_target_move,
            'get_date_from': self.get_date_from,
            'get_date_to': self.get_date_to,
            'get_accounts_ids': self.get_accounts_ids,
            'get_historic_strict': self.get_historic_strict,
            'get_special_period': self.get_special_period,
            'display_target_move':self.get_display_target_move,
            'get_signatures_report': self.get_signatures_report,
            'get_amount_currency':self.get_amount_currency,
            'get_account_base_report':self.get_account_base_report,
         })
    
    #####################################BASIC FUNCTIONS ##############################
    
    #Basic function that extract the id of the wizard and return the object (model)
    
    '''
        The method _get_info return a browse (return the complete model)
    '''
    def _get_info(self, data, field, model):
        info = data.get('form', {}).get(field)
        if info:
            return self.pool.get(model).browse(self.cr, self.uid, info)
        return False
    
    '''
        The method _get_form_param return the real value in the wizard. 
    '''
    def _get_form_param(self, param, data, default=False):
        return data.get('form', {}).get(param, default)
    
    #########################################################################
    
    def get_start_period(self, data):
        return self._get_info(data,'period_from', 'account.period')
    
    def get_end_period(self, data):
        return self._get_info(data,'period_to', 'account.period')
    
    def get_fiscalyear(self, data):
        return self._get_info(data,'fiscalyear_id', 'account.fiscalyear')
    
    def get_chart_account_id(self, data):
        return self._get_info(data, 'chart_account_id', 'account.account')
    
    def get_filter(self, data):
        return self._get_form_param('filter', data)
    
    def get_target_move(self, data):
        return self._get_form_param('target_move', data)
    
    def get_date_from(self, data):
        return self._get_form_param('date_from', data)

    def get_date_to(self, data):
        return self._get_form_param('date_to', data)
    
    #Case special for conciliation bank -> account_ids is an unicode.
    def get_accounts_ids (self, cr, uid, data):
        if isinstance(data['form']['account_ids'], unicode):
            return self.pool.get('account.account').browse(cr, uid, [int(data['form']['account_ids'])])[0]
        
        return self._get_info(data,'account_ids', 'account.account')
    
    def get_historic_strict (self, data):
        return self._get_form_param('historic_strict', data)
    
    def get_special_period (self, data):
        return self._get_form_param('special_period', data)
    
    def get_amount_currency (self, data):
        return self._get_form_param('amount_currency', data)
    
    def get_account_base_report(self, data):
        return self._get_info(data, 'account_base_report', 'account.financial.report')
    
    ################################## INFO DISPLAY ###########################
    
    def get_display_target_move(self, data):
        val = self._get_form_param('target_move', data)
        if val == 'posted':
            return _('All Posted Entries')
        elif val == 'all':
            return _('All Entries')
        else:
            return val
    
    ##################### SIGNATURES ############################
     #Return the users that can sign the report.
    def get_signatures_report(self, cr, uid, report_name):  
      report_id = self.pool.get('ir.actions.report.xml').search(cr, uid,[('name','=', report_name)])
      report_obj = self.pool.get('ir.actions.report.xml').browse(cr, uid, report_id)
#      return report_obj[0].signature_users
      return []