from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools

#class res_country(osv.osv):
#
#    _inherit = 'res.country'
#
##Filling state code on change of state in customer form view
#    def name_get(self, cr, uid, ids, context=None):
#        if context is None:
#            context = {}
#        if isinstance(ids, (int, long)):
#            ids = [ids]
#        res = []
#        for record in self.browse(cr, uid, ids, context=context):
#            code = record.code
#            res.append((record.id, code))
#        return res
#
#res_country()
class res_country_state(osv.osv):

    _inherit = 'res.country.state'

#Filling state code on change of state in customer form view
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            code = record.code
            res.append((record.id, code))
        return res

res_country_state()