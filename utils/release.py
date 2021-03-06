#! /usr/bin/env python

import argparse
import sys

import semver
import git
import bump_cwl_version


parser = argparse.ArgumentParser(
  description='Create a git release')
parser.add_argument(
  '--major',
  action='store_true',
  help='creates a major release')
args = parser.parse_args()
major_bump = args.major

repo = git.Repo('.') # Assumes script is run from repo root
assert not repo.is_dirty(), 'Cannot create a release: repo is dirty. Commit first, then rerun script.'

# Ensure everything is up to date
repo.remote().fetch()
branch = repo.active_branch
if branch.name != 'main':
  raise Exception(f'The active branch is {branch}, not main. Please switch to main before performing a release.')

# This assumes the remote is named origin
commits_behind = len(list(repo.iter_commits('main..origin/main')))
if commits_behind != 0:
  raise Exception(f'Branch is {commits_behind} commits behind remote. Pull before attempting release.')

# Ensure the branch has a tracking_branch set
tracking_branch = branch.tracking_branch()
if tracking_branch is None:
  raise Exception('Please set a tracking branch before attempting release.')

# Find the latest tag
tags = repo.tags
tags_sorted = sorted(repo.tags, key=lambda t: t.commit.committed_date)
last_tag = str(tags_sorted[-1])

# Use semver to create the new version
current_version = semver.VersionInfo.parse(last_tag[1:])
if major_bump:
  new_version = current_version.bump_major()
else:
  new_version = current_version.bump_minor()

# Update the version for all cwl tools
tools_dir = 'cwl' # assuming relative to repo root
templates_dir = "template"
bump_cwl_version.main(tools_dir=tools_dir, new_version=str(new_version),
                      templates_dir=templates_dir)

# Check whether repo is dirty before attempting commit
if repo.is_dirty():
  repo.git.add(tools_dir)
  # '[skip-ci]' in commit to avoid the next patch increment --
  # ci will run when the tag is pushed below
  repo.git.commit( m=f'Update docker image version in CWL tool to {new_version} [skip-ci]' )
  repo.remote().push()

# Create and push the new tag
new_tagname = f'v{str(new_version)}'
new_tag = repo.create_tag(new_tagname)
repo.remote().push(new_tag)
