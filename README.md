# Dynamics Contact Checks


## Usage

```
python3 checkAccount.py
```

## Getting started

### 1. UCSD VPN
User needs to be on the UCSD VPN to query data from dynamics. 
Refer to this [page](https://blink.ucsd.edu/technology/network/connections/off-campus/VPN/) to find more information about how to set up Virtual Private Networks (VPN) at UCSD.

### 2. config.json
Refer to `config.example.json` to enter your SDSC username and password to get an access to dynamics. 


`slack_url` is currently set to send messages to `script-health-checks` channel. Take a look at this [page](https://sdsc-ucsd.atlassian.net/wiki/spaces/CS/pages/631734751/Slack+Client-Service-Bot) to find more information about how to send the message to different Slack channels.

### 3. Output file
After the script runs, it saves the output file into [Confluence.](https://sdsc-ucsd.atlassian.net/wiki/spaces/CS/pages/2151907329/Dynamics+Contact+Check+Output+WIP) The filename is the date of which the script ran. 

### 4. geckodriver
In order to use Selenium WebDriver, the user needs to download a driver that integrates with the browser. In this script, we will be using the FireFox WebDriver called `GeckoDriver`. You can download it from [here](https://github.com/mozilla/geckodriver/releases). This driver will allow Selenium to use the browser to search contact information from Blink.

## Dependancy / External Libraries

`dynamics.dynamics_client`: used to query contact information from Dynamics.

`selenium`: uses web driver to search for HTML elements to grab contact information from Blink.

`slack_sdk.webhook`: uses Slack Webhooks to send message to a specific channel.

`confluence_client`: used to upload the files to Confluence