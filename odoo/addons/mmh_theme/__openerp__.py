# -*- coding: utf-8 -*-
{
  'name':'MMH UI Customizations',
  'description': 'Custom User Interface for Mountain Meadow Herbs',
  'summary': 'Visual customizations for MMH',
  'version':'1.0',
  'author':"Three Stratum, LLC",
  'website':'http://mountainmeadowherbs.com',
  'category': 'Custom',
  'depends': ['web'],
  'auto_install': True,
  'bootstrap': True, # load early for login screen

  'data': [
    'static/src/xml/base.xml',
    'views/mmh_theme.xml',
  ],
  
  'qweb': [
    'static/src/xml/base.xml',
  ],
}