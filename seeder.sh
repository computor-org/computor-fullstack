#!/bin/bash

set -a
source .env.dev
set +a

cd src && python seeder.py