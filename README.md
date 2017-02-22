#Signal Sciences TA for Splunk App

This app for Splunk connects to the Signal Sciences API in order to pull data into Splunk. 

## Configuration

Currently the app requires the configuration to be manually updated in the config.env file. It is recommended to make a copy of the one in the default folder and put it in the local folder.

````
export SIGSCI_EMAIL='email@domain.com'
export SIGSCI_PASSWORD='PASSWORD'
export SIGSCI_CORP='CORPNAME'
export SIGSCI_SITE_NAME='DASHBOARDVIEW'
````

After the values have been setup and the app enabled things will run automatically. There is an expectaction that there will be an index called "sigsci".
