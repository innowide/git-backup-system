# git-backup-system

A small backup system for github repositories using a user token.

## Setup

This program uses docker engine version 3 to run.

- In the "src" folder, create and fill the ".env" file

```bash
touch .env
```

```txt
GITHUB_USER=your_github_username
GITHUB_TOKEN=your_github_token
TARGET=/repos-backup # Do not touch this
GITHUB_ORG=your_github_org (optional)
```

> :warning: The token must have the "repo" scope to be able to clone private repositories. You can create a token by following the following tutorial [here](https://docs.github.com/en/enterprise-server@3.6/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

- Next to the Dockerfile, create a "repos" folder.

```bash
mkdir repos
```

(it will be mounted into the container to get the json file and repos backups)

> :warning: The folder **must be owned** by the **same user** who runs the container. Otherwise, the container will not be able to write in it.

- Create a file named repos.conf in the newly created folder.

```bash
touch repos.conf
```

- Put the repos local names and http cloning url in the config file\

```txt
name1 https://github.com/url/to/repo1
name2 https://github.com/url/to/repo2
```

- Run docker to build & deploy container

```bash
docker compose up -d
```

> It will run the container in background and restart at boot or crash, you can check the logs with
>
> ```bash
> docker logs -f git-backup-system
> ```
>
> or attach to the container with
>
> ```bash
> docker attach git-backup-system
> ```
>
> to see what does the container do.

- Stop the container

```bash
docker compose down
```

> :warning: The container will not stop if you don't stop it manually. The scipt will check everyday at midnight if there is a new commit to backup by pulling the repos

## Some data

To see directly or notify once the backup is done, you can use the "repos.json" file generated in the mounted directory.\
It contains all the information needed to see the last pull date, most recent commit hash, error if one occured, etc...\

> :warning: The file is updated only when the backup is done, so if you want to see the current status of the backup, you can check the logs of the container.

## License

This project is licensed under the terms of the MIT license.
