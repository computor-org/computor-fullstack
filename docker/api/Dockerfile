FROM prefecthq/prefect:2.20.3-python3.10

RUN apt-get update && apt-get install -y postgresql-client

RUN useradd -ms /bin/bash uvicorn
USER uvicorn
WORKDIR /home/uvicorn

ADD src /home/uvicorn/src
ADD db /home/uvicorn/db
ADD docker/api/migrations_up.sh /home/uvicorn/migrations_up.sh
ADD docker/api/alembic_up.sh /home/uvicorn/alembic_up.sh

RUN pip install --no-cache-dir --upgrade -r src/requirements.txt

ADD docker/api/startup.bash startup.bash