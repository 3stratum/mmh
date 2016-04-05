import time

from openerp.osv import fields, osv
from openerp.tools.translate import _


class post_journal(osv.osv_memory):
    _name='post.journal'
    
    def post_selected_jornal(self,cr,uid,ids, context=None):
        move_ids = context.get('active_ids')
        move_obj = self.pool.get('account.move')

        for each_move in move_ids:
            print"fjksdlfjlksd",each_move
            move = move_obj.browse(cr,uid,each_move)
            print"fjdlsfjslkf",each_move
            if move.state == 'draft':
                move_obj.post(cr, uid, [each_move], context=context)
            else:
                continue

        return {'type': 'ir.actions.act_window_close'}


post_journal()