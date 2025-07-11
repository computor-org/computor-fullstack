FROM prefecthq/prefect:2.20.3-python3.10

RUN apt-get update && apt-get install -y postgresql-client

RUN useradd -ms /bin/bash uvicorn
USER uvicorn
WORKDIR /home/uvicorn

ADD src /home/uvicorn/src
ADD migrations.sh /home/uvicorn/migrations.sh

RUN pip install --no-cache-dir --upgrade -r src/requirements.txt

ADD docker/api/startup.bash startup.bash