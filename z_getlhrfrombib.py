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


def readBib(userId, authtoken):
    readheaders = {
        'Authorization' : 'Bearer %s' % authtoken
        , 'Accept' : 'application/atom+json' 
    }

    try:
        # read = requests.get(readurl, headers=readheaders)
        read = requests.get(APIURLBIB + bibnum, headers=readheaders)
        read.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if read.status_code == 401:
            raise ValueError('Token expired')
        else:
            SystemExit(err)
    
    return read.json()['entries']

APIURLBIB = "https://circ.sd00.worldcat.org/LHR?q=oclc%3A"

TOKEN = getToken()

for line in sys.stdin:
    bibnum = line.strip()
    try:
        lhrs = readBib(bibnum, TOKEN)
        # lhrJson = json.dumps(lhr.json())
        with open('lhrs.txt', 'w') as file:
            for lhr in lhrs:
                file.write(lhr['content']['id']+'\n')
    except ValueError:
        print('getting new token')
        TOKEN = getToken()
        lhr = readBib(bibnum, TOKEN)
