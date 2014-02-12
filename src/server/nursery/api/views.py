from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import yaml
from sqlite_wrapper import RepoWrapper, DeployWrapper
from api import DeploymentStatus, DeploymentType


def index(request):
    return HttpResponse("Nursery Server")

@csrf_exempt
def init(request, repo):
    conf = request.POST.get("conf", "")
    print(conf)
    if not conf:
        json_reply = { "status" : "error", "repo": repo, "msg": "Configuration yaml is missing"}
        return HttpResponse(json.dumps(json_reply), content_type = 'application/json')
    
    data = yaml.load(conf)
    branch = data['branch']['name']
    if not RepoWrapper.get_repo(url = repo, branch = branch):
        RepoWrapper.create_new_repo(url = repo, branch = branch)
        json_reply = { "status" : "ok", "repo": repo, "branch": branch}
    else:
        json_reply = { "status" : "error", "repo": repo, "branch": branch, 
                      "msg" : "This repo/branch has already been initialized"}
    return HttpResponse(json.dumps(json_reply), content_type = 'application/json')

@csrf_exempt
def deploy(request, repo):
    # launch a new deploy command in async if all well
    # get the affected folders
    # get the affected instances
    # run for each event the scripts
    # anounce deploy has ended
    hash = request.POST.get("hash", "")
    branch = request.POST.get("branch", "")
    if not hash or not branch:
        json_reply = { "status": "error",
                      "repo": repo,
                      "branch": branch,
                      "hash": hash,
                      "msg": "something is missing"}
        return HttpResponse(json.dumps(json_reply), content_type = 'application/json')
    
    msg = "deployment scheduled - good luck"
    status = "ok"
    # look if the deployment is possible
    db_repo = RepoWrapper.get_repo(url = repo, branch = branch)
    if not db_repo:
        # we should have a repo defined else we can't deploy
        msg = "Error: no repo was found on the server"
        status = "Error"
        json_reply = {"status" : status, "msg": msg}
        return HttpResponse(json.dumps(json_reply), content_type = 'application/json')
    
    ## we have found the repo config look for other ongoing deployments
    db_deployment = DeployWrapper.find_last_deployment(db_repo.id)
    if not db_deployment:# no deployment was ever made for this branch/repo
        DeployWrapper.create_new_deployment(repo = db_repo, hash = hash, type = DeploymentType.CLIENT)
    else:#we have past deployments
        if int(db_deployment.status) < DeploymentStatus.ENDED and not db_repo.allow_multiple_deploy:
            # we have an ongoing deployment and can't proceed
            json_reply = { "status": "error",
                      "repo": repo,
                      "branch": branch,
                      "hash": hash,
                      "msg": "another deployment is scheduled and multiple deploys are not allowed"}
            return HttpResponse(json.dumps(json_reply), content_type = 'application/json')
        
        elif int(db_deployment.status) != DeploymentStatus.ENDED:#last deployment was not completed fine                
            if int(db_deployment.status) > DeploymentStatus.ENDED :
                msg += " !WARNING: Last deployment ended with the status: %s \n" % (db_deployment.status )
            else:
                msg += " !WARNING: Another deployment is on, prev deployment status: %s \n" % (db_deployment.status )  
        # if we got this far a new deployment can be inserted to the db
        DeployWrapper.create_new_deployment(repo = db_repo, hash = hash, type = DeploymentType.CLIENT)                    
    
    json_reply = {"status" : status, "msg" : msg}
    return HttpResponse(json.dumps(json_reply), content_type = 'application/json')
           
@csrf_exempt   
def status(request, repo):
    from async.celery import create_deploy
    create_deploy.delay(None)
    return HttpResponse("Nursery Server status: %s " % (repo))

def rollback(request, repo, branch):
    hash = request.POST.get("hash", "")
    return HttpResponse("Nursery Server Rollback: %s %s %s " % (repo,branch, hash))

def modify(request, repo, branch):
    return HttpResponse("Nursery Server Modify: %s %s" % (repo,branch))

def audit(request, repo, branch):
    return HttpResponse("Nursery Server Audit: %s %s" % (repo,branch))