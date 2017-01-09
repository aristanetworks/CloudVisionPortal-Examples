#!/usr/bin/python
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

''' Example of how to access interface information via the CloudVision
    Analytics Engine on the CloudVision Platform (CVP).

    Usage:
    python cvp_port_inventory.py

    Notes:
    1) The output is not lined up well. The goal of this script is to give
       an example of how to get the information from the CloudVision Analytics
       Engine.
    2) There is a long delay between printing the header and the first line
       of data. The delay is the result of collecting and processing the
       VLAN information from the switch.
    3) There is a delay between printing each switch entry. This is because
       we are collecting the LLDP information for the port.
    4) Sometimes a MAC address will be printed as '(Invalid MAC address)'.
       This error occurs because the mac address is packed into a string
       and then converted to a unicode string for transmission. The unicode
       string being received contains the unicode replacement character \ufffd
       in it which causes the unpack to fail. Here is an example value
       of a packed MAC address unicode string that triggers this
       error: u'\x00PV\ufffd\ufffd\ufffd'
    5) The script lacks extensive error checking when walking paths to
       data.
'''

import itertools
from netaddr import IPAddress
import re
import socket
import struct

import requests

from cvp_client_errors import CvpApiError, CvpRequestError

# ********* Customer Tunables **********
# Address of CVP Node
CVP_HOST = 'cvpdev'
# Timeout for RESTful API Requests
TIMEOUT = 60
# Delimiter string to use between fields in output
DELIM = ' ^ '

# Script Variables
AERIS = '/aeris/v1/rest'
HEADERS = {'Accept' : 'application/json',
           'Content-Type' : 'application/json'}

# CloudVision Analytics Engine Sysdb path to ARP table
PATH_ARP = 'Smash/arp/status/arpEntry'
# CloudVision Analytics Engine Sysdb path to l2 mac table
PATH_MAC = 'Smash/bridging/status/smashFdbStatus'
# CloudVision Analytics Engine Sysdb path to switch hostname
PATH_HOSTNAME_CONFIG = 'Sysdb/sys/net/config'
# CloudVision Analytics Engine Sysdb path to Interface Status.
PATH_INTF_STATUS = 'Sysdb/interface/status/eth/phy/slice/1/intfStatus'
# CloudVision Analytics Engine Sysdb path to Interface Configuration.
PATH_INTF_CONFIG = 'Sysdb/interface/config/eth/phy/slice/1/intfConfig'
# CloudVision Analytics Engine Sysdb path to Interface IP address
PATH_INTF_IPADDR = 'Sysdb/ip/config/ipIntfConfig'
# CloudVision Analytics Engine Sysdb path to LLDP Info
PATH_LLDP = 'Sysdb/l2discovery/lldp/status/all/portStatus'
# CloudVision Analytics Engine Sysdb path to Vlan Info
PATH_VLANS = 'Sysdb/bridging/config/vlanConfig'

def is_good_response(response, prefix):
    ''' Check for errors in a response from a GET or POST request.
        The response argument contains a response object from a GET or POST
        request.  The prefix argument contains the prefix to put into the
        error message.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    if not response.ok:
        msg = '%s: Request Error: %s' % (prefix, response.reason)
        print msg
        raise CvpRequestError(msg)

    if 'errorCode' in response.text:
        joutput = response.json()
        if 'errorMessage' in joutput:
            err_msg = joutput['errorMessage']
        else:
            err_msg = joutput['errorCode']
        msg = ('%s: Request Error: %s' % (prefix, err_msg))
        print msg
        raise CvpApiError(msg)

def get(session, url):
    ''' Make a GET request to CloudVision Analytics Engine.

        Args:
            session (obj): A request session object.
            url (str): URL to use for the request.

        Returns:
            The JSON response.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    # Possible Exceptions from this call:
    # ConnectionError, HTTPError, ReadTimeout, TooManyRedirects, Timeout
    return session.get(url, headers=HEADERS, timeout=TIMEOUT)

def get_switch_list(session):
    ''' Get the list of switches that the CloudVision Analytics Engine is
        serving data for.  Note that the CloudVision Analytics Engine returns a
        historical list. If data was collected from a switch at some point in
        time and then removed or renamed, then the CloudVision Analytics Engine
        will still return the switch name if the CloudVision Analytics Engine
        has data stored for that switch.

        Args:
            session (obj): A request session object.

        Returns:
            The list of switch serial numbers.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''

    # URL to get list of switches
    url = 'http://%s%s' % (CVP_HOST, AERIS)

    response = get(session, url)
    is_good_response(response, 'GET')

    # response.json() contains the dict of the response. The keys
    # to the dict are the names of the switches.
    return response.json().keys()

def get_switch_hostname(session, switch):
    ''' Get the host name for a switch given the device id (serial number).

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.

        Returns:
            The host name string for the switch.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''

    # URL to get switch host name
    url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_HOSTNAME_CONFIG)

    response = get(session, url)
    is_good_response(response, 'GET')

    # response.json() contains the dict of the response.
    try:
        hostname = response.json()['startState']['updates']['hostname']['_value']
    except KeyError:
        hostname = 'UNKNOWN'
    return hostname

def get_interface_list(session, switch):
    ''' Get the list of interfaces for the give switch name.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.

        Returns:
            The list of interface names.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_INTF_CONFIG)

    response = get(session, url)
    is_good_response(response, 'GET')

    # response.json() contains the dict of the response. The keys
    # to the updates dict are the names of the interfaces.
    return response.json()['startState']['updates'].keys()

def get_vlan_config(session, switch):
    ''' Get the vlan configurations for the given switch.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.

        Returns:
            A dict keyed by interface name containing a list of vlans
            for that interface.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_VLANS)

    response = get(session, url)
    is_good_response(response, 'GET')

    # response.json() contains the dict of the response. The keys
    # to the updates dict are the configuration fields associated with the
    # interface.
    vlan_info = {}
    vlans = response.json()['startState']['updates']
    for vlan in vlans:
        # Skip vlan 1
        if vlan == '1':
            continue
        # Get the vlan config
        ptr = vlans[vlan]['_value']['_ptr']
        url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, ptr)
        response = get(session, url)
        is_good_response(response, 'GET')
        vlan_cfg = response.json()['startState']['updates']
        # Get the list of interfaces for the vlan
        try:
            ptr = vlan_cfg['intf']['_value']['_ptr']
            url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, ptr)
            response = get(session, url)
            is_good_response(response, 'GET')
            interfaces = response.json()['startState']['updates']
            vlan_info[vlan] = interfaces.keys()
        except:
            # No interfaces assigned to the vlan
            pass

    # The vlan info is currently indexed by vlan. We want to re-index the
    # info by interface.
    intf_info = {}
    for vlan in vlan_info:
        interfaces = vlan_info[vlan]
        for intf in interfaces:
            if intf in intf_info:
                intf_info[intf].append(vlan)
            else:
                intf_info[intf] = [vlan]
    return intf_info

def get_interface_config(session, switch, interface):
    ''' Get the interface configuration for the given interface on the given
        switch.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.
            interface (str): The name of the interface.

        Returns:
            A dict containing the interface configuration.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    url = 'http://%s%s/%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_INTF_CONFIG,
                                    interface)

    response = get(session, url)
    is_good_response(response, 'GET')

    # response.json() contains the dict of the response. The keys
    # to the updates dict are the configuration fields associated with the
    # interface.
    return response.json()['startState']['updates']

def get_interface_status(session, switch, interface):
    ''' Get the interface status for the given interface on the given switch.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.
            interface (str): The name of the interface.

        Returns:
            A dict containing the interface status.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    url = 'http://%s%s/%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_INTF_STATUS,
                                    interface)

    response = get(session, url)
    is_good_response(response, 'GET')

    # response.json() contains the dict of the response. The keys
    # to the updates dict are the status fields associated with the interface.
    return response.json()['startState']['updates']

def map_link_status(link_status):
    ''' Map the link status to connected/notconnect.

        Args:
            link_status (str): The link status value.

        Returns:
            String containing the link status.
    '''
    lmap = {'linkUp' : 'connected',
            'linkDown' : 'notconnect',
            'linkUnknown' : 'unknown'}
    if link_status in lmap.keys():
        return lmap[link_status]
    return 'unknown'

def get_interface_ip_addr(session, switch, interface):
    ''' Get the interface IP address for the given interface on the given
        switch. Currently not used, left as an extra example.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.
            interface (str): The name of the interface.

        Returns:
            A string containing the IP address.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    url = ('http://%s%s/%s/%s/%s' %
           (CVP_HOST, AERIS, switch, PATH_INTF_IPADDR, interface))

    response = get(session, url)
    is_good_response(response, 'GET')

    data = response.json()['startState']['updates']
    try:
        addr = data['addrWithMask']['_value']['address']['value']
        ip_addr = IPAddress(addr)
        return str(ip_addr)
    except:
        # No address assigned to the interface. Just return spaces.
        return ' ' * 15

def get_interface_lldp(session, switch):
    ''' Get the Neighbor Device ID and Neighbor Port ID for all interfaces
        on the given switch.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.

        Returns:
            A dict keyed by the Interface Name with a value consisting of
            an array of dicts containing the Neighbor Device ID and Neighbor
            Port ID. Similar to the output from 'show lldp neighbor'. Returns
            an empty array if there are no entries found.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_LLDP)
    response = get(session, url)
    is_good_response(response, 'GET')

    intf_data = response.json()['startState']['updates']
    info = {}
    for interface in intf_data:
        # Get the path to the data
        ptr = intf_data[interface]['_value']['_ptr']
        url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, ptr)
        response = get(session, url)
        is_good_response(response, 'GET')
        data = response.json()['startState']['updates']
        if 'remoteSystemByMsap' in data:
            ptr = data['remoteSystemByMsap']['_value']['_ptr']
            url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, ptr)
            response = get(session, url)
            is_good_response(response, 'GET')
            entries = response.json()['startState']['updates']
            if entries != {}:
                # Loop over the keys looking for the port ID with a
                # portIdSubtype of pidInterfaceName or pidMacAddress and
                # return that for the port ID.
                port_id = 'UNKNOWN'
                for key in entries.keys():
                    subtype = entries[key]['_key']['portIdentifier']['portIdSubtype']['Name']
                    port_id = entries[key]['_key']['portIdentifier']['portId']['value']
                    if subtype == 'pidMacAddress':
                        port_id = format_mac_addr(port_id)

                    # Search for the neighbor device ID
                    ptr = entries[key]['_value']['_ptr']
                    url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, ptr)
                    response = get(session, url)
                    is_good_response(response, 'GET')
                    data = response.json()['startState']['updates']

                    # Get Neighbor Device Id
                    if 'sysName' not in data:
                        # If the sys_name is not in the current entry then
                        # get the sys_name from the remoteSystem entry
                        ptr = data['remoteSystem']['_value']['_ptr'] + '/1'
                        url = ('http://%s%s/%s/%s' %
                               (CVP_HOST, AERIS, switch, ptr))
                        response = get(session, url)
                        is_good_response(response, 'GET')
                        data = response.json()['startState']['updates']

                    sys_name = data['sysName']['_value']['value']

                    entry = {'dev_id': sys_name, 'port_id': port_id}
                    if interface in info:
                        info[interface].append(entry)
                    else:
                        info[interface] = [entry]

    return info

def get_interface_arp(session, switch):
    ''' Get the IP address from the ARP table and lookup the hostname for it
        for all interfaces on the switch.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.

        Returns:
            A dict keyed by the Interface Name with a value consisting of
            an array of dicts containing the IP address and the MAC address.
            The IP address maybe empty. Returns an empty array if there are
            no entries found.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    # Get the ARP info
    url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_ARP)
    response = get(session, url)
    is_good_response(response, 'GET')

    # Process the ARP table and add the entries.
    data = response.json()['startState']['updates']
    info = {}
    for arp_entry in data:
        ip_addr = data[arp_entry]['_key']['addr']
        interface = data[arp_entry]['_key']['intfId']
        mac_addr = data[arp_entry]['_value']['ethAddr']

        if ip_addr:
            try:
                (name, _, _) = socket.gethostbyaddr(ip_addr)
            except:
                # Could look up MAC vendor ID: https://macvendors.co/api
                name = ip_addr
        else:
            name = ' ' * 15

        entry = {'dev_id': name, 'port_id': mac_addr}
        if interface in info:
            info[interface].append(entry)
        else:
            info[interface] = [entry]
    return info

def get_interface_mac(session, switch):
    ''' Get the MACs from the MAC table for all interfaces on the switch.

        Args:
            session (obj): A request session object.
            switch (str): The device id (serial number) of the switch.

        Returns:
            A dict keyed by the Interface Name with a value consisting of
            an array of dicts containing empty IP address and the MAC address.
            Returns an empty array if there are no entries found.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    # Get the MAC info
    url = 'http://%s%s/%s/%s' % (CVP_HOST, AERIS, switch, PATH_MAC)
    response = get(session, url)
    is_good_response(response, 'GET')

    # Process the ARP table and add the entries.
    data = response.json()['startState']['updates']
    info = {}
    for mac_entry in data:
        mac_addr = data[mac_entry]['_key']['addr']
        interface = data[mac_entry]['_value']['intf']
        entry_type = data[mac_entry]['_value']['entryType']['Name']
        if entry_type != 'learnedDynamicMac':
            continue

        entry = {'dev_id': ' ' * 15, 'port_id': mac_addr}
        if interface in info:
            info[interface].append(entry)
        else:
            info[interface] = [entry]
    return info


def get_interface_remote_info(arp, mac, lldp, interface):
    ''' Get the Remote Device ID and Remote Port ID for the specified
        interface on the given switch. First try to get the information
        via LLDP ('show lldp neighbor'), if not available, get the info
        from the ARP table. If nothing found then return spaces for the
        entries.

        Args:
            arp (dict): The ARP table for the switch.
            mac (dict): The MAC table for the switch
            lldp (dict): The LLDP info info for the switch.
            interface (str): The name of the interface.

        Returns:
            An array of dicts containing the Remote Device ID and Remote Port
            ID for the interface.

        Raises:
            CvpApiError: A CvpApiError is raised if there was a JSON error.
            CvpRequestError: A CvpRequestError is raised if the request
                is not properly constructed.
    '''
    # Check the LLDP info and return the entry if it exists
    if interface in lldp:
        return lldp[interface]

    # Check the ARP info and return the entry if it exists
    if interface in arp:
        return arp[interface]

    # Check the MAC info and return the entry if it exists
    if interface in mac:
        return mac[interface]

    # Nothing, return a blank entry
    return [{'dev_id': ' ' * 15, 'port_id': ' ' * 15}]

def format_mac_addr(addr):
    ''' Format a packed MAC address to a string.

        Args:
            addr (str): A dict containing the MAC address in 3 decimal words.

        Returns:
            The MAC address in three groups of four hexadecimal digits
            separated by dots.
    '''
    # Sanity check on the address
    assert len(addr) == 6

    # Convert the unicode string to hex
    try:
        addr_str = '%04x.%04x.%04x' % struct.unpack('>HHH', addr)
    except struct.error:
        # Hit this error because the mac address is packed into a string
        # and then converted to a unicode string for transmission. The unicode
        # string being received as the unicode replacement character \ufffd
        # in it which causes the unpack to fail. Here is an example value
        # of a packed Mac address unicode string that triggers this
        # error: u'\x00PV\ufffd\ufffd\ufffd'
        addr_str = '(Invalid MAC address)'
    return addr_str

INTF_NAME_RE = re.compile(r'([^0-9/]+)(?:(\d+)/?)?(?:(\d+)/?)?(?:(\d+))?(?:\.(\d+))?$')

def parse_interface(name):
    ''' Parse an interface name for the purpose of comparing.

        Args:
            name (str): The interface name.

        Returns:
            List containing the components of the interface name.
    '''
    # Interface name is comprised of one or more alphabet chars followed
    # by digits and maybe a slash and maybe more digits.
    match = INTF_NAME_RE.match(name)
    basename = match.group(1)
    stack = int(match.group(2) or '0')
    mod = int(match.group(3) or '0')
    port = int(match.group(4) or '0')
    sub = int(match.group(5) or '0')
    return (basename, stack, mod, port, sub)

def compare_interfaces(name1, name2):
    ''' Compare interface names for the purpose of sorting.

        Args:
            namel (str): The first interface name.
            name2 (str): The second interface name.

        Returns:
            Comparing name1 to name2, return negative value for less-than,
            return zero if they are equal, or return a positive value for
            greater-than.
    '''
    pname1 = parse_interface(name1)
    pname2 = parse_interface(name2)
    return cmp(pname1, pname2)

def main():
    ''' Collect the port inventory information and print it out.
    '''
    # Using Session is currently not required but the CloudVision Analytics
    # Engine will require credentials when it goes into production.
    session = requests.Session()

    # Get a list of switches by serial number (CVP device ID)
    switches_by_sn = get_switch_list(session)

    # Print out the heading
    print '    Switch                                                 Remote           Remote'
    print '     Name        Port     Status  Speed         Duplex     IP Addr         MAC Addr         Vlans  Description'
    print '--------------------------------------------------------------------------------------------------------------'
    # Loop over each switch
    for sw_sn in switches_by_sn:
        hostname = get_switch_hostname(session, sw_sn)
        # Get the vlan information for the switch indexed by interface name
        vlan_info = get_vlan_config(session, sw_sn)
        interfaces = get_interface_list(session, sw_sn)
        lldp = get_interface_lldp(session, sw_sn)
        arp = get_interface_arp(session, sw_sn)
        macs = get_interface_mac(session, sw_sn)
        for interface in sorted(interfaces, cmp=compare_interfaces):
            config = get_interface_config(session, sw_sn, interface)
            status = get_interface_status(session, sw_sn, interface)
            remote = get_interface_remote_info(arp, macs, lldp, interface)
            # Get the first remote entry
            dev_id = remote[0]['dev_id']
            port_id = remote[0]['port_id']
            pname = status['deviceName']['_value']
            lstatus = map_link_status(status['linkStatus']['_value']['Name'])
            speed = status['speed']['_value']['Name']
            duplex = status['duplex']['_value']['Name']
            desc = config['description']['_value']
            if interface in vlan_info:
                vlan = ','.join(vlan_info[interface])
            else:
                vlan = '    '
            print DELIM.join((hostname, pname, lstatus, speed, duplex, dev_id,
                              port_id, vlan, desc))
            # process subsequent remote entries
            for entry in itertools.islice(remote, 1, None):
                print 'Remote Continuation: ' + \
                    DELIM.join((entry['dev_id'], entry['port_id']))

if __name__ == '__main__':
    main()
