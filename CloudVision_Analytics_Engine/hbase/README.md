# Arista CloudVision&reg; Analytic Engine hbase Examples
This directory contains scripts that modify hbase settings or the data stored. This data is used by the CloudVision Analytics Engine (CVAE).

## cvp_aeris_reduce_storage.sh

This script will reduce the amount of versions stored of the data in the
CVAE table. This in effect will reduce the storage used by CVAE over time.

## cvp_aeris_truncate.sh

This script will delete all data stored in the CVAE database. This is useful
when going from a test environment to a production environment.
