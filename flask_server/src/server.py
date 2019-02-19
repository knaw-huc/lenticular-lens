from datasets_config import DatasetsConfig
from config_db import db_conn
import datetime
from flask import Flask, jsonify, request, send_file
from helpers import get_job_data, hash_string, update_job_data
import json
import psycopg2
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
import random
import time
app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/datasets')
def datasets():
    return jsonify(DatasetsConfig().data)


@app.route('/handle_json_upload/', methods=['POST'])
def handle_json_upload():
    resources_json = json.dumps(request.json['resources'], indent=2)
    resources_filename = './generated_json/resources_' + hash_string(resources_json) + '.json'

    matches_json = json.dumps(request.json['matches'], indent=2)
    matches_filename = './generated_json/matches_' + hash_string(matches_json) + '.json'

    job_id = hash_string(resources_filename.split('/')[-1] + matches_filename.split('/')[-1])

    response = {'job_id': job_id}

    if not get_job_data(job_id):
        json_file = open(resources_filename, 'w')
        json_file.write(resources_json)
        json_file.close()

        json_file = open(matches_filename, 'w')
        json_file.write(matches_json)
        json_file.close()

        job_data = {
            'resources_form_data': json.dumps(request.json['resources_original']),
            'mappings_form_data': json.dumps(request.json['matches_original']),
            'resources_filename': resources_filename,
            'mappings_filename': matches_filename,
            'status': 'Requested',
            'requested_at': datetime.datetime.now(),
        }

        update_job_data(job_id, job_data)

    return jsonify(response)


@app.route('/job/<job_id>')
def job_data(job_id):
    return jsonify(get_job_data(job_id))


@app.route('/job/<job_id>/result/download')
def download_rdf(job_id):
    return send_file('/output/rdf/%s_output.nq.gz' % job_id, as_attachment=True)


@app.route('/job/<job_id>/result/<mapping_name>')
def result(job_id, mapping_name):
    if request.accept_mimetypes.accept_html:
        response = index()
    else:
        view_name = hash_string(mapping_name)
        count_query = psycopg2_sql.SQL('SELECT count(*) FROM {schema}.{view}').format(
            schema=psycopg2_sql.Identifier('job_' + job_id),
            view=psycopg2_sql.Identifier(view_name)
        )
        rows_query = psycopg2_sql.SQL('SELECT * FROM {schema}.{view} LIMIT 100').format(
            schema=psycopg2_sql.Identifier('job_' + job_id),
            view=psycopg2_sql.Identifier(view_name)
        )

        n = 0
        while True:
            try:
                with db_conn() as conn:
                    with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                        cur.execute(count_query)
                        rows_count = cur.fetchone()['count']
                        cur.execute(rows_query)
                        rows = cur.fetchall()
                        response_data = {
                            'mapping_name': mapping_name,
                            'rows': rows,
                            'rows_total': rows_count,
                        }
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                n += 1
                print('Database error. Retry %i' % n)
                time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
            else:
                break

        response = jsonify(response_data)

    # We need to disable caching because the AJAX request is done to the same URL
    response.cache_control.no_cache = True
    return response
