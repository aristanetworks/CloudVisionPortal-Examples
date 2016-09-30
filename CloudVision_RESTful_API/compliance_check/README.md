# compliancecheck
Script to perform a periodic compliance check of a CVP server and report devices which are out of compliance.

This script utilizes the daemon module located at https://github.com/serverdensity/python-daemon/blob/master/daemon.py to create a 
daemon to validate the configuration compliance of Arista switches managed by Cloud Vision Portal.  

Aside from the daemon module, you'll need to install the cvp, cvpServices, and requests_2_4_0 modules, all of which can be downloaded
from the cvp server from the /cvp/tools directory

usage:compliancecheck.py (start|stop|restart) -i <interval seconds> -u <cvp username> -p <cvp password> --mail --syslog --print
