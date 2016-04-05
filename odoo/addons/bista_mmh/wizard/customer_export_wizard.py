from openerp.osv import fields, osv
import xmlrpclib
from io import open
from datetime import datetime
import getpass
from tools.translate import _
import time
import base64
import netsvc
logger = netsvc.Logger()
import csv
import StringIO
import binascii
from base64 import b64decode
import cStringIO
import unicodedata


class customer_export_wizard(osv.osv_memory):
    """
        A wizard to manage import of csv file
    """
    _name = 'customer.export.wizard'
    _description = 'Export CSV File'
    _columns = {
        'main_host':fields.char('Main host',size=256),
        'db':fields.char('database',size=256),
        'uname':fields.char('User Name',size=256),
        'pwd':fields.char('Password',size=256),
        'exportfile_csv' : fields.binary('CSV file'),
    }

#    Export data from .csv file

    def export_data(self, cr, uid, ids, context):
        BLUE = '\033[94m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        END = '\033[0m'
        bufs=cStringIO.StringIO()
        writer_in=csv.writer(bufs, 'UNIX')
        res_obj=self.pool.get('res.partner')
        data=self.browse(cr,uid,ids[0])
        main_host = 'http://192.168.1.13:8069'
        db = data.db
        uname = data.uname
        pwd = data.pwd
        print"---", main_host
        sc=xmlrpclib.ServerProxy(main_host + '/xmlrpc/common')
        uid_new=sc.login(db,uname,pwd)
        sc1=xmlrpclib.ServerProxy(main_host + '/xmlrpc/object')

#        print color.BLUE + color.BOLD + '\nSuccessfully connected to the server...' + color.END

#        print color.RED + color.BOLD + '\nExample value for fields: "id","property_account_payable/id","property_account_receivable/id","name","notification_email_send","phone","active","customer","supplier"' + color.END
#        print color.RED + color.BOLD + 'It has to be in the exact format, that is, double quoted and comma saperated' + color.END
#        fields = raw_input("Enter the field names: ")
        fields='"id","name"'
        fields = [fields]
        fields=unicode(fields).replace("'",'')
        fields = eval(fields)
        count=0
        print"\nExported file will be created(with name, 'OE_exported_partners.csv') in the directory/folder where the current script resides."

        # Search all active/in-active partners
        res_id = sc1.execute(db, uid, pwd, 'res.partner', 'search', [])
        
        print"\nExporting %s record(s)...", res_id

        export = sc1.execute(db, uid_new, pwd, 'res.partner', 'export_data',res_id, fields)
        print"\nData exported successfully..."

        fields=unicode(fields).replace('[','')
        fields=unicode(fields).replace(']','')
        fields=unicode(fields).replace(' ','')
        fields=unicode(fields).replace("'",'"')

        vals=''
        flag=True

        for i in export['datas']:
            for x in i:
                if flag:
                    vals = x and vals + '"' + unicode(x) + '"' or vals + '""'
                    flag = False
                else:
                    vals = x and vals + ',"' +  unicode(x) + '"' or vals + ',""'
            vals += "\n"
            flag = True

        print"\nNow, dumping the data to the file 'OE_exported_partners.csv'..." 

        fil = open('OE_exported_partners.csv','a+')
        fil.write(fields+u"\n")
        fil.write(vals)
        fil.close()
        out=base64.encodestring(fil.getvalue())
        print"\nHurray, data dumped successfully..."
        return self.write(cr, uid, ids, {'state':'done', 'exportfile_csv':out,'name':'Export.csv'}, context=context)
#        print color.BLUE + color.BOLD + "\nHurray, data dumped successfully..." + color.END

 
