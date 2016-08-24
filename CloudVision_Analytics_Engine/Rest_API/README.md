# Arista CloudVision&reg; Analytic Engine RESTful API Examples
This directory contains scripts that use the CloudVision Analytic Engine (CVAE)
RESTful API. The power in CVAE is that it streams the telemetry data to the
consumer of that data so that polling is not required. Even so, there are still
legacy applications that require polling to get specific telemetry data.
Instead of polling all the switches you can poll CVAE to get the data you need.

## port_inventory
Python script that polls CVAE for information about the switch ports and
displays the information.
