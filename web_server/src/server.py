from datasets_config import DatasetsConfig
from config_db import db_conn
import datetime
from flask import Flask, jsonify, request, send_file
from helpers import get_job_data, hash_string, update_job_data
import json
import psycopg2
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
import random
import subprocess
import time
app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('core/index.html')


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


@app.route('/job/<job_id>/cluster/<cluster_id>')
def cluster_visualization(job_id, cluster_id):
    return index()


@app.route('/job/<job_id>/cluster/<cluster_id>/graph')
def get_cluster_graph_data(job_id, cluster_id):
    return jsonify({"graph": {"confidence": 0.91, "links": [{"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)", "color": "black", "strenght": "0.95652173913", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)", "color": "black", "strenght": "0.95652173913", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)", "color": "black", "strenght": "0.95652173913", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)", "color": "black", "strenght": "0.95652173913", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)", "color": "black", "strenght": "0.95652173913", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)", "color": "black", "strenght": "0.95652173913", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Ecartico 10471)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Ecartico 10471)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Ecartico 10471)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Ecartico 10471)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Ecartico 10471)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "0.913043478261", "value": 4, "source": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "0.954545454545", "value": 4, "source": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Kipshaven, Lucas [van](Ecartico 10471)", "color": "black", "strenght": "1", "value": 4, "source": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)"}, {"distance": 250, "target": "Raets, Cristina(Baptism002 saaId24360646p1)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)"}, {"distance": 250, "target": "Raets, Cristina(Baptism002 saaId24404578p1)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24404578p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24360646p1)"}, {"distance": 250, "target": "Raets, Cristina(Baptism002 saaId24484767p1)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24484767p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24360646p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24484767p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24404578p1)"}, {"distance": 250, "target": "Raets, Cristina(Baptism002 saaId24500952p1)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24500952p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24360646p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24500952p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24404578p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24500952p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24484767p1)"}, {"distance": 250, "target": "Raets, Cristina(Baptism002 saaId24562839p1)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24562839p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24360646p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24562839p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24404578p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24562839p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24484767p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24562839p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24500952p1)"}, {"distance": 250, "target": "Raets, Cristina(Baptism002 saaId24616076p1)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24616076p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24360646p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24616076p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24404578p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24616076p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24484767p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24616076p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24500952p1)"}, {"distance": 150, "target": "Raets, Cristina(Baptism002 saaId24616076p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24562839p1)"}, {"distance": 250, "target": "Raets, Christina(Burial008 saaId11146443p2)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)"}, {"distance": 250, "target": "Raets, Christina(Burial008 saaId11146456p1)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)"}, {"distance": 150, "target": "Raets, Christina(Burial008 saaId11146456p1)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Christina(Burial008 saaId11146443p2)"}, {"distance": 250, "target": "Raets, Christina(Ecartico 10470)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Lucas [van](Ecartico 10471)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "0.933333333333", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24360646p1)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "0.933333333333", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24404578p1)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "0.933333333333", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24484767p1)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "0.933333333333", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24500952p1)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "0.933333333333", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24562839p1)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "0.933333333333", "value": 4, "source": "Raets, Cristina(Baptism002 saaId24616076p1)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Christina(Burial008 saaId11146443p2)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Christina(Burial008 saaId11146456p1)"}, {"distance": 250, "target": "Raets, Christina(Marriage003 saaId26543348p2)", "color": "purple", "strenght": 1, "value": 4, "dash": "20,10,5,5,5,10", "source": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)"}, {"distance": 150, "target": "Raets, Christina(Marriage003 saaId26543348p2)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Christina(Burial008 saaId11146443p2)"}, {"distance": 150, "target": "Raets, Christina(Marriage003 saaId26543348p2)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Christina(Burial008 saaId11146456p1)"}, {"distance": 150, "target": "Raets, Christina(Ecartico 10470)", "color": "black", "strenght": "1", "value": 4, "source": "Raets, Christina(Marriage003 saaId26543348p2)"}], "messageConf": "", "decision": 0.152, "metrics": "\tESTIMATED QUALITY&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp:  [0.848]&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp|&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp[MIN: 0.774]&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp|&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp[AVERAGE: 0.814]&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp|&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp[COMPLETE: 0.829]\t</br>INTERPRETATION&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp: The network is an ACCEPTABLE representation of a unique real world object and BECAUSE there are less intermediate(s) and no bridge</br>NON WEIGHTED NETWORK METRICS USED : Bridges [0.0]&nbsp&nbsp&nbsp&nbsp&nbsp&nbspDiameter [0.385]&nbsp&nbsp&nbsp&nbsp&nbsp&nbspClosure [42/45 = 0.07]</br>WEIGHTED NETWORK METRICS USED&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp  : Bridges [0.0]&nbsp&nbsp&nbsp&nbsp&nbsp&nbspDiameter [0.414]&nbsp&nbsp&nbsp&nbsp&nbsp&nbspClosure [40.324/45 = 0.1]&nbsp&nbsp&nbsp&nbsp&nbsp&nbspimpact: [0.171]&nbsp&nbsp&nbsp&nbsp&nbsp&nbspquality: [0.829]", "nodes": [{"size": "10", "group": 0, "id": "Kipshaven, Luicas [van](Baptism002 saaId24360646p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24360646p2"}, {"size": "10", "group": 0, "id": "Kipshaven, Luicas [van](Baptism002 saaId24404578p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24404578p2"}, {"size": "10", "group": 0, "id": "Kipshaven, Luijcas [van](Baptism002 saaId24484767p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24484767p2"}, {"size": "10", "group": 0, "id": "Kipshaven, Luijcas [van](Baptism002 saaId24500952p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24500952p2"}, {"size": "10", "group": 0, "id": "Kipshaven, Luicas [van](Baptism002 saaId24562839p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24562839p2"}, {"size": "10", "group": 0, "id": "Kipshaven, Lucas [van](Baptism002 saaId24616076p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24616076p2"}, {"size": "10", "group": 1, "id": "Kipshaven, Lucas [van](Burial008 saaId11146443p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpBegraafregistersVoor1811/saaId11146443p1"}, {"size": "10", "group": 1, "id": "Kipshaven, Lucas [van](Burial008 saaId11146456p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpBegraafregistersVoor1811/saaId11146456p2"}, {"size": "10", "group": 2, "id": "Kipshaven, Lucas [van](Ecartico 10471)", "uri": "http://www.vondel.humanities.uva.nl/ecartico/persons/10471"}, {"size": "10", "group": 3, "id": "Kipshaven, Lucas [van](Marriage003 saaId26543348p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpOndertrouwregister/saaId26543348p1"}, {"size": "5", "group": 0, "id": "Raets, Cristina(Baptism002 saaId24360646p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24360646p1"}, {"size": "5", "group": 0, "id": "Raets, Cristina(Baptism002 saaId24404578p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24404578p1"}, {"size": "5", "group": 0, "id": "Raets, Cristina(Baptism002 saaId24484767p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24484767p1"}, {"size": "5", "group": 0, "id": "Raets, Cristina(Baptism002 saaId24500952p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24500952p1"}, {"size": "5", "group": 0, "id": "Raets, Cristina(Baptism002 saaId24562839p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24562839p1"}, {"size": "5", "group": 0, "id": "Raets, Cristina(Baptism002 saaId24616076p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24616076p1"}, {"size": "5", "group": 1, "id": "Raets, Christina(Burial008 saaId11146443p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpBegraafregistersVoor1811/saaId11146443p2"}, {"size": "5", "group": 1, "id": "Raets, Christina(Burial008 saaId11146456p1)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpBegraafregistersVoor1811/saaId11146456p1"}, {"size": "5", "group": 2, "id": "Raets, Christina(Ecartico 10470)", "uri": "http://www.vondel.humanities.uva.nl/ecartico/persons/10470"}, {"size": "5", "group": 3, "id": "Raets, Christina(Marriage003 saaId26543348p2)", "uri": "http://goldenagents.org/uva/SAA/person/IndexOpOndertrouwregister/saaId26543348p2"}], "id": "N8168393585806295922"}})


@app.route('/server_status/')
def status():
    status_process = subprocess.run(['python', '/app/status.py'], capture_output=True, text=True)
    return status_process.stdout.replace('\n', '<br>')
