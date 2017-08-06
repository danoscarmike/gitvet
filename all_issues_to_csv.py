import csv
from datetime import datetime as dt
import github3
import os
import time


def all_issues_to_csv():

    # read in organizations
    with open('./inputs/GITHUB_ORGS') as f:
        organizations = f.readlines()
        organizations = [x.strip() for x in organizations]
    
    # read in repositories
    with open('./inputs/REPOS') as f:
        repos = f.readlines()
        repos = [x.strip() for x in repos]

    # organizations = ['']
    # repos = ['']
    # file_tag = ''

    # Authenticate with GitHub using Personal Access Token
    g = github3.login(token=os.environ('GH_TOKEN'))
    new_file = '../output_files/' + dt.now().strftime("%Y%m%d") + file_tag + '_all_issues.csv'

    with open(new_file , 'w') as csvfile:
        print "Writing to file {}".format(new_file)
        datawriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        datawriter.writerow(['issue_id', 'org', 'repo', 'issue_number',
                             'issue_is_pr', 'issue_title', 'issue_created_at',
                             'issue_updated_at', 'issue_closed_at',
                             'repo_open_issues_count', 'issue_labels'])
        org_counter = 0
        for org in organizations:
            org_counter += 1
            # call github for all repos in the org
            all_repos_in_org = g.repositories_by(org)
            repo_counter = 0
            for repo in all_repos_in_org:
                repo_counter += 1
                if repo.name in repos:
                    repo_path = org + '/' + repo.name + '/'
                    if repo.has_issues:
                        for issue in repo.issues(state='all'):
                            print "Org {}/{}. Writing issue {}{}"\
                                .format(org_counter,len(organizations),
                                repo_path, issue.number)
                            created_date = issue.created_at.replace(tzinfo=None)
                            if issue.updated_at:
                                updated_date = issue.updated_at.replace(tzinfo=None)
                            else:
                                updated_date = issue.updated_at
                            if issue.closed_at:
                                closed_date = issue.closed_at.replace(tzinfo=None)
                            else:
                                closed_date = issue.closed_at
                            issue_labels = [label.name.encode('utf-8','ignore')
                                            for label in issue.labels()]
                            issue_title = issue.title.encode('utf-8','ignore')
                            if issue.pull_request():
                                issue_is_pr = 'TRUE'
                            else:
                                issue_is_pr = 'FALSE'
                            datawriter.writerow([issue.id, org, repo,
                                                issue.number, issue_is_pr,
                                                issue_title, created_date,
                                                updated_date, closed_date,
                                                repo.open_issues_count,
                                                issue_labels])

if __name__ == "__main__":
    all_issues_to_csv()
