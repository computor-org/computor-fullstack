#!/bin/bash

bash migrations_up.sh
bash alembic_up.sh
cd src && python server.py