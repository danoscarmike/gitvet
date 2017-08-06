import time

from datetime import datetime as dt

import check_rate_limit as crl


def get_issue_metadata(gh_login, org, repos, state):

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

    Raises:
        N/A
    """

    # Initialize dictionary for results
    data = {}

    for repo in repos:
        # set up repo specific variables, data structures and counters
        repo_path = org + '/' + repo
        data[repo_path] = {'open_issues_count': 0,
                           'prs': {'open_pr_count': 0,
                                   'pr_aggregate_age': 0},
                           'issues': {}}
        issue_counter = 0
        pr_counter = 0
        pr_aggregate_age = 0

        # get issue generator from GitHub
        print 'Getting issues from ' + org + '/' + repo
        issues = gh_login.issues_on(org, repo, state=state)

        for issue in issues:
            # check remaining rate limit
            if crl.remaining() > 100:
                pass
            else:
                print 'Rate limit low; going to sleep until rate resets'
                crl.print_remaining()
                time.sleep(crl.reset() - int(time.time()))

            created_date = issue.created_at.replace(tzinfo=None)

            if issue.pull_request():
                pr_counter += 1
                pr_aggregate_age += (dt.utcnow() - created_date).days
                continue
            else:
                issue_counter += 1
                print 'Adding issue number:', str(issue.number)
                # add this issue to the issues sub-dictionary in the
                # data dictionary (key is GitHub issue number)
                data[repo_path]['issues'][issue.number] = {}

                # add the issue's metadata to the new sub-dictionary
                data[repo_path]['issues'][issue.number]['created'] = \
                    issue.created_at.isoformat()
                data[repo_path]['issues'][issue.number]['updated'] = \
                    issue.updated_at.isoformat()
                data[repo_path]['issues'][issue.number]['title'] = \
                    issue.title
                if issue.assignee:
                    data[repo_path]['issues'][issue.number][
                        'assignee'] = issue.assignee.name

                # add list of issue's labels
                if issue.labels():
                    data[repo_path]['issues'][issue.number]['labels'] = [
                        label.name for label in issue.labels()
                        ]

        data[repo_path]['prs']['open_pr_count'] = pr_counter
        data[repo_path]['prs']['pr_aggregate_age'] = pr_aggregate_age
        data[repo_path]['open_issues_count'] = issue_counter

    data['updated'] = dt.utcnow().isoformat()

    return data
