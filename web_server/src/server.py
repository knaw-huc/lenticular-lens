from datasets_config import DatasetsConfig
from config_db import db_conn, run_query
import datetime
from flask import Flask, jsonify, request, send_file
import gzip
from helpers import get_job_data, hasher, update_job_data
from clustering import cluster_csv, get_cluster_data, hash_string, linkset_to_csv, cluster_reconciliation_csv, \
    cluster_and_reconcile
import json
from os.path import join, splitext
import pickle
import psycopg2
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
import random
from src.Generic.Utility import pickle_deserializer
from src.Clustering.IlnVisualisation import plot_reconciliation as visualise_2, plot as visualise_1, plot_compact as visualise_3
import subprocess
import time

app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('core/index.html')


@app.route('/datasets')
def datasets():
    return jsonify(DatasetsConfig().data)


@app.route('/job/create/', methods=['POST'])
def job_create():
    job_id = hash_string(request.json['job_title'] + request.json['job_description'])
    del request.json['job_id']

    update_job_data(job_id, request.json)

    return jsonify({'result': 'created', 'job_id': job_id})


@app.route('/job/update/', methods=['POST'])
def job_update():
    job_id = request.json['job_id']

    job_data = {
        'job_title': request.json['job_title'],
        'job_description': request.json['job_description'],
    }

    if 'resources_original' in request.json:
        job_data['resources_form_data'] = json.dumps(request.json['resources_original'])
    if 'matches_original' in request.json:
        job_data['mappings_form_data'] = json.dumps(request.json['matches_original'])

    if 'resources' in request.json:
        resources_json = json.dumps(request.json['resources'], indent=2)
        resources_filename = '/common/src/LLData/generated_json/resources_' + hash_string(resources_json) + '.json'
        job_data['resources_filename'] = resources_filename

        json_file = open(resources_filename, 'w')
        json_file.write(resources_json)
        json_file.close()

    if 'matches' in request.json:
        matches_json = json.dumps(request.json['matches'], indent=2)
        matches_filename = '/common/src/LLData/generated_json/matches_' + hash_string(matches_json) + '.json'
        job_data['mappings_filename'] = matches_filename

        json_file = open(matches_filename, 'w')
        json_file.write(matches_json)
        json_file.close()

    update_job_data(job_id, job_data)

    return jsonify({'result': 'updated', 'job_id': job_id, 'job_data': job_data})


@app.route('/job/<job_id>')
def job_data(job_id):
    return jsonify(get_job_data(job_id))


@app.route('/job/<job_id>/clusters/<clustering_id>')
def clusters(job_id, clustering_id):
    clusters = {}
    from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
    clusters_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f'{clustering_id}-1.txt')

    extended_filename_base = F"{clustering_id}_ExtendedBy_{splitext(request.args.get('association'))[0]}_{clustering_id}"
    extended_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f"{extended_filename_base}-1.txt")
    cycles_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f"{extended_filename_base}-2.txt")

    if not clusters_data:
        response = jsonify(clusters_data)
        response.status_code = 500
        return response

    i = 1
    for cluster_id, cluster_data in clusters_data.items():
        i += 1
        cluster_data['index'] = i
        if cycles_data and cluster_id in cycles_data:
            cluster_data['extended'] = 'yes'
            cluster_data['reconciled'] = 'yes'
        else:
            cluster_data['reconciled'] = 'no'
            cluster_data['extended'] = 'yes' if extended_data and cluster_id in extended_data else 'no'
        clusters[cluster_id] = cluster_data
        if i == 20:
            break

    return jsonify(clusters)


@app.route('/job/<job_id>/result/download')
def download_rdf(job_id):
    return send_file('/common/src/LLData/rdf/%s_output.nq.gz' % job_id, as_attachment=True)


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


@app.route('/job/<job_id>/create_clustering/', methods=['POST'])
def create_clustering(job_id):
    from src.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
    filename = f'alignment_{hasher(job_id)}_{request.json["mapping_label"]}.csv.gz'
    csv_filepath = join(CSV_ALIGNMENTS_DIR, filename)
    clustering_id = None
    if request.json['association_file'] != '':
        if request.json['clustered']:
            cluster_reconciliation_csv(request.json['association_file'], job_id, request.json['mapping_label'])
        else:
            cluster_and_reconcile(request.json['association_file'], job_id, request.json['mapping_label'],
                                  request.json['association_file'])
    else:
        clustering_id = cluster_csv(csv_filepath, job_id, request.json['mapping_label'])

        try:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                INSERT INTO clusterings
                (clustering_id, job_id, mapping_name, clustering_type)
                VALUES (%s, %s, %s, %s)
                ''', (
                clustering_id, job_id, request.json['mapping_label'], request.json.get('clustering_type', 'default')))
        except psycopg2.IntegrityError:
            pass

    return jsonify(clustering_id)


@app.route('/job/<job_id>/cluster/<clustering_id>/<cluster_id>')
def cluster_visualization(job_id, clustering_id, cluster_id):
    return index()


@app.route('/job/<job_id>/cluster/<clustering_id>/<cluster_id>/graph', methods=['POST'])
def get_cluster_graph_data(job_id, clustering_id, cluster_id):
    cluster_data = request.json['cluster_data'] if 'cluster_data' in request.json else get_cluster_data(clustering_id,
                                                                                                        cluster_id)
    associations = request.json['associations'] if 'associations' in request.json else None
    mapping_label = run_query("SELECT mapping_name FROM clusterings WHERE clustering_id = %s", (clustering_id,))[0]
    sub_clusters = f'Reconciled_{hasher(job_id)}_{mapping_label}_{hasher(associations)}'
    get_cluster = request.json.get('get_cluster', True)
    get_cluster_compact = request.json.get('get_cluster_compact', True)
    get_reconciliation = request.json.get('get_reconciliation', True) if associations else False

    golden_agents_specifications = {
        "data_store": "POSTGRESQL",
        "sub_clusters": sub_clusters,
        "associations": associations,
        "serialised": clustering_id,
        "cluster_id": cluster_id,
        "cluster_data": {
            "nodes": cluster_data['nodes'],
            'strengths': cluster_data['strengths'],
            "links": cluster_data["links"]
        },
        "properties": [
            # MARRIAGE_PERSON
            {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_ondertrouwregister",
             "entity_type": "saaOnt_Person",
             "property": "saaOnt_full_nameList"
             },
            # BAPTISM_PERSON
            {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_doopregister",
             "entity_type": "saaOnt_Person",
             "property": "saaOnt_full_name"
             },
            {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico",
             "entity_type": "foaf_Person",
             "property": "foaf_name"
             },
            {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico",
             "entity_type": "schema_Person",
             "property": "foaf_name"
             },
            {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__onstage_20190220",
             "entity_type": "schema_Person",
             "property": "schema_name"
             },
            {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_begraafregisters",
             "entity_type": "saaOnt_Person",
             "property": "saaOnt_full_name"
             },
        ]
    }

    # import sys
    # print(golden_agents_specifications, file=sys.stderr)
    return jsonify({
        'cluster_graph': visualise_1(specs=golden_agents_specifications, activated=True) if get_cluster else None,
        'cluster_graph_compact': visualise_3(specs=golden_agents_specifications, activated=True)[0] if get_cluster_compact else None,
        'reconciliation_graph': visualise_2(specs=golden_agents_specifications, activated=True)[
            1] if get_reconciliation else None,
    })


@app.route('/job/<job_id>/run_alignment/<alignment>', methods=['POST'])
def run_alignment(job_id, alignment):
    if 'restart' in request.json and request.json['restart'] is True:
        query = psycopg2_sql.SQL("DELETE FROM alignment_jobs WHERE job_id = %s AND alignment = %s")
        params = (job_id, alignment)
        run_query(query, params)

    try:
        query = psycopg2_sql.SQL("INSERT INTO alignment_jobs (job_id, alignment, status, requested_at) VALUES (%s, %s, %s, now())")
        params = (job_id, alignment, 'Requested')
        run_query(query, params)
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'})

    return jsonify({'result': 'ok'})


@app.route('/server_status/')
def status():
    status_process = subprocess.run(['python', '/app/status.py'], capture_output=True, text=True)
    return status_process.stdout.replace('\n', '<br>')
