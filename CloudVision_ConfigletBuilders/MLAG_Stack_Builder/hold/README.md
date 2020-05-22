MLAG Stack Configlet Builder

The goal of this Configlet Builder is to automate the MLAG Stack in a campus environment
where there is no out-of-band management.

An explanation of how to use this builder can be found at:
https://eos.arista.com/?p=25059&preview=true

Assumptions for script
* Default gateway for Management is .1
* One uplink per switch
* Multiple downlinks per switch
* MLAG Stack Pair hostnames should end in 1 or 2, A or B, LEFT or RIGHT depending on MLAG peer position.
* MLAG downlinks to member switches are at 25G
