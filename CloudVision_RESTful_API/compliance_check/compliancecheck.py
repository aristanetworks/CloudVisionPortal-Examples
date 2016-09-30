#!/usr/bin/env python
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
__author__ = 'jkelly@arista.com'

'''

   Script to check the configuration compliance of devices in CVP.
   The goal is to have the script run periodically to validate the config status,
   and then email and/or syslog a list of devices found to be out of compliance.

   Description:
   Run every X interval
   Call compliance check from root container
   Generate list of non-compliant systems
   If configured, email list
   If configured, iterate list and SYSLOG to configured server
   If configured, print report locally

   Contingencies:
   Username / Password must be inside script/script configuration or specified on command line
   Tested with GMAIL only - Email username and password (app specific) need to be set for gmail
   X interval should be configurable with comment discouraging setting this to low

   Requirements:
   python json
   cvp, requests_2_4_0 (can be downloaded from /cvp/tools on CVP server)

   The awesome python daemon module found here:
   https://github.com/serverdensity/python-daemon/blob/master/daemon.py

   And licensed here:
   https://creativecommons.org/licenses/by-sa/3.0/


'''

import getopt
import json
import logging
from logging import handlers
import smtplib
from email.mime.text import MIMEText
import sys, time

try:
    from daemon import Daemon
except NameError:
    print "Please install the daemon module located at https://github.com/serverdensity/python-daemon/blob/master/daemon.py"

# Can be pulled from CVP server under /cvp/tools

import requests_2_4_0 as requests
from requests_2_4_0 import packages
import cvp

# Configuration settings, modify as needed.

MIN_INTERVAL = 60  # This is the minimum recommended interval the script should run in seconds
CVPSERVER = None  # CVP server name mandatory, use quotes
SYSLOGSERVER = '/var/run/syslog'  # syslog server ip, mandatory if using syslog, use quotes
EMAILFROM = None  # Email from address, use quotes, mandatory if using email
EMAILTO = None  # Email To address, use quotes, mandatory if using email

#Needs to be a one time password for two factor auth with gmail.  generate a new app specific password and use that
EMAILPASS = None  # Email password, mandatory if using gmail
EMAILSERVER = None  # Email server, for gmail, 'smtp.gmail.com' mandatory if using mail
EMAILPORT = 587  # Email server port, for gmail, 587 is default

CURSTATUS = {}

assert CVPSERVER is not None
assert SYSLOGSERVER is not None

class MyDaemon(Daemon):
    def run(self):
        while True:
            main()
            time.sleep(INTERVAL)

class Switch(object):
    """
    Define switch properties

    Variables:
    self.ipaddress - ip address used to manage the switch from CVP
    self.macaddress - mac address of the switch - used by cvp to identify and execute certain tasks
    self.reachable - is the switch reachable, determined by cvp ip reachability check?
    self.compliant - is the switch configuration synchronized with CVP's view of the configuration?
    self.fqdn - not currently used, theoretically to provide fqdn of switch
    self.status - status code, 0, 1, or 2 to determine whether the switch is unreachable, out of compliance,
    or in compliance

    Functions:
    makestatus - returns status information of a given switch

    """

    def __init__(self):
        self.ipaddress = None
        self.macaddress = None
        self.reachable = None
        self.compliant = None
        self.fqdn = None
        self.status = None

    def makestatus(self):
        if self.reachable is False:
            self.status = 0
        else:
            if self.compliant is True:
                self.status = 2
            else:
                self.status = 1
        return self.status

switchstatus = Switch()


def getComplianceList():

    """
    Function to generate lists of which switches are reachable, and which are out of compliance

    :return:
      unreachable - list of unreachable devices
      outofcompliance - list of devices out of config compliance
    """
    global CURSTATUS
    unreachable = []
    outofcompliance = []
    # Pull the list of devices from CVP
    devicelist = getDeviceLists()
    # iterate through list, check if device is reachable first, then if so, check compliance
    for device in devicelist:
        try:
            switchstatus.reachable = checkDeviceStatus(devicelist[device])
            switchstatus.ipaddress = devicelist[device]
            if switchstatus.reachable is True:
                switchstatus.compliant = server.deviceComplianceCheck(device)
        except:
            raise
        # get the status code and create lists for unreachables and out of compliance switches
        status = switchstatus.makestatus()
        try:
            if status == CURSTATUS[switchstatus.ipaddress]:
                continue

        except KeyError:
            CURSTATUS[switchstatus.ipaddress] = status
        except:
            raise

        if status == 0:
            unreachable.append(switchstatus.ipaddress)
        elif status == 1:
            outofcompliance.append(switchstatus.ipaddress)
        CURSTATUS[switchstatus.ipaddress] = status



    return unreachable, outofcompliance  #, CURSTATUS


def getDeviceLists():
    """
    Function to pull list of devices from CVP

    Returns:
    devices - dictionary of devices as kv pair mac_address: ip_address
    """

    devices = {}
    devicelist = server.getDevices()
    for device in devicelist:
        devices[device.macAddress] = device.ipAddress
    return devices


def checkDeviceStatus(device):
    """
    Function to check reachability of a switch, calls cvp ipConnectivityTest

    :param device: device ip address, used by cvp api to check reachability

    :return:
    reachable - whether or not the switch is reachable
    """
    data = {"ipAddress": device}
    try:
        #print server.cvpService.url, data
        pingstatus = server.cvpService.doRequest( requests.post, '%s/web/provisioning/ipConnectivityTest.do' % server.cvpService.url, data=json.dumps(data), cookies=server.cvpService.cookies)
        if pingstatus['data'] == 'success':
            reachable = True
        else:
            reachable = False
    except cvp.cvpServices.CvpError as e:
        if str(e).startswith('122605'):
            reachable = False
        else:
            reachable = False
            print "An error occurred %s" % e
    return reachable

def sendMail(switchlist, text):
    """
    Function to email a list of unreachable or out of compliance switches to a given email address
    The way this is written will work with gmail.  If using two factor authentication, you need to
    create a new app specific password in gmail

    :param switchlist: list of switches which are either unreachable or out of compliance
    :param text: beginning of the report, identifies whether or not report lists unreachable or out of comp.
    """
    body = text + "\n"
    for switch in switchlist:
        body += switch + "\n"
    msg = MIMEText(body)
    msg['Subject'] = text
    msg['From'] = EMAILFROM
    msg['To'] = EMAILTO
    msg = msg.as_string()
    try:
        emailserver = smtplib.SMTP(EMAILSERVER, EMAILPORT)
        emailserver.starttls()
        emailserver.login(EMAILFROM, EMAILPASS)
        emailserver.sendmail(EMAILFROM, EMAILTO, msg)
        emailserver.quit()
    except:
        raise


def sendSyslog(switchlist, text):
    """
    Function to send a syslog message for each unreachable and out of compliance switch

    :param switchlist: list of switches which are either unreachable or out of compliance
    :param text: Initial text of syslog message, indicates type of message
    """

    cvplogger = logging.getLogger('CvpLogger')
    cvplogger.setLevel(logging.WARNING)
    termlogger = logging.StreamHandler(sys.stdout)
    logwriter = logging.handlers.SysLogHandler(address= SYSLOGSERVER)  #, 514))
    cvplogger.addHandler(logwriter)
    cvplogger.addHandler(termlogger)
    for switch in switchlist:
        cvplogger.critical('%s %s' % (text, switch))
    logwriter.close()
    cvplogger.removeHandler(logwriter)
    termlogger.close()
    cvplogger.removeHandler(termlogger)


def printer(switchlist, text):
    """
    Function to print output of reachability and compliance checks to the local terminal.  Useful for testing.

    :param switchlist: list of switches which are either unreachable or out of compliance
    :param text: Initial text of terminal message, indicates type of message

    """

    print text
    for switch in switchlist:
        print switch


def notify(switchlist, text, EMAIL, SYSLOG, PRINT):
    """
    Function to determine where results are sent

    :param switchlist: list of switches which are either unreachable or out of compliance
    :param text: Initial text of message, indicates type of message
    :param EMAIL: Whether or not to email the message to the configured server and recipient
    :param SYSLOG: Whether or not to syslog the message to the configured syslog server
    :param PRINT: Whether or not to print the results to the local terminal

    """

    if PRINT is True:
        printer(switchlist, text)
    if EMAIL is True:
        sendMail(switchlist, text)
    if SYSLOG is True:
        sendSyslog(switchlist, text)


def usage():
    print "usage:compliancecheck.py (start|stop|restart) -i <interval seconds> -u <cvp username> -p <cvp password> --mail --syslog --print"


def getargs(argv):
    """
    Get any CLI arguments to overrride config settings

    :param argv:
    :return:
    INTERVAL - Interval in seconds, defaults to 60 from global config
    CVPUSER - CVP username, default cvpadmin from global config
    CVPPASS - CVP password, default arista from global config
    EMAIL - Send email or not, boolean, default to false from global config
    SYSLOG - Send syslong or not, boolean, default to false from global config
    PRINT - Print locally or not, boolean, default to false from global config
    """
    global MIN_INTERVAL  #, EMAIL, CVPUSER, CVPPASS, SYSLOG, PRINT, INTERVAL, RUN
    INTERVAL = 3600  # How frequently to call script
    CVPUSER = None
    CVPPASS = None
    SYSLOG = False
    EMAIL = True
    PRINT = False

    assert CVPUSER is not None
    assert CVPPASS is not None

    if not len(argv) == 1:
        try:
            opts, args = getopt.getopt(argv, "hi:u:p:", ["mail", "syslog", "print", "daemonize", "run"])
        except getopt.GetoptError:
            usage()
            sys.exit(2)
        for opt, arg in opts:
            if opt == "-h":
                usage()
                sys.exit(2)
            elif opt == "-i":
                INTERVAL = int(arg)
                print INTERVAL
                if INTERVAL <= MIN_INTERVAL:
                    print 'Warning, configured polling interval %s is below the recommended min interval of %s' \
                          % (INTERVAL, MIN_INTERVAL)
                    print 'You are hereby discouraged'
            elif opt == "-u":
                CVPUSER = arg
            elif opt == "-p":
                CVPPASS = arg
            elif opt == "--mail":
                assert EMAILFROM is not None
                assert EMAILTO is not None
                assert EMAILPASS is not None
                assert EMAILSERVER is not None
                EMAIL = True
            elif opt == "--syslog":
                assert SYSLOGSERVER is not None
                SYSLOG = True
            elif opt == "--print":
                PRINT = True
            else:
                usage()
                sys.exit(2)
    else:
        print 'drat'
        usage()
        sys.exit(2)
    return INTERVAL, CVPUSER, CVPPASS, EMAIL, SYSLOG, PRINT


def main():
    if SYSLOG is True:
        assert SYSLOGSERVER is not None
    if EMAIL is True:
        assert EMAILFROM is not None
        assert EMAILTO is not None
        assert EMAILPASS is not None
        assert EMAILSERVER is not None
    try:
        global server
        server = cvp.Cvp(CVPSERVER)
        server.authenticate(CVPUSER, CVPPASS)
    except requests.HTTPError as e:
        print "Error connecting to CVP Server, trying again in 60 seconds: %s" % str(e)
        time.sleep(60)
    except packages.urllib3.exceptions.ProtocolError as e:
        if str(e) == "('Connection aborted.', gaierror(8, 'nodename nor servname provided, or not known'))":
            print "DNS Error: The CVP Server %s can not be found" % CVPSERVER
            sys.exit(2)
        elif str(e) == "('Connection aborted.', error(54, 'Connection reset by peer'))":
            print "Error, connection aborted"
        else:
            raise
    except:
        raise
    try:
        unreachable, outofcompliance = getComplianceList()
        # If there are any unreachable switches, send the list to the notify function for reporting
        if len(unreachable) > 0:
            text = "%s CVP_Compliance_Checker: UNREACHABLE: " % time.asctime()
            notify(unreachable, text, EMAIL, SYSLOG, PRINT)
        # If there are switches out of compliance, send the list to notify function for reporting
        if len(outofcompliance) > 0:
            text = "%s CVP_Compliance_Checker: OUT_OF_COMPLIANCE: " % time.asctime()
            notify(outofcompliance, text, EMAIL, SYSLOG, PRINT)
    # If CVP can't be reached, try again in 1 minute, could probably use a counter to abort after x tries
    except requests.HTTPError as e:
        print "Error reaching CVP server, trying again in 60 seconds %s" % str(e)
        time.sleep(60)
        #continue
    except packages.urllib3.exceptions.ProtocolError as e:
        if str(e) == "('Connection aborted.', gaierror(8, 'nodename nor servname provided, or not known'))":
            print "DNS Error: The CVP Server %s can not be found.  Check the hostname and try again." % CVPSERVER
            sys.exit(2)
        else:
            raise
    except:
        raise
    print "#"*120
    print "Executing Compliance Check @ ", time.asctime()
    print "#"*120


if __name__ == "__main__":
        daemon = MyDaemon('/tmp/cvpcompliancecheck.pid')
        INTERVAL, CVPUSER, CVPPASS, EMAIL, SYSLOG, PRINT = getargs(sys.argv[2:])
        daemon.INTERVAL = INTERVAL
        daemon.CVPUSER = CVPUSER
        daemon.CVPPASS = CVPPASS
        daemon.EMAIL = EMAIL
        daemon.SYSLOG = SYSLOG
        daemon.PRINT = PRINT
        if len(sys.argv) >= 2:
                if 'start' == sys.argv[1]:
                        print 'CVP Compliance Checker started.  Executing every %s seconds.' % INTERVAL
                        sendSyslog([CVPSERVER], 'CVP Compliance Checker started.  Executing every %s seconds against' % INTERVAL)
                        print '#'*120
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        sendSyslog([CVPSERVER], 'Compliance Checker Stopping against')
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                else:

                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                usage()
                sys.exit(2)