#!/bin/env python3
import github3
import requests
import shutil
import os
from os import getcwd, chdir
from subprocess import getoutput
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class repo_backup:
    """
    A class to represent a GitHub repository.
    """
    def __init__(self, name: str = ''):
        self.commitHash = None
        self.lastPull = None
        self.hasError = False
        self.error = None
        self.cloneUrl = None
        self.name = name

    @property
    def dict(self):
        """
        Returns the repo as a dictionary.
        """
        return {
            "clone_url": self.cloneUrl,
            "commitHash": self.commitHash,
            "lastPull": self.lastPull,
            "hasError": self.hasError,
            "error": self.error
        }

    def backup(self, root_dir: str, target: str = '.', token: str = ''):
        """
        Backs up the repo.
        """
        chdir(root_dir  )
        if os.path.isdir(("{}/" + self.name).format(target)):
            print("Pulling {}...".format(self.name), end="")
            chdir(("{}/" + self.name).format(target))
            getoutput("git pull")
            chdir("..")
        else:
            print("Cloning {}...".format(self.name), end="")
            getoutput("git clone {} {}/{}".format(
                self.cloneUrl.replace("https://", "https://{}@".format(
                    token
                )),
                target,
                self.name
            ))
        print('Done')

        chdir(("{}/" + self.name).format(target))
        self.commitHash = getoutput("git rev-parse HEAD")
        self.lastPull = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print("Repo last pull:", self.lastPull)
        print("Commit hash:", self.commitHash, end="\n\n")
        chdir("..")

class backupdata:
    """
    A class to represent the repositories to backup.
    """
    def __init__(self, user: str = '', org: str = '', token: str = '', target: str = '', root_dir: str = os.getcwd()):
        self.github_user = user
        self.github_org = org
        self.github_token = token
        self.target = target
        self.repos = {}
        self.root_dir = root_dir

    def backup(self):
        """
        Backs up the repositories.
        """
        for repo in self.repos:
            self.repos[repo].backup(self.root_dir, self.target, self.github_token)

user = os.getenv("GITHUB_USER")
org = os.getenv("GITHUB_ORG")
token = os.getenv("GITHUB_TOKEN")
target = os.getenv("TARGET")

res = requests.get("https://api.github.com/orgs/{}/repos".format(org), auth=(user, token))
repos = backupdata(user, org, token, target)

for repo in res.json():
    repos.repos[repo['name']] = repo_backup(repo['name'])
    repos.repos[repo['name']].cloneUrl = repo['clone_url']

repos.backup()