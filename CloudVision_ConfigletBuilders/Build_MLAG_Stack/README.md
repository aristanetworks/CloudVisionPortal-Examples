MLAG Stack Configlet Builder

The goal of this Configlet Builder is to automate the MLAG Stack in a campus environment
where there is no out-of-band management.

An explanation of how to use this builder can be found at:
https://eos.arista.com/?p=25840&preview=true

Assumptions for script
* Minimum EOS release is 4.23 for MLAG Stack Peers and Members
* CVP version 2019.x or greater
* The default gateway for the management VLAN is .1
* Multiple downlinks per switch allow any number of MLAG Stack Member ports.
* MLAG Stack Peer hostnames should end in 1 or 2, A or B, LEFT or RIGHT depending on MLAG peer position.  A set of MLAG Peers would normally have a notation like this to distinguish between the Peers.
* MLAG downlinks to member switches are assumed to be 25G since that is the greatest number of higher speed links on the POE switch.
* MLAG VLAN is assumed to be 4094, and the Management VLAN cannot be 4094.
