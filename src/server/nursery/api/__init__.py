from enum import Enum

class DeploymentStatus(Enum):
     SCHEDULED = 0 
     STARTED = 10 
     # status like 11, 12 etc will be internal checks to see where some process might get blocked
     #ended ->
     ENDED = 90 #ok
     FAILED = 100 
     # we will calculate the failed as 100+exact status before being declared failed
     # like 35 will become 135, this way we mark the deployment as failed 
     # but we keep it's original status
     CANCELED = 200
     
class DeploymentType(Enum):
    GIT = 0 # by a hook in github
    CLIENT = 1 # using the deploy command
    FORCED = 2 # using another repo    
# here needs to be added the functions for getting the modules to work with the server config