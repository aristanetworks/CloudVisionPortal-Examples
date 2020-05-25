from cvprac.cvp_client import CvpClient
import git
import os
import time
import shutil
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEBUG = 0

# syncFrom can be either cvp or git:
#  cvp - configlets are sync'd from cvp to the repo over commiting what's in the repo (CVP is the source of truth)
#  git - configlets are sync'd from git to cvp overwritting what is in CVP (git is the source of truth)
syncFrom = "git"

# Path for git workspace (include trailing /)
gitTempPath = '/tmp/GitConfiglets/'
gitRepo = 'https://github.com/terensapp/cvpbackup'
gitBranch = 'master'
# Relative path within the repo to the configlet directory, leave blank if they reside in the root
configletPath = ''
ignoreConfiglets = ['.git','.md']
# cvpNodes can be a single item or a list of the cluster
cvpNodes = ['54.193.119.19']
cvpUsername = 'arista'
cvpPassword = 'arista'


# Initialize the client
cvpClient = CvpClient()

# Attempt to connect to CVP, if it's not available wait 60 seconds
attempts = 0
while 1:
   try: 
      cvpClient.connect(cvpNodes, cvpUsername, cvpPassword)
      if cvpClient.api.get_cvp_info()['version']:
         break
   except:
      attempts += 1
      print "Cannot connect to CVP waiting 1 minute attempt",attempts
      time.sleep(60)


# Function to sync configlet to CVP
def syncConfiglet(cvpClient,configletName,configletConfig):
   try:
      # See if configlet exists
      configlet = cvpClient.api.get_configlet_by_name(configletName)
      configletKey = configlet['key']
      configletCurrentConfig = configlet['config']
      # For future use to compare date in CVP vs. Git (use this to push to Git)
      configletCurrentDate = configlet['dateTimeInLongFormat']
      # If it does, check to see if the config is in sync, if not update the config with the one in Git
      if configletConfig == configletCurrentConfig:
        if DEBUG > 4:
          print "Configlet", configletName, "exists and is up to date!"
      else:
        cvpClient.api.update_configlet(configletConfig,configletKey,configletName)
        if DEBUG > 4:
          print "Configlet", configletName, "exists and is now up to date"
     
   except:
      addConfiglet = cvpClient.api.add_configlet(configletName,configletConfig)
      if DEBUG > 4:
        print "Configlet", configletName, "has been added"

##### End of syncConfiglet

def cloneRepo():
  # Download/Update the repo
  try:
     if os.path.isdir(gitTempPath):
        shutil.rmtree(gitTempPath)
     repo = git.Repo.clone_from(gitRepo,gitTempPath,branch=gitBranch)
  except:
     print "There was a problem downloading the files from the repo"
#### End of cloneRepo

def syncFromGit(cvpClient):
  cloneRepo()

  configlets = os.listdir(gitTempPath + configletPath)

  for configletName in configlets:
     if configletName not in ignoreConfiglets and not configletName.endswith(tuple(ignoreConfiglets)):
        with open(gitTempPath + configletPath + configletName, 'r') as configletData:
           configletConfig=configletData.read()
        syncConfiglet(cvpClient,configletName,configletConfig)

  if os.path.isdir(gitTempPath):
     shutil.rmtree(gitTempPath)
#### End of SyncFromGit

def syncFromCVP(cvpClient):
  cloneRepo()
  repo = git.Repo(gitTempPath)

  for configlet in cvpClient.api.get_configlets()['data']:
    file = open(gitTempPath + configlet['name'],"w")
    file.write(configlet['config'])
    file.close()
    repo.index.add([configlet['name']])

  repo.git.add(update=True)
  repo.index.commit("Syncing repo with CVP")
  repo.git.push("origin")
#### End of syncFromCVP

if syncFrom == 'cvp':
  print "Syncing configlets from CVP to git repo"
  syncFromCVP(cvpClient)
  print "Completed successfully"
elif syncFrom == 'git':
  print "Syncing configlets from git repo to CVP"
  syncFromGit(cvpClient)
  print "Completed successfully"
else:
  print "Invalid sync option"
