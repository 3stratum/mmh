
import logging
import csv
import random
from openerp.osv import fields, osv
from openerp.osv.orm import BaseModel
from openerp.tools.translate import _
from openerp.tools import email_split
from openerp import SUPERUSER_ID
import base64


class customer_wizard(osv.osv_memory):
    """
        A wizard to manage import of csv file
    """
    _name = 'customer.wizard'
    _description = 'Upload CSV File'

#    Importing data from .csv file

    def import_data(self, cr, uid, ids, context):
        data=self.browse(cr,uid,ids[0])
	if not data.upload_file:
	    raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))
	module_data = data.upload_file
	val = base64.decodestring(module_data)
        split_data = val.split("\r")
        if len(split_data)==1 and split_data[0].find('\n')!=-1:
            split_data = tuple(split_data[0].split('\n'))
        fields = split_data[0].split(",")
        fields_data = []
        for each_field in fields:
            each_field = each_field.replace('"','')
            fields_data.append(each_field)
        data=[]
        for i in range(1,len(split_data)):
                data_new=tuple(split_data[i].split(","))
                if len(data_new)>1:
                    data.append(data_new)
        x = self.pool.get('res.partner')
        fields = x.load(cr,uid,fields_data,data)
        ir_model_data_obj = self.pool.get('ir.model.data')
        print "ir_model_data_objir_model_data_objir_model_data_obj",ir_model_data_obj
        return True
    _columns = {
        'upload_file': fields.binary('Upload File'),         
    }

   
