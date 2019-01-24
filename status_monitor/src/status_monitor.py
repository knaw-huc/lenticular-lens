from config_db import db_conn, run_query
from datasets_config import DatasetsConfig
import datetime
import errno
import json
import os
from psycopg2 import sql as psycopg2_sql
import requests
import shutil
import subprocess
import time
import urllib.request


if __name__ == '__main__':
    with open('/app/test_config.json', 'r') as config_file:
        config_data = json.load(config_file)

    while True:
        renamed_views = []
        job_id = None
        try:
            for resource in config_data['resources']:
                collection = DatasetsConfig().dataset(resource['dataset_id']).collection(resource['collection_id'])
                if collection.has_cached_view:
                    cached_view_name = collection.view_name
                    renamed_views.append(cached_view_name)
                    run_query(psycopg2_sql.SQL('ALTER VIEW {} RENAME TO {};').format(psycopg2_sql.Identifier(cached_view_name), psycopg2_sql.Identifier(cached_view_name + '_backup')))
                    run_query(psycopg2_sql.SQL('ALTER MATERIALIZED VIEW {} RENAME TO {};').format(psycopg2_sql.Identifier(cached_view_name + '_full'), psycopg2_sql.Identifier(cached_view_name + '_full_backup')))

            response = requests.post("http://web_server:8000/handle_json_upload/", data=json.dumps(config_data))
            job_id = response.json()['job_id']

            job_status = None
            while job_status not in ['Finished', 'Failed']:
                response = requests.get("http://web_server:8000/job/" + job_id)
                job_status = response.json()['status']
                time.sleep(5)

            if job_status == 'Finished':
                with urllib.request.urlopen("http://web_server:8000/job/%s/result/download" % job_id) as response,\
                     open('temp_results.nq.gz', 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)

                subprocess.run(['gzip', '-df', 'temp_results.nq.gz'])
                if subprocess.run(['md5sum', '-c', '/app/temp_results.nq.md5'], stdout=subprocess.PIPE).returncode == 0:
                    print('Smoke test passed at ' + str(datetime.datetime.now()))

        finally:
            for view_name in renamed_views:
                run_query(psycopg2_sql.SQL('ALTER VIEW {} RENAME TO {};').format(
                    psycopg2_sql.Identifier(view_name + '_backup'),
                    psycopg2_sql.Identifier(view_name)))
                run_query(psycopg2_sql.SQL('ALTER MATERIALIZED VIEW {} RENAME TO {};').format(
                    psycopg2_sql.Identifier(view_name + '_full_backup'),
                    psycopg2_sql.Identifier(view_name + '_full')))

            for filename in ['temp_results.nq.gz', 'temp_results.nq']:
                try:
                    os.remove(filename)
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise

            run_query(psycopg2_sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE;').format(psycopg2_sql.Identifier('job_' + job_id)))

        time.sleep(60 * 60)
