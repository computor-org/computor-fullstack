# Computor Server
## Getting started

Required for development
* psql (Postgres 16)
  * On MacOS, if `psql` is not available after install, do `brew link postgresql@16`
* docker, docker-compose
  * Windows: Docker Desktop (makes `docker` command available also in WSL)
  * MacOS: OrbStack
  * Linux: Docker
* python 3.10
* git
  * Be sure to set your name and email in git!

Clone the repos
```bash
git clone git@github.com:computor-org/computor-fullstack.git
```

Setup a virtual environment on Python 3.10 with
```bash
deactivate
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

Make sure that Docker (or orbstack on MacOS) are running. Start the development environment with
```bash
cd execution-backend-stub
bash startup_dev.sh
```
This will start all services, except the Python FastAPI. This Python service already needs an existing database. For development this process is done manually. In the productive mode, `startup_prod.sh` handles the database setup already.

Be sure that the local PostgreSQL server is disabled, so the one exposed by Docker is used! E.g. on Ubuntu
```
sudo systemctl stop postgresql
sudo systemctl disable postgresql
```

Start the migration with
```bash
bash migrations_up.sh
```


Start
```bash
bash alembic_up.sh
```
to migrate the schema to the current version.

Start the server with
```
bash startup_fastapi_dev.sh
```
Check if the server is running API docs on http://0.0.0.0:8000/docs .

Start the system agent with
```
bash startup_system_agent_dev.sh
```

Install the CLI with
```bash
pip install -e src
```

Start the CLI with
```bash
computor
```
and see if it runs.
## Creating a Course
You find the course definition template in `docs/course.yaml`. To create a course, you need a gitlab group. Add the relevant group members. The system will need API tokens with `owner` privileges. Now create a group access token with role `owner` and access to

* api
* read_repository
* write_repository
* create_runner
* manage_runner

Make a copy of `docs/course.yaml` and edit it. Be **careful** not to put dashes, numbers alone, or any special characters into any fields.

* Set `organization.gitlab.parent` to the parent group ID in gitlab. Set your organization and course family name.
* Set `course.executionBackends.slug` to `itp-python`.

If you have access to an already existing course, you can create a new course from the assignments repository with

* Set `course.source.url` to `https://gitlab.com/.../assignments.git`
* Create a read access token for the source repository and copy it to `course.source.token`.


Login with

```bash
computor login
Auth method (basic, gitlab, github): basic
API url: http://localhost:8000
Username: admin
Password: admin
```
These are the defaults in the template `.env.dev`

Create the course with

```bash
computor apply -f course.yaml -d true
```

Get the course ID with

```bash
computor rest list -t courses
````

Copy `docs/users.csv`, keep the header line and add your own GitLab user with role `_maintainer` (with an underline). You can retrieve your GitLab username by clicking your profile picture. Then run

```bash
computor import users -f users.csv -c <course_id>
```

Don't forget to stop the services with CTRL+C !
