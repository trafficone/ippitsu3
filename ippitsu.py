#!/usr/bin/env python
#
# 2009 Jason Schlesinger
#  GPL'd
# Inspired by Axel's Ippitsu
#
import cgi
import time
import os
import json
from datetime import datetime,tzinfo
from google.appengine.dist import use_library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django','1.2')

import wsgiref.handlers
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext import webapp

# STORE ALL INPUTS IN THESE
class Message(db.Model):
  #author = db.StringProperty()
  content = db.TextProperty()
  date = db.DateTimeProperty(auto_now_add=True)


class MainPage(webapp.RequestHandler):
  def get(self):
    try:
      message = db.GqlQuery("SELECT * "
                            "FROM Message "
                            "ORDER BY date DESC LIMIT 1")
      mesg_result = cgi.escape(message[0].content)
      mesg_date = message[0].date
    except IndexError:
      #fail safe if there is nothing in the database
      mesg_result = ""
      mesg_date = "Never Written"
    template_values = { 
    'content': mesg_result,
    'now': str(datetime.today()),
    'last_write':  str(mesg_date)}
    if 'json=true' in self.request.query_string :
      self.response.out.write(json.dumps(template_values))
    elif (['HTTP_X_REQUESTED_WITH'] not in self.request.headers.keys() or 
        (['HTTP_X_REQUESTED_WITH'] in self.request.headers.keys() and 
         self.request.headers['HTTP_X_REQUESTED_WITH'] != 'XMLHttpRequest')):
      template_values['not_ajax']=  "\
        <link type=\"text/css\" href=\"/css/smoothness/jquery-ui-1.8.12.custom.css\" rel=\"Stylesheet\" />\
        <link type=\"text/css\" href=\"/css/style.css\" rel=\"Stylesheet\" />\
        <!-- Okay, so I'm loading libraries from other sites, but I'm not double-paying Google for bandwidth of stuff they're hosting for free. -->\
        <script type=\"text/javascript\" src=\"https://ajax.googleapis.com/ajax/libs/jquery/1.5.1/jquery.min.js\"></script>\
        <script type=\"text/javascript\" src=\"https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.12/jquery-ui.min.js\"></script>\
        <!-- This, I can explain - I'm lazy. -->\
        <script type=\"text/javascript\" src=\"http://cdn.jquerytools.org/1.2.5/tiny/jquery.tools.min.js\"></script>"
      path = os.path.join(os.path.dirname(__file__), 'templates/ippitsu2.html')
      self.response.out.write(template.render(path, template_values))
  def post(self):
    message = Message()
    message.content = self.request.get('new_contents')
    message.put()
    try:
      message = db.GqlQuery("SELECT * "
                            "FROM Message "
                            "ORDER BY date DESC LIMIT 1")
      mesg_result = cgi.escape(message[0].content)
      mesg_date = message[0].date
    except IndexError:
      #fail safe if there is nothing in the database
      mesg_result = ""
      mesg_date = "Never Written"
    template_values = { 
    'content': mesg_result,
    'now': str(datetime.today()),
    'last_write':  str(mesg_date)}
    self.response.out.write(json.dumps(template_values))
    #self.redirect('/ippitsu2')

application = webapp.WSGIApplication([
  ('/ippitsu2', MainPage),
], debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
