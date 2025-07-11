#!/bin/bash

set -a
source .env
set +a

cd frontend && yarn && yarn start