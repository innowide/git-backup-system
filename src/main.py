#!/bin/env python3
import os
import subprocess
import json
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
import time
import requests

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
        os.chdir(root_dir) # Ensure we are in the root directory
        if os.path.isdir(target + "/" + self.name): # Check if the repo is already cloned
            print("\nPulling {}...".format(self.name), end="") # Pull the repo
            os.chdir(target + "/" + self.name)
            error = subprocess.run(["git", "pull"]).returncode
        else:
            print("Cloning {}...".format(self.name), end="") # Clone the repo
            os.chdir(target)
            error = subprocess.run(["git", "clone", self.cloneUrl.replace("https://", "https://{}@".format(token)) , self.name]).returncode

            if error != 0: # Check if the repo was cloned successfully
                pass
            else:
                os.chdir(self.name)

        if error != 0: # Set error and skip the rest of the backup opetations if there was an error
            self.hasError = True
            self.error = error
            print("Error")
            print("Error backing up {}".format(self.name))
            return
        elif self.hasError: # Reset the error if there was no error this time
            self.hasError = False
            self.error = None
        print('Done')

        new_hash = subprocess.getoutput("git rev-parse HEAD") # Update or construct the commit information
        self.lastPull = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print("Repo last pull:", self.lastPull)
        print("Commit hash" + new_hash)
        self.commitHash = new_hash
        self.lastCommit = subprocess.getoutput("git log -1 --format=%cd")

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
        self.failed_repos = []

    def backup(self):
        """
        Backs up the repositories.
        """
        if not os.path.isdir(self.target):
            os.mkdir(self.target)
        for repo in self.repos:
            self.repos[repo].backup(self.root_dir, self.target, self.github_token)
            if self.repos[repo].hasError:
                self.failed_repos.append(repo)

        os.chdir(self.target)

    def backup_failed(self):
        """
        Backs up the failed repositories.
        """
        failed_repos = []
        for repo in self.failed_repos:
            self.repos[repo].backup(self.root_dir, self.target, self.github_token)
            if self.repos[repo].hasError:
                failed_repos.append(repo)
        self.failed_repos = failed_repos

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
    load_dotenv()

    user = os.getenv("GITHUB_USER") # Load the environment variables from .env
    org = os.getenv("GITHUB_ORG")
    token = os.getenv("GITHUB_TOKEN")
    target = os.getenv("TARGET")
    slack_webhook = os.getenv("SLACK_WEBHOOK")
    max_tries = int(os.getenv("RETRY_COUNT"))
    retry_delay = int(os.getenv("RETRY_DELAY"))
    error_retry = os.getenv("ERROR_RETRY")
    print("Retry on error:", error_retry)

    use_slack = False

    if not slack_webhook:
        use_slack = False
        print("No Slack webhook found!")
    else:
        use_slack = True
    if not user:
        time.sleep(1) # Prevents the script from using too much CPU
        raise Exception("No github user found!")
    if not token:
        time.sleep(1) # Prevents the script from using too much CPU
        raise Exception("No github token found!")
    if not user:
        time.sleep(1) # Prevents the script from using too much CPU
        raise Exception("No github user found!")

    while True:
        repos = backupdata(user, org, token, target) # Create/Recreate the backupdata object

        if os.path.exists(target + "/repos.conf"):
            with open(target + "/repos.conf", 'r') as f:
                repos_conf = f.readlines()
        else:
            time.sleep(1) # Prevents the script from using too much CPU
            raise Exception("No repos config found!")

        for repo in repos_conf: # Check & load the repos from the config
            repo = repo.split(' ')
            if len(repo) != 2:
                raise Exception("Invalid repos config!")
            if repo[0] not in repos.repos:
                repos.repos[repo[0]] = repo_backup(repo[0])
                repos.repos[repo[0]].cloneUrl = repo[1].strip()

        if use_slack: # Send slack startup message
            print("Sending slack startup message...")
            requests.post(slack_webhook, json={"text": "*Starting backup*..."})

        now = datetime.now() # Backup the repos
        repos.backup()
        time_elapsed = (datetime.now() - now).seconds
        print("Backup finished in {} seconds.".format(time_elapsed))


        if use_slack: # Send slack backup end message
            print("Sending slack checkup message...")
            text = "*Backup finished in {} seconds.*\n".format(time_elapsed)
            for repo in repos.repos:
                if repos.repos[repo].hasError:
                    text += "> :x: Error backing up {}: {}\n".format(repo, repos.repos[repo].error)
                else:
                    text += "> :white_check_mark: Successfully backed up {}.\n".format(repo)
            requests.post(slack_webhook, json={"text": text})

        if error_retry == "True":
            tries = 0
            while len(repos.failed_repos) > 0 and tries < max_tries: # Backup the failed repos
                tries += 1
                print("Retry in " + str(retry_delay) + " seconds...")
                time.sleep(retry_delay)
                print("Backing up failed repos...")
                now = datetime.now()
                repos.backup_failed()
                time_elapsed = (datetime.now() - now).seconds
                if use_slack: # Send slack backup end message
                    print("Sending slack checkup message...")
                    text = "*Failed repos backup try finished in {} seconds.*\n".format(time_elapsed)
                    if len(repos.failed_repos) == 0:
                        do_sleep = False
                        text += "> :white_check_mark: Successfully backed up all failed repos.\n"
                    else:
                        do_sleep = True
                        for repo in repos.repos:
                            if repos.repos[repo].hasError:
                                text += "> :x: Error backing up {}: {}\n".format(repo, repos.repos[repo].error)
                    requests.post(slack_webhook, json={"text": text})

        print("Saving backup data to" + target + "/repos.json")
        with open(target + "/repos.json", 'w+') as f: # Save the backup json data
            f.write(repos.json)
        print("Backup data saved to repos.json")
        print("Next backup at midnight...") # Wait until midnight
        midnight = datetime(now.year, now.month, now.day, 0, 0, 0) + timedelta(days=1)
        now = datetime.now()
        print("Going to sleep for {} seconds...".format((midnight - now).seconds))
        time.sleep((midnight - now).seconds)
