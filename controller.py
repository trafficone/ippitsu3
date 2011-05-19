import os
from google.appengine.dist import use_library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django','1.2')

import simplejson as json,datetime,models,datetime
from google.appengine.api import users
from google.appengine.ext.webapp import template

#These classes & methods should handle the basic functions of model interaction 
#  Data should be passed in through initial arguments and passed out through 
#  the return value or raise and exception

def authcheck(project_id):
  if type(project_id)==int and models.Project.get_by_id(project_id).owner != users.get_current_user():
    raise Exception('notauth')
  elif type(project_id)==str and models.Project.get(project_id).owner != users.get_current_user():
    raise Exception('notauth')

class static():
  @staticmethod
  def get(page):
    if page in ["/index.html","/index.php","/index.asp","/index.htm","home","/",""]:
      dictio = dict()
      dictio["user"]=users.get_current_user()
      path = os.path.join(os.path.dirname(__file__),'templates/static/index.html')
      #TODO: prettify this with latest projects/actions
      return template.render(path, dictio)
    elif page in ["settings","settings.html","settings.php"]:
      dictio = dict()
      dictio["user"]=users.get_current_user()
      path = os.path.join(os.path.dirname(__file__),'templates/static/settings.html')
      return template.render(path, dictio)
    elif page in ["about.php","about.html","about-us.html"]:
      dictio = dict()
      dictio["user"]=users.get_current_user()
      path = os.path.join(os.path.dirname(__file__),'templates/static/about.html')
      return template.render(path, dictio)
    elif page in ["faq.php","faq.html","faq.htm"]:
      path = os.path.join(os.path.dirname(__file__),'templates/static/faq.html')
      return template.render(path, {})
    else:
      raise Exception('notfound')

class project(): 
  #load a specific project (optionally with status)
  @staticmethod
  def form(options=None):
    dictio=dict()
    if 'get_with' in options.keys(): get_with = options['get_with']  
    if 'id' in options.keys(): 
      id = options['id'].split('_')[1]
      authcheck(id)
      proj = models.Project.get(id);
      if proj == None: raise Exception('notfound')
      dictio["project"] = proj.to_dict()
      dictio["project"]["start_date"] = "%s/%s/%s"%(proj.start_date.year,proj.start_date.month,proj.start_date.day)
      dictio["project"]["deadline"] = "%s/%s/%s"%(proj.deadline.year,proj.deadline.month,proj.deadline.day)
    dictio["statuses"] = []
    for status in models.Status.all():
        stat = status.to_dict()
        dictio["statuses"].append({"name":stat["name"],"description":stat["description"],"id":stat["id"]})
    path = os.path.join(os.path.dirname(__file__),'templates/project_form.html') 
    return template.render(path,dictio)#json.dumps(pdict)

  #produce a list of all projects for a user and render the list_view page
  @staticmethod
  def list_view(options=None):
    if options and 'filter_by' in options.keys():filter_by=options['filter_by']
    if options and 'sort_by' in options.keys:sort_by=options['sort_by']
    path = os.path.join(os.path.dirname(__file__),'templates/project_list.html')
    projs = models.Project.all(keys_only=True).filter("owner =",users.get_current_user())
    projs_list = []
    for proj in projs:
      projct = models.Project.get(proj)
      proj_dict = projct.to_dict()
      proj_dict["status"] = proj_dict["status"].name 
      proj_dict["budget_left"] = proj_dict["budget"] - reduce(lambda x,y:x+y.amount,models.Expense.all().filter("project =",proj),0) 
      projs_list.append(proj_dict)
    dictio = {"projects":projs_list}
    return template.render(path, dictio)
  
  #produce a summary of a given project
  @staticmethod
  def summary(options):
    id = options['id'].split('_')[1]
    path = os.path.join(os.path.dirname(__file__),'templates/project_overview.html')
    proj = models.Project.get(id);
    steps = models.Step.all().filter("project =",proj.key()).filter("status.name IN",["In Progress","Queued"]).order("deadline").fetch(10)
    blocks = models.Block.all().filter("project =",proj.key()).filter("status.name IN",["In Progress","Queued","Thought","Hiatus","Blocked"]).order("-fix_cost").fetch(10)
    expenses = models.Expense.all(keys_only=True).filter("project =",proj.key()).order("date").fetch(10)
    total_expenses = reduce(lambda x,y: x+y.amount,models.Expense.all(keys_only=True).filter("project =",proj.key()),0)
    summ = dict()
    summ["project"]=proj.to_dict()
    summ["steps"] = map(models.Step.to_dict,steps)
    summ["blocks"] = map(models.Block.to_dict,blocks)
    summ["expenses"] = map(models.Expense.to_dict,expenses)
    summ["project"]["budget_left"] = summ["project"]["budget"] - total_expenses
    return template.render(path,summ)

  #update the column with the given value
  @staticmethod
  def update(options):
    id = options['id']
    authcheck(id)
    proj_model = models.Project.get(id)
    options["owner"]=proj_model.owner
    try:
      proj = models.Project.from_dict(options,proj_model)
      proj.put()
    except:
      return "an ERROR"
    #TODO: Find the cause of this error
 
  #add a record to the project table
  @staticmethod
  def add(options):
    #project is an JSON encoded project
    proj = options
    proj["owner"] = users.get_current_user()
    try:
      newproj = models.Project.from_dict(proj)
      newproj.put()
    except Exception, e:
      #TODO: Implement AJAX validation loop here
      return "ERROR: "+e.args[0]
  
  #delete a record from the project table
  @staticmethod
  def delete(options):
    id = options['id']
    proj=models.Project.get_by_id(id)
    if proj == None: raise Exception('notfound')
    authcheck(id)
    proj.delete()

class step():
  #load a specific
  @staticmethod 
  def form(options=None):
    path = os.path.join(os.path.dirname(__file__),'templates/step_form.html')
    retval = dict()
    retval["projects"] = []
    projects = models.Project.all().filter("owner = ",users.get_current_user())
    for proj in projects: 
      retval["projects"].append({"name":proj.name,"description":proj.description,"id":proj.key()})
    retval["statuses"] = []
    for status in models.Status.all():
        retval["statuses"].append({"name":status.name,"description":status.description,"id":status.key()})
    if 'id' in options.keys():
      id = options['id']
      step = models.Step.get(id);
      retval["step"] = step.to_dict()
    return template.render(path,retval) 

  #list all steps in a given project
  @staticmethod
  def list_view(options):
    project = options['project']
    path = os.path.join(os.path.dirname(__file__),'templates/steps.html')
    proj = models.Project.get(project)
    authcheck(proj)
    steps = model.Step.all(keys_only=True).filter("project =",project)
    step_list = map(models.Step.to_dict,steps)
    dictio = {"steps":steps}
    return template.render(path, dictio)
  
  @staticmethod
  def update(options):
    id = options['id']
    step = models.Step.get(id)
    if step == None: raise Exception('notfound')
    authcheck(step.project.key())
    new_step = models.Step.from_dict(options,step)
    new_step.put()
    
  @staticmethod
  def add(options):
    stp = options['stp']
    authcheck(step["project"])
    newstep = models.Step.from_dict(options)
    newstep.put()
    
  @staticmethod
  def delete(options):
    id = options['id']
    step = models.Step.get_by_id(id)
    if step == None: raise Exception('notfound')
    authcheck(step.project)
    step.delete()


#TODO: Block and budget classes
class block():
  @staticmethod
  def add(options):
    blok = options['blok']
    block = json.loads(blok)
    block["owner"]=users.get_current_user()
    newblock = models.Block()
    for key in block.keys():
        eval("newblock.%s = %s"%(key,block[key]))
    newblock.put()
    
  @staticmethod
  def update(options):
    id = options['id']
    col = options['col']
    value = options['value']
    block = models.Block.get_by_id(id)
    if block == None: raise Exception('notfound')
    authcheck(block.project)
    eval("block.%s = %s"%(col,value))
    block.put()
    
  @staticmethod
  def delete(options):
    id = options['id']
    block = models.Block.get_by_id(id)
    if block == None: raise Exception('notfound')
    authcheck(block.project)
    block.delete()
    
  @staticmethod
  def list_view(options):
    project = options['project']
    path = os.path.join(os.path.dirname(__file__),'templates/blocks.html')
    proj = models.Project.get_by_id(project)
    authcheck(project)
    blocks = model.Block.all(keys_only=True).filter("project =",project)
    block_list = map(to_dict,blocks)
    dictio = {"blocks":block_list}
    return template.render(path, dictio)

class budget():
  @staticmethod
  def add(options):
    expnse = options['expnse']
    expense = json.loads(expnse)
    expense["owner"]=users.get_current_user()
    newexpense = models.Expense()
    for key in expense.keys():
        eval("newexpense.%s = %s"%(key,expense[key]))
    newexpense.put()

  @staticmethod
  def update(options):
    id = options['id']
    col = options['col']
    value = options['value']
    expense = models.Expense.get_by_id(id)
    if expense == None: raise Exception('notfound')
    authcheck(expense.project)
    eval("expense.%s = %s"%(col,value))
    expense.put()
  @staticmethod
  def delete(options):
    id = options['id']
    expense = models.Expense.get_by_id(id)
    if expense == None: raise Exception('notfound')
    authcheck(expense.project)
    expense.delete()
  @staticmethod
  def list_view(options):
    project = options['project']
    path = os.path.join(os.path.dirname(__file__),'templates/expenses.html')
    proj = models.Project.get_by_id(project)
    authcheck(project)
    expenses = model.Expense.all(keys_only=True).filter("project =",project)
    expense_list = map(to_dict,expenses)
    dictio = {"expenses":expense_list,"tables":model.TABLES}
    return template.render(path, dictio)
