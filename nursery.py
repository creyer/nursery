#!/usr/bin/env python
from __future__ import with_statement
import argparse
import sys
import logging
import urllib, urllib2
import json
from fabric.operations import local
from fabric.api import hide
import yaml 

VERSION = "0.0.1"
SERVER_FILE = ".server"
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_repo_info():
    with hide('commands'):
        f_out = local('git remote -v|grep push|grep origin', capture = True)
    remote_git = ""      
    start = f_out.find("http")
    end = f_out.find(".git")
    remote_git = f_out[start:end]
    repo_name = remote_git[remote_git.rfind('/')+1:]
    return repo_name

def get_current_branch():
    with hide('commands'):
        f_out = local('git branch', capture = True)
    start = f_out.find('* ')
    end = f_out.find('\n')
    branch = f_out[start+2:end]
    return branch      

def get_last_hash():
    with hide('commands'):
        f_out = local('git rev-parse HEAD', capture = True)
    start = 0
    end = f_out.find('\n')
    branch = f_out[start:end]
    return branch    
    

class Server(object):
    def __init__(self):
        try:
            with open(".server") as f:
                self.address = f.readlines()[0]
                self.repo = get_repo_info()
                self.current_branch = get_current_branch()
                ok = self.post_to_server('info')
                logging.debug("endpoint: %s" % (ok))
        except IOError:
            self.address = None
    
    def parse_yaml(self,yaml_file):
        try:
            data = yaml.load(yaml_file.read())
            if data is not None:
                return data
            return False
        except Exception as e:
            logging.error(e)
            return False  

      
    """ Run a normal client deployment """
    def deploy(self, git_hash = None):
        if git_hash is None:
            git_hash = get_last_hash()
        deploy = {'hash': git_hash, 'branch': get_current_branch()}
        req = self.post_to_server("deploy", deploy)
        result = json.loads(req)
        self.parse_server_response(result)
    
    def parse_server_response(self,result):
        if result['status'] == "ok":
            print result['msg']
        else:
            logging.error(result)
            print ("Error occured: %s" % (result['msg']))
            sys.exit()

    """" Sends a new init configuration for deployment on a branch and current repo """
    def init_config(self, config_file):
        conf = {'conf':self.parse_yaml(config_file)}
        if not conf['conf']:
            print "Your config file could not be parsed"
            sys.exit()        
        req = self.post_to_server("init.config", conf)     
        result = json.loads(req)
        self.parse_server_response(result) 

    """ Creates the base url for the api """   
    def get_base_url(self, command = None):
        return {
            'info': 'http://%s' % (self.address),
            'init.config': 'http://%s/api/%s/init/' % (self.address, self.repo),
            'deploy': 'http://%s/api/%s/deploy/' % (self.address, self.repo),
            }.get(command, 'http://%s/api/%s' % (self.address, self.repo)) 


    """ Post requests to deploy server """
    def post_to_server(self, command = None, data_dict = None):
        if self.address is not None:            
            url_2 = self.get_base_url(command)
            if data_dict is not None:    
                logging.debug("sending post data: %s to: %s" % (data_dict, url_2))        
                data = urllib.urlencode(data_dict)
                req = urllib2.Request(url_2, data)
                try:
                    rsp = urllib2.urlopen(req)
                except urllib2.URLError, e:
                    logging.error("Error 2: couldn't communicate with the server on: %s" % (url_2))
                    sys.exit()    
            else:
                req = urllib2.Request(url_2)
                try:
                    logging.debug("executing get on: %s" % (url_2))
                    rsp = urllib2.urlopen(req)
                except urllib2.URLError, e:
                    logging.error("Error 3: couldn't communicate with the server on: %s" % (url_2))
                    sys.exit()
            return rsp.read()
        else: 
            logging.error("Error 4: Can't comunicate with the server")
            sys.exit()


class DeployAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logging.debug('DeployAction %r %r %r' % (namespace, values, option_string))
        setattr(namespace, self.dest, values)
        if values is None:
            server.deploy()
        else:
            server.deploy(values)

""" This will read a local config yaml which will be sent to the server
    If the server will have this repo and branch already configured 
    an error will be trigered.
    This method can't be used to overwrite config data """
class InitAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        logging.debug('%r %r %r' % (namespace, values, option_string))
        setattr(namespace, self.dest, values)
        server.init_config(values)
        # TODO verify with the server if exists already an initiated config for this repo
        # if exists an error will be displayed  

class SetupAction(argparse.Action):
     def __call__(self, parser, namespace, values, option_string=None):
        logging.debug('%r %r %r' % (namespace, values, option_string))
        setattr(namespace, self.dest, values)
        server = values
        # write hidden file with the server address
        f = open(SERVER_FILE,'w')
        f.write('%s' %(server)) # python will convert \n to os.linesep
        f.close() 

        
server = Server()
parser = argparse.ArgumentParser(description = 'Nursery deplkoy system')
parser.add_argument('-v','--version', action = 'version', version = '%(prog)s '+VERSION)
parser.add_argument('-s','--setup', nargs='?', metavar='Server', action = SetupAction,help = 'setup a nursery deploy system, you need to specify the nursery server endpoint like: http://www.my-nursery-server.com')
# each branch needs it's own config file
parser.add_argument('-c','--config', metavar='config.yaml', action = InitAction, type = file,help = 'init a new repo deployment with config file you specify')
parser.add_argument('-d','--deploy',nargs='?', metavar='hash', action = DeployAction, type = file,help = 'create a new async deploy')
parser.add_argument('-i','--info', action='store_true', help = 'some info Nursery Client knows about')


if not len(sys.argv) > 1:
    parser.print_help()
else:
    args = parser.parse_args()
    logging.debug(args)
    if args.info:
        if server.address is not None:
            print ("remote deploy server: %s" % server.address)
            print ("repo: %s" % server.repo)
            print ("branch: %s" % server.current_branch)

# comication with the server - done
# setup server (with amazon credentials & stuff)
# initialize branch deploy with deploy server
    # read config yaml and send it to the server - file sent - ok
    # read the response and show it - ok
    # read the file on the server - ok

#TODO
    # on the server store the git deploy command so it can be processed assync
        # 3 way to deploy git, client, forced
        # - client
            # client -> git deploy (last hash) -> ok
            # store in db the command if allow_multiple_deploy & stuff
            # parse the command assync
            # build file list
            # get instances
            # get scripts
            # make the deployment
    # on the server we need to modelate this yaml file to the db
    # find a good way to insert instances in db
    # filter a deployment based on touced files
    # make a deployment    

  


