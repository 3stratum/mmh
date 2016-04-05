from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import base64
import csv
from datetime import datetime
from openerp.addons.account_statement_base_import.parser.file_parser import FileParser
from openerp.addons.account_statement_base_import.parser.generic_file_parser import GenericFileParser
from openerp.addons.account_statement_base_import.parser import BankStatementImportParser

class GenericFileParserMMH(GenericFileParser):


    def __init__(self, parse_name, ftype='csv', **kwargs):
        super(GenericFileParserMMH, self).__init__(parse_name, ftype=ftype, **kwargs)

    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it. It is the responsibility
        of every parser to give this dict of vals, so each one can implement his
        own way of recording the lines.
            :param:  line: a dict of vals that represent a line of result_row_list
            :return: dict of values to give to the create method of statement line,
                     it MUST contain at least:
                {
                    'name':value,
                    'date':value,
                    'amount':value,
                    'ref':value,
                    'label':value,
                }
        """
        print "line ids"
#        return {
#            'name': line.get('label', line.get('ref', '/')),
#            'date': line.get('date', datetime.datetime.now().date()),
#            'amount': line.get('amount', 0.0),
#            'ref': line.get('ref', '/'),
#            'label': line.get('label', ''),
#        }
#
        return {
            'name': line.get('Serial Number', line.get('ref', '/')),
            'date': line.get('Posted Date', datetime.datetime.now().date()),
            'amount': line.get('Amount', 0.0),
            'ref': line.get('Serial Number', '/'),
            'label': line.get('ref', ''),
        }

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the new_bank_statement_parser class factory. Return true if
        the providen name is generic_csvxls_so
        """
        return parser_name == 'generic_csvxls_so'




