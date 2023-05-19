from __future__ import annotations
from collections import Counter
import os
from typing import cast
from jira import JIRA
from jira.client import ResultList
from jira.resources import Issue
from datetime import datetime
import json
import argparse
import configparser

#todo
# 1. filter for history to only store fields that are needed, reduce history file size.
# 2. command line args for query, fields, expand, output file

parser = argparse.ArgumentParser(prog="JiraIssueExtract", description="Use a config file to define issues to search and extract from a JIRA instance with Token based authentication")
parser.add_argument('--config',action='store', default='JiraIssueExtract.ini', help='location of the configuration.ini file')
args = parser.parse_args()

config = configparser.ConfigParser()
#with open(args.config, 'r') as configfile:
print('Using config file: ', config.read(args.config))



JIRA_SERVER = config['SERVER']['ServerUrl']    #"https://devtrack.vanderlande.com"
JIRA_TOKEN = config['SERVER']['ServerToken']  #"NzcxNjE1MzcyMTAxOkqke3YT4/FhAANlh9Nr7nZ1AN2i"
#file information
outputFile = config['QUERY']['OutFile']

#query details
jql =config['QUERY']['Jql']
#fieldsToRetrieve = ["assignee","created","environment","issuekey","issuetype","priority","resolution","resolutiondate","status","summary","customfield_11322","customfield_11323","customfield_11325","customfield_12328","customfield_14320","customfield_14520","customfield_15422","customfield_16521"]
fieldsToRetrieve = config['QUERY']['ReturnFields'].split(",")
expandFields = config['QUERY']["ExpandFields"].split(",")
filterchangelog = config['QUERY']["FilterChangelog"].split(",")
chunk_size = int(config['QUERY']['QueryBatch'])
maxReturn = int(config['QUERY']['MaxReturn'])


# Some Authentication Methods
jira = JIRA(server=JIRA_SERVER,
    #basic_auth=("admin", "admin"),  # a username/password tuple [Not recommended]
    # basic_auth=("email", "API token"),  # Jira Cloud: a username/token tuple
     token_auth=JIRA_TOKEN,  # Self-Hosted Jira (e.g. Server): the PAT token
    # auth=("admin", "admin"),  # a username/password tuple for cookie auth [Not recommended]
)

jiraissues = {}

try:
    file1 = open(outputFile, 'r+')
    prdb = json.loads(file1.read())
    file1.seek(0)
except IOError:
    print("no file found, creating")
    file1 = open(outputFile, 'w+')

# Who has authenticated
#myself = jira.myself()
i = 0
print(f"Starting {i}, {datetime.now()}")
while True:
# Note: we cast() for mypy's benefit, as search_issues can also return the raw json !
#   This is if the following argument is used: `json_result=True`
    chunk = cast(ResultList[Issue],jira.search_issues(jql,i,chunk_size,fields=fieldsToRetrieve, expand=expandFields))
    #chunk = jira.search_issues("project=wplat and status = closed",i,chunk_size,json_result=True)
    i += chunk_size
    for issue in chunk:
        #if issue.changelog:
        #    for history in issue.changelog.histories:   
        #        for item in history.items:        
        #            if item.field not in filterchangelog:
                        #delete the item.
        #                print("delete item")
        jiraissues[issue.key] = issue.raw
    file1.write(json.dumps(jiraissues,indent=0))
    file1.seek(0)
    print(f"Retrieved {i}, {datetime.now()}")
    if i>= chunk.total or i >= maxReturn:
        break
file1.close

