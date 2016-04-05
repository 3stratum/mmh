import time
import openerp.pooler as pooler
from openerp.report import report_sxw
from openerp.osv import fields, osv
from openerp.tools.translate import _

class fedex_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(fedex_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_image':self._get_image,
                })

    def _get_image(self,data):
        ir_attach = pooler.get_pool(self.cr.dbname).get('ir.attachment')
        ids=data[0]
        result = []        
        if ids:
            for each in ids:
                attach_ids=ir_attach.search(self.cr,self.uid,[('res_id','=',each),('res_model','=','stock.picking.out')])
                for each_att in attach_ids:
                    datas=ir_attach.browse(self.cr,self.uid,each_att)                    
                    result.append(datas)                    
        return result
report_sxw.report_sxw('report.fedex.report.bista','stock.picking.out','bista_addons/bista_shipping/report/fedex_label_report.rml', parser=fedex_report,header=False)