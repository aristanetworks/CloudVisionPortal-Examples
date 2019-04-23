#!/usr/bin/env python
#
# Copyright (c) 2016, Arista Networks, Inc.
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
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
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

import cvp, optparse, smtplib
from email.mime.text import MIMEText
from string import Template

# Compliance codes for devices and containers
DEVICE_IN_COMPLIANCE = 0
DEVICE_CONFIG_OUT_OF_SYNC = 1
DEVICE_IMAGE_OUT_OF_SYNC = 2
DEVICE_IMG_CONFIG_OUT_OF_SYNC = 3
DEVICE_IMG_CONFIG_IN_SYNC = 4
DEVICE_NOT_REACHABLE = 5
DEVICE_IMG_UPGRADE_REQD = 6
DEVICE_EXTN_OUT_OF_SYNC = 7
DEVICE_CONFIG_IMG_EXTN_OUT_OF_SYNC = 8
DEVICE_CONFIG_EXTN_OUT_OF_SYNC = 9
DEVICE_IMG_EXTN_OUT_OF_SYNC = 10
DEVICE_UNAUTHORIZED_USER = 11

complianceCodes = {
   DEVICE_IN_COMPLIANCE : 'In compliance',
   DEVICE_CONFIG_OUT_OF_SYNC : 'Config out of sync',
   DEVICE_IMAGE_OUT_OF_SYNC : 'Image out of sync',
   DEVICE_IMG_CONFIG_OUT_OF_SYNC : 'Image and Config out of sync',
   DEVICE_IMG_CONFIG_IN_SYNC : 'Unused',        # was: 'Image and Config in sync'
   DEVICE_NOT_REACHABLE : 'Device not reachable',
   DEVICE_IMG_UPGRADE_REQD : 'Image upgrade required',
   DEVICE_EXTN_OUT_OF_SYNC : 'Extensions out of sync',
   DEVICE_CONFIG_IMG_EXTN_OUT_OF_SYNC : 'Config, Image and Extensions out of sync',
   DEVICE_CONFIG_EXTN_OUT_OF_SYNC : 'Config and Extensions out of sync',
   DEVICE_IMG_EXTN_OUT_OF_SYNC : 'Image and Extensions out of sync',
   DEVICE_UNAUTHORIZED_USER : 'Unauthorized User',
}

usage = 'usage: %prog [options]'
op = optparse.OptionParser(usage=usage)
op.add_option( '-c', '--cvphostname', dest='cvphostname', action='store', help='CVP host name FQDN or IP', type='string')
op.add_option( '-u', '--cvpusername', dest='cvpusername', action='store', help='CVP username', type='string')
op.add_option( '-p', '--cvppassword', dest='cvppassword', action='store', help='CVP password', type='string')
op.add_option( '-e', '--email', dest='email', action='store', help='Sender address for email', type='string')
op.add_option( '-r', '--recipient', dest='recipient', action='store', help='Recipient address for email', type='string')
op.add_option( '-s', '--smtpserver', dest='smtpserver', action='store', help='IP address for SMTP server', type='string')

opts, _ = op.parse_args()

host = opts.cvphostname
user = opts.cvpusername
password = opts.cvppassword
email = opts.email
recipient = opts.recipient
smtpserver = opts.smtpserver

server = cvp.Cvp( host )
server.authenticate( user , password )

#container = server.getContainer(containerName)
#events = server.containerComplianceCheck(container)

#for event in events:
#	print event.complianceCode

devices = server.getDevices()
nonCompliant = []
body = ""

for device in devices:
	compliance = server.deviceComplianceCheck(device)
	if compliance != 0:
		nonCompliantMessage = complianceCodes[compliance]
		nonCompliantDevice = {	'device': device.fqdn,
								'message': nonCompliantMessage }
		nonCompliant.append(nonCompliantDevice)

if nonCompliant:
	for nonCompliantDevice in nonCompliant:
		Replacements = {
							'device': nonCompliantDevice['device'],
							'message': nonCompliantDevice['message']
						}

		tmpbody = Template("""
Device $device is non-compliant due to: $message

""").safe_substitute(Replacements)
		body = body + tmpbody

	msg = MIMEText(body)
	msg['Subject'] = 'Device compliance report'
	msg['From'] = email
	msg['To'] = recipient
	msg = msg.as_string()

	try:
		emailserver = smtplib.SMTP(smtpserver, 25)
		emailserver.sendmail(email, recipient, msg)
		emailserver.quit()
	except:
		raise
