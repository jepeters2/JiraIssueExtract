import ast
import os
import json
import argparse
import configparser
import requests
from typing import cast
from datetime import datetime
from atlassian import Bitbucket
from collections import Counter
from unidiff import PatchSet

#TODO: only update new diffs for any repo. build file if it doesn't exist, update any pr that status changed, add any new prs. make this incremental
#TODO: recover the file if there is a failure in processing so it can continue where it left off

parser = argparse.ArgumentParser(prog="JBitbucketExtract", description="Use a config file to define issues to search and extract from a bitbucket service with Token based authentication")
parser.add_argument('--config',action='store', default='BitbucketExtract.ini', help='location of the configuration.ini file')
args = parser.parse_args()

config = configparser.ConfigParser()
print('Using config file: ', config.read(args.config))



BB_SERVER = config['DEFAULT']['ServerUrl']    #"https://devtrack.vanderlande.com"
BB_TOKEN = config['DEFAULT']['ServerToken']  #"NzcxNjE1MzcyMTAxOkqke3YT4/FhAANlh9Nr7nZ1AN2i"
#file information
outputFile = config['DEFAULT']['OutFile']
getDiffs = int(config['DEFAULT']['getDiffs'])
maxDiffs = int(config['DEFAULT']['maxDiffs'])
project = config['DEFAULT']['project']

bitbucket = Bitbucket(url=BB_SERVER,token=BB_TOKEN)
prdb ={}
#Dont remove the file, open it if it exists. if it does read everything into the dict for searching
try:
    file1 = open(outputFile, 'r+')
    prdb = json.loads(file1.read())
    file1.seek(0)
except IOError:
    print("no file found, creating")
    file1 = open(outputFile, 'w+')

repos = bitbucket.repo_list(project,limit=200)

for repo in repos:
    #print("pulling repo: ", repo['slug'])
    pullrequests = bitbucket.get_pull_requests(project,repo["slug"],"ALL","newest",maxDiffs,0)
    i = 0
    prAdd = 0
    prUpdate = 0

    for pullrequest in pullrequests:
        key = repo['slug'] + '-' + str(pullrequest['id'])

        minimalPRDetail = {
            "project": repo['project']['key'],
            'repository': repo['slug'],
            'id':  pullrequest['id'],
            'state': pullrequest['state'],
            'diffurl': pullrequest["links"]["self"][0]["href"] + ".diff",
            'stats': {'Lines Added': -1,'Lines Removed': -1, 'Files Added': -1,'Files Removed': -1,'Files Modified':-1}
        }
        
        prFileRecord = prdb.get(key)
        if prFileRecord is None:
            #record not found it needs to be added
            prFileRecord = minimalPRDetail
            prAdd +=1
            if getDiffs == 1 :
                diffReq = requests.get(minimalPRDetail['diffurl'],headers={"Authorization": "Bearer " + BB_TOKEN})
                try:
                    patch = PatchSet(diffReq.iter_lines(),encoding = diffReq.encoding)
                    prFileRecord['stats'] = {'Lines Added': patch.added,'Lines Removed':patch.removed, 'Files Added':patch.added_files.__len__(),'Files Removed':patch.removed_files.__len__(),'Files Modified':patch.modified_files.__len__()}
                except:
                    prFileRecord['stats'] = {'Lines Added': -1,'Lines Removed': -1, 'Files Added': -1,'Files Removed': -1,'Files Modified':-1}
        elif prFileRecord['state'] != pullrequest['state']:
            #record was found, state does not match, update record
            prFileRecord['state'] = pullrequest['state']
            prUpdate += 1
            #TODO move this into a function so I don't have to duplicate it on two places?
            if getDiffs == 1 :
                diffReq = requests.get(minimalPRDetail['diffurl'],headers={"Authorization": "Bearer " + BB_TOKEN})
                try:
                    patch = PatchSet(diffReq.iter_lines(),encoding = diffReq.encoding)
                    prFileRecord['stats'] = {'Lines Added': patch.added,'Lines Removed':patch.removed, 'Files Added':patch.added_files.__len__(),'Files Removed':patch.removed_files.__len__(),'Files Modified':patch.modified_files.__len__()}
                except:
                    prFileRecord['stats'] = {'Lines Added': -1,'Lines Removed': -1, 'Files Added': -1,'Files Removed': -1,'Files Modified':-1}
                
                #update the dictionary.
        prdb[key] = prFileRecord
        #file1.write(json.dumps({key: minimalPRDetail}) + "\n")
        i+=1
        if i >= maxDiffs:
            break
    #update the file per repository
    file1.write(json.dumps(prdb,indent=0))
    file1.seek(0)
    print(f"Wrote: {repo['slug']} number of prs: {i}, prs Added {prAdd}, prs updated {prUpdate} time: {datetime.now()}")
file1.close

