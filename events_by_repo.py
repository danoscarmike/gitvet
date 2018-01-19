import csv
import os
import pytz
import six
import sys

from datetime import datetime as dt

import github3

org = six.text_type(sys.argv[1])

with open(sys.argv[2]) as f:
    repos = f.readlines()
repos = [x.strip() for x in repos]

# Authenticate with GitHub using Personal Access Token
g = github3.login(token=os.environ['GH_TOKEN'])

file_time = dt.now(pytz.utc).strftime("%Y%m%d_%H:%M%Z")

with open('../output_files/%s_all_events.csv' % file_time,
          'w') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    for repo in repos:
        print('Getting events from %s' % repo)
        for event in g.repository(org, repo).events():
            if event.type in ['IssuesEvent', 'IssueCommentEvent']:
                row = [repo,
                       event.id,
                       event.type,
                       event.as_dict()['payload']['action'],
                       event.created_at,
                       event.actor]
                writer.writerow(row)
