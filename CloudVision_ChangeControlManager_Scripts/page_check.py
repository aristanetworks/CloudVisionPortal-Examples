#!/usr/bin/env python
#
# Copyright (c) 2019, Arista Networks
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
CCCM Script - Check for avialable web page url
Description - Simple CCM script to check for the prescence of a web page

Notes -
Global Variables available to script using cvplibrary
   CVP_USERNAME - Username of the current user
   CVP_PASSWORD - Password of the current user
   CVP_IP - IP address of the current device
   CVP_MAC - MAC of the current device
   CVP_SERIAL - Serial number of the current device
   CVP_SESSION_ID - Session id of current cvp user, this can be passed around to cvp api
   SCRIPT_ARGS - A dictionary of arguments passed to the Script Action configured in associated yaml file

Audit Logging function
   alog(string) - alog function writes the string to the audit logs tagged with the specific change control
   calling the script

Required Arguments
   pageURL - web page to look for
   deviceList - list of devices to check from
   failCount  - Number of Page Tests that can fail before web_check fails
   username   - Username to access devices
   password   - Password to use to access devices
   timeout    - How long to wait for a response

Smaple yaml file
   name : page_check
   args:
    deviceList: "10.83.30.110,10.83.30.111,10.83.30.112,10.83.30.115"
    pageURL: "https://10.83.30.100/cv"
    failCount: 2
    username: 'username'
    password: 'password'
    timeout: 1

"""
# Import required CVP Libraries
from cvplibrary.auditlogger import alog # CVP auit log function
from cvplibrary import Device, CVPGlobalVariables, GlobalVariableNames # CVP Variables
from cvplibrary.request_session import RequestSession

# Import Python Libraries
import paramiko
import re

# Check to see if this script is being tested or run in CVP
test = False
if not RequestSession.getSessionId():
   test = True

# Log message handling
def outMsg(test,msgTxt):
    """ Output log messages to stdout if testing
      or CVP CC log if running in CVP
    """
    if test:
        print(msgTxt)
    else:
        alog(msgTxt)

# Create Script variables
scriptArgs = CVPGlobalVariables.getValue( GlobalVariableNames.SCRIPT_ARGS)
scriptArgs['deviceList']=re.split(',',scriptArgs['deviceList'])

# Internal Variables
host_port = 22
passed = 0
failed = 0

# Write entry to Log
outMsg(test, "page_check - check Web Page connectivity")

# Intialise SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Start ping tests from devices in deviceList
for device_ip in scriptArgs['deviceList']:
   outMsg(test, "page_check: Connecting to %s" %device_ip)
   ssh.connect(device_ip, port=host_port, username=scriptArgs['username'], password=scriptArgs['password'])
   stdin, stdout, stderr = ssh.exec_command('curl --insecure -I -m %s %s' %(scriptArgs['timeout'],scriptArgs['pageURL']))
   output = stdout.readlines()
   error = stderr.readlines()
   if "Failed" in str(error[-1]) or "Error" in str(error[-1]):
      outMsg(test, "page_check: Access form %s to %s: Failed (1)" %(device_ip, scriptArgs['pageURL']))
      outMsg(test,"page_check: %s" %error[-1])
      failed += 1
   else:
      if "200 OK" in output[0]:
         outMsg(test, "page_check: Access form %s to %s: Pass" %(device_ip, scriptArgs['pageURL']))
         passed += 1
      else:
         outMsg(test, "page_check: Access form %s to %s: Failed (2)" %(device_ip, scriptArgs['pageURL']))
         outMsg(test,"page_check: %s" %output[0])
         failed += 1
   ssh.close()
# If number of Page tests that failed exceeds failCount
# fail the whole test
if int(scriptArgs['failCount']) > failed:
   outMsg(test, "page_check: Passed - Number of failures must be less than %s. %s devices can access %s" %(scriptArgs['failCount'],
                                                                                              passed,scriptArgs['pageURL']))
else:
   outMsg(test, "page_check: Failed - Number of failures must be less than %s. %s devices were not able to access %s" %(scriptArgs['failCount'],
                                                                                                                         failed,scriptArgs['pageURL']))
   if not test:
      raise UserWarning("page_check: Failed")
