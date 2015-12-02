#!/usr/bin/python
# vim: set fileencoding=utf-8

import argparse
import json
import sys
import os
import github
import datetime

USER_TOKEN = ""
ISSUE_PROPS = ('created_at', 'closed_at', 'updated_at', 'id', 'pull_request', 'state')
REPO_PROPS = ('watchers_count', 'forks_count', 'network_count')
THREE_MONTHS = PRG = ('/', '\\', '-')

args = argparse.ArgumentParser()
args.add_argument('-d', '--daysback', type=int, help='Obtain information no older then the specified number of days', default=14)
args.add_argument('repo_name')
parsed = args.parse_args()

def progress(s=' ', n=1):
  sys.stdout.write('\r' + s + PRG[n % len(PRG)])
  sys.stdout.flush()

def get_last_years_commits(repo):
  activity = repo.get_stats_commit_activity()
  if not activity:
    return []
  return [x.total for x in activity]

def get_issues(repo, days, state='open'):
  issues, n = [], 0
  for x in repo.get_issues(since=datetime.datetime.now() - datetime.timedelta(days=days), state=state):
    progress('Fetching issues ', n)
    issues.append(dict(
      zip(ISSUE_PROPS, 
          [getattr(x, p) for p in ISSUE_PROPS])
    ))
    n += 1
  sys.stdout.write('\r')
  return issues

def get_repo_stats(repo):
  x = dict(
      zip(REPO_PROPS, 
          [getattr(repo, p) for p in REPO_PROPS]))
  # contributors doesn't contain much useful info
  # x.update({'contributors': [(y.author.login, y.author.email) for y in repo.get_stats_contributors()]})
  return x

def reducer((issues, issues_closed, prs, prs_closed), item):
  if item['pull_request']:
    if item['state'] == "open":
      prs.append(item)
    else:
      prs_closed.append(item)
  else:
    if item['state'] == "open":
      issues.append(item)
    else:
      issues_closed.append(item)
  return (issues, issues_closed, prs, prs_closed)

gh = github.Github(USER_TOKEN)
repo = gh.get_repo(parsed.repo_name)

number_of_commits = dict(last_year_commits=sum(get_last_years_commits(repo)))
notoriety = get_repo_stats(repo)

all_issues_prs = get_issues(repo, parsed.daysback, 'all')

issues_open, issues_closed, pull_requests_open, pull_requests_closed = reduce(reducer, all_issues_prs, ([], [], [], []))

issues = dict(opened_issues=len(issues_open), closed_issues=len(issues_closed),
     opened_prs=len(pull_requests_open), closed_prs=len(pull_requests_closed))

if notoriety:
  issues.update(notoriety)
if number_of_commits:
  issues.update(number_of_commits)

json.dump(issues, sys.stdout)
