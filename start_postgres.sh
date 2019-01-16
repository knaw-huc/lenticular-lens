#!/bin/sh
docker build -t postgres_timbuctoo . && docker run --rm -it -p:5432:5432  --name postgres -e POSTGRES_PASSWORD= -e PGDATA=/pgdata -v pgdata:/pgdata postgres_timbuctoo
