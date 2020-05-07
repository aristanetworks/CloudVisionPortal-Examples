# Installing CCM Scripts

CVP requires two files for Custom Scripts:
   - Python script file
   - Yaml configuration file

**Change Control Script**
This script will be associated with the device(s) modified in the Change Control.
The device information is available as globalVariables (CVP_IP,  CVP_MAC, CVP_SERIAL)
The information for the user executing the Change Control is available as global variables(CVP_USERNAME, CVP_PASSWORD and CVP_SESSION_ID).
The script can use the Rest Client library and Device library to extend its functionality.  
CVP audit logging is available within scripts using the ‘alog()’ function

**Change Control Script Config YAML**
The YAML config file containing parameters:
Name - the script name used in identifying the specific script to add to Change Controls.
Args - optional parameter which contains a list of static arguments which can be passed to the script.

**Installing and Checking Scripts**
Copy the script and Config file to the CVP server

   scp ./{{name of script}}.* root@{{CVP server name}}:/home/cvpadmin/

Test the Script on the CVP Server

login to the CVP server as root
   cd /home/cvpadmin
   /cvpi/tools/script-util test -device {{macAddress of Test Switch}} -config ./{{script name}}.yaml -path ./{{script name}}.py -user {{cvp username}} -passwd {{cvp user password}}

should result in something similar to:

   I0917 13:16:32.530398   31009 dial.go:123] connecting to {localhost:9900 static:///localhost:9900}...
   I0917 13:16:32.962890   31009 script.go:343] script succeeded. Ouput:

Upload script and config file to the CVP Application:

   /cvpi/tools/script-util upload -config ./{{script name}}.yaml -path ./{{script name}}.py

should result in:

   I0917 13:28:45.875159    2787 dial.go:123] connecting to {localhost:9900 static:///localhost:9900}...
   script uploaded successfully!!
