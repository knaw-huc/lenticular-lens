#!/bin/sh
docker run --rm -it --link postgres:postgres postgres psql -h postgres -U postgres
