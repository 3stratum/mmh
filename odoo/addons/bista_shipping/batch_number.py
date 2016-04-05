from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import tempfile
import time

class batch_numbers(osv.osv):
    _inherit = 'batch.numbers'
    _columns = {
        'labels_generated': fields.boolean('Labels Generated'),
    }
    _defaults = {
        'labels_generated': lambda *a: False,
    }
batch_numbers()
