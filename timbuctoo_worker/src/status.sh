#!/usr/bin/env bash

if ps ax | grep -v grep | grep "python\s/app/timbuctoo_worker.py" >/dev/null; then
    echo "Timbuctoo worker running";
else
    echo -e "\e[1m\e[91mTimbuctoo worker NOT running!\e[0m"
fi

python /app/status.py