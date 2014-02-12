from models import Repo, Deployment
from datetime import datetime
from api import DeploymentStatus, DeploymentType

class RepoWrapper():
    @staticmethod
    def get_repo(url,branch):
        repo_set = Repo.objects.filter(url = url, branch = branch)
        if repo_set.exists():
            return repo_set[0]
        else:
            return False
        
    @staticmethod
    def get_repo(id):
        repo = Repo.objects.get(id = id)
        if repo.exists():
            return repo
        else:
            return False
    
    @staticmethod    
    def create_new_repo(url,branch):
        repo = Repo(url = url, branch = branch)
        repo.save()
        return repo
    
class DeployWrapper():
    @staticmethod
    def create_new_deployment(repo, hash, type):
        #create a new deployment and an async task to parse it
        deployment = Deployment(repo = repo, 
                                hash = hash, 
                                type = type,
                                status = DeploymentStatus.SCHEDULED)
        #save this deployment
        deployment.save()
        
        #the async task will mark this deployment as STARTED
        from async.celery import process_deploy
        process_deploy.delay(deployment)
        
        
    @staticmethod
    def find_last_deployment(repo_id):
        deployments = Deployment.objects.filter(repo = repo_id)      
        if deployments.exists():
            return deployments.latest(field_name = "deployment_date")
        else:
            return False
        
    @staticmethod
    def get_previous_finised_deployment_with(repo_id):
        deployments = Deployment.objects.filter(repo = repo_id, status = DeploymentStatus.ENDED)
        if deployments.exists():
            return deployments.latest(field_name = "deployment_date")
        else:
            return False
    
    @staticmethod
    def get_deployment(id):
        deployment = Deployment.objects.get(id = id)      
        if deployment.exists():
            return deployment
        else:
            return False


