from openerp.osv import fields, osv

class cashFlowreportWizard(osv.osv_memory):
    
    _inherit = "account.report.wiz"
    _name = "cash.flow.report.wiz"
    _description = "Cash Flow Report Wizard"

    _columns = {
        'enable_period_comparison' : fields.boolean('Enable Periods Cash Flow',help="Enables Period comparsion"),

    }

    def onchange_enable_period_change(self, cursor, uid, ids, enable_period_comparison, context=None):

        vals = {}
        if enable_period_comparison:
            vals['filter'] = 'filter_period'
        return {'value' : vals}

    def _print_report(self, cursor, uid, ids, data, context=None):
        print "ids",ids
        cash_flow_obj = self.browse(cursor, uid, ids[0])

        if cash_flow_obj.enable_period_comparison:
            data['form'].update({'enable_period_comp' : True})
        else:
            data['form'].update({'enable_period_comp' : False})
            
        context = context or {}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'cash_flow_report',
            'datas': data
            }

    