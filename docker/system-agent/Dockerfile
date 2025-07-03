FROM prefecthq/prefect:2.20.3-python3.10

ARG SYSTEM_GIT_NAME
ARG SYSTEM_GIT_EMAIL

ENV SYSTEM_GIT_NAME=${SYSTEM_GIT_NAME}
ENV SYSTEM_GIT_EMAIL=${SYSTEM_GIT_EMAIL}

RUN useradd -ms /bin/bash prefect
USER prefect
WORKDIR /home/prefect

ADD docker/system-agent/requirements.txt /home/prefect/requirements.txt
ADD docker/system-agent/flows.py /home/prefect/flows.py
ADD docker/system-agent/startup.bash /home/prefect/startup.bash
ADD src/ctutor_backend /home/prefect/ctutor_backend

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN git config --global user.email "${SYSTEM_GIT_EMAIL}"
RUN git config --global user.name "${SYSTEM_GIT_NAME}"