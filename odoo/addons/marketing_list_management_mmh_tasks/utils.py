# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
_logger = logging.getLogger(__name__)


def send_email(obj, cr, uid, id, module, xml_tmpl_id, context=None):
    model_pool = obj.pool['ir.model.data']
    try:
        template_id = model_pool.get_object_reference(
            cr, uid, module, xml_tmpl_id)[1]  # (u'email.template', <id>)
    except ValueError:
        _logger.error("Default email template is not defined",
                      exc_info=True)
        return False

    template_pool = obj.pool['email.template']
    values = template_pool.generate_email(
        cr, uid, template_id, id, context=context)

    attachments = values.pop('attachments') or []
    values.pop('email_recipients')

    mail_pool = obj.pool['mail.mail']
    msg_id = mail_pool.create(cr, uid, values, context=context)

    # Adding in template defined attachments
    attachment_ids = []
    attachment_pool = obj.pool['ir.attachment']

    for fname, fcontent in attachments:
        attachment_data = {
            'name': fname,
            'datas_fname': fname,
            'datas': fcontent,
            'res_model': mail_pool._name,
            'res_id': msg_id,
        }

        attachment_ids.append(attachment_pool.create(
            cr, uid, attachment_data, context=context))

    if attachment_ids:
        mail_pool.write(cr, uid, msg_id,
                        {'attachment_ids': [(6, 0, attachment_ids)]},
                        context=context)

    return msg_id
