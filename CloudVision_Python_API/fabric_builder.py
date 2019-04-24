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

import cvp, optparse, json
from string import Template

#
# Support functions for main code
#

def configletExists( cvpServer , configlet_name ):
	configlet_exist = 0
	myConfiglets = cvpServer.getConfiglets()
	for myConfiglet in myConfiglets:
		if myConfiglet.name == configlet_name:
			configlet_exist = 1
	return configlet_exist

def updateMyConfiglet( cvpServer , configlet_name , configlet_config ):
	myConfiglet = cvpServer.getConfiglet( configlet_name )
	myConfiglet.config = configlet_config
	cvpServer.updateConfiglet( myConfiglet )

def containerExists( cvpServer , container_name ):
	container_exist = 0
	myContainers = cvpServer.getContainers()
	for myContainer in myContainers:
		if myContainer.name == container_name:
			container_exist = 1
	return container_exist
#
# Parse command line options.
#

usage = 'usage: %prog [options]'
op = optparse.OptionParser(usage=usage)
op.add_option( '-c', '--cvphostname', dest='cvphostname', action='store', help='CVP host name FQDN or IP', type='string')
op.add_option( '-u', '--cvpusername', dest='cvpusername', action='store', help='CVP username', type='string')
op.add_option( '-p', '--cvppassword', dest='cvppassword', action='store', help='CVP password', type='string')
op.add_option( '-n', '--name', dest='dcname', action='store', help='Name of DC to build', type='string')
op.add_option( '-s', '--spines', dest='spines', action='store', help='Number of spine switches in DC fabric', type='int')
op.add_option( '-l', '--leafs', dest='leafs', action='store', help='Number of leaf switch MLAG pairs in DC fabric', type='int')
op.add_option( '-y', '--mlag', dest='mlag', action='store', help='If leafs are MLAG pairs or not', type='string')
op.add_option( '-w', '--mlagnetwork', dest='mlagnetwork', action='store', help='Network to use for MLAG peer', type='string')
op.add_option( '-q', '--mlagtrunkinterfaces', dest='mlagtrunkinterfaces', action='store', help='The two interfaces to use for MLAG trunk, ex. Ethernet3,Ethernet4', type='string')
op.add_option( '-d', '--defaultgw', dest='defaultgw', action='store', help='Default gateway for management network', type='string')
op.add_option( '-m', '--mgmtnetwork', dest='mgmtnet', action='store', help='Management network prefix without last octet. Example: 192.168.0.', type='string')
op.add_option( '-o', '--mgmtnetmask', dest='mgmtnetmask', action='store', help='Management network netmask in bit length. Example: 24', type='int')
op.add_option( '-v', '--vxlanloopback', dest='vxlanloopback', action='store', help='Prefix to use for VXLAN loobacks without last octet. Example: 192.168.0.', type='string')
op.add_option( '-z', '--loopback', dest='loopback', action='store', help='Prefix to use for loobacks without last octet. Example: 192.168.0.', type='string')
op.add_option( '-x', '--linknetworks', dest='linknetwork', action='store', help='Prefix to use for linknetworks without last octet. Example: 192.168.0.', type='string')
op.add_option( '-t', '--type', dest='deploymenttype', action='store', help='Type of deployment, her for ip fabric HER, cvx for ip fabric cvx, evpn for ip fabric EVPN', type='string')
op.add_option( '-b', '--cvxserver', dest='cvxserver', action='store', help='IP address on CVX server', type='string')
op.add_option( '-e', '--is-virtual', dest='virtual', action='store', help='If virtual is yes, interface naming will fit vEOS-lab. If virtual is no, interface naming is adaptd to 1RU and 2RU leafs and spines', type='string', default='yes')
op.add_option( '-f', '--no-uplinks', dest='uplinks', action='store', help='Number of uplinks from leaf to each spine', type='int')
op.add_option( '-g', '--offset', dest='offset', action='store', help='Which switch number to continue with when building next DC if IP resources are shared.', type='int',default=1)
op.add_option( '-i', '--mgmt-ip', dest='mgmtip', action='store', help='Which IP to start on in MGMT subnet', type='int',default=1)
op.add_option( '-a', '--debug', dest='debug', action='store', help='If debug is yes, nothing will actually be sent to CVP and proposed configs are written to terminal', type='string', default='no')
op.add_option( '-4', '--syslogserver', dest='syslogserver', action='store', help='IP of syslogserver for logging from switches', type='string')
op.add_option( '-k', '--snmp_private', dest='snmp_private', action='store', help='SNMP private community', type='string')
op.add_option( '-r', '--snmp_public', dest='snmp_public', action='store', help='SNMP public community', type='string')
op.add_option( '-1', '--primary_ntp', dest='primary_ntp', action='store', help='IP of primary NTP server', type='string')
op.add_option( '-2', '--second_ntp', dest='second_ntp', action='store', help='IP of secondary NTP server', type='string')
op.add_option( '-3', '--log_facility', dest='log_facility', action='store', help='Log facility for syslog', type='string')
op.add_option( '-5', '--spine-start-asn', dest='spine_start_asn', action='store', help='Starting ASN for spine which also is offset for the rest of the Datacenter.', type='int')
op.add_option( '-6', '--max-routes', dest='max_routes', action='store', help='Max routes to announce in underlay.', type='int')
op.add_option( '-7', '--max-evpn-routes', dest='max_evpn_routes', action='store', help='Max routes to announce in EVPN.', type='int')

opts, _ = op.parse_args()

#
# Assign command line options to variables and assign static variables.
#

host = opts.cvphostname
user = opts.cvpusername
password = opts.cvppassword
name = opts.dcname
no_spine = opts.spines
no_leaf = opts.leafs
defaultgw = opts.defaultgw
mgmtnetwork = opts.mgmtnet
mgmtnetmask = opts.mgmtnetmask
vxlanloopback = opts.vxlanloopback
loopback = opts.loopback
linknetwork = opts.linknetwork
deploymenttype = opts.deploymenttype
cvxserver = opts.cvxserver
mlag = opts.mlag
mlagnetwork = opts.mlagnetwork
mlagtrunkinterfaces = opts.mlagtrunkinterfaces
debug = opts.debug
virtual = opts.virtual
uplinks = opts.uplinks
syslogserver = opts.syslogserver
snmp_private = opts.snmp_private
snmp_public = opts.snmp_public
log_facility = opts.log_facility
primary_ntp = opts.primary_ntp
second_ntp = opts.second_ntp
spine_start_asn = opts.spine_start_asn
max_routes = opts.max_routes
max_evpn_routes = opts.max_evpn_routes

parentName = 'Tenant'
my_spine_container_name = name + " Spine"
my_leaf_container_name = name + " Leaf"
dc_configlet_name = name + " Base config"
configlet_list = []
cvx_configlet_list = []
leaf_configlet_list = []
max_ecmp = no_spine * uplinks

#
# The first part of the code builds a dictionary representing first all the spines
# and their relevant data to create their config.
#
# Second part of the code builds a dictionary representing first all the leafs
# and their relevant data to create their config.
#

#
# Build the DC list of spine switches in dictionary form.
#

linksubnetcounter = 0
loopbackcounter = 0
vxlanloopbackcounter = 0
mgmtnetworkcounter = 1

DC = []
Leafs = []

for counter in range(1,no_spine+1):
	spine_name = name + "spine" + str(counter)
	interface_list = []
	element_dict = {}
	element_dict['name'] = spine_name
	element_dict['loopback'] = loopback + str(loopbackcounter)
	loopbackcounter = loopbackcounter + 1
	element_dict['mgmt'] = mgmtnetwork + str(mgmtnetworkcounter)
	mgmtnetworkcounter = mgmtnetworkcounter + 1
	counter3 = 1

	for counter2 in range(1,no_leaf+1):
		for i in range(1,uplinks+1):
			if virtual == "no":
				spine_interface_name = "Ethernet"+str(counter3)+"/1"
			else:
				spine_interface_name = "Ethernet"+str(counter3)

			leaf_name = name + "leaf" + str(counter2)
			neighbor_dict = {}
			neighbor_dict['neighbor'] = leaf_name
			link = linknetwork + str(linksubnetcounter)
			neighborlink = linknetwork + str(linksubnetcounter+1)
			neighborint = str(linksubnetcounter+1)
			linksubnetcounter = linksubnetcounter + 2
			neighbor_dict['linknet'] = link
			neighbor_dict['neighbor_ip'] = neighborlink
			if virtual == "no":
				neighbor_dict['neighbor_interface'] = "Ethernet" + str(i + 48 + ((counter - 1) * uplinks)) + "/1"
			else:
				neighbor_dict['neighbor_interface'] = "Ethernet" + str(i + ((counter - 1) * uplinks))
			
			neighbor_dict['local_interface'] = spine_interface_name
			neighbor_dict['neighbor_int'] = neighborint
			
			neighbor_asn = spine_start_asn + counter2
			if neighbor_asn % 2 == 1:
				neighbor_dict['asn'] = neighbor_asn
			else:
				neighbor_dict['asn'] = neighbor_asn - 1 
			
			interface_list.append(neighbor_dict)
			counter3 = counter3 + 1
		
		element_dict['interfaces'] = interface_list
	
	DC.append(element_dict)

#
# Build the Leaf list of leaf switches in dictionary form.
#

#
# If leafs are organised as MLAG pairs, build accordingly.
#

if mlag == "yes":
	for counter in range (1,no_leaf+1):
		leaf_dict = {}
		leaf_dict['name'] = name + "leaf" + str(counter)
		leaf_dict['loopback'] = loopback + str(loopbackcounter)
		loopbackcounter = loopbackcounter +1
		if vxlanloopbackcounter % 2 == 1:
			mlaginterface = mlagnetwork + "0"
			mlagpeer = mlagnetwork + "1"
			leaf_dict['mlaginterface'] = mlaginterface
			leaf_dict['mlagpeer'] = mlagpeer
			leaf_dict['vxlan'] = vxlanloopback + str(vxlanloopbackcounter - 1)
		else:
			mlaginterface = mlagnetwork + "1"
			mlagpeer = mlagnetwork + "0"
			leaf_dict['mlaginterface'] = mlaginterface
			leaf_dict['mlagpeer'] = mlagpeer
			leaf_dict['vxlan'] = vxlanloopback + str(vxlanloopbackcounter)
		vxlanloopbackcounter = vxlanloopbackcounter +1
		leaf_dict['mgmt'] = mgmtnetwork + str(mgmtnetworkcounter)
		mgmtnetworkcounter = mgmtnetworkcounter + 1
		asn = spine_start_asn + counter
		if asn % 2 == 1:
			leaf_dict['asn'] = asn
		else:
			leaf_dict['asn'] = asn - 1 

		Leafs.append(leaf_dict)
#
# If leafs are organised standalone, build accordingly.
#

if mlag == "no":
	for counter in range (1,no_leaf+1):
		leaf_dict= {}
		leaf_dict['name'] = name + "leaf" + str(counter)
		leaf_dict['loopback'] = loopback + str(loopbackcounter)
		loopbackcounter = loopbackcounter +1
		leaf_dict['vxlan'] = vxlanloopback + str(vxlanloopbackcounter)
		vxlanloopbackcounter = vxlanloopbackcounter +1
		leaf_dict['mgmt'] = mgmtnetwork + str(mgmtnetworkcounter)
		mgmtnetworkcounter = mgmtnetworkcounter + 1
		asn = spine_start_asn + counter
		leaf_dict['asn'] = asn

		Leafs.append(leaf_dict)

#
# Build a VTEP list for the HER use case.
#

if deploymenttype == "her":
	vteplist = ""
	for leaf in Leafs:
		if leaf['vxlan'] not in vteplist:
			vteplist = vteplist + " " + leaf['vxlan']

#
# If debug is activated, dump the dictionaries that represents the network to stdout 
#

if debug != "no":
	print '%s' % ( json.dumps(DC, sort_keys=True, indent=4) )
	print '!'
	print '!'
	print '!'
	print '%s' % ( json.dumps(Leafs, sort_keys=True, indent=4) )

#
# Connect and authenticate with CVP server
#

if debug == "no":
	server = cvp.Cvp( host )
	server.authenticate( user , password )

#
# Create needed configlets for the new DC
#

Replacements = {
                "defaultgw": defaultgw,
                "syslog": syslogserver,
                "private": snmp_private,
                "public": snmp_public,
                "facility": log_facility,
                "primary_ntp": primary_ntp,
                "second_ntp": second_ntp               
                }

dc_base_config = Template("""
!
transceiver qsfp default-mode 4x10G
!
logging buffered 128000
logging console informational
logging format timestamp high-resolution
logging facility $facility
logging host $syslog
logging source-interface Management1
!
snmp-server community $private rw
snmp-server community $public ro
!
ntp server $primary_ntp prefer version 4
ntp server $second_ntp version 4
!
spanning-tree mode mstp
!
no aaa root
!
ip virtual-router mac-address 00:11:22:33:44:55
!
ip route 0.0.0.0/0 $defaultgw
ip routing
!
management api http-commands
   protocol http
   cors allowed-origin all
   no shutdown
""").safe_substitute(Replacements)

if deploymenttype == "evpn":
	Replacements = {
    				"dummy":"dummy"
                }

	arbgp_config = Template("""
!
service routing protocols model multi-agent 
!
""").safe_substitute(Replacements)
	dc_base_config = dc_base_config + arbgp_config

#
# Build standalone shared configlets for CVX use case
#

if deploymenttype == "cvx":
	Replacements = {
					"cvxserver": cvxserver
					}

	cvx_config = Template("""
!
management cvx
   no shutdown
   server host $cvxserver
!
""").safe_substitute(Replacements)

#
# Create Vxlan1 configlets based on CVX deployment type.
#

if deploymenttype == "cvx":
	Replacements = { "dummy": "dummy"
					}
	vxlan_leaf_config = Template("""
interface Vxlan1
   vxlan source-interface Loopback1
   vxlan udp-port 4789
   vxlan controller-client
!
""").safe_substitute(Replacements)

#
# Create Vxlan1 config based on HER deployment type.
#

if deploymenttype == "her":
	Replacements = { "dummy": "dummy",
					 "vteplist": vteplist
					}
	vxlan_leaf_config = Template("""
interface Vxlan1
   vxlan source-interface Loopback1
   vxlan udp-port 4789
   vxlan flood vtep$vteplist
!
""").safe_substitute(Replacements)

#
# Create Vxlan1 config based on EVPN deployment type.
#

if deploymenttype == "evpn":
	Replacements = { "dummy": "dummy"
					}
	vxlan_leaf_config = Template("""
interface Vxlan1
   vxlan source-interface Loopback1
   vxlan udp-port 4789
!
""").safe_substitute(Replacements)

# If debug is activated, only print config that should have gone into configlets,
# do not actually create configlets. If debug is not activated, create configlets
# and add them to CVP.
#

if debug == "no":
	dc_configlet = cvp.Configlet( dc_configlet_name , dc_base_config  )
	if configletExists( server , dc_configlet_name ):
		updateMyConfiglet( server , dc_configlet_name , dc_base_config )
		rebuild = 1
	else:
		server.addConfiglet( dc_configlet )
		configlet_list.append( dc_configlet )
		rebuild = 0

	vxlan_configlet_name = name + " Interface VXLAN1 base configuration"
	if rebuild == 1:
		updateMyConfiglet ( server , vxlan_configlet_name , vxlan_leaf_config )
	else:
		vxlan_configlet = cvp.Configlet( vxlan_configlet_name, vxlan_leaf_config )
		server.addConfiglet( vxlan_configlet )#

	if deploymenttype == "cvx":
		cvx_configlet_name = name + " CVX client configuration"
		cvx_configlet = cvp.Configlet( cvx_configlet_name, cvx_config )
		if configletExists( server , cvx_configlet_name ):
			updateMyConfiglet( server , cvx_configlet_name , cvx_config )
		else:
			server.addConfiglet( cvx_configlet )
			cvx_configlet_list.append( cvx_configlet )
else:
	print "Contents of configlet %s:" % ( dc_configlet_name )
	print "%s" % ( dc_base_config )
	print "!"
	print "!"
	print "!"
	vxlan_configlet_name = name + " Interface VXLAN1 base configuration"
	print "Contents of configlet %s:" % ( vxlan_configlet_name )
	print "%s" % ( vxlan_leaf_config )
	print "!"
	print "!"
	print "!"
	if deploymenttype == "cvx":
		cvx_configlet_name = name + " CVX client configuration"
		print "Contents of configlet %s:" % ( cvx_configlet_name )
		print "%s" % ( cvx_config )
		print "!"
		print "!"
		print "!"

#
# Build base config configlets for spines and add them to CVP.
# Start with config that is the same in all deployment types.
#

for spine_switch in DC:
	Replacements = {
					"hostname": spine_switch['name'],
					"loopaddress": spine_switch['loopback'],
					"mgmtaddress": spine_switch['mgmt'],
					"mgmtnetmask": mgmtnetmask
					}

	spine_base_config = Template("""
!
hostname $hostname
!
interface Loopback0
   ip address $loopaddress/32
!
interface Management1
   ip address $mgmtaddress/$mgmtnetmask
""").safe_substitute(Replacements)
	
	for interface in spine_switch['interfaces']:
		Replacements = {
						"local_interface": interface['local_interface'] ,
						"description": interface['neighbor'],
						"linknet": interface['linknet']
						}
		add_to_spine_config = Template("""
!
interface $local_interface
   description $description
   no switchport
   ip address $linknet/31
!""").safe_substitute(Replacements)

		spine_base_config = spine_base_config + add_to_spine_config

	if debug == "no":
		spine_configlet_name = spine_switch['name'] + " configuration"
		if rebuild == 1:
			updateMyConfiglet( server , spine_configlet_name , spine_base_config )
		else:
			spine_configlet = cvp.Configlet( spine_configlet_name , spine_base_config )
			server.addConfiglet( spine_configlet )
	else:
		spine_configlet_name = spine_switch['name'] + " configuration"
		print "Contents of configlet %s:" % ( spine_configlet_name )
		print "%s" % ( spine_base_config )
		print "!"
		print "!"
		print "!"
#
# Create configlets unique for spine in cvx and her deployment types
# and add them to CVP.
#

	if deploymenttype == "her" or deploymenttype == "cvx":
		Replacements = {
						"routerid": spine_switch['loopback'],
						"linknet": linknetwork + "0/24",
						"uplinks": uplinks,
						"asn": spine_start_asn,
						"max_routes": max_routes,
						"max_ecmp": max_ecmp
						}

		spine_bgp_config = Template("""
router bgp $asn
   router-id $routerid
   maximum-paths $max_ecmp ecmp $max_ecmp
   neighbor leafs peer-group
   neighbor leafs maximum-routes $max_routes 
   redistribute connected""").safe_substitute(Replacements)

		for interface in spine_switch['interfaces']:
			Replacements = {
							"neighbor": interface['neighbor_ip'],
							"asn": interface['asn']
							}
			add_to_sping_bgp_config = Template("""
   neighbor $neighbor peer-group leafs
   neighbor $neighbor remote-as $asn""").safe_substitute(Replacements)
			spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config
#
# Create config unique for spine in evpn deployment type
#

	if deploymenttype == "evpn":
		Replacements = {
						"routerid": spine_switch['loopback'],
						"linknet": linknetwork,
						"uplinks": uplinks,
						"asn": spine_start_asn,
						"max_routes": max_routes,
						"max_evpn_routes": max_evpn_routes,
						"max_ecmp": max_ecmp
						}

		spine_bgp_config = Template("""
router bgp $asn
   router-id $routerid
   maximum-paths $max_ecmp ecmp $max_ecmp
   neighbor leafs peer-group
   neighbor leafs maximum-routes $max_routes
   neighbor EVPN peer-group
   neighbor EVPN fall-over bfd
   neighbor EVPN maximum-routes $max_evpn_routes
   neighbor EVPN next-hop-unchanged
   neighbor EVPN update-source Loopback0
   neighbor EVPN ebgp-multihop 4
   neighbor EVPN send-community extended
   redistribute connected""").safe_substitute(Replacements)

		for interface in spine_switch['interfaces']:
			Replacements = {
							"neighbor": interface['neighbor_ip'],
							"asn": interface['asn']
							}
			add_to_sping_bgp_config = Template("""
   neighbor $neighbor peer-group leafs
   neighbor $neighbor remote-as $asn""").safe_substitute(Replacements)
			spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config

		for leaf in Leafs:
			Replacements = {
							"neighbor": leaf['loopback'],
							"asn": leaf['asn']
							}
			add_to_sping_bgp_config = Template("""
   neighbor $neighbor peer-group EVPN
   neighbor $neighbor remote-as $asn""").safe_substitute(Replacements)
			spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config

		add_to_sping_bgp_config = ("""
   address-family evpn""")
		spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config

		for leaf in Leafs:
			Replacements = {
							"neighbor": leaf['loopback'],
							"asn": leaf['asn']
							}
			add_to_sping_bgp_config = Template("""
      neighbor $neighbor activate""").safe_substitute(Replacements)
			spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config

		add_to_sping_bgp_config = ("""
   address-family ipv4""")
		spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config

		for leaf in Leafs:
			Replacements = {
							"neighbor": leaf['loopback'],
							"asn": leaf['asn']
							}
			add_to_sping_bgp_config = Template("""
      no neighbor $neighbor activate""").safe_substitute(Replacements)
			spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config


	if debug == "no":
		spine_bgp_configlet_name = spine_switch['name'] + " BGP configuration"
		if rebuild == 1:
			updateMyConfiglet( server , spine_bgp_configlet_name , spine_bgp_config )
		else:
			spine_bgp_configlet = cvp.Configlet( spine_bgp_configlet_name , spine_bgp_config )
			server.addConfiglet( spine_bgp_configlet )
	else:
		spine_bgp_configlet_name = spine_switch['name'] + " BGP configuration"
		print "Contents of configlet %s:" % ( spine_bgp_configlet_name )
		print "%s" % ( spine_bgp_config )
		print "!"
		print "!"
		print "!"



# Build base config configlets for leafs and add them to CVP.
# Start with config that is the same in all deployment types.
#

for leaf in Leafs:
	if deploymenttype == "her":
		Replacements = {
						"hostname": leaf['name'],
						"loopback": leaf['loopback'],
						"vxlan": leaf['vxlan'],
						"mgmtip": leaf['mgmt'],
						"mgmtnetmask": mgmtnetmask
						}
		leaf_config = Template("""
!
hostname $hostname
!
interface Loopback0
   ip address $loopback/32
!
interface Loopback1
   ip address $vxlan/32
!
interface Management1
   ip address $mgmtip/$mgmtnetmask
!
""").safe_substitute(Replacements)

	if deploymenttype == "cvx":
		Replacements = {
						"hostname": leaf['name'],
						"loopback": leaf['loopback'],
						"vxlan": leaf['vxlan'],
						"mgmtip": leaf['mgmt'],
						"mgmtnetmask": mgmtnetmask
						}
		leaf_config = Template("""
!
hostname $hostname
!
interface Loopback0
   ip address $loopback/32
!
interface Loopback1
   ip address $vxlan/32
!
interface Management1
   ip address $mgmtip/$mgmtnetmask
!
""").safe_substitute(Replacements)


	if deploymenttype == "evpn":
		Replacements = {
						"hostname": leaf['name'],
						"loopback": leaf['loopback'],
						"mgmtip": leaf['mgmt'],
						"mgmtnetmask": mgmtnetmask,
						"vxlan": leaf['vxlan']
						}
		leaf_config = Template("""
!
hostname $hostname
!
interface Loopback0
   ip address $loopback/32
!
interface Loopback1
   ip address $vxlan/32
!
interface Management1
   ip address $mgmtip/$mgmtnetmask
!
""").safe_substitute(Replacements)		

#
# Create MLAG config when leafs are organised as MLAG pairs.
#

	if mlag == "yes":
		mlagtrunkinterfacelist = mlagtrunkinterfaces.split(',')
		mlagtrunkinterface1 = mlagtrunkinterfacelist[0]
		mlagtrunkinterface2 = mlagtrunkinterfacelist[1]
		Replacements = { "mlaginterface": leaf['mlaginterface'],
						 "mlagpeer": leaf['mlagpeer'],
						 "mlagtrunkinterface1": mlagtrunkinterface1,
						 "mlagtrunkinterface2": mlagtrunkinterface2
						}
		mlag_add_to_leaf_config = Template("""
!
vlan 4094
   name MLAGPEER
   trunk group mlagpeer
!
no spanning-tree vlan 4094
!
interface port-channel 2000
   switchport trunk group mlagpeer
   switchport mode trunk
!
interface $mlagtrunkinterface1
   channel-group 2000 mode active
!
interface $mlagtrunkinterface2
   channel-group 2000 mode active
!
interface Vlan4094
   ip address $mlaginterface/31
!
mlag
   local-interface vlan 4094
   peer-address $mlagpeer
   peer-link port-channel 2000
   domain-id MLAG
!
""").safe_substitute(Replacements)
		leaf_config = leaf_config + mlag_add_to_leaf_config

#
# Create BGP configlets for CVX and HER deployment types.
# I.e. underlay BGP configlets.
#

	if (deploymenttype == "her" or deploymenttype == "cvx") and mlag == "no":
		Replacements = {
						"routerid": leaf['loopback'],
						"uplinks": uplinks,
						"asn": leaf['asn'],
						"spine_asn": spine_start_asn,
						"max_ecmp": max_ecmp,
						"max_routes": max_routes
						}
		leaf_bgp_config = Template("""
router bgp $asn
   router-id $routerid
   maximum-paths $max_ecmp ecmp $max_ecmp
   neighbor spines peer-group
   neighbor spines remote-as $spine_asn
   neighbor spines maximum-routes $max_routes
   redistribute connected""").safe_substitute(Replacements)

	if (deploymenttype == "her" or deploymenttype == "cvx") and mlag == "yes":
		Replacements = {
						"routerid": leaf['loopback'],
						"mlagpeer": leaf['mlagpeer'],
						"uplinks": uplinks,
						"asn": leaf['asn'],
						"spine_asn": spine_start_asn,
						"max_ecmp": max_ecmp,
						"max_routes": max_routes

						}
		leaf_bgp_config = Template("""
router bgp $asn
   router-id $routerid
   maximum-paths $max_ecmp ecmp $max_ecmp
   neighbor spines peer-group
   neighbor spines remote-as $spine_asn
   neighbor spines maximum-routes $max_routes
   neighbor mlag-neighbor peer-group
   neighbor mlag-neighbor remote-as $asn
   neighbor mlag-neighbor update-source vlan4094
   neighbor $mlagpeer peer-group mlag-neighbor
   redistribute connected""").safe_substitute(Replacements)

#
# Create BGP configlets for EVPN deployment types.
# I.e. underlay and EVPN overlay BGP configlets.
#

	if deploymenttype ==  "evpn" and mlag == "no":
		Replacements = {
						"asn": leaf['asn'] ,
						"routerid": leaf['loopback'],
						"uplinks": uplinks,
						"spine_asn": spine_start_asn,
						"max_ecmp": max_ecmp,
						"max_routes": max_routes,
						"max_evpn_routes": max_evpn_routes
						}
		leaf_bgp_config = Template("""
router bgp $asn
   router-id $routerid
   maximum-paths $max_ecmp ecmp $max_ecmp
   neighbor EVPN peer-group
   neighbor EVPN update-source Loopback0
   neighbor EVPN ebgp-multihop 4
   neighbor EVPN send-community extended
   neighbor EVPN fall-over bfd
   neighbor EVPN maximum-routes $max_routes 
   neighbor spines peer-group
   neighbor spines remote-as $spine_asn
   neighbor spines maximum-routes $max_evpn_routes""").safe_substitute(Replacements)

	if deploymenttype ==  "evpn" and mlag == "yes":
		Replacements = {
						"asn": leaf['asn'] ,
						"routerid": leaf['loopback'],
						"mlagpeer": leaf['mlagpeer'],
						"uplinks": uplinks,
						"spine_asn": spine_start_asn,
						"max_ecmp": max_ecmp,
						"max_routes": max_routes,
						"max_evpn_routes": max_evpn_routes
						}
		leaf_bgp_config = Template("""
router bgp $asn
   router-id $routerid
   maximum-paths $max_ecmp ecmp $max_ecmp
   neighbor EVPN peer-group
   neighbor EVPN update-source Loopback0
   neighbor EVPN ebgp-multihop 4
   neighbor EVPN send-community extended
   neighbor EVPN fall-over bfd
   neighbor EVPN maximum-routes $max_evpn_routes
   neighbor mlag-neighbor peer-group
   neighbor mlag-neighbor remote-as $asn
   neighbor mlag-neighbor update-source vlan4094
   neighbor $mlagpeer peer-group mlag-neighbor
   neighbor spines peer-group
   neighbor spines remote-as $spine_asn
   neighbor spines maximum-routes $max_routes""").safe_substitute(Replacements)

#
# Build interface configlets for each leaf. Add BGP neighbor configuration to
# BGP configlets.
#

	for spine_switch in DC:
		for interface in spine_switch['interfaces']:
			if interface['neighbor'] == leaf['name']:
				Replacements = {
								"interface": interface['neighbor_interface'],
								"description": spine_switch['name'],
								"neighbor_ip": interface['neighbor_ip']
								}
				add_to_leaf_config = Template("""
!
interface $interface
   description $description
   no switchport
   ip address $neighbor_ip/31
!
""").safe_substitute(Replacements)
				leaf_config = leaf_config + add_to_leaf_config

				if deploymenttype == "her" or deploymenttype == "cvx":
					Replacements = {
									"neighborip": linknetwork + str(int(interface['neighbor_int']) -1)
									}
					add_to_leaf_bgp_config = Template("""
   neighbor $neighborip peer-group spines""").safe_substitute(Replacements)
					leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

				if deploymenttype == "evpn":
					Replacements = {
									"neighborip": linknetwork + str(int(interface['neighbor_int']) -1)
					}
					add_to_leaf_bgp_config = Template("""
   neighbor $neighborip peer-group spines""").safe_substitute(Replacements)
					leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config
					
	if deploymenttype == "evpn":
		for evpnleaf in DC:
			Replacements = {
							"loopback": evpnleaf['loopback'],
							"asn": spine_start_asn
							}
			add_to_leaf_bgp_config = Template("""
   neighbor $loopback peer-group EVPN
   neighbor $loopback remote-as $asn""").safe_substitute(Replacements)
			leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
	
		add_to_leaf_bgp_config = """
   address-family evpn"""
		leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
		for evpnleaf in DC:
			Replacements = {
							"loopback": evpnleaf['loopback'],
							"asn": spine_start_asn
							}
			add_to_leaf_bgp_config = Template("""
      neighbor $loopback activate""").safe_substitute(Replacements)
			leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
		add_to_leaf_bgp_config = """
   address-family ipv4"""
		leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config
		for evpnleaf in DC:
			Replacements = {
							"loopback": evpnleaf['loopback'],
							"asn": spine_start_asn
							}
			add_to_leaf_bgp_config = Template("""
      no neighbor $loopback activate""").safe_substitute(Replacements)
			leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
		add_to_leaf_bgp_config = """
      redistribute connected"""
		leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

#
# If debug is activated, only print config that should have gone into configlets,
# do not actually create configlets. If debug is not activated, create configlets
# and add them to CVP.
#

	if debug == "no":
		leaf_configlet_name = leaf['name'] + " configuration"
		if rebuild == 1:
			updateMyConfiglet ( server , leaf_configlet_name , leaf_config )
		else:
			leaf_configlet = cvp.Configlet( leaf_configlet_name , leaf_config )
			server.addConfiglet( leaf_configlet )
		
		leaf_bgp_configlet_name = leaf['name'] + " bgp configuration"
		if rebuild == 1:
			updateMyConfiglet ( server , leaf_bgp_configlet_name , leaf_bgp_config )
		else:
			leaf_bgp_configlet = cvp.Configlet( leaf_bgp_configlet_name , leaf_bgp_config )
			server.addConfiglet( leaf_bgp_configlet )		
	else:
		leaf_configlet_name = leaf['name'] + " configuration"
		print "Contents of configlet %s:" % ( leaf_configlet_name )
		print "%s" % ( leaf_config )
		print "!"  
		print "!"
		print "!"
		leaf_bgp_configlet_name = leaf['name'] + " bgp configuration"
		print "Contents of configlet %s:" % ( leaf_bgp_configlet_name )
		print "%s" % ( leaf_bgp_config )
		print "!"
		print "!"
		print "!"



#
# If debug is not activated, create Container structure for new DC
#

if debug == "no":
	if rebuild == 0:
		my_dc_container = cvp.Container( name, parentName )
		server.addContainer( my_dc_container )
		server.mapConfigletToContainer( my_dc_container , configlet_list )
		if deploymenttype == "cvx":
			server.mapConfigletToContainer( my_dc_container , cvx_configlet_list )

		my_leaf_container = cvp.Container( my_leaf_container_name , name )
		server.addContainer( my_leaf_container )
		leaf_configlet_list.append( vxlan_configlet )
		server.mapConfigletToContainer( my_leaf_container , leaf_configlet_list )

		my_spine_container = cvp.Container( my_spine_container_name , name )
		server.addContainer( my_spine_container )
