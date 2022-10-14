# Trogs

## Description
This is the source code to my newest [audio-streaming site](https://mushmud.com).  This is a 2020 rewrite and redesign of a [site originally created in 2009](https://github.com/davidwmartines/MushMud-Archive).  The intent is to provide a very simple and clean DIY audio streaming and sharing platform, geared towards independent musicians.  There are purposely no social features such as liking, commenting, following, etc.

### Tech
The server-side component of site is written in Python using the Flask framework.  The client-side scripting is minimal, and uses JQuery to coordinate playlist functionality across html audio elements.  The "Create" section of the site, where users can upload their own music, is implemented as a simple SPA using Vue.js and Bootstrap.

## Architecture
The app uses a very simple architecture, leveraging a few AWS services as well as Auth0 for authentication:

#### Elastic Beanstalk
The Flask app is deployed to an Elastic Beanstalk instance.  The deployment is done via a GitHub commit action which, upon commit to the master branch, creates and uploads a source code package to AWS and triggers a deploy.

#### S3
An S3 bucket is used to store and serve the user-uploaded images and audio files.  Users can create create songs on the site by uploading any of several types of audio files streamable through native browser support of the HTML5 audio element (MP3, M4A, OGG, Flac, Wave).  Users can upload artist-profile images and album-cover artwork as JPEG files, which are resized and cached in S3 using the Flask-Resize library.

#### DynamoDB
A single DynamoDB table houses the data for all artist, album, and track entities.  To keep costs **low** (i.e. below AWS free-tier limits, i.e. $0), careful use of Global Secondary Indexes (GSIs) and read/write request unit allocation is used.  All views and API GET requests on the site are loaded using single queries against specially designed GSIs, (no scans used at all), making use of overloaded indexes and compound result sets.

#### Auth0
Auth0 (via authlib) is used to let users authenticate and access the "Create" section of the site.  Currently enabled are the Google, Amazon, and Auth0 providers.


## Dev Env Setup

1. ensure using the right venv (python interpreter)
2. set env vars:

```
# Auth0 stuff, for authentication
AUTH0_ACCESS_TOKEN_URL
AUTH0_AUTHORIZE_URL
AUTH0_API_BASE_URL
AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET

# S3 bucket for images and audio files
AWS_CONTENT_BUCKET

# set to 'development' for local debug mode.
FLASK_ENV

# for session
FLASK_SECRET_KEY
```

optional:
```
# override the default aws profile, e.g. use 'local' for development:
AWS_PROFILE
# when using local, need this:
AWS_ENDPOINT_URL

# these override the applied aws profile with settings specific to connecting to S3.
# these are used locally so we can connect to remote S3 for images and uploading,
# but still use the current aws profile for DynamoDB.
AWS_CONTENT_ACCESS_KEY_ID
AWS_CONTENT_SECRET_ACCESS_KEY
AWS_CONTENT_REGION
```

3. (optional) setup a local DynamoDB:

```sh

docker-compose up -d
cd ./data
./create_table.sh
./import_data.sh
```
To use the local db, set these env vars:
```sh
export AWS_PROFILE=local
export AWS_ENDPOINT_URL=http://localhost:8042
```

Local AWS requires an aws profile called "local".

Add to `~/.aws/config` :
```
[profile local]
region = localhost
output = json
```

Add to `~/.aws/credentials` :
```
[local]
aws_access_key_id = <any 6 char random string>
aws_secret_access_key = <any 6 char random string>
```
Note: If using **NoSQLWorkbench** to connect to local DynamoDB, use the same values for `aws_access_key_id` and `aws_secret_access_key` that it uses.

4. Start:
```sh
python3 trogs_app/application.py
```

## Deployment to Elastic Beanstalk

Automated deplyment to Elastic Beanstalk is performed by a GitHub Action, defined in 
`./.github/workflows/deploy-to-eb.yml`.  

The depoloyment is trigged by any commit to the `master` branch.

Only the **trogs_app** directory (where the actual Flask app lives) gets zipped and uploaded.  Therefore the `requirements.txt` is there.  


### Temporary hack due to EB and python requirements (and my ignorance) ### 

*Need to make sure **pyodbc** is not in `/trogs_app/requirements.txt`, since pyodbc does not seem to install in EB and breaks the EB environment.  So need to manually remove after runnning pip freeze!*  

Pyodbc **IS** in the root level `requirements.txt` file, since it is used in the utils/importer module, for extracting data from the legacy SQL database.  (utils is only for local use, and not deployed to EB.)


## Update 10/2021
Since my AWS Free Account expired, as of now I am hosting in Azure using a B1 app service.  The following Application Settings just need to be set:
```
AUTH0_ACCESS_TOKEN_URL
AUTH0_API_BASE_URL
AUTH0_AUTHORIZE_URL
AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET
AWS_ACCESS_KEY_ID
AWS_CONTENT_BUCKET
AWS_DEFAULT_REGION
AWS_SECRET_ACCESS_KEY
FLASK_SECRET_KEY
```

## Update 10/2022
Back on AWS, since Azure got too expensive.
