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
    #set pytz.timezone variable
    pacific = pytz.timezone('US/Pacific')

    #extract list of repos from text file
    with open(repo_file) as f:
        repos = f.readlines()
    repos = [x.strip() for x in repos]
    f.close()

    with open('../output_files/closed_issue_counts.csv', 'a') as csvfile:
        fieldnames = ['repo', 'issue.number', 'closed_at']
        datawriter = csv.DictWriter(csvfile, delimiter=',',
                                    fieldnames=fieldnames, quotechar='"')
        for repo in repos:
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
                    # add this issue to the issues sub-dictionary in the
                    # data dictionary (key is GitHub issue number)
                    closed_date = issue.closed_at.astimezone(pacific)
                    closed_date = closed_date.strftime('%m/%d/%Y')
                    row = {'repo': repo, 'issue.number': issue.number,
                           'closed_at': closed_date}
                    datawriter.writerow(row)
                    print('%d written to file' % issue.number)
    csvfile.close()

if __name__ == "__main__":
    g = github3.login(token=os.environ['GH_TOKEN'])
    main(g, sys.argv[1])
