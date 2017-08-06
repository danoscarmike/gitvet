import csv
import json
import os

from datetime import datetime as dt

import github3

import read_issue_metadata as rim


def main(state):
    """
    Function that reads in an input file
    containing GitHub repository names, calls read_issue_metadata
    and returns a JSON file of issue data.

    Args:
        state: GitHub state of issue ('open', 'closed'
               or 'all')
        sys.argv: path to input file

    Returns:
        A JSON file of issue metadata

    Raises:
        N/A
    """

    # with open('./inputs/REPOS') as f:
    #   repos = f.readlines()
    # repos = [x.strip() for x in repos]

    # Authenticate with GitHub using Personal Access Token
    g = github3.login(token=os.environ['GH_TOKEN'])

    data = rim.read_issue_metadata(g, ['google-cloud-ruby'], state)
    data_json = json.dumps(data)

    file_time = dt.now().strftime("%Y%m%d")

    print 'Dumping data to json file'
    with open('../output_files/' + file_time + '_raw_veneer_issue_meta.json',
              'w') as f:
        data = json.dump(data, f, sort_keys=True, indent=4, separators=(
             ',', ': '))

    return data_json


def state_of_triage(data):

    p0_labels = ['Priority: P0', 'priority: P0', 'priority: p0', 'P0', 'p0']
    p1_labels = ['Priority: P1', 'priority: P1', 'priority: p1', 'P1', 'p1']
    p2_labels = ['Priority: P2+', 'priority: P2+', 'priority: p2+',
                 'P2+', 'p2+', 'Priority: P2', 'priority: P2', 'priority: p2',
                 'P2', 'p2']
    fr_question = ['Type: Enhancement', 'Type: Question', 'type: enhancement',
                   'type: question', 'enhancement']

    analysis = {}

    # Load/decode the data JSON
    data_decode = json.loads(data)

    for repo in data_decode:
        if repo == 'updated':
            continue
        else:

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

                if any(x in data_decode[repo]['issues'][issue]['labels']
                       for x in p0_labels):
                    analysis[repo]['p0']['count'] += 1
                    analysis[repo]['p0']['age'] += (dt.utcnow() -
                                                    created_date).days

                elif any(y in data_decode[repo]['issues'][issue]['labels']
                         for y in p1_labels):
                    analysis[repo]['p1']['count'] += 1
                    analysis[repo]['p1']['age'] += (dt.utcnow() -
                                                    created_date).days

                elif any(z in data_decode[repo]['issues'][issue]['labels']
                         for z in p2_labels):
                    analysis[repo]['p2+']['count'] += 1
                    analysis[repo]['p2+']['age'] += (dt.utcnow() -
                                                     created_date).days

                elif any(x in data_decode[repo]['issues'][issue]['labels']
                         for x in fr_question):
                    analysis[repo]['fr_question']['count'] += 1
                    analysis[repo]['fr_question']['age'] += (
                        dt.utcnow() - created_date).days

                else:
                    analysis[repo]['no_priority_label']['count'] += 1
                    analysis[repo]['no_priority_label']['age'] += (
                        dt.utcnow() - created_date).days

            if analysis[repo]['p0']['count'] > 0:
                analysis[repo]['p0']['age'] = analysis[repo]['p0'][
                    'age']/analysis[repo]['p0']['count']
            if analysis[repo]['p1']['count'] > 0:
                analysis[repo]['p1']['age'] = analysis[repo]['p1'][
                    'age']/analysis[repo]['p1']['count']
            if analysis[repo]['p2+']['count'] > 0:
                analysis[repo]['p2+']['age'] = analysis[repo]['p2+'][
                    'age']/analysis[repo]['p2+']['count']
            if analysis[repo]['no_priority_label']['count'] > 0:
                analysis[repo]['no_priority_label']['age'] = analysis[repo][
                    'no_priority_label']['age']/analysis[repo][
                    'no_priority_label']['count']
            if analysis[repo]['fr_question']['count'] > 0:
                analysis[repo]['fr_question']['age'] = analysis[repo][
                    'fr_question']['age']/analysis[repo]['fr_question'][
                        'count']

    file_time = dt.now().strftime("%Y%m%d")

    with open('../output_files/' + file_time +
              '_triage_state.csv', 'w') as csvfile:

        datawriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        datawriter.writerow(['repo', 'issues', 'p0', 'p0_age', 'p1',
                             'p1_age', 'p2+', 'p2_age', 'no_p', 'no_p_age',
                             'fr/question', 'fr/question_age', 'pulls',
                             'pulls_age'])

        for repo in analysis:
            datawriter.writerow([repo,
                                 analysis[repo]['issues']['count'],
                                 analysis[repo]['p0']['count'],
                                 analysis[repo]['p0']['age'],
                                 analysis[repo]['p1']['count'],
                                 analysis[repo]['p1']['age'],
                                 analysis[repo]['p2+']['count'],
                                 analysis[repo]['p2+']['age'],
                                 analysis[repo]['no_priority_label']['count'],
                                 analysis[repo]['no_priority_label']['age'],
                                 analysis[repo]['fr_question']['count'],
                                 analysis[repo]['fr_question']['age'],
                                 analysis[repo]['prs']['count'],
                                 analysis[repo]['prs']['age']])

        print 'State of triage data written to file (../output_files/' + \
              file_time + '_triage_state.csv)'


if __name__ == "__main__":
    data = main('open')
    state_of_triage(data)
