#!/usr/bin/env bash

timbuctoo_worker_instances=5
alignments_worker_instances=2
clusterings_worker_instances=2

. .env >/dev/null 2>&1

if [[ $? == 0 ]]; then
    echo "Environment configuration found. Settings applied."
else
    echo "No environment configuration found. Using default settings."
fi

docker-compose up \
    --build \
    --scale timbuctoo_worker=${timbuctoo_worker_instances} \
    --scale alignments_worker=${alignments_worker_instances} \
    --scale clusterings_worker=${clusterings_worker_instances} \
    "$@"
