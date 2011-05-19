#figure out which page to send to the user
#handle 404, 401, and 500 errors
#import all of the controllers
#then choose which method to implement based on the URL requested
#surround the whole thing in a try/except, and return a 500 if an exception is thrown
#also, log the exception details, URL requested, cookeies, user, etc. if there's an error

import os
from google.appengine.dist import use_library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django','1.2')


import traceback
import logging
import controller
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

not_ajax =  "\
        <link type=\"text/css\" href=\"/css/smoothness/jquery-ui-1.8.12.custom.css\" rel=\"Stylesheet\" />\n\
        <link type=\"text/css\" href=\"/css/style.css\" rel=\"Stylesheet\" />\n\
        <link type=\"text/css\" href=\"/css/datatable.css\" rel=\"Stylesheet\" />\n\
        <!-- Okay, so I'm loading libraries from other sites, but I'm not double-paying Google for bandwidth of stuff they're hosting for free. -->\n\
        <script type=\"text/javascript\" src=\"https://ajax.googleapis.com/ajax/libs/jquery/1.5.1/jquery.min.js\"></script>\n\
        <script type=\"text/javascript\" src=\"https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.12/jquery-ui.min.js\"></script>\n\
        <!-- This, I can explain - I'm lazy. -->\n\
        <script type=\"text/javascript\" src=\"http://cdn.jquerytools.org/1.2.5/tiny/jquery.tools.min.js\"></script>\n\
        <script type=\"text/javascript\" src=\"/js/jquery.dataTables-1.6.min.js\"></script>\n"

hpath = os.path.join(os.path.dirname(__file__),'templates/header.html')

class MainHandler(webapp.RequestHandler):
  def get(self):
    #@todo: figure out the page title, surf options and username and pass them to the template
    user = users.get_current_user()
    request = self.request.path[1:].split('/')
    if request[0] == "login.php":
      request[0]="/index.php"
    
    title = dict()
    title["primary"] = request[0]
    menu = ["home","ippitsu2"]
    if not user:
      #user not logged in
      menu.extend(["login","register"])
    else:
      menu.extend(["projects","settings"])
      title["user"] = user
      title["logout"] = users.create_logout_url("/")
      fullquery =  self.request.query_string.split('&')
      args = dict()
      if '=' in fullquery[0]: 
        for query in fullquery:
          quer = query.split('=')
          args[quer[0]]=quer[1]
    try:
      #ippitsu2.appspot.com/controller/method/tracker.php?value1=a&value2=b...
      if(len(request)>1):
        title["secondary"] = request[1]
        resp = eval("controller.%s.%s(%s)"%(request[0],request[1],args))
      else:
        title["primary"] = "home"
        resp = controller.static.get(request[0])
    except Exception, err:
      e = err.args[0]
      if e == "notfound": 
        path =  os.path.join(os.path.dirname(__file__),'404.html')
        self.response.set_status(404)
        self.response.out.write(template.render(path, {"url":self.request.url}))
      elif e == "notauth":
        path = os.path.join(os.path.dirname(__file__),'401.html')
        self.response.set_status(401)
        self.response.out.write(template.render(path,{"url":self.request.url}))
        logging.info("INFO: User "+user.get_current_user()+" tried to access unauthorized content.")
      else:
        raise Exception(traceback.format_exc())
    except:
      path = os.path.join(os.path.dirname(__file__),'500.html')
      self.response.set_status(500)
      self.response.out.write(template.render(path,{"url":self.request.url}))
      logging.error(traceback.format_exc())
    else:
      #make everything partial loadable!
      if ('X-Requested-With' in self.request.headers.keys() and self.request.headers['X-Requested-With'] == 'XMLHttpRequest')\
        or 'ajax' in self.request.arguments():
        #is_ajax 
        self.response.out.write(resp)
      else:
        #not is_ajax
        self.response.out.write(template.render(hpath,{"content":resp,"title":title,"menu":menu,"not_ajax":not_ajax}))
      
  def post(self):
    try:
      request = self.request.path[1:].split('/')
      args = dict()
      for arg in self.request.arguments(): args[arg]=self.request.get(arg)
      #ippitsu2.appspot.com/controller/method/tracker.php
      resp = eval("controller.%s.%s"%(request[0],request[1],))(args)
    except Exception, err:
      e = err.args[0]
      if e == "notfound": 
        path =  os.path.join(os.path.dirname(__file__),'404.html')
        self.response.set_status(404)
        self.response.out.write(template.render(path, {"url":self.request.url}))
      elif e == "notauth":
        path = os.path.join(os.path.dirname(__file__),'401.html')
        self.response.set_status(401)
        self.response.out.write(template.render(path,{"url":self.request.url}))
        logging.info("INFO: User "+user.get_current_user()+" tried to access unauthorized content.")
      else:
        raise Exception(traceback.format_exc())
    except:
      path = os.path.join(os.path.dirname(__file__),'500.html')
      self.response.set_status(500)
      self.response.out.write(template.render(path,{"url":self.request.url}))
      logging.error(traceback.format_exc())
    else:
      if 'X-Requested-With' in self.request.headers.keys() and self.request.headers['X-Requested-With'] == 'XMLHttpRequest':
        #is_ajax 
        self.response.out.write(resp)
      else:
        #not is_ajax
        self.response.out.write(template.render(hpath,{"content":resp,"not_ajax":not_ajax}))

    
application = webapp.WSGIApplication([
  ('/.*', MainHandler),
], debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
