#!/usr/bin/python2.7

#This script creates the templates needed for Arista config generations @ Comcast DC
# The script uses three input CSV Files
#
# --
# Suresh Kanagala ( SE- Arista Networks )

import csv
import re
import collections
import jinja2
import json
from collections import defaultdict
from jinja2 import Template
from jinja2 import Environment, PackageLoader
from cvplibrary import Form
from cvplibrary import CVPGlobalVariables, GlobalVariableNames
from cvplibrary import RestClient
import sys

def netid_to_serialnum(net_id):
 query='http://localhost:8080/web/provisioning/getNetElementById.do?netElementId=%s' % mac;
 client= RestClient(query,'GET');
 if client.connect():
   dev_info = json.loads(client.getResponse())
   return dev_info['serialNumber']
 return None

mac = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_MAC)
serialnum = netid_to_serialnum(mac)

with open('mgmt_applicator.csv', 'rb') as f:
    reader=csv.reader(f)
    sertohost=list(reader)
# Capturing the hostname of the device
for items in sertohost:
    if items[0] == serialnum and items[1].startswith(('as', 'sw')):
        hostname = items[1]

with open('bgpfile.csv', 'rb') as f:
    reader=csv.reader(f)
    bgpinfo=list(reader)
# Capturing hostnames of all BGP hosts here
bgp_col1 = set()
for row in bgpinfo:
    bgp_col1.add(row[0])
bgp_col1=list(bgp_col1)
# Store BGP peer info
bgpdata=defaultdict(list)
for row in bgpinfo:
    if hostname == row[0]:
        bgpdata[hostname].append(row)
bgpdata=dict(bgpdata)

with open('loopback.csv', 'rb') as f:
    reader=csv.reader(f)
    loopbackinfo=list(reader)
# Store Loopback info
for row in loopbackinfo:
    if hostname == row[0]:
        loopback0 = row[1]
        loopback60 = row[2]

# Setup for using Jinja templates
template_loader = jinja2.FileSystemLoader('./templates')
env = jinja2.Environment(loader=template_loader,
                         undefined=jinja2.DebugUndefined)
if hostname.startswith('sw'):
    template = env.get_template('sw_template.j2')
elif hostname.startswith('as'):
    template = env.get_template('as_template.j2')
if template:
    print (template.render({'bgpdata': bgpdata,
                            'hostname': hostname,
                            'loopback0': loopback0,
                            'loopback60': loopback60}))