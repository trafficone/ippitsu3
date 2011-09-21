from datetime import date
from google.appengine.ext import db

def str_to_date(stri):
  dat = map(int,stri.split("/"))
  return date(dat[0],dat[1],dat[2])

class Status(db.Model):
  name = db.StringProperty(required=True) #notnull
  description = db.StringProperty()
  def to_dict(self):
    return {
      "id":self.key(),
      "name":self.name,
      "description":self.description
    }

#TODO: add an array of collab users
class Project(db.Model):
  name = db.StringProperty(required=True) #notnull
  status = db.ReferenceProperty(Status,required=True) #notnull
  description = db.StringProperty(required=True)
  start_date = db.DateProperty(required=True) #notnull
  budget = db.IntegerProperty(required=True) #notnull #last two digits are cents
  created = db.DateProperty(default=date.today(),required=True)
  deadline = db.DateProperty() #notnull
  owner = db.UserProperty(required=True) #notnull
  def delete(self):
    for exp in Expense.all().filter("project =",self.key()):
      exp.delete()
    for stp in Step.all().filter("project =",self.key()):
      stp.delete()
    for blk in Block.all().filter("project =",self.key()):
      blk.delete()
  def to_dict(self):
    return {
      "id":self.key(),
      "name":self.name,
      "description":self.description,
      "status":self.status,
      "start_date":self.start_date,
      "budget":self.budget/100.0,
      "deadline":self.deadline}
  @staticmethod
  def from_dict(dictionary,project=None):
    if project==None:
      return Project(name = dictionary["name"],
        description=dictionary["description"],
        status=Status.get(dictionary["status"]),
        start_date=str_to_date(dictionary["start_date"]),
        budget=int(float(dictionary["budget"].replace("$",""))*100),
        deadline=str_to_date(dictionary["deadline"]),
        owner=dictionary["owner"])
    else:
      project.name = dictionary["name"]
      project.description=dictionary["description"]
      project.status=Status.get(dictionary["status"])
      project.start_date=str_to_date(dictionary["start_date"])
      project.budget=int(float(dictionary["budget"].replace("$",""))*100)
      project.deadline=str_to_date(dictionary["deadline"])
      return project
    
class Step(db.Model):
  name = db.StringProperty(required=True) #notnull
  description = db.StringProperty(required=True) #notnull
  project = db.ReferenceProperty(Project,required=True) #notnull
  status = db.ReferenceProperty(Status,required=True) #notnull
  created = db.DateProperty(default=date.today(),required=True) #notnull
  deadline = db.DateProperty(required=True) #notnull
  mission_critical = db.IntegerProperty(choices=set([0,1])) #0=false 1=true
  def delete(self):
    for blk in Block.all().filter("step =",self.key()):
      blk.step = None
      blk.put()
    for exp in Expense.all().filter("ftbl =",TABLES[2]).filter("fkey =",self.key()):
      exp.ftbl = None
      exp.fkey = None
      exp.put()
    super(Step,self).delete()
  def to_dict(self): return {"id":self.key(),
    "name":self.name,
    "description":self.description,
    "project":self.project,
    "status":self.status,
    "start_date":self.created,
    "deadline":self.deadline,
    "mission_critical":self.mission_critical}
  @staticmethod
  def from_dict(dictionary,step=None):
    if 'mission_critical' in dictionary.keys():
      dictionary["mission_critical"]=1
    else:
      dictionary["mission_critical"]=0
    if step == None:
      return Step(name=dictionary["name"],
        description=dictionary["description"],
        project=Project.get(dictionary["project"]),
        status=Status.get(dictionary["status"]),
        created=str_to_date(dictionary["start_date"]),
        deadline=str_to_date(dictionary["deadline"]),
        mission_critical=dictionary["mission_critical"])
    else:
      step.name=dictionary["name"]
      step.description=dictionary["description"]
      step.project=Project.get(dictionary["project"])
      step.status=Status.get(dictionary["status"])
      created=str_to_date(dictionary["start_date"])
      step.deadline=str_to_date(dictionary["deadline"])
      step.mission_critical=dictionary["mission_critical"]
      return step
class Block(db.Model):
  name = db.StringProperty(required=True) #notnull 
  description = db.StringProperty(required=True) #notnull
  status = db.ReferenceProperty(Status,required=True) #notnull
  project = db.ReferenceProperty(Project,required=True) #notnull
  step = db.ReferenceProperty(Step)
  discovery_date = db.DateProperty(default=date.today(),required=True) #notnull
  fix_cost = db.IntegerProperty(required=True) #notnull
  def delete(self):
    for exp in Expense.all().filter("ftbl =",TABLES[3]).filter("fkey =",self.key()):
      exp.ftbl = None
      exp.fkey = None
      exp.put()
    super(Block,self).delete()
  def to_dict(self): return {
    "id":self.key(),
    "name":self.name,
    "description":self.description,
    "status":self.status,
    "project":self.project,
    "step":self.step,
    "discovery_date":self.discovery_date,
    "fix_cost":self.fix_cost/100}
  @staticmethod
  def from_dict(dictionary,block=None):
    if "step" in dictionary.keys() and dictionary["step"]!="":
      stepspot=Step.get(dictionary["step"])
    else:
      stepspot=None
    if block == None:
      return Block(
        name=dictionary["name"],
        description=dictionary["description"],
        status=Status.get(dictionary["status"]),
        project=Project.get(dictionary["project"]),
        step=stepspot,
        discovery_date=str_to_date(dictionary["discovery_date"]),
        fix_cost=int(float(dictionary["fix_cost"].replace("$",""))*100))
    else:
      block.name=dictionary["name"]
      block.description=dictionary["description"]
      block.status=Status.get(dictionary["status"])
      block.project=Project.get(dictionary["project"])
      block.step=stepspot 
      block.discovery_date=str_to_date(dictionary["discovery_date"])
      block.fix_cost=int(float(dictionary["fix_cost"].replace("$",""))*100)
      return block
  
class Expense(db.Model):
  TABLES = {"Status":Status,"Project":Project,"Step":Step,"Block":Block}
  name = db.StringProperty(required=True) #notnull
  description = db.StringProperty(required=True) #notnull
  project = db.ReferenceProperty(Project,required=True) #notull
  pay_for = db.StringProperty(required=True) #notnull
  amount = db.IntegerProperty(required=True) #notnull
  date = db.DateProperty(default=date.today(),required=True) #notnull
  ftab = db.StringProperty(choices=set(TABLES.keys()))
  fkey = db.ReferenceProperty() #try to validate
  def to_dict(self): return {
    "id":self.key(),
    "name":self.name,
    "description":self.description,
    "project":self.project,
    "pay_for":self.pay_for,
    "amount":self.amount/100.0,
    "date":self.date,
    "ftab":self.ftab,
    "fkey":self.fkey}
  @staticmethod
  def from_dict(dictionary,expense=None):
    if not "ftab" in dictionary.keys() or dictionary["ftab"] == "None":dictionary["ftab"]=None
    if not "fkey" in dictionary.keys() or dictionary["fkey"] == "None":dictionary["fkey"]=None
    if dictionary["ftab"] != None and dictionary["fkey"] != None:
      dictionary["fkey"] = Expense.TABLES[dictionary["ftab"]].get(dictionary["fkey"])
    if expense == None:
      return Expense(
        name=dictionary["name"],
        description=dictionary["description"],
        project=Project.get(dictionary["project"]),
        pay_for=dictionary["pay_for"],
        amount=int(float(dictionary["amount"].replace("$",""))*100),
        date=str_to_date(dictionary["date"]),
        ftab=dictionary["ftab"],
        fkey=dictionary["fkey"])
    else:
      expense.name=dictionary["name"]
      expense.description=dictionary["description"]
      expense.project=Project.get(dictionary["project"])
      expense.pay_for=dictionary["pay_for"]
      expense.amount=int(float(dictionary["amount"].replace("$",""))*100)
      expense.date=str_to_date(dictionary["date"])
      expense.ftab=dictionary["ftab"]
      expense.fkey=dictionary["fkey"]
      return expense

#TODO: add a user table with user prefs       
