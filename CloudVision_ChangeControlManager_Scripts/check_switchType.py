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
CCM Script - Check device Type
Description - Simple CCM script to demonstrate functionality and application

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

Smaple yaml file
   name : check_switchType
   args:
      switchType : vEOS

"""
# Import required Librarys
import json
from cvplibrary.auditlogger import alog # CVP auit log function
from cvplibrary import Device, CVPGlobalVariables, GlobalVariableNames # CVP Variables

# Create Script variables
ipAddress = CVPGlobalVariables.getValue( GlobalVariableNames.CVP_IP)
scriptArgs = CVPGlobalVariables.getValue( GlobalVariableNames.SCRIPT_ARGS)

# Write entry to Log
alog("running show version from script to check switch type")
# Connect to Device specified in Change Control
switch = Device(ipAddress)
# Run show commands on switch
cmdOut = switch.runCmds(["show version","show hostname"])
# Check if the switch type is correct
if str(scriptArgs['switchType']) not in cmdOut[0]["response"]["modelName"]:
    logTxt = "WARNING: switch %s is not a %s it is a %s" %(cmdOut[1]["response"]["hostname"],
                                                  scriptArgs['switchType'],
                                                  cmdOut[0]["response"]["modelName"])
    alog(logTxt)
    assert(False)
else:
    logTxt = "SUCCESS: switch %s is a %s" %(cmdOut[1]["response"]["hostname"],
                                            cmdOut[0]["response"]["modelName"])
    alog(logTxt)
