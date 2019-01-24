#!/usr/bin/env bash

jobs_worker_instances=2
timbuctoo_worker_instances=5

. .env >/dev/null 2>&1

if [[ $? == 0 ]]; then
    echo "Environment configuration found. Settings applied."
else
    echo "No environment configuration found. Using default settings."
fi

docker-compose up \
    --build \
    --scale jobs_worker=${jobs_worker_instances} \
    --scale timbuctoo_worker=${timbuctoo_worker_instances} \
    "$@"
