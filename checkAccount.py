import pandas as pd

from dynamics.dynamics_client import DynamicsClient

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options

import re
import datetime
from slack_sdk.webhook import WebhookClient

import json

from confluence_client import ConfluenceClient

# read values from the config.json file
with open('config.json', 'r') as f:
    config = json.load(f)

# Authentication
username = config['dynamics']['username']
password = config['dynamics']['password']
host = 'dynamics.sdsc.edu'
org_name = 'sandiegosupercomputercenter'

dynamics_client = DynamicsClient(username, password, host, org_name)

# all accounts that are not external (filter out the external accounts)
accountInfo = dynamics_client.query("/accounts?$filter=new_affiliation ne 100000002")

# get all the contact IDS
contactIDs = []
for i in range(len(accountInfo)):
    contactIDs.append( ( accountInfo[i]["_primarycontactid_value"] ) )

# query contact information from the ID
contactInfo = []
for i in range(len(contactIDs)):
    try:
        contactInfo.append( dynamics_client.query("/contacts?$filter=contactid eq " + contactIDs[i]) )
    # contact info does not exist
    except TypeError:
        continue

lastnameList = []
firstnameList = []
phoneList = []
emailList = []

# output their full name + phone number + email address
for i in range( len(contactInfo) ):

    if contactInfo[i][0]['lastname'] is None:
        lastname = "NONE"
    else:
        lastname = contactInfo[i][0]['lastname']

    if contactInfo[i][0]['firstname'] is None:
        firstname = "NONE"
    else:
        firstname = contactInfo[i][0]['firstname']

    if contactInfo[i][0]['telephone1'] is None:
        phoneNumber = "NONE"
    else:
        phoneNumber = contactInfo[i][0]['telephone1']

    if contactInfo[i][0]['emailaddress1'] is None:
        emailAddress = "NONE"
    else:
        emailAddress = contactInfo[i][0]['emailaddress1']

    lastnameList.append(lastname)
    firstnameList.append(firstname)
    phoneList.append(phoneNumber)
    emailList.append(emailAddress)

# creates a dataframe that has all the customer's information from Dynamics
dict = {'Last Name': lastnameList, 'First Name': firstnameList, 'Business Phone': phoneList, 'Email Address': emailList}  
contactInfo_df = pd.DataFrame(dict) 

lastName = contactInfo_df["Last Name"].reset_index(drop=True)
firstName = contactInfo_df["First Name"].reset_index(drop=True)
businessPhone = contactInfo_df["Business Phone"].reset_index(drop=True)
emailAddress = contactInfo_df["Email Address"].reset_index(drop=True)

# the output file name is the current date
e = datetime.datetime.now()
currDateTime = e.strftime("%Y-%m-%d")
filename = currDateTime + ".txt"
f = open(filename,'w')

# instance of Options class allows us to configure Headless Firefox
options = Options()
options.headless = True

# search customer's information through Blink to compare the contact information between the two platforms
for i in range(len(contactInfo_df)):
        
    # create new driver for every 10 searches to avoid 'too many attempts' error on Blink
    if i%10==0:
        driver = webdriver.Firefox(executable_path='./geckodriver', options=options)

    # input lastname and firstname and automatically search on the web driver
    driver.get(config['blink_url'])
    lastNameSearchBox = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//input[@id="faculty_last_name"]')))
    firstNameSearchBox = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//input[@id="faculty_first_name"]')))
    searchButton = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//input[@class="btn btn-primary primary"]')))
    lastNameSearchBox.send_keys(lastName[i])
    # Get rid of middle name written down in first name column to avoid confusions
    firstNameSearchBox.send_keys(firstName[i].split(" ")[0])
    searchButton.send_keys(Keys.ENTER)

    f.write("Currently checking: " + lastName[i] + ", " + firstName[i] + "\n")

    # Grab phone number from Blink
    try:
        tel = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, '//a[@class="tel"]'))).text
        # take just the ten digit numbers using the regular expression
        tel = re.sub("[^0-9]", "", tel)

    # if Blink does not have their phone number
    except TimeoutException:
        tel = "NONE "

    # Grab email address from Blink
    try:
        em = WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='col-xs-10']/a"))).get_attribute('href')
        # Get rid of the "mailto:" from the email element
        em = em[7:]
    
    # if Blink does not have their email address
    except TimeoutException:
        em = "NONE "

    if businessPhone[i] != "NONE":
        currPhone = re.sub("[^0-9]", "", businessPhone[i]) 
    else:
        currPhone = "NONE"

    currEmail = emailAddress[i]


    # Check whether the phone number and email addresses are consistent between the two platforms
    if (currPhone != tel) | (currEmail != em):
        if currPhone != tel:
            f.write("Incorrect Phone number - Dynamics: " + currPhone + ", Blink: " + tel + "\n")
        if currEmail != em:
            f.write("Incorrect email address - Dynamics: " + currEmail + ", Blink: " + em + "\n")
    else:
        f.write("Correct: Phone number and email address matches on both platforms\n")
    f.write("\n")

f.close()

# upload the output file into Confluence
confluence_client = ConfluenceClient( config['confluence']['username'], config['confluence']['token'], config['confluence']['url'])
upload_success = confluence_client.upload_attachment( config['confluence']['space_id'], "./" + filename )

fileLink = config['file_link'] + "/" + config['confluence']['space_id'] + "/" + filename + "?api=v2"

# send the link to slack channel
slack_url = config['slack_url']
webhook = WebhookClient(slack_url)

response = webhook.send(text="Dynamics Contact Checks script successfully finished. \n Following is the <" + fileLink + "|output file>")
