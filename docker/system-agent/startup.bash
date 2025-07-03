#!/bin/bash

python /home/prefect/flows.py
prefect agent start --pool $PREFECT_WORK_POOL --work-queue $PREFECT_WORK_QUEUE
