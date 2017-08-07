from __future__ import absolute_import
from __future__ import division

import copy
import csv
import json
import os
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
    file_time = dt.now().strftime("%Y%m%d")
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

    p0_labels = ['priority: p0', 'p0']
    p1_labels = ['priority: p1', 'p1']
    p2_labels = ['priority: p2+', 'p2+', 'priority: p2', 'p2']
    fr_question = ['enhancement', 'type: enhancement', 'type: question',
                   'question']

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

        for issue in data_decode[repo]['issues']:
            created_date = dt.strptime(
                data_decode[repo]['issues'][issue]['created'],
                "%Y-%m-%dT%H:%M:%S+00:00")

            # it is invalid for an issue to carry multiple priority labels
            # so count the most severe p0 THEN p1 THEN p2+ THEN fr_question

            if any(w.lower() in data_decode[repo]['issues'][issue]['labels']
                   for w in p0_labels):
                analysis[repo]['p0']['count'] += 1
                analysis[repo]['p0']['age'] += (dt.utcnow() -
                                                created_date).days

            elif any(x.lower() in data_decode[repo]['issues'][issue]['labels']
                     for x in p1_labels):
                analysis[repo]['p1']['count'] += 1
                analysis[repo]['p1']['age'] += (dt.utcnow() -
                                                created_date).days

            elif any(y.lower() in data_decode[repo]['issues'][issue]['labels']
                     for y in p2_labels):
                analysis[repo]['p2+']['count'] += 1
                analysis[repo]['p2+']['age'] += (dt.utcnow() -
                                                 created_date).days

            elif any(z in data_decode[repo]['issues'][issue]['labels']
                     for z in fr_question):
                analysis[repo]['fr_question']['count'] += 1
                analysis[repo]['fr_question']['age'] += (
                    dt.utcnow() - created_date).days

            else:
                analysis[repo]['no_priority_label']['count'] += 1
                analysis[repo]['no_priority_label']['age'] += (
                    dt.utcnow() - created_date).days

        for bucket, data in analysis[repo].iteritems():
            if data['count'] <= 0:
                continue
            analysis[repo][bucket]['age'] /= data['count']

    file_time = dt.now().strftime("%Y%m%d")

    with open('../output_files/%s_repo_issue_analysis.csv' % file_time,
              'w') as csvfile:
        fieldnames = ['repo', 'issues', 'issues_age', 'p0', 'p0_age', 'p1',
                      'p1_age', 'p2+', 'p2+_age', 'no_priority_label',
                      'no_priority_label_age', 'fr_question', 'fr_question_age',
                      'prs', 'prs_age']

        # analysis[repo] = {'issues': {'count': 0, 'age': 0},
        #                   'prs': {'count': 0, 'age': 0},
        #                   'p0': {'count': 0, 'age': 0},
        #                   'p1': {'count': 0, 'age': 0},
        #                   'p2+': {'count': 0, 'age': 0},
        #                   'no_priority_label': {'count': 0, 'age': 0},
        #                   'fr_question': {'count': 0, 'age': 0}}

        # repo, analysis[repo]['issues']['count'],
        #              analysis[repo]['p0']['count'],
        #              analysis[repo]['p0']['age'],
        #              analysis[repo]['p1']['count'],
        #              analysis[repo]['p1']['age'],
        #              analysis[repo]['p2+']['count'],
        #              analysis[repo]['p2+']['age'],
        #              analysis[repo]['no_priority_label']['count'],
        #              analysis[repo]['no_priority_label']['age'],
        #              analysis[repo]['fr_question']['count'],
        #              analysis[repo]['fr_question']['age'],
        #              analysis[repo]['prs']['count'],
        #              analysis[repo]['prs']['age']]


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


# def open_issues_since_date(data, start_date):
#     """Function that takes JSON product of analyze_issue_metadata.main
#     and writes out a csv file of issue count by repo, where the
#     issues created date is >= start_date OR the issue has a priority label.
#
#     Args:
#         data: JSON file
#         start_date: earliest issue creation date of interest
#                     <string> of pattern: 'YYYY-MM-DD'
#
#     Output:
#         csv file
#     """
#
#     analysis = {}
#
#     # Load/decode the data JSON
#     data_decode = json.loads(data)
#
#     for repo in data_decode:
#         if repo == 'updated':
#             continue
#
#         analysis[repo] = {'issues': {'count': 0, 'age': 0}}




if __name__ == "__main__":
    data = main(sys.argv[1], sys.argv[2], 'open')
    analyze_issue_metadata(data)
