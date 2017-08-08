from __future__ import absolute_import
from __future__ import division

import csv
import json
import os
import pytz
import re
import six
import sys

from datetime import datetime as dt

import github3

import get_issue_metadata as gim


def main(org, repos, state):

    """Command line tool that reads in an input file
    containing GitHub repository names, calls read_issue_metadata
    and returns a JSON file of issue data.

    Usage (command line):
        $ python analyze_issue_metadata.py googlecloudplatform repos.txt

    Args:
        state: GitHub state of issue ('open', 'closed'
               or 'all')
        org: github owner or organization
        repos: path to input file containing names of repos belonging to
               owner or org in sys.argv[1].  One repo name per line.

    Returns:
        A JSON of issue metadata
    """

    org = six.text_type(sys.argv[1])

    with open(sys.argv[2]) as f:
        repos = f.readlines()
    repos = [x.strip() for x in repos]

    # Authenticate with GitHub using Personal Access Token
    g = github3.login(token=os.environ['GH_TOKEN'])

    data = gim.get_issue_metadata(g, org, repos, state)

    # Dump the data to a JSON file
    data_json = json.dumps(data)
    file_time = dt.now(pytz.utc).strftime("%Y%m%d_%H:%M%Z")
    print('Dumping data to json file')
    with open('../output_files/' + file_time + '_raw_veneer_issue_meta.json',
              'w') as f:
        data = json.dump(data, f, sort_keys=True, indent=4, separators=(
             ',', ': '))

    return data_json


def analyze_issue_metadata(data):
    """Function that takes JSON product of analyze_issue_metadata.main
    and writes out a csv file of issue type statistics by repo.

    Args:
        data: JSON file

    Output:
        csv file
    """

    analysis = {}

    # Load/decode the data JSON
    data_decode = json.loads(data)

    for repo in data_decode:
        if repo == 'updated':
            continue

        analysis[repo] = {'issues': {'count': 0, 'age': 0},
                          'prs': {'count': 0, 'age': 0},
                          'p0': {'count': 0, 'age': 0},
                          'p1': {'count': 0, 'age': 0},
                          'p2+': {'count': 0, 'age': 0},
                          'no_priority_label': {'count': 0, 'age': 0},
                          'fr_question': {'count': 0, 'age': 0}}

        analysis[repo]['issues']['count'] = data_decode[repo][
                                              'open_issues_count']
        analysis[repo]['prs']['count'] = data_decode[repo]['prs'][
                                           'open_pr_count']

        # if there are prs, calculate their mean age
        if analysis[repo]['prs']['count'] > 0:
            analysis[repo]['prs']['age'] = data_decode[repo]['prs'][
                'pr_aggregate_age']/analysis[repo]['prs']['count']

        for issue_number, issue_meta in data_decode[repo]['issues'].items():
            created_date = dt.strptime(
                data_decode[repo]['issues'][issue_number]['created'],
                "%Y-%m-%dT%H:%M:%S+00:00")

            analysis[repo]['issues']['age'] += (dt.utcnow() -
                                                created_date).days

            # determine the issue type (p0, p1, ...), and
            # increment that type's counter and aggregate age
            analysis[repo][determine_issue_type(issue_meta)]['count'] += 1
            analysis[repo][determine_issue_type(issue_meta)]['age'] += (
                dt.utcnow() - created_date).days

        for issue_type, data in analysis[repo].items():
            if data['count'] <= 0:
                continue
            analysis[repo][issue_type]['age'] /= data['count']

    file_time = dt.now(pytz.utc).strftime("%Y%m%d_%H:%M%Z")

    with open('../output_files/%s_repo_issue_analysis.csv' % file_time,
              'w') as csvfile:
        fieldnames = ['repo', 'issues', 'issues_age', 'p0', 'p0_age', 'p1',
                      'p1_age', 'p2+', 'p2+_age', 'no_priority_label',
                      'no_priority_label_age', 'fr_question', 'fr_question_age',
                      'prs', 'prs_age']

        datawriter = csv.DictWriter(csvfile, delimiter=',',
                                    fieldnames=fieldnames, quotechar='"')
        datawriter.writeheader()
        for repo,metadata in analysis.items():
            row = {'repo': repo}
            for issue_category, issue_data in metadata.items():
                row.update({issue_category: issue_data['count'],
                           issue_category + '_age': issue_data['age']})
            datawriter.writerow(row)
        print('State of triage data written to file '
              '(../output_files/%s_repo_issue_analysis.csv)' % file_time)


def all_issues_to_csv(data):
    """
    """

    all_issues = {}

    # Load/decode the data JSON
    data_decode = json.loads(data)

    for repo in data_decode:
        for issue in repo:
            for issue_number, issue_meta in issue.items():
                all_issues['issue_number'] = issue_number
                all_issues['issue_category'] = row.append(
                    determine_issue_type(issue_meta))
                all_issues['title'] = issue_meta['title']
                all_issues['created'] = issue_meta['created']
                all_issues['updated'] = issue_meta['updated']
                if issue_meta['closed']:
                    all_issues['closed'] = issue_meta['closed']

def determine_issue_type(issue):
    """Return the type of issue that this is deemed to be.

    Args:
        issue (dict): The issue as returned from GitHub.
                      It must have a `labels` key, which should be a list.

    Returns:
        str: The type of issue this is.
    """

    for label in issue['labels']:
        if re.search(r'p0$', label.lower()):
            return 'p0'
    for label in issue['labels']:
        if re.search(r'p1$', label.lower()):
            return 'p1'
    for label in issue['labels']:
        if re.search(r'p2\+?$', label.lower()):
            return 'p2+'
    for label in issue['labels']:
        if re.search(r'question', label.lower()) or re.search(r'enhancement', label):
            return 'fr_question'

    return 'no_priority_label'


if __name__ == "__main__":
    data = main(sys.argv[1], sys.argv[2], 'all')
    analyze_issue_metadata(data)
    all_issues_to_csv(data)
