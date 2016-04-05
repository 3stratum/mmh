import openerp.addons.web.http as http
#from openerp.addons.web.http import request

class Tfa(http.Controller):
  
    _cp_path = '/user'

    

    @http.jsonrequest
    def tfa_enabled(self, req, db, login, base_location=None):
      print "user/tfa_enabled"
      return True

  
  
    #def getcategories(self, req, model, fields=False, offset=0, limit=False, domain=None, sort=None):
        #return self.do_search_read(req, model, fields, offset, limit, domain, sort)
    #def do_search_read(self, req, model, fields=False, offset=0, limit=False, domain=None
                       #, sort=None):
        #""" Performs a search() followed by a read() (if needed) using the
        #provided search criteria

        #:param req: a JSON-RPC request object
        #:type req: openerpweb.JsonRequest
        #:param str model: the name of the model to search on
        #:param fields: a list of the fields to return in the result records
        #:type fields: [str]
        #:param int offset: from which index should the results start being returned
        #:param int limit: the maximum number of records to return
        #:param list domain: the search domain for the query
        #:param list sort: sorting directives
        #:returns: A structure (dict) with two keys: ids (all the ids matching
                  #the (domain, context) pair) and records (paginated records
                  #matching fields selection set)
        #:rtype: list
        #"""
        #Model = req.session.model(model)

        #ids = Model.search(domain, offset or 0, limit or False, sort or False,
                           #req.context)
        #if limit and len(ids) == limit:
            #length = Model.search_count(domain, req.context)
        #else:
            #length = len(ids) + (offset or 0)
        #if fields and fields == ['id']:
            ## shortcut read if we only want the ids
            #return {
                #'length': length,
                #'records': [{'id': id} for id in ids]
            #}

        #records = Model.read(ids, fields or False, req.context)
        #records.sort(key=lambda obj: ids.index(obj['id']))
        #return {
            #'length': length,
            #'records': records
        #}
        