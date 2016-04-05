# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from openerp.osv import osv, fields
import time
import datetime
import xmlrpclib
import urllib2
import base64
from openerp.tools.translate import _
from xml.dom.minidom import parse, parseString
import os
import httplib, ConfigParser, urlparse

import logging
_logger = logging.getLogger(__name__)


class Session:
    def Initialize(self, username, password,environment):
        self.username = username
        self.password = password
        self.environment = environment

########## Call
class Call:
    RequestData = ""  # just a stub

    def MakeCall(self, CallName,username,password,link):
        _logger.info("RequestData %s", self.RequestData)
        concat_str = str(username)+":"+str(password)
        encoded_str = base64.b64encode(concat_str)
        environment = self.Session.environment
        if environment =='sandbox':
            domain ='ct.soa-gw.canadapost.ca'
        else:
            domain='soa-gw.canadapost.ca'
        conn = httplib.HTTPSConnection(domain)
        if CallName == 'GetService':
            command = '/rs/ship/service'
            method="GET"
        elif CallName == 'GetRates':
            command = '/rs/ship/price'
            method="POST"
        elif CallName == 'GetShipping':
            command = '/rs/0008079622/ncshipment'
            method="POST"
        elif CallName == 'Getartifact':
            command = link
            method="GET"
        conn.request(method, command, self.RequestData, self.GenerateHeaders(CallName,encoded_str))
        response = conn.getresponse()
        data = response.read()
        if CallName == 'Getartifact':
            return data
        conn.close()
        responseDOM = parseString(data)
        desc_error = []
        for each in  responseDOM.getElementsByTagName('messages'):
            descp = each.getElementsByTagName('description')[0].toxml()
            descData=descp.replace(descp,'')
            desc_error.append(descData)
            raise osv.except_osv(_('Warning !'), _(descp))
    # check for any <Error> tags and print
        # TODO: Return a real exception and log when this happens
        tag = responseDOM.getElementsByTagName('Error')
        if (tag.count!=0):
            for error in tag:
                print "\n",error.toprettyxml("  ")
        return responseDOM

    def GenerateHeaders(self,callname,encoded_str):
        httpHeaders = {
		"Accept-language": "en-CA",
                "Authorization": "Basic "+ encoded_str
            }
        if callname=="GetService":
            httpHeaders["Accept"] = "application/vnd.cpc.ship.rate+xml"
        elif callname=="GetRates":
            httpHeaders["Accept"] = "application/vnd.cpc.ship.rate+xml"
            httpHeaders["Content-Type"] = "application/vnd.cpc.ship.rate+xml"
        elif callname=="GetShipping":
            httpHeaders["Accept"] = "application/vnd.cpc.ncshipment+xml"
            httpHeaders["Content-Type"] = "application/vnd.cpc.ncshipment+xml"
        if callname=="Getartifact":
            httpHeaders["Accept"] = "application/pdf"
        _logger.info("httpHeaders %s",httpHeaders)
        return httpHeaders

########## GetToken
class GetService:
    Session = Session()

    def __init__(self, username,password,environment):
        self.Session.Initialize(username,password,environment)

    def getShippingservice(self, nodelist):
        transDetails = []
        for node in nodelist:
            for cNode in node.childNodes:
                info = {}
                if cNode.nodeName == 'service':
                    if cNode.childNodes:

                        for ch_Node in cNode.childNodes:

                            if ch_Node.nodeName == 'service-code':
                                info[ch_Node.nodeName] = ch_Node.childNodes[0].nodeValue
                            elif ch_Node.nodeName == 'service-name':
                                info[ch_Node.nodeName] = ch_Node.childNodes[0].nodeValue
                        transDetails.append(info)
        _logger.info("transDetails %s",transDetails)
        return transDetails

    def Get(self):
        api = Call()
        api.Session = self.Session
        api.RequestData = ''
        val = []

        responseDOM = api.MakeCall("GetService",api.Session.username,api.Session.password,'')
        transInfo = self.getShippingservice(responseDOM.getElementsByTagName('services'))
        return transInfo

########## GetRates
class GetRates:
    Session = Session()

    def __init__(self, username,password,environment):
        self.Session.Initialize(username,password,environment)

    def getShippingrates(self, nodelist):
        transDetails = []
        for node in nodelist:
            for cNode in node.childNodes:
                info = {}
                if cNode.nodeName == 'price-details':
                    if cNode.childNodes:
                        for ch_Node in cNode.childNodes:
                            if ch_Node.nodeName == 'base':
                                info[ch_Node.nodeName] = ch_Node.childNodes[0].nodeValue
                            elif ch_Node.nodeName == 'taxes':
                                for c_node in ch_Node.childNodes:
                                    if c_node.nodeName == 'gst':
                                        info[c_node.nodeName] = c_node.childNodes[0].nodeValue
                                    if c_node.nodeName == 'pst':
                                        info[c_node.nodeName] = c_node.childNodes[0].nodeValue
                                    if c_node.nodeName == 'hst':
                                        info[c_node.nodeName] = c_node.childNodes[0].nodeValue
                        transDetails.append(info)
        _logger.info("transDetails %s",transDetails)
        return transDetails

    def Get(self,xml):
        api = Call()
        api.Session = self.Session
        api.RequestData = xml
        _logger.info("xml request %s",xml)
        val = []
        responseDOM = api.MakeCall("GetRates",api.Session.username,api.Session.password,'')
        transInfo = self.getShippingrates(responseDOM.getElementsByTagName('price-quote'))
        return transInfo

########## GetShipping
class GetShipping:
    Session = Session()

    def __init__(self, username,password,environment):
        self.Session.Initialize(username,password,environment)

    def getlinks(self, nodelist):
        for node in nodelist:
            for cNode in node.childNodes:
                info = {}
                if cNode.nodeName == 'link':
                    info[cNode.nodeName] = cNode.getAttribute("href")
            return cNode.getAttribute("href")

    def Get(self,xml):
        api = Call()
        api.Session = self.Session
        api.RequestData = xml
        val = {}
        responseDOM = api.MakeCall("GetShipping",api.Session.username,api.Session.password,'')
        tracking_no = responseDOM.getElementsByTagName('tracking-pin')[0].childNodes[0].data
        if tracking_no:
            val['tracking_no'] =tracking_no
        link = self.getlinks(responseDOM.getElementsByTagName('links'))
        if link:
            val['link'] =link
        return val

class Getartifact:
    Session = Session()

    def __init__(self, username,password,environment):
        self.Session.Initialize(username,password,environment)

    def Get(self,link):
        api = Call()
        api.Session = self.Session
        api.RequestData = ''
        val = {}
        responseDOM = api.MakeCall("Getartifact",api.Session.username,api.Session.password,link)
        return responseDOM

def call(cr, uid,method,username,password,environment,*arguments):
    if method == 'GetService':
        gs = GetService(username,password,environment)
        result = gs.Get()
        return result
    if method == 'Getartifact':
        ga = Getartifact(username,password,environment)
        result = ga.Get(arguments[0])
        return result
    elif method == 'GetRates':
        gr = GetRates(username,password,environment)
        result = gr.Get(arguments[0])
        return result
    elif method == 'GetShipping':
        gsh = GetShipping(username,password,environment)
        result = gsh.Get(arguments[0])
        return result