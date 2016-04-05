import base64
from tools.translate import _
from osv import osv, fields
import time
import datetime


class location_account(osv.osv_memory):

    _name = 'location.account'
    _description = "location account"

    _columns = {
        'csv_file' : fields.binary('CSV file',required=True),
    }

    def import_csv(self, cr, uid, ids,context):

        '''
            code to import the csv for location accounts mapping
        '''
        data = self.browse(cr, uid, ids[0])

        if not data.csv_file:
            raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))
        module_data = data.csv_file
        val = base64.decodestring(module_data)


        location_account_data = val.split("\r")
        if len(location_account_data)==1 and location_account_data[0].find('\n')!=-1:
            location_account_data = location_account_data[0].split('\n')

        for i in range(0,len(location_account_data)):

            if i==0:
                continue
            location_account_data_lines = location_account_data[i]
            location_account_data_line = location_account_data_lines.split(',')

            if location_account_data_line[0] == '' or location_account_data_line[0] == '\n':
                continue
            elif location_account_data_line[1] == '' or location_account_data_line[1] == '\n':
                continue

            location = location_account_data_line[0].replace(" ","")
            location = location.replace("\"","")

            cr.execute("select * from stock_location where name ='%s'"%(location))
            location_data = cr.dictfetchone()


            if location_data:
                account_in_code = location_account_data_line[1].replace(" ","")
                account_in_code = account_in_code.replace("\"","")

                cr.execute("select * from account_account where code ='%s'"%(account_in_code))
                account_data_in = cr.dictfetchone()

                account_out_code = location_account_data_line[2].replace(" ","")
                account_out_code = account_out_code.replace("\"","")

                cr.execute("select * from account_account where code ='%s'"%(account_out_code))
                account_data_out = cr.dictfetchone()

                if not account_data_in or not account_data_out:
                    continue
                
                cr.execute('''
                            update stock_location
                            set valuation_in_account_id=%s,valuation_out_account_id=%s
                            where id=%s
                '''%(account_data_in['id'],account_data_out['id'],location_data['id']))
            
            
        return {'type':'ir.actions.act_window_close'}


location_account()

class import_inventory_csv(osv.osv_memory):
    """ Import Module """

    _name = "import.inventory.csv"
    _description = "Import Journal Entries"
    _columns = {
          'csv_file': fields.binary('CSV file', required=True),
          }
    _defaults = {

    }

    def update_product(self,cr,uid,ids,context):


        '''
        Code to import Inventory csv
        '''

        prod_templ=[]
        product_categ=[]
        update_products=0
        pro_obj=self.pool.get('product.product')
        if context.get('obj_name_filemaker'):
            val = ids
            if context.get('filemaker_ids',False):
                ids = context.get('filemaker_ids',False)
        else:
            data = self.pool.get('import.inventory.csv').browse(cr, uid, ids[0])
            if not data.csv_file:
                raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))
            module_data = data.csv_file
            val = base64.decodestring(module_data)

        product_inv_data = val.split("\r")
        if len(product_inv_data)==1 and product_inv_data[0].find('\n')!=-1:
            product_inv_data = tuple(product_inv_data[0].split('\n'))

        for i in range(1,len(product_inv_data)):
            """check for the number of columns"""
            header0 = product_inv_data[0].split(",")
            if len(header0) < 3 :
                raise osv.except_osv(_('CSV Error !'), _('Invalid header'))
            product_inv_data_lines = product_inv_data[i]
            product_single_line = product_inv_data_lines.split(",")
#            print "single line",product_single_line
            if len(product_single_line)>1:
                order = {
                    'Part ID': product_single_line[1].replace('"','').replace('\x0b',''),
                    'magento':product_single_line[3].replace('"','').replace('\x0b',''),
                }

                if order:

                    part_id = order['Part ID'] or ''
                    magento=order['magento'] or ''
                    print'magento============================',magento
                    if magento =='Y' or magento =='y':
                        product_id = self.pool.get('product.product').search(cr,uid,[('default_code','=',part_id),('active','=',True)])
#                        if len(product_id)<1:
#                            raise osv.except_osv(_('Product Error !'), _('No Product exists with same refrence %s in database'%part_id))

                        if len(product_id)>1:
                            raise osv.except_osv(_('Product Error !'), _('More than one Product exists with same refrence %s in database'%part_id))

                        if  product_id:
                            prod_obj=self.pool.get('product.product').browse(cr,uid,product_id[0])

                            prod_obj.write({'magento_exportable':True,'set':1})
                            update_products=update_products+1
                            product_categ.append(prod_obj.categ_id.id)
                            if prod_obj.product_tmpl_id.is_multi_variants==True:
                                prod_templ.append(prod_obj.product_tmpl_id.name)

        product_categ=list(set(product_categ))
        prod_templ=list(set(prod_templ))
        print'product_categ========================',product_categ
        print'update_products=====================',update_products
        print'prod_templ==========================',prod_templ
        return {
                'type': 'ir.actions.act_window_close'

        }
    def set_inventory_zero(self, cr, uid, ids, context):

        pro_obj=self.pool.get('product.product')
        loc_obj=self.pool.get('stock.location')
        product_ids=pro_obj.search(cr,uid,[('active','=',True),('type','=','product')])
        not_updateprod=[]
        for product_id in pro_obj.browse(cr,uid,product_ids):
            if not product_id.categ_id.location:
                not_updateprod.append(product_id.name)
            if product_id.categ_id.location:
                location_ids=loc_obj.search(cr,uid,[('usage','=','internal')])
                location_ids.remove(product_id.categ_id.location.id)
                for loc in location_ids:
                    cr.execute('insert into stock_inventory_line \
                            (product_id,product_uom,product_qty,location_id,inventory_id,company_id) \
                            values (%s,%s,%s,%s,%s,%s)', (product_id.id,product_id.uom_id.id,0,loc,context['active_id'],1))
                
        return {
                'type': 'ir.actions.act_window_close'

        }


    def import_csv(self, cr, uid, ids, context):

        '''
        Code to import Inventory csv
        '''
        
        not_update_products=[]
        update_products=0
        pro_obj=self.pool.get('product.product')
        if context.get('obj_name_filemaker'):
            val = ids
            if context.get('filemaker_ids',False):
                ids = context.get('filemaker_ids',False)
        else:
            data = self.pool.get('import.inventory.csv').browse(cr, uid, ids[0])
            if not data.csv_file:
                raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))
            module_data = data.csv_file
            val = base64.decodestring(module_data)

        product_inv_data = val.split("\r")
        if len(product_inv_data)==1 and product_inv_data[0].find('\n')!=-1:
            product_inv_data = tuple(product_inv_data[0].split('\n'))

        for i in range(1,len(product_inv_data)):
            """check for the number of columns"""
            header0 = product_inv_data[0].split(",")
            if len(header0) < 3 :
                raise osv.except_osv(_('CSV Error !'), _('Invalid header'))
            product_inv_data_lines = product_inv_data[i]
            product_single_line = product_inv_data_lines.split(",")
            print "single line",product_single_line
            if len(product_single_line)>1:
                order = {
                    'Location': product_single_line[5].replace('"','').replace('\x0b','').replace('\n',''),
                    'Part ID': product_single_line[0].replace('"','').replace('\x0b',''),
                    'ProductQtY': product_single_line[4].replace('"','').replace('\x0b',''),
                    'product_uom':product_single_line[2].replace('"','').replace('\x0b',''),
                    'name' : product_single_line[1].replace('"','').replace('\x0b',''),
                }

                if order:
                    loc = order['Location'].split(":") or ''
                    loc=loc[0]
                    part_id = order['Part ID'] or ''
                    qty = order['ProductQtY'] or 0
                    uom=order['product_uom'] or False
                    uom_id=self.pool.get('product.uom').search(cr,uid,[('name','=',uom)])
		    print'part_id=================================',part_id
                    product_id = self.pool.get('product.product').search(cr,uid,[('default_code','=',part_id),('active','=',True)])
                    if len(product_id)>1:
                        raise osv.except_osv(_('Product Error !'), _('More than one Product exists with same refrence %s in database'%part_id))
                    if not uom_id:
                        raise osv.except_osv(_('CSV Error !'), _('UOM not found in database'))
                    if not product_id:
                        raise osv.except_osv(_('CSV Error !'), _('No Item with Sap Description having Partnumber and Sap Part'))

                    if  product_id:
                        prod_obj=self.pool.get('product.product').browse(cr,uid,product_id[0])
                        if uom_id[0]!=prod_obj.uom_id.id:
                            raise osv.except_osv(_('CSV Error !'), _('UOM not match in CSV sheet and product master'))
                        location=self.pool.get('stock.location').search(cr,uid,[('name','ilike',loc)])
                        if location:
                            location_id=location[0]
                        else:
                            raise osv.except_osv(_('Warning!'),_("Location %s not find in database."%loc))
                        print"gsdjfhasjkfhsakl0",location_id
                        uom_id=prod_obj.product_tmpl_id.uom_id.id
                        cr.execute('insert into stock_inventory_line \
                                (product_id,product_uom,product_qty,location_id,inventory_id,company_id) \
                                values (%s,%s,%s,%s,%s,%s)', (product_id[0],uom_id,qty,location_id,context['active_id'],1))
                        update_products=update_products+1
        return {
                'type': 'ir.actions.act_window_close'

        }
import_inventory_csv()
class update_products(osv.osv_memory):
    _name = "update.product"
    _description = "update products"
    _columns = {
          'csv_file': fields.binary('CSV file', required=True),
          }
    def import_csv(self, cr, uid, ids, context):

        '''
        Code to Update Products
        '''
        pro_obj=self.pool.get('product.product')
        not_update_products=[]
        if context.get('obj_name_filemaker'):
            val = ids
            if context.get('filemaker_ids',False):
                ids = context.get('filemaker_ids',False)
        else:
            data = self.pool.get('update.product').browse(cr, uid, ids[0])
            if not data.csv_file:
                raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))
            module_data = data.csv_file
            val = base64.decodestring(module_data)

        product_inv_data = val.split("\r")
        if len(product_inv_data)==1 and product_inv_data[0].find('\n')!=-1:
            product_inv_data = tuple(product_inv_data[0].split('\n'))

        for i in range(1,len(product_inv_data)):
            """check for the number of columns"""
            header0 = product_inv_data[0].split(",")
#            if len(header0) < 3 or len(header0) > 3:
            if len(header0) < 2 :
                raise osv.except_osv(_('CSV Error !'), _('Invalid header'))
            product_inv_data_lines = product_inv_data[i]
            product_single_line = product_inv_data_lines.split(",")
            if len(product_single_line)>1:
                order = {
                    'part_id': product_single_line[0].replace('"','').replace('\x0b','').replace('\n',''),
                    'category': product_single_line[1].replace('"','').replace('\x0b',''),
                }

                if order:
                    part_id = order['part_id'].split(":") or ''
                    part_id=part_id[0]
                    category = int(order['category']) or ''

                    product_id = self.pool.get('product.product').search(cr,uid,[('default_code','=',part_id)])
                    print"part_idddddddddddddd!1111111111111",part_id
                    print"part_idddddddddddddd",product_id

#                    if len(product_id)>1:
#                            raise osv.except_osv(_('CSV Error !'), _('Duplicate Item in Openerp having Partnumber in csv '))
                    if not product_id:
                        not_update_products.append(part_id)
                        continue
                        raise osv.except_osv(_('CSV Error !'), _('No Item with Sap Description having Partnumber and Sap Part'))


                    if  product_id:
                        prod_obj=pro_obj.browse(cr,uid,product_id[0])

                        print"jfkhdfkjs",prod_obj,category
                        pro_obj.write(cr,uid,prod_obj.id,{'categ_id': category})

        print'==not_update_product===',not_update_products

        return {
                'type': 'ir.actions.act_window_close'

        }


update_products()
