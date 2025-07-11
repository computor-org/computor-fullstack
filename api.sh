#!/bin/bash

set -a
source .env
set +a

cd src && python3 server.py