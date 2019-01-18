#!/usr/bin/env bash

if ps ax | grep -v grep | grep "python\s/app/jobs_worker.py" >/dev/null; then
    echo "Worker running";
else
    echo -e "\e[1m\e[91mWorker NOT running!\e[0m"
fi

python /app/status.py