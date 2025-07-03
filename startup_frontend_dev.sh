#!/bin/bash

set -a
source .env.dev
set +a

cd frontend && yarn && yarn start