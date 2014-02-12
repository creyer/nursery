from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings
from api.helpers.git import Git
from api import DeploymentStatus

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nursery.settings')

app = Celery('async')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task(bind=True)
def _list_files_in_deploy(self, deployment_id , run = 1):
    """ 
    This async is taking care of getting the file list affected by this deployment
    The files could be already specified by a git hook or it could be searched for
    This method handles deployments with hashes only
    """
    status = 1
    deployment = DeployWrapper.get_deployment(deployment_id)
    #set another status so we know
    deployment.status = DeploymentStatus.STARTED + status
    deployment.save()
    repo = RepoWrapper.get_repo(deployment.repo_id)
    last_deployment_ended = DeployWrapper.get_previous_finised_deployment_with(deployment.repo_id)
    git_url = repo.url
    branch = repo.branch
    old_hash = last_deployment_ended.deployed_hash
    new_hash = deployment.hash
    files = Git.get_affected_files(git_url, branch, old_hash, new_hash)
    #write the changed files to our current deployment
    deployment.files = files
    deployment.save()
    #go to next step
    _get_affected_instances.delay(deployment_id)
    
@app.task(bind=True)
def _get_affected_instances(self, deployment_id , run = 1):
    status = 5
    deployment = DeployWrapper.get_deployment(deployment_id)
    deployment.status = DeploymentStatus.STARTED + status
    deployment.save()
    instances = Instances.get_affected_instances_from_deployment(deployment_id)
    # the synchronisation will be done inside the Instances methods
    # when we return all instances will have been executed the pre deploy
    Instances.send_pre_deploy_event_to(instances)
    _deploy_instances.delay(deployment_id, instances)
    
    # insatnce = Instances.get_ffectedInstances_from_files(files)
    # send predeploy event
    # deploy on instances
    # send after deploy event
@app.task(bind=True)
def _deploy_instances(self, deployment_id , instances):
    status = 10 
    deployment = DeployWrapper.get_deployment(deployment_id)
    deployment.status = DeploymentStatus.STARTED + status
    deployment.save()
    Git.deploy_on_instances(instances)
    #incerase the status for we have deployed
    status = 15
    deployment = DeployWrapper.get_deployment(deployment_id)
    deployment.status = DeploymentStatus.STARTED + status
    deployment.save()
    # send hook to instances
    # the synchronisation will be done inside the Instances methods
    # when we return all instances will have been executed the post deploy
    Instances.send_post_deploy_event_to(instances)
    #if everything wen well untill now just have 1 more step 
    _deploy_end.delay(deployment_id)

@app.task(bind=True)
def _deploy_end(deployment_id):
    deployment = DeployWrapper.get_deployment(deployment_id)
    deployment.status = DeploymentStatus.ENDED
    deployment.save()
    #TODO: anounce happy users
    
@app.task(bind=True)
def process_deploy(self, deployment , run = 1):
    print ("run %d %s" % (run, deployment))
    #check if previous deployment has ended, then we can proceed else reschedule
    db_deployment = DeployWrapper.find_last_deployment(deployment.repo_id)
    start = True
    if not db_deployment:# no deployment was ever made for this branch/repo
        print "start new deployment id: %s" %  deployment.id
    else:#we have past deployments
        if int(db_deployment.status) < DeploymentStatus.ENDED:
            start = False
    if start:        
        """ !!! MAGIC starts here!!! """
        #set this deployment as started
        db_deployment.status = DeploymentStatus.STARTED
        db_deployment.save()
        # each async step will lead to another async step
        _list_files_in_deploy.delay(db_deployment.id)
        #sendit to another async procesing
        #get the list of files affected by the deployment
        #establish where we should deploy
        #run eventualy pre deploy scripts
        #run deployment
        #run after deployment scripts
        #anounce hapy users        
    else:       
            # previuos deployment is still on
            # new deployment can't start            
            if run < 5:
                # reschdule in 3 minutes
                from datetime import datetime, timedelta
                run_again = datetime.utcnow() + timedelta(minutes = 3)
                process_deploy.apply_async((deployment, run + 1), eta = run_again)
            else:
                #already have tried enugh, something is not good, mark this deployment as failed        
                deployment.status = DeploymentStatus.FAILED
                deployment.save()
                print ("marked deployment as failed")
  
  
@app.task(bind=True)
def create_deploy_old(self, deployment):
    deployment.status = DeploymentStatus.STARTED    
    try:
        Git.deploy_hash_on_instance (
             'https://github.com/creyer/fps-automated-test.git', 
             'master',
             '396a84fb159b3aa3cd69eadee6cb126cbaca2d01',
             '8fda26d934495e9cff61147d080d80f821830d3f',
             { 'host':'127.0.0.1',
              'user':'vagrant',
              'port':2222, 
              'pem': '/home/creyer/.vagrant.d/insecure_private_key',
              'location':'/tmp/test'
              }
             )
        #write to db, this step ocured fine
        return True
    except:
        print "Error ocured"
        #write to db this deploy has failed
        return False