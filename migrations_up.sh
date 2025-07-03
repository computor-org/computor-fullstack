#!/bin/bash

set -e

set -a
source .env.dev
set +a

export PGPASSWORD=${POSTGRES_PASSWORD}

DB_CONNECT_RETRIES=5

until psql -p ${POSTGRES_PORT} -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "select 1" > /dev/null 2>&1 || [ $DB_CONNECT_RETRIES -eq 0 ]; do
    echo "Waiting for postgres server [${DB_CONNECT_RETRIES}]..."
    ((DB_CONNECT_RETRIES=DB_CONNECT_RETRIES-1))
    sleep 5
done

TABLE_EXISTS=$(psql -p ${POSTGRES_PORT} -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tAc "SELECT to_regclass('public.user');" | tr -d '"')

if [ $TABLE_EXISTS == "user" ]; then
    echo "Db already initialised."
else
    SQL_DIR="db/migrations/"

    for sql_file in $(ls $SQL_DIR | grep -E '^V[0-9]+\.[0-9]+_.*\.sql$' | sort); do
        echo "Running migration: $sql_file"
        psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -d ${POSTGRES_DB} -U ${POSTGRES_USER} -a -f "$SQL_DIR/$sql_file"
    done
fi