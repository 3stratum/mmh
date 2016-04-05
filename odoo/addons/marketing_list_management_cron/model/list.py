# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv.orm import Model
from openerp.osv import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.base.ir.ir_cron import _intervalTypes
from datetime import datetime
import pytz


class ListHeader(Model):

    _inherit = 'list.header'
    _columns = {
        'interval_number': fields.integer(
            'Interval Number', help="Repeat every x."),
        'interval_type': fields.selection(
            [
                ('minutes', 'Minutes'),
                ('hours', 'Hours'),
                ('work_days', 'Work Days'),
                ('days', 'Days'),
                ('weeks', 'Weeks'),
                ('months', 'Months')
            ],
            'Interval Unit'),
        'numbercall': fields.integer(
            'Number of Calls',
            help="How many times the method is called,\n "
                 "a negative number indicates no limit."),
        'nextcall': fields.datetime(
            'Next Execution Date', required=True,
            help="Next planned execution date for this job."),
    }
    _defaults = {
        'nextcall': fields.datetime.now,
        'interval_number': 1,
        'interval_type': 'weeks',
        'numbercall': 1,
    }

    def process_lists(self, cr, uid, context=None):
        cr.execute("""SELECT * FROM list_header
              WHERE numbercall != 0
                AND active AND nextcall <= (now() at time zone 'UTC')
              ORDER BY generated_date""")
        jobs = cr.dictfetchall()
        for job in jobs:
            self._process_job(cr, uid, job, context=context)

    def _process_job(self, cr, uid, job, context=None):
        """ Run a given job taking care of the repetition.

        :param job_cr: cursor to use to execute the job, safe to commit/rollback
        :param job: job to be run (as a dictionary).
        :param cron_cr: cursor holding lock on the cron job row, to use to update the next exec date,
            must not be committed/rolled back!
        """
        try:
            now = fields.datetime.context_timestamp(cr, uid, datetime.now())
            nextcall = fields.datetime.context_timestamp(
                cr, uid, datetime.strptime(
                    job['nextcall'],
                    DEFAULT_SERVER_DATETIME_FORMAT))
            numbercall = job['numbercall']

            ok = False
            while nextcall < now and numbercall:
                if numbercall > 0:
                    numbercall -= 1
                if not ok:
                    self.call_tasks(cr, uid, job['id'], context=context)
                if numbercall:
                    nextcall += _intervalTypes[job['interval_type']](job['interval_number'])
                ok = True
            addsql = ''
            if not numbercall:
                addsql = ', active=False'
            cr.execute(
                "UPDATE list_header SET nextcall=%s, numbercall=%s"+addsql+" WHERE id=%s",
                (nextcall.astimezone(pytz.UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                 numbercall, job['id']))
        finally:
            cr.commit()

    def call_tasks(self, cr, uid, list_id, context=None):
        raise NotImplementedError("Needs to extend it!")
