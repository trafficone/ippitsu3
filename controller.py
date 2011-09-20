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
  elif type(project_id)==models.Project and project_id.owner != users.get_current_user():
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
    elif page in ["contact.html"]:
      if users.get_current_user() != None:
        import recaptcha
        path = os.path.join(os.path.dirname(__file__),'templates/static/contact.html')
        return template.render(path,{'captcha':recaptcha.displayhtml(public_key='6Ld7IMgSAAAAAJNZJcIsENwlG7Qw8q3ICDu0h_dE',use_ssl=False,error=None)})
      else:
        path = os.path.join(os.path.dirname(__file__),'templates/static/nocontact.html')
        return template.render(path,{})
    elif page in ["legal.html"]:
      path = os.path.join(os.path.dirname(__file__),'templates/static/legal.html')
      return template.render(path,{})
    else:
      raise Exception('notfound')

class email():
  @staticmethod
  def send(options):
    from os import environ
    import recaptcha
    challenge = options['recaptcha_challenge_field']
    response = options['recaptcha_response_field']
    remoteip = environ['REMOTE_ADDR']
    f = open('captcha.key','r')
    cResponse = recaptcha.submit(challenge,response,f.read(),remoteip)
    if cResponse.is_valid and users.get_current_user() != None:
      #send email
      from google.appengine.api import mail
      mail.send_mail(sender=str(users.get_current_user().email()),
          to="Jason Ippitsu3 <trafficone+i3@gmail.com>",
          subject="[IPPITSU3] "+options['subject'],
          body=options['body'])
      return "Success"
    else:
      return "You failed the Turing test"

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
      dictio["project"]["start_date"] = "%d/%d/%d"%(proj.start_date.year,proj.start_date.month,proj.start_date.day)
      dictio["project"]["deadline"] = "%d/%d/%d"%(proj.deadline.year,proj.deadline.month,proj.deadline.day)
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
      budget_left = proj_dict["budget"] - reduce(lambda x,y:x+y.amount/100.0,models.Expense.all().filter("project =",proj),0)
      proj_dict["budget_left"] = "$%.2f"%(budget_left)
      proj_dict["budget"] = "$%.2f"%(proj_dict["budget"])
      projs_list.append(proj_dict)
    dictio = {"projects":projs_list}
    return template.render(path, dictio)
  
  #produce a summary of a given project
  @staticmethod
  def summary(options):
    id = options['id'].split('_')[1]
    path = os.path.join(os.path.dirname(__file__),'templates/project_overview.html')
    proj = models.Project.get(id);
    steps = models.Step.all().filter("project =",proj).filter("status IN",models.Status.all().filter('name = ',"In Progress").fetch(1)).order("deadline").fetch(10)
    blocks = models.Block.all().filter("project =",proj).filter("status IN",models.Status.all().filter('name IN',["In Progress","Queued","Thought","Hiatus","Blocked"]).fetch(5)).fetch(10)
    expenses = models.Expense.all().filter("project =",proj).fetch(10)
    total_expenses = reduce(lambda x,y: x+y.amount/100.0,models.Expense.all().filter("project =",proj.key()),0)
    summ = dict()
    summ["project"]=proj.to_dict()
    summ["steps"] = map(models.Step.to_dict,steps)
    summ["blocks"] = map(models.Block.to_dict,blocks)
    summ["expenses"] = map(models.Expense.to_dict,expenses)
    summ["project"]["budget_left"] = "$%.2f"%(summ["project"]["budget"] - total_expenses)
    summ["project"]["budget"]="$%.2f"%(summ["project"]["budget"])
    summ["project"]["id"]=id
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
  #load a specific step for editing
  @staticmethod 
  def form(options):
    path = os.path.join(os.path.dirname(__file__),'templates/step_form.html')
    retval = dict()
    #retval["projects"] = []
    #projects = models.Project.all().filter("owner = ",users.get_current_user())
    #for proj in projects: 
    #  retval["projects"].append({"name":proj.name,"description":proj.description,"id":proj.key()})
    retval["statuses"] = []
    for status in models.Status.all():
        retval["statuses"].append({"name":status.name,"description":status.description,"id":status.key()})
    if 'id' in options.keys():
      id = options['id'].split('_')[1]
      step = models.Step.get(id);
      retval["step"] = step.to_dict()
      retval["step"]["project"] = retval["step"]["project"].to_dict() 
      retval["step"]["start_date"] = "%d/%d/%d"%(retval["step"]["start_date"].year, retval["step"]["start_date"].month, retval["step"]["start_date"].day)
      retval["step"]["deadline"] = "%d/%d/%d"%(retval["step"]["deadline"].year,retval["step"]["deadline"].month,retval["step"]["deadline"].day)
    elif 'project' in options.keys():
      project = options['project'].split('_')[1]
      authcheck(project)
      proj=models.Project.get(project)
      retval["step"]={"project":proj.to_dict()}
    return template.render(path,retval) 

  #list all steps in a given project
  @staticmethod
  def list_view(options):
    project = options['project'].split('_')[1]
    path = os.path.join(os.path.dirname(__file__),'templates/step_list.html')
    proj = models.Project.get(project)
    authcheck(proj)
    steps = models.Step.all().filter("project =",proj)
    #step_list = map(models.Step.to_dict,steps)
    step_list = []
    for step in steps:
      stepadd = step.to_dict();
      stepadd['status'] = stepadd['status'].name
      stepadd['project']= stepadd['project'].name
      step_list.append(stepadd)
    dictio = {"steps":step_list,"project":proj.to_dict()}
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
    step = options
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
  
  @staticmethod
  def json_list(options):
    project = options["id"].split('_')[1]
    authcheck(project)
    proj = models.Project.get(project)
    steps = dict()
    for step in models.Step.all().filter("project = ",proj):
      steps[str(step.key())]=step.name
    return json.dumps(steps)

#TODO: Block and budget classes
class block():
  #load a specific block for editing
  #TODO: Speed this up!!!
  @staticmethod 
  def form(options):
    path = os.path.join(os.path.dirname(__file__),'templates/block_form.html')
    retval = dict()
    retval["steps"]=[]
    retval["statuses"]=[]
    for status in models.Status.all():
      retval["statuses"].append({"name":status.name,"description":status.description,"id":status.key()})
    if 'id' in options.keys():
      id = options['id'].split('_')[1]
      block = models.Block.get(id);
      retval["steps"]=map(models.Step.to_dict(),models.Step.all().filter("project =",block.project))
      retval["block"] = block.to_dict()
      retval["block"]["step"] = retval["block"]["step"].name if retval["block"]["step"]!=None else "None"
      retval["block"]["project"] = retval["block"]["project"].to_dict() 
      retval["block"]["discovery_date"] = "%d/%d/%d"%(retval["block"]["discovery_date"].year, retval["block"]["discovery_date"].month, retval["block"]["discovery_date"].day)
      retval["block"]["fix_cost"] = "$%.2f"%(retval["block"]["fix_cost"])
    elif "project" in options.keys():
      project=options["project"].split("_")[1]
      proj=models.Project.get(project)
      for step in models.Step.all().filter("project =",proj):
        retval["steps"].append(step.to_dict())
      retval["block"]={"project":proj.to_dict()}
    return template.render(path,retval) 
  
  @staticmethod
  def add(options):
    authcheck(options["project"])
    newblock = models.Block.from_dict(options)
    newblock.put()
    
  @staticmethod
  def update(options):
    id = options['id']
    block = models.Block.get(id)
    if block == None: raise Exception('notfound')
    authcheck(block.project)
    new_block = models.Block.from_dict(options,block)
    new_block.put()
  
  @staticmethod
  def delete(options):
    id = options['id']
    block = models.Block.get_by_id(id)
    if block == None: raise Exception('notfound')
    authcheck(block.project)
    block.delete()
    
  @staticmethod
  def list_view(options):
    project = options['project'].split('_')[1]
    path = os.path.join(os.path.dirname(__file__),'templates/block_list.html')
    proj = models.Project.get(project)
    authcheck(project)
    blocks = models.Block.all().filter("project =",proj)
    #block_list = map(models.Block.to_dict,blocks)
    block_list = []
    for block in blocks:
      blockadd = block.to_dict()
      blockadd["status"]=blockadd["status"].name
      if blockadd["step"]==None: 
        blockadd["step"]="None"
      else:
        blockadd["step"]=blockadd["step"].name
      blockadd["project"]=blockadd["project"].name
      blockadd["fix_cost"]="$%.2f"%(blockadd["fix_cost"])
      block_list.append(blockadd)
    dictio = {"blocks":block_list, "project":project}
    return template.render(path, dictio)
    
class budget():
  @staticmethod
  def form(options):
    path = os.path.join(os.path.dirname(__file__),'templates/expense_form.html')
    retval=dict()
    #populate project
    if 'project' in options.keys():
      project = options['project'].split('_')[1]
      proj = models.Project.get(project)
    elif 'id' in options.keys():
      expense = options['id'].split('_')[1]
      expen = models.Expense.get(expense).to_dict()
      proj = expen["project"]
      retval["expense"] = expen
      retval["expense"]["amount"] = "$%.2f"%expen["amount"]
      retval["expense"]["date"] = "%d/%d/%d"%(expen["date"].year,expen["date"].month,expen["date"].day)
      retval["expense"]["fkey"] = {"name":expen["fkey"].name,"value":str(expen["fkey"].key())}
      retval["expense"]["ftab"]
    authcheck(proj)
    retval["project"] = proj.to_dict()
    retval["fkey"] = dict()
    retval["fkey"]["None"] = [{"name":"None","value":"None"}]
    retval["fkey"]["Step"] = []
    for step in models.Step.all().filter("project =",proj):
      retval["fkey"]["Step"].append({"name":step.name,"value":str(step.key())})
    retval["fkey"]["Block"] = []
    for block in models.Block.all().filter("project =",proj):
      retval["fkey"]["Block"].append({"name":block.name,"value":str(block.key())})
    retval["alltheshit"] = json.dumps(retval["fkey"])
    retval["ftab"] =[
        {"table":"None","name":"Unspecified"},
        {"table":"Step","name":"Step Item"},
        {"table":"Block","name":"Block Item"}]
    return template.render(path,retval)

  @staticmethod
  def add(options):
    authcheck(options["project"])
    newexpense = models.Expense.from_dict(options)
    newexpense.put()

  @staticmethod
  def update(options):
    id = options['id']
    expense = models.Expense.get(id)
    if expense == None: raise Exception('notfound')
    authcheck(expense.project)
    expense.from_dict(options,expense)
    expense.put()

  @staticmethod
  def delete(options):
    id = options['id']
    expense = models.Expense.get(id)
    if expense == None: raise Exception('notfound')
    authcheck(expense.project)
    expense.delete()
    
  @staticmethod
  def list_view(options):
    project = options['project'].split('_')[1]
    path = os.path.join(os.path.dirname(__file__),'templates/expense_list.html')
    proj = models.Project.get(project)
    authcheck(project)
    expenses = models.Expense.all().filter("project =",proj)
    expense_list = map(models.Expense.to_dict,expenses)
    for expense in expense_list:
      expense["fkey"] = expense["fkey"].name
      expense["amount"] = "$%.2f"%expense["amount"]
    dictio = {"expenses":expense_list,"tables":models.Expense.TABLES}
    return template.render(path, dictio)

def request(classname,method,args):
  import types
  if classname in globals().keys() and type(globals()[classname])==types.ClassType:
    if method in dir(eval(classname)) and (type(eval(classname+"."+method))==types.MethodType or type(eval(classname+"."+method))==types.FunctionType):
      return eval(classname+"."+method)(args)
  raise Exception("Should be a 404 error")
