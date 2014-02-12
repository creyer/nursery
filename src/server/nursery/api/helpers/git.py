from tempfile import mkdtemp, mkstemp
from fabric.operations import local, put, run
from fabric.api import hide, lcd
from fabric.api import env
import datetime
from time import time
from fabric.context_managers import settings
import shutil

class Git():
    @staticmethod
    def get_repo_name(repo_url):
        # extract name of the repo from url
        start = repo_url.find("http")
        end = repo_url.find(".git")
        remote_git = repo_url[start:end]
        repo_name = remote_git[remote_git.rfind('/')+1:]
        return repo_name
    
    @staticmethod
    def get_affected_files(repo_url, branch, hash_new, hash_old):
        repo_name = Git.get_repo_name(repo_url)
        st = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d.%H-%M-%S')
        deploy_id = st + "_" + hash_new + "_" + hash_old
        tmp_dir = mkdtemp(deploy_id)
        s_files = ""
        with hide('commands'):
            with lcd(tmp_dir):
                c_clone = local('git clone %s' % repo_url, capture = False)
                with lcd("%s/%s" % (tmp_dir, repo_name)):
                    local('git checkout %s' % branch, capture = False)
                    local('git reset --hard %s' % hash_new, capture = False)
                    s_files = local('git diff --stat --name-only %s %s' % (hash_old, hash_new), capture = True)
        files = s_files.split("\n")
        shutil.rmtree(tmp_dir)
        return files
    
            
    @staticmethod
    def deploy_hash_on_instance_deprecated(repo_url, branch, hash_new, hash_old, instance_with_access):
        #TODO: establish were the files need to be written (simlink)
        """
        repo_url            - the url for the repo like https://github.com/creyer/fps-automated-test.git
        branch              - the name of the branch to deploy
        hash_new            - the git hash we would like to deploy
        hash_old            - the old value of the hash, that exists on the remote instance
                              at the moment this field is mandatory
        instance_with_access- a dictionary with the follosing fields for the insatnce to be deployed:
        *   host      - like 127.0.0.1
            [port]    - like 22
            [user]    - like root
            [pem]     - the url for the key to that instance (this is suposed to exist on this server)
        *   location  - where the new deployment should be done 
                        (! this is the up folder, in a next step, a simlink will be created pointing 
                        to the new deployment)  
            
        """
        # extract name of the repo from url
        repo_name = Git.get_repo_name(repo_url)
        
        st = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d.%H-%M-%S')
        deploy_id = st + "_" + hash_new + "_" + hash_old
        tmp_dir = mkdtemp(deploy_id)
        # get the files that have changed between the commits
        with hide('commands'):
            with lcd(tmp_dir):
                #c_go = local('lcd %s' % tmp_dir, capture = False)
                c_clone = local('git clone %s' % repo_url, capture = False)
                with lcd("%s/%s" % (tmp_dir, repo_name)):
                    local('git checkout %s' % branch, capture = False)
                    local('git reset --hard %s' % hash_new, capture = False)
                    c_files = local('git diff --stat --name-only %s %s' % (hash_old, hash_new), capture = True)
                    
            print(c_files)
        # deploy
        host_string = instance_with_access['host']
        pem = ""
        if 'pem' in instance_with_access:
            pem = instance_with_access['pem']
            
        user = ""
        if 'user' in instance_with_access:
            user = instance_with_access['user']
            host_string = "%s@%s" % (user, host_string)
        port = ""
        if 'port' in instance_with_access:
            port = instance_with_access['port']
            host_string = "%s:%s" % (host_string,port)
        
        files = c_files.split("\n")
        for f in files:
            with settings(parallel=True, host_string = host_string, user = user, port = port,key_filename = pem):
                env.host_string = host_string #"vagrant@127.0.0.1:2222"
                #env.user = user
                #env.port = "2222"
                env.key_filename = pem
                #env.use_ssh_config = False
                #env.host = ["127.0.0.1"]
                where = "%s/%s" % (instance_with_access['location'], deploy_id)
                run("mkdir -p %s" % where)
                put("%s/%s/%s" % (tmp_dir, repo_name, f), where)
        # delete the tmp directory on the server
        try:
            shutil.rmtree(tmp_dir)  # delete directory
        except OSError as exc:
            if exc.errno != 2:  # code 2 - no such file or directory
                raise  # re-raise exception    
        
    