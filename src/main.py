#!/bin/env python3
import os
import subprocess
import json
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
import time

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
        self.lastCommit = None

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
            "lastCommit": self.lastCommit,
            "error": self.error
        }

    def backup(self, root_dir: str, target: str = '.', token: str = ''):
        """
        Backs up the repo.
        """
        os.chdir(root_dir)
        if os.path.isdir(target + "/" + self.name):
            print("\nPulling {}...".format(self.name), end="")
            os.chdir(target + "/" + self.name)
            error = subprocess.run(["git", "pull"]).returncode
        else:
            print("Cloning {}...".format(self.name), end="")
            os.chdir(target)
            error = subprocess.run(["git", "clone", self.cloneUrl.replace("https://", "https://{}@".format(token)) , self.name]).returncode
            if error != 0:
                pass
            else:
                os.chdir(self.name)

        if error != 0:
            self.hasError = True
            self.error = error
            print("Error")
            print("Error backing up {}".format(self.name))
            return
        elif self.hasError:
            self.hasError = False
            self.error = None
        print('Done')

        new_hash = subprocess.getoutput("git rev-parse HEAD")
        self.lastPull = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print("Repo last pull:", self.lastPull)
        if new_hash != self.commitHash:
            print("Commit hash" + new_hash)
            self.commitHash = new_hash + ""
            self.lastCommit = subprocess.getoutput("git log -1 --format=%cd")
        else:
            print("Commit hash:", self.commitHash)

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
        if not os.path.isdir(self.target):
            os.mkdir(self.target)
        for repo in self.repos:
            self.repos[repo].backup(self.root_dir, self.target, self.github_token)
        os.chdir(self.target)
    
    def loadJson(self, path: str = 'repos.json'):
        """
        Loads the backup data from a JSON file.
        """
        print("Loading backup data from {}...".format(path))
        with open(path, 'r') as f:
            data = json.load(f)
            for repo in data['repos']:
                self.repos[repo] = repo_backup(repo)
                self.repos[repo].cloneUrl = data['repos'][repo].get('clone_url')
                self.repos[repo].commitHash = data['repos'][repo].get('commitHash', "HEYYYYYYY")
                self.repos[repo].lastPull = data['repos'][repo].get('lastPull')
                self.repos[repo].hasError = data['repos'][repo].get('hasError')
                self.repos[repo].error = data['repos'][repo].get('error')
                self.repos[repo].lastCommit = data['repos'][repo].get('lastCommit')
    @property
    def json(self):
        """
        Returns the backup data as a JSON string.
        """
        return json.dumps({
            "repos": {repo: self.repos[repo].dict for repo in self.repos}
        })

if __name__ == "__main__":
    user = os.getenv("GITHUB_USER")
    org = os.getenv("GITHUB_ORG")
    token = os.getenv("GITHUB_TOKEN")
    target = os.getenv("TARGET")
    
    repos = backupdata(user, org, token, target)
    
    while True:
        if os.path.exists(target + "/repos.conf"):
            with open(target + "/repos.conf", 'r') as f:
                repos_conf = f.readlines()
        else:
            time.sleep(1) # Prevents the script from using too much CPU
            raise Exception("No repos config found!")

        for repo in repos_conf:
            repo = repo.split(' ')
            if len(repo) != 2:
                raise Exception("Invalid repos config!")
            if repo[0] not in repos.repos:
                repos.repos[repo[0]] = repo_backup(repo[0])
                repos.repos[repo[0]].cloneUrl = repo[1].strip()

        now = datetime.now()
        repos.backup()
        print("Backup finished in {} seconds.".format((datetime.now() - now).seconds))

        with open(target + "/repos.json", 'w+') as f:
            f.write(repos.json)
        print("Backup data saved to repos.json")
        print("Next backup at midnight...")
        midnight = datetime(now.year, now.month, now.day, 0, 0, 0) + timedelta(days=1)
        now = datetime.now()
        print("Going to sleep for {} seconds...".format((midnight - now).seconds))
        time.sleep((midnight - now).seconds)