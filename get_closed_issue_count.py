from __future__ import absolute_import
from __future__ import division

import csv
import json
import os
import pytz
import re
import six
import sys
import time

from datetime import datetime as dt

import check_rate_limit as crl

import github3


def main(gh_login, repo_file):

    """
    Function uses the GitHub v3 API to read the issues for each repo
    in the list provided.  The following issue metadata is extracted
    and returned in a JSON-like object.

    Args:
        gh_login: an authenticated GitHub session.
        repos: list of GitHub repository names.
        state: state of the issues to get via the API - can be 'open',
               'closed' or 'all'.

    Returns:
        A JSON-like file of issue metadata:
        'repoorg/reponame': {
            'open_issues_count': <int>,
            'prs': {'open_pr_count': <int>,
                    'pr_aggregate_age': <int>},
            'issues': {
                issue.number: {
                    assignee: <string>,
                    created: <isoformat date>,
                    labels: [
                        <string>, ...
                    ]
                    title: <string>,
                    updated: <isoformat data>
                }
            }
        }
    """

    #extract list of repos from text file
    with open(repo_file) as f:
        repos = f.readlines()
    repos = [x.strip() for x in repos]

    pacific = pytz.timezone('US/Pacific')

    # Initialize dictionary for results
    data = {}
    for repo in repos:
        # set up repo specific variables, data structures and counters
        data[repo] = {}

        # get issue generator from GitHub
        print('Getting issues from %s' % repo)
        org, repo_name = repo.split("/")
        issues = gh_login.issues_on(org, repo_name, state='closed')

        for issue in issues:
            # check remaining rate limit
            if crl.remaining() > 100:
                pass
            else:
                print('Rate limit low; going to sleep until rate resets')
                crl.print_remaining()
                time.sleep(crl.reset() - int(time.time()))

            if issue.pull_request():
                continue
            else:
                print('Adding issue number: %d' % issue.number)
                # add this issue to the issues sub-dictionary in the
                # data dictionary (key is GitHub issue number)
                closed_date = issue.closed_at.astimezone(pacific)
                data[repo][issue.number] = closed_date.strftime('%m/%d/%Y')

    data['updated'] = dt.now(pacific).isoformat()

    # print json.dumps(data, indent = 4, sort_keys=True)

    file_time = dt.now(pacific).strftime("%Y%m%d_%H%M%Z")

    with open('../output_files/%s_closed_issue_counts.csv' % file_time,
              'w') as csvfile:
        fieldnames = ['repo', 'issue.number', 'closed_at']

        datawriter = csv.DictWriter(csvfile, delimiter=',',
                                    fieldnames=fieldnames, quotechar='"')
        datawriter.writeheader()
        for repo, repo_data in data.items():
            if repo == 'updated':
                continue
            else:
                row = {'repo': repo}
                # print(repo_data)
                # print type(repo_data)
                for issue, issue_data in repo_data.items():
                    row.update({'issue.number': issue,
                                'closed_at': data[repo][issue]})
                    datawriter.writerow(row)
        print('Written to file.')

if __name__ == "__main__":
    g = github3.login(token=os.environ['GH_TOKEN'])
    main(g, sys.argv[1])
