import pytz
import time

from datetime import datetime as dt

import check_rate_limit as crl


def get_issue_metadata(gh_login, repos, state):

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

    # Initialize dictionary for results
    data = {}
    for repo in repos:
        # set up repo specific variables, data structures and counters
        data[repo] = {'open_issues_count': 0,
                      'prs': {'open_pr_count': 0,
                              'pr_aggregate_age': 0},
                      'issues': {}}
        issue_counter = 0
        pr_counter = 0
        pr_aggregate_age = 0

        # get issue generator from GitHub
        print('Getting issues from %s' % repo)
        org, repo_name = repo.split("/")
        issues = gh_login.issues_on(org, repo_name, state=state)

        for issue in issues:
            # check remaining rate limit
            if crl.remaining() > 100:
                pass
            else:
                print('Rate limit low; going to sleep until rate resets')
                crl.print_remaining()
                time.sleep(crl.reset() - int(time.time()))

            created_date = issue.created_at

            if 'pull_request' in issue.as_dict():
                pr_counter += 1
                pr_aggregate_age += (dt.now(pytz.utc) - created_date).days
                continue
            else:
                issue_counter += 1
                print('Adding issue number: %d' % issue.number)
                # add this issue to the issues sub-dictionary in the
                # data dictionary (key is GitHub issue number)
                data[repo]['issues'][issue.number] = {}

                # add the issue's metadata to the new sub-dictionary
                data[repo]['issues'][issue.number]['created'] = \
                    issue.created_at.isoformat()
                data[repo]['issues'][issue.number]['updated'] = \
                    issue.updated_at.isoformat()
                data[repo]['issues'][issue.number]['title'] = \
                    issue.title
                if issue.assignee:
                    data[repo]['issues'][issue.number][
                        'assignee'] = issue.assignee.login

                # add list of issue's labels
                if issue.labels():
                    data[repo]['issues'][issue.number]['labels'] = [
                        label.name for label in issue.labels()
                        ]

        data[repo]['prs']['open_pr_count'] = pr_counter
        data[repo]['prs']['pr_aggregate_age'] = pr_aggregate_age
        data[repo]['open_issues_count'] = issue_counter

    data['updated'] = dt.now(pytz.utc).isoformat()

    return data
