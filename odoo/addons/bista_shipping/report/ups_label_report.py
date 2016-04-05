import time
import openerp.pooler as pooler
from openerp.report import report_sxw 
from openerp.osv import fields, osv 
from openerp.tools.translate import _

class ups_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ups_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_image':self._get_image,
                })
        
    def _get_image(self,data):
        ir_attach = pooler.get_pool(self.cr.dbname).get('ir.attachment')
        ids=data[0]
        result = []
        extensionsToCheck = ('.png','.gif','.pdf')
        if ids:
            for each in ids:                
                attach_ids=ir_attach.search(self.cr,self.uid,[('res_id','=',each),('res_model','=','stock.picking.out')])
                for each_att in attach_ids:
                    datas=ir_attach.browse(self.cr,self.uid,each_att)
                    attachment_name = str(datas.name)
                    do_name=datas.res_name
                    if attachment_name.endswith(extensionsToCheck):#Checks Only for Image files
                        result.append(datas)                                        
        return result
report_sxw.report_sxw('report.ups.report.bista','stock.picking.out','bista_addons/bista_shipping/report/ups_label_report.rml', parser=ups_report,header=False)

