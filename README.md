# Trogs!

## Description
todo

## Design
todo

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
```

optional:
```
AWS_PROFILE
AWS_ENDPOINT_URL
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
