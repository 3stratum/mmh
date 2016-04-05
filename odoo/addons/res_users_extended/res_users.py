import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools

from osv import osv, fields
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
logger = logging.getLogger('product')


import time
import struct
import hmac
import hashlib
import base64


class res_users(osv.osv):
       _name = "res.users"
       _inherit = "res.users"
       
       
       def onchange_clear_secret_key(self, cr, uid, ids, two_factor_authentication, context=None):
	 secret_key = ''
	 return {
	   'value':{
	     'secret_key': secret_key
	     }
	   }
       
       def get_secret_key_url(self, cr, uid, ids, context=None):
	 
	 user_record = self.browse(cr, uid, ids)
	 username = user_record[0].login.replace(" ","")
	 secretkey = user_record[0].secret_key
	 if not secretkey:
	   raise osv.except_osv(_('Warning!'), _("Please provide the secret key for the user."))
	   return False
	 domain = (user_record[0].company_id.name).replace(" ","")
	 
	 url = "https://www.google.com/chart"
	 url += "?chs=200x200&chld=M|0&cht=qr&chl=otpauth://totp/"
	 url += username + "@" + domain + "?secret=" + secretkey
	 return url
	 
	 
       def send_secret_key(self, cr, uid, ids, context=None):

	  template_id = self.pool.get('email.template').search(cr, uid, [('name','like','Send QR code')])
	  user_email = self.browse(cr, uid, ids)[0].email
	  user_id = self.browse(cr, uid, ids)[0].id

	  if len(template_id):
	    if not user_email:
	      raise osv.except_osv(_('Warning!'), _("Please provide email id of the user."))
	    else:

	      return self.pool.get('email.template').send_mail(cr, uid, template_id[0], user_id, True, context=context)
	 
	 
       def _check_secret_key(self, cr, uid, ids, context=None):
	  record = self.browse(cr, uid, ids)
	  for data in record:
	    if data.two_factor_authentication:
	      if not data.secret_key:
		return False
	      elif len(data.secret_key)<16:
		return False
	      else:
		for each in data.secret_key:
		  if each.isdigit():
		    if not int(each) in range(2,8):
		      return False
		  else:
		    if not each.isupper():
		      return False
	  return True
	 
	
       _columns = {
	 'secret_key': fields.char('Google Authenticator Secret Key', size=16, help="Use combination of A-Z and 2-7 only to create a secret key."),
	 'two_factor_authentication' : fields.boolean("Enable Two Factor Authentication.")
	 }
       
       _defaults = {
	 'two_factor_authentication': False,
	 }
       _constraints = [(_check_secret_key, 'Error: Enter secret key in correct format. Use combination of A-Z and 2-7 only to create a secret key.', ['secret_key'])]


       @tools.ormcache(skiparg=2)
       def check_credentials_google(self, cr, secretkey, token):
	 
         """ Override this method to plug additional authentication methods"""

	 tm = int(time.time() / 30)

	 secretkey = base64.b32decode(secretkey)

	   # try 30 seconds behind and ahead as well
	 #for ix in [-3,-2,-1, 0, 1, 2, 3]:
	 #for ix in [-8,-7,-6,-5]:
#Last Error Time : Tue Apr 14 16:46:55 UTC 2015 : Server time is 6 minutes behind and login matches at -12 index

	 for ix in range(-20,20):
	   # convert timestamp to raw bytes
	   b = struct.pack(">q", tm + ix)

	   # generate HMAC-SHA1 from timestamp based on secret key
	   hm = hmac.HMAC(secretkey, b, hashlib.sha1).digest()

	  # extract 4 bytes from digest based on LSB
	   offset = ord(hm[-1]) & 0x0F
	   truncatedHash = hm[offset:offset+4]

	  # get the code from it
	   code = struct.unpack(">L", truncatedHash)[0]
	   code &= 0x7FFFFFFF;
	   code %= 1000000;
	   
#	   _logger.info("Two_factor_authenticatio secret_key:%s Token:%s", secretkey, token)
#	   _logger.info("Attempt number : %d",ix)
#	   _logger.info("%06d" % code)


	   if ("%06d" % code) == str(token):
	     return True
	   #else:
	     ##_logger.info("Unverified")
	 raise openerp.exceptions.AccessDenied()
	 return False


       def login_google(self, db, login, token):

           if not token:
               return False

           cr = pooler.get_db(db).cursor()
           try:
               # autocommit: our single update request will be performed atomically.
               # (In this way, there is no opportunity to have two transactions
               # interleaving their cr.execute()..cr.commit() calls and have one
               # of them rolled back due to a concurrent access.)
               cr.autocommit(True)
               # check if user exists
               res = self.search(cr, SUPERUSER_ID, [('login','=',login)])

               if res:
                   user_id = res[0]

                   user_record = self.browse(cr, SUPERUSER_ID, user_id)
                   secret_key = user_record.secret_key

                   # check credentials
                   verified = self.check_credentials_google(cr, secret_key, token)
           except openerp.exceptions.AccessDenied:
               _logger.info("Login failed for db:%s login:%s", db, login)
               verified = False
           finally:
               cr.close()
           return verified

	
       def authenticate_google(self, db, login, token, user_agent_env):

           verified = self.login_google(db, login, token)

           return verified
	 
       def tfa_enabled(self, db, login, user_agent_env):
           """Verifies and returns whether user has enabled Two Factor Authentication"""
           if not login:
               return False
           #user_id = False
           cr = pooler.get_db(db).cursor()
           try:
               # autocommit: our single update request will be performed atomically.
               # (In this way, there is no opportunity to have two transactions
               # interleaving their cr.execute()..cr.commit() calls and have one
               # of them rolled back due to a concurrent access.)
               cr.autocommit(True)
               # check if user exists
               res = self.search(cr, SUPERUSER_ID, [('login','=',login)])
               if res:
                   user_id = res[0]

                   user_record = self.browse(cr, SUPERUSER_ID, user_id)
                   tfa_enabled = user_record.two_factor_authentication

           except openerp.exceptions.AccessDenied:
               _logger.info("Login failed for db:%s login:%s", db, login)
               tfa_enabled = False
           finally:
               cr.close()
           return tfa_enabled	 


res_users()
