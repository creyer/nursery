from django.db import models

class Repo(models.Model):
    url = models.CharField(max_length=200)
    branch = models.CharField(max_length=100)
    allow_multiple_deploy = models.BooleanField(default = False)
    added_date = models.DateTimeField(auto_now_add = True)
    

class Scripts(models.Model):
    name = models.CharField(max_length=100)
    repo = models.ForeignKey(Repo)
    url = models.CharField(max_length=50) 
    # the allowed events are hardcoded for now
    # pre - before any instance is touced            
    # start - before any files have been copyied on the instance in a new hash location
    # updated - files have been copied but the old version is still in place
    # end - the new version is in
    # deployed - all instances have been updated
    event = models.CharField(max_length=50)
     
     
class Instances(models.Model):
    meta_name = models.CharField(max_length=100)
    restart = models.CharField(max_length=200) 
    models.ManyToManyField(Scripts)
    
    
class Folders(models.Model):
    path = models.CharField(max_length=200)
    models.ManyToManyField(Scripts)
    
    
class Deployment(models.Model):
    repo = models.ForeignKey(Repo)
    deployment_date = models.DateTimeField(auto_now_add = True)
    status = models.IntegerField()
    # a deployment could be iniated by git, client, forced (when another repo is used)
    type = models.CharField(max_length=100)
    hash = models.CharField(max_length=100)
    files = models.CharField(max_length=1000)
       