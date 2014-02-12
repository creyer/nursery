"""
    Collection of functions which will deal with the server instamces
    connect, deploy, run scripts
    All functions should be called from an async process
    an instance is a dictionary and has the folowing structure
    instance: {        
        ip: 'the ip of the instance 
             this could be obtained from some external service as the intances are grouped by meta names 
             Mandatory',
        user: 'the user name - Optional',
        key_file_path: 'file with the key for the server - Optional',
        port: 'port for the ssh connection with the instance - should be there',
        deployment_path:'the absolute url of where to copy the new deployment files
                         ex: if we specifie: /home/user/deploy
                         then under this folder we will have many folders each one corespoding to
                         each deployment id
                         we will copy from the last deployment localy in the new location and then 
                         modify the files that have changed
                        '
        scripts: [
            {
                id: 'the order in which the scripts will run on one instance is given by their id - Mandatory'
                name: "script name - Optiona",
                event: "on what event this script should run - [pre_deploy,post_deploy] Mandatory",
                deployments_paths: [
                    "list of paths for wich this script should run - this should be in a regex form",
                    "this list is mandatory"
                ],
                command: "absolute path from the login folder to the actual script which need to run - Mandatory"
            }
        ]          
    }
    Ex:
    i = [{"ip": "127.0.0.1","user": "vagrant","key_file_path": "~/.vagrant.d/insecure_private_key","port": "2222","scripts": [{"id": "1","name":"t1","event": "pre_deploy","deployments_paths": [".*"],"command": "~/t1.sh"},{"id": "2","name":"t2","event": "pre_deploy","deployments_paths": [".*"],"command": "~/t2.sh"}]}]
    from api.helpers.instances import Instances
    Instances.send_pre_deploy_event_to(i, ["c"])
"""

from fabric.api import env
from fabric.api import run, execute
from fabric.context_managers import settings
import re

class Instances():
    @staticmethod
    def deploy(deploy_id, instances, files):
        """just copy the files (old+new) to a new location on the instances"""
        # get the last folder from instance and copy it to the new location
        hosts = []
        for instance in instances:
            hosts.append(instance['ip'])
        with settings(parallel=True, hosts = hosts):
            # create new folder in deployment_path with name deploy_id
            TODO
            # copy in new location latest updated directory from machine
            TODO
            #
            
            #copy new files from here to the new folder
            TODO
    
    @staticmethod
    def send_pre_deploy_event_to(instances, files):
        Instances._send_event_to("pre_deploy", instances, files)
        
    @staticmethod
    def send_post_deploy_event_to(instances):
        Instances._send_event_to("post_deploy", instances, files)
        
        
    @staticmethod
    def _send_event_to(event_name, instances, files):
        hosts = []
        for instance in instances:
            hosts.append(instance['ip'])
        with settings(parallel=True, hosts = hosts):
            # the env variables are global so all instances need to accept the same login
            env.user = instance['user']
            env.key_filename = instance['key_file_path']
            env.port = instance['port']
            execute(Instances._send_event_to_instance, event_name, instance, files)
             
    
    @staticmethod
    def _send_event_to_instance(event_name, instance, files):
        """
        There is no event on the server, what we will
        do is to call the scripts which reply to this event
        name and which are affected by the deploy path
        """
        # we might have an issue here because env is a global variable        
        scripts_to_run = []
        scripts = instance['scripts'] 
        for script in scripts:
            if script['event'] == event_name:
                for path in script['deployments_paths']:
                    for file in files:
                        p = re.compile(path, re.IGNORECASE)
                        m = p.match(file)
                        if m:
                            scripts_to_run.append(script)
        # sort the scripts to run by their id so we have a specific order
        scripts_to_run.sort(key = lambda x: x['id'])
        # we can now run the scripts on this instance
        for script in scripts_to_run:
            print("Executing on %s:%s as %s command %s" % (env.host, env.port, env.user, script['command']))
            run(script['command'])
            
            
    @staticmethod
    def get_affected_instances_from_deployment(deployment_id):
        """ 
        Returns the list of all afected instances by a deploy,
        based on the regex patern that each instance has defined
        aplied to the modified files from the deployment
        """
        deployment = DeployWrapper.get_deployment(deployment_id)
        # list instances meta for this repo
        repo_metas = RepoWrapper.get_metas_for_repo(deployment.repo_id)
        # list all instances interested about this repo
        meta = {}
        for name in repo_metas:
            # get the array of instances for one meta key
            # in the wrapper we might have a logic to get the list
            # from an external service like Amazon
            instances_on_meta = InstancesWrapper.get_instances_on_meta(name)
            meta[name] = instances_on_meta
        files = deployment.files  
        # filter instances
        instances_with_meta = []
        for name in repo_metas:
            instances_with_meta[name] = [
                     instance for instance in meta[name] 
                     if Instances._instance_deployment_has_files(instance,files)
                 ]
        # each instance might have different scripts running on different folders  
        # we will not take care about this right now, as we just want the instances 
        # to be returned ASAP
        return instances_with_meta
    
    
    @staticmethod          
    def _instance_deployment_has_files(instance, files):
        """
        return if instance is affected by (has subscribed to) this files deployment
        each instance has scripts, and each script has deployments_paths
        """
        import re
        for scripts in instance.scripts:
            for script in scripts:
                for path in script.deployments_paths:
                    for file in files:
                        p = re.compile(path, re.IGNORECASE)
                        m = p.match(file)
                        if m:
                            return True
        return False
    
    
    
    