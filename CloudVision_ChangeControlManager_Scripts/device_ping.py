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
CCM Script - PIng Test Between 2 Devices
Description - Simple CCM script to ping between two devices

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
   deviceList - list of Linux devices to ping from
   targetList - list of devices to ping
   passmark   - Percentage of recieved Pings required to Pass each Ping test
   failCount  - Number of Ping Tests that can fail before ping_device fails
   username   - Username to access devices
   password   - Password to use to access devices
   pingCount  - Number of Pings to send
   timeout    - Ping timeout

Smaple yaml file
   name : device_ping
   args:
    deviceList: "10.83.30.110,10.83.30.111,10.83.30.112,10.83.30.115"
    targetList: "192.168.50.10,192.168.51.10,192.168.52.10,192.168.53.10"
    passmark: 100
    failCount: 1
    username: 'username'
    password: 'password'
    pingCount: 5
    timeout: 5

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
scriptArgs['targetList']=re.split(',',scriptArgs['targetList'])

# Internal Variables
host_port = 22
passed = 0
failed = 0

# Write entry to Log
outMsg(test, "device_ping - checking endpoint connectivity")

# Intialise SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Start ping tests from devices in deviceList
for device_ip in scriptArgs['deviceList']:
    outMsg(test, "device_ping: Connecting to %s" %device_ip)
    ssh.connect(device_ip, port=host_port, username=scriptArgs['username'], password=scriptArgs['password'])
    for target in scriptArgs['targetList']:
        stdin, stdout, stderr = ssh.exec_command('ping -c %s -w %s %s' %(scriptArgs['pingCount'],
                                                                         scriptArgs['timeout'],target))
        output = stdout.readlines()
        # Extract Ping results
        ping_stats = re.split(',', output[-2])
        ping_tx = re.split('(\d+)',ping_stats[0])[1]
        ping_rx = re.split('(\d+)',ping_stats[1])[1]
        ping_pkl = re.split('(\d+)',ping_stats[2])[1]
        ping_pkr = 100-int(ping_pkl)
        # Check Ping Results and Log them
        if int(ping_pkr) >= int(scriptArgs['passmark']):
            outMsg(test, "device_ping: Ping form %s to %s - Pass" %(device_ip, target))
            passed += 1
        else:
            outMsg(test, "device_ping: Ping form %s to %s - Failed" %(device_ip, target))
            failed += 1
    ssh.close()
# If number of Ping tests that failed exceeds failCount
# fail the whole test
if int(scriptArgs['failCount']) > failed:
    outMsg(test, "device_ping: Passed - Number of failures must be less than %s. %s device(s) recieved the required number of pings" %(scriptArgs['failCount'],passed))
else:
    outMsg(test, "device_ping: - Failed Number of failures must be less than %s. %s device(s) did not recieve the required number of pings" %(scriptArgs['failCount'],failed))
    if not test:
      raise UserWarning("device_ping: Failed")
