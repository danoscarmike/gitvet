import time

from datetime import datetime as dt

import check_rate_limit as crl


def read_issue_metadata(gh_login, repos, state):

    # Function accepts a github3 login object and a list of repos to read from.
    # Function returns a custom data structure continaing issue metadata

    org = 'googlecloudplatform'

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
