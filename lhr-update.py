#!/usr/bin/env python3
import json
from base64 import b64encode
from os.path import exists
import sys
import pyjq
import requests
from dotenv import dotenv_values

if exists('.env'):
    config = dotenv_values('.env')
else:
    sys.exit('.env file not found, exiting')

try:
    WSKEY   = config['WSKEY']
    SECRET  = config['SECRET']
    INSTID  = config['INSTID']
except KeyError:
    sys.exit('one or more of the expected variables not found in .env file, exiting')

combo       = WSKEY+':'+SECRET
auth        = combo.encode()
authenc     = b64encode(auth)
authheader  = { 'Authorization' : 'Basic %s' %  authenc.decode() }
url         = "https://oauth.oclc.org/token?grant_type=client_credentials&scope=WMS_COLLECTION_MANAGEMENT"

def getToken():
    try:
        r = requests.post(url, headers=authheader)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    return r.json()['access_token']

def readBib(authtoken):
    readheaders = {
        'Authorization' : 'Bearer %s' % authtoken
        , 'Accept' : 'application/atom+json' 
    }

    try:
        read = requests.get("https://circ.sd00.worldcat.org/LHR?q=oclc%3A"+bibnum, headers=readheaders)
        read.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if read.status_code == 401:
            raise ValueError('Token expired')
        else:
            SystemExit(err)
    
    return read.json()['entries']


def readLhr(authtoken):
    readheaders = {
        'Authorization' : 'Bearer %s' % authtoken
        , 'Accept' : 'application/atom+json' 
    }

    try:
        # read = requests.get(APIURL + lhrnum, headers=readheaders)
        read = requests.get(lhrnum, headers=readheaders)
        read.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if read.status_code == 401:
            raise ValueError('Token expired')
        else:
            SystemExit(err)
        
    return read

def updateLhr(lhrnum, moddedRecord, etag, authtoken):
    updateheaders =  {
        'Authorization' : 'Bearer %s' % authtoken
        , 'Accept' : 'application/scim+json' 
        , 'Content-Type' : 'application/atom+json' 
        , 'If-Match' : etag
    }

    try:
        # update = requests.put(APIURL + lhrnum, headers=updateheaders, data=moddedRecord)
        update = requests.put(lhrnum, headers=updateheaders, data=moddedRecord)
        update.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if update.status_code == 401:
            raise ValueError('Token expired')
        else:
            SystemExit(err)

    return update

## Read mod.jq for modifier
# with open('mod.jq', 'r') as file:
#     MODJQ = file.read()
# MODJQ = "."
MODJQ = '.content.shelvingDesignation.information = "miko"'

# APIURL = "https://circ.sd00.worldcat.org/LHR/"

# old token to test refresh
# TOKEN = "tk_vziB66LUGsTrc0MRpml5yo4VYoKWUPTvUXfj"
TOKEN = getToken()

# loop over bibs
for line in sys.stdin:
    bibnum = line.strip()
    try:
        lhrs = readBib(TOKEN)
        with open('lhrs.txt', 'w') as file:
            for lhr in lhrs:
                file.write(lhr['content']['id']+'\n')
    except ValueError:
        print('getting new token')
        TOKEN = getToken()
        lhr = readBib(TOKEN)


# loop over lhrs
# for line in sys.stdin:
with open('lhrs.txt', 'r') as f:
    lhrs = f.read().splitlines()

for line in lhrs:
    lhrnum = line.strip()
    
    if lhrnum == "":
        continue

    try:
        # lhr = readLhr(lhrid, TOKEN)
        # lhr = readLhr(lhrnum, TOKEN)
        lhr = readLhr(TOKEN) #car global
        # for debugging
        lhrJson = json.dumps(lhr.json())
    except ValueError:
        # token has expired, get a fresh token and redo read
        print('getting new token')
        TOKEN = getToken()
        lhr = readLhr(TOKEN)

    # Extract ETag for safe update
    ETag = lhr.headers['ETag']

    # Create modded record with MODJQ
    modded = json.dumps(pyjq.one(MODJQ, lhr.json()))

    # Update Lhr record
    try:
        update = updateLhr(lhrnum, modded, ETag, TOKEN)
        # print simple confirmation
        print(str(lhrnum) + "\t" + str(update.status_code))
    except ValueError:
        # token has expired, get a fresh token and redo update
        print('update getting new token')
        TOKEN = getToken()
        update = updateLhr(lhrnum, modded, ETag, TOKEN)
