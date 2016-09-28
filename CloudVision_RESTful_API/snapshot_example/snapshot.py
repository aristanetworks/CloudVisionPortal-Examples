#!/usr/bin/env python
'''
This program uses cvprac, the CloudVision Portal API to first get a template-ID
for snapshot template: SnapshotOfConfig1 and container-ID for container: mlane1,
then POST a request for CVP to capture snapshot configs for every switch in the
cotainer.
'''
from cvprac.cvp_client import CvpClient    # Import CvpClient class module
clnt = CvpClient()                                    # create clnt object from CvpClient class
clnt.connect(['192.168.1.143'], 'cvpadmin', 'cvpadmin1')     # Connect to CVP

#  Next get Container information for mlane1
result = clnt.get('/inventory/add/searchContainers.do?queryparam=mlane1&startIndex=0&endIndex=0')
# And, extract the container key or container-ID.
contnr = result['data'][0]['key']

# Get information for snapshot template: SnapshotOfConfig1
result2 = clnt.get('/snapshot/getSnapshotTemplates.do?startIndex=0&endIndex=0&queryparam=SnapshotOfConfig1')
# And, extract it's key or template-ID
snapTemplt = result2['data'][0]['key']

# Build a dictionary which includes: "templateid" and "containerid"
parms2 = { "templateId": snapTemplt, "containerId": contnr}

# Execute a POST to the Container Snapshot module and pass the parameter dictionary: parms2
snapResult = clnt.post('/snapshot/captureContainerLevelSnapshot.do', parms2)

# Print out the returned result which shoud be "success"
print snapResult

