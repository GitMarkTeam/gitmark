# GitMark

[![](https://images.microbadger.com/badges/version/gitmark/gitmark.svg)](https://microbadger.com/images/gitmark/gitmark "gitmark") [![](https://images.microbadger.com/badges/image/gitmark/gitmark.svg)](https://microbadger.com/images/gitmark/gitmark "gitmark")

## Features

GitMark is an application to manage GitHub repositories(including your starred repositories and the repositories you want to collect to a list).

The following features are applied by GitMark:

- Manage your favorite GitHub repositories
  - Import your starred repotories from GitHub
  - Manage repository records in GitMark
- Manage repositories by tags(Not yet)
- Add repositories to collections
- Share collections(Not yet)
- Add references for specified repository(Not yet)

## Demo

[GitMark](http://gitmark.igevin.info)


## How to use

It is recommended to run GitMark with docker image, you can get the image as follow:

```bash
(sudo) docker pull gitmark/gitmark
```

Then run with `docker-compose` with a 'docker-compose.yml' file like this:

```yaml

gitmark:
  # restart: always
  image: gitmark/gitmark
  ports:
    - "8000:8000"
    # - "5000:5000"
  links:
    - mongo:mongo
    - redis:redis

  env_file: .env

mongo:
  # restart: always
  image: mongo:3.2

  volumes:
    - /mongo/data

redis:
  # restart: always
  image: redis:3.0
```

At least you need to set these environment variables:

```bash

# GitHub OAuth Application details:
export GITHUB_ID=some-github-id
export GITHUB_SECRET=some-github-secret

# I use basic auth with GitHub APIs, so GitHub username and password are needed
export APP_USER=someone
export APP_PASS=some_password

# Currently I use qiniu(http://www.qiniu.com/) to store images:
export QINIU_AK=some-qiniu-ak
export QINIU_SK=some-qiniu-sk
export BUCKET=some-bucket
export QINIU_URL=http://qiniu.igevin.tech/
```

### Superuser Creation

If you set this environment varible, you can create superusers:

```bash
export allow_su_creation=true
```

Then you can visit the superuser creation page:

```
http://some-domain/accounts/registration/su/
```