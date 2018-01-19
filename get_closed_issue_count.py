from __future__ import absolute_import
from __future__ import division

import collections
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


def main(gh_login, repo_file, since):

    """
    Function uses the GitHub v3 API to read the issues for each repo
    in the list provided.

    Args:
        gh_login: an authenticated GitHub session.
        repo_file: file containing list of GitHub repository names.
        since: only issues updated at or after this time are returned. 
               This is a timestamp in ISO 8601 format:
               YYYY-MM-DDTHH:MM:SSZ.

    Returns:
        Writes to CSV file
    """
    #set pytz.timezone variable
    pacific = pytz.timezone('US/Pacific')

    #extract list of repos from text file
    with open(repo_file) as f:
        repos = f.readlines()
    repos = [x.strip() for x in repos]
    f.close()

    with open('closed_etag_file.json', 'r+') as etag_file:
        try:
            etags = json.load(etag_file)
        except:
            print("No JSON data in 'closed_etag_file.json'")
            etags = {}

        with open('../output_files/closed_issue_counts.csv', 'a') as csvfile:
            fieldnames = ['repo', 'issue.number', 'closed_at']
            datawriter = csv.DictWriter(csvfile, delimiter=',',
                                        fieldnames=fieldnames, quotechar='"')
            for repo in repos:
                # get issue generator from GitHub
                print('Getting issues from %s' % repo)
                org, repo_name = repo.split("/")
                try:
                    etag = etags[org][repo_name]
                    print "Etag found. Passing to API call."
                    issues = gh_login.issues_on(org, repo_name, state='closed',
                                                since=since, etag=etag)
                except:
                    print("No etag found for %s/%s." % (org, repo_name))
                    issues = gh_login.issues_on(org, repo_name, state='closed',
         					since=since)

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
                try:
                    etags[org][repo_name] = issues.etag
                except:
                    etags[org] = {}
                    etags[org][repo_name] = issues.etag
            csvfile.close()
        etag_file.seek(0)
        json.dump(etags, etag_file)
        etag_file.truncate()
    etag_file.close()


if __name__ == "__main__":
    g = github3.login(token=os.environ['GH_TOKEN'])
    main(g, sys.argv[1], sys.argv[2])
