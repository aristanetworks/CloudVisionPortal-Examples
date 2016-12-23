# Arista CloudVision&reg; Portal Configlet Builder Examples
Configlet builder which configures and enables MLAG on switches previously configured with EX6_BasicBuilder and manual BGP configuration.  EX7_BuildMLAG builder requires ipaddress.py in /cvp/pythonlab/Lib/cvplibrary.  

Recommended EOS versions are 4.15.9M / 4.17.1F or newer. Caveats to consider if running older EOS releases:
  * many show commands executed in json queries aren't supported prior to EOS-4.15.2F
  * If modifying script to run in ZTP mode, review BUG161328 relative to switchport or encapsulation dot1q vlan commands for logical interfaces.  Resolved in 4.15.9 / 4.17.1.
  
EX6_BasicBuilder and EX7_BuildMLAG are smaller subsets of UniversalBuilder extracted for training purposes. UniversalBuilder is a soon to be shared configlet builder and custom library which builds L3 ECMP Spine, Leaf (including Mgmt) and CVX devices from ZTP mode to fully functional and managed by CVP. Configured features include basic management, MLAG, northbound interfaces to Spines / southbound interfaces to Leafs, associated BGP / OSPF configurations, CVX and VxLAN.
