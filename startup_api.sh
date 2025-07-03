#!/usr/bin/env bash

set -a
source .env.dev
set +a

cd src && python3 server.py