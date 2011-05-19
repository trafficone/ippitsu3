import os
import traceback
import logging
import controller
import models
from google.appengine.dist import use_library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django','1.2')

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

class MainHandler(webapp.RequestHandler):
  def get(self):
    path = os.path.join(os.path.dirname(__file__),self.request.path[1:])
    self.response.out.write(template.render(path,{})) #currently only directly renders HTML pages

  def post(self):
    if(self.request.path=="/admin/status/add"):
      newstat = models.Status(name=self.request.get('name'),description=self.request.get('description'))
      newstat.put()
    self.redirect("/".join(self.request.path.split("/")[0:1]))
     

application = webapp.WSGIApplication([
  ('/admin/.*', MainHandler),
], debug=True)

def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()