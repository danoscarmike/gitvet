import os
import six
import sys

from datetime import datetime as dt

import github3

from google.cloud import bigquery


def events_to_bigquery(org, repo_file):
    '''Docstring goes here
    It will be multiline
    '''

    # Test variables
    project_id = 'gapic-test'
    dataset_name = 'oneplatform_veneer_github'
    table_name = 'events'

    # Initialize bigquery client, dataset and table
    client = bigquery.Client(project=project_id)
    dataset = client.dataset(dataset_name)
    table = dataset.table(table_name)

    table.reload()

    # If dataset or table name is invalid abort
    if not dataset.exists():
        print('Dataset %s does not exist.' % dataset_name)
        return
    if not table.exists():
        print('Table %s does not exist.' % table_name)
        return
    if not table.schema:
        print('Schema not set for table %s' % table.name)
        return

    # Prepare for GitHub calls
    org = six.text_type(org)

    with open(repo_file) as f:
        repos = f.readlines()
    repos = [x.strip() for x in repos]

    # Authenticate with GitHub using Personal Access Token
    g = github3.login(token=os.environ['GH_TOKEN'])

    # Get data and write to BigQuery table
    for repo in repos:
        rows = []
        print('Getting events from %s' % repo)
        for event in g.repository(org, repo).events(500):
            if event.type in ['IssuesEvent', 'IssueCommentEvent']:
                issue = event.as_dict()['payload']['issue']
                issue_id = issue.number
                if event.as_dict()['payload']['issue'].labels():
                    labels = six.text_type([label.name for label in
                                            issue.labels()])
                    print labels
            elif event.type in ['PullRequestEvent']:
                issue_id = event.as_dict()['payload']['number']
                labels = None
            else:
                continue
            rows.append((repo, event.id, event.type,
                         event.as_dict()['payload']['action'],
                         event.created_at.isoformat(), event.actor.login,
                         labels, issue_id))
        table.insert_data(rows)


if __name__ == "__main__":
    events_to_bigquery(sys.argv[1], sys.argv[2])
