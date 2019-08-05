import re
import json
import gzip
import subprocess

from os.path import join, splitext

import psycopg2
from psycopg2 import sql as psycopg2_sql

from flask import Flask, jsonify, send_file, request, abort, make_response

from common.config_db import db_conn, run_query
from common.datasets_config import DatasetsConfig
from common.helpers import get_job_data, hasher, update_job_data
from common.ll.Generic.Utility import pickle_deserializer
from common.ll.Clustering.IlnVisualisation import plot, plot_compact, plot_reconciliation

from web_server.clustering import cluster_csv, get_cluster_data, hash_string, cluster_reconciliation_csv

from common.ll.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
from common.ll.DataAccess.PostgreSQL.Query import get_values_for

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
        job_data['resources'] = json.dumps(request.json['resources'])
    if 'matches' in request.json:
        job_data['mappings'] = json.dumps(request.json['matches'])

    update_job_data(job_id, job_data)

    return jsonify({'result': 'updated', 'job_id': job_id, 'job_data': job_data})


@app.route('/job/<job_id>')
def job_data(job_id):
    job_data = get_job_data(job_id)
    if job_data:
        return jsonify(job_data)
    return abort(404)


@app.route('/job/<job_id>/run_alignment/<alignment>', methods=['POST'])
def run_alignment(job_id, alignment):
    if 'restart' in request.json and request.json['restart'] is True:
        query = psycopg2_sql.SQL("DELETE FROM alignment_jobs WHERE job_id = %s AND alignment = %s")
        params = (job_id, alignment)
        run_query(query, params)

        query = psycopg2_sql.SQL("DELETE FROM clusterings WHERE job_id = %s AND alignment = %s")
        run_query(query, params)

    try:
        query = psycopg2_sql.SQL(
            "INSERT INTO alignment_jobs (job_id, alignment, status, requested_at) VALUES (%s, %s, %s, now())")
        params = (job_id, alignment, 'Requested')
        run_query(query, params)
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'})

    return jsonify({'result': 'ok'})


@app.route('/job/<job_id>/alignment/<alignment>')
def result(job_id, alignment):
    filename = f'alignment_{hasher(job_id)}_alignment_{alignment}.csv.gz'
    csv_filepath = join(CSV_ALIGNMENTS_DIR, filename)

    response = make_response(send_file(csv_filepath, mimetype='text/csv'))
    response.headers['Content-Encoding'] = 'gzip'
    return response


@app.route('/job/<job_id>/alignment/<alignment>/properties', methods=['POST'])
def alignment_properties(job_id, alignment):
    targets = request.json['targets'] if 'targets' in request.json else None
    resources = set()

    filename = f'alignment_{hasher(job_id)}_alignment_{alignment}.csv.gz'
    with gzip.open(join(CSV_ALIGNMENTS_DIR, filename), mode="rt", encoding="utf-8") as csv:
        position = 0
        for line in csv:
            position += 1
            split = (line.strip()).split(sep=',')
            resources.update([split[0].strip(), split[1].strip()])

    return jsonify(get_values_for(resources, targets))


@app.route('/job/<job_id>/create_clustering/', methods=['POST'])
def create_clustering(job_id):
    filename = f'alignment_{hasher(job_id)}_alignment_{request.json["alignment"]}.csv.gz'
    csv_filepath = join(CSV_ALIGNMENTS_DIR, filename)
    if request.json['association_file'] != '':
        if request.json['clustered']:
            reconciliation_result = cluster_reconciliation_csv(request.json['association_file'], job_id,
                                                               request.json['alignment'])

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                UPDATE clusterings
                SET extended_count = %s, cycles_count = %s
                WHERE job_id = %s AND alignment = %s
                ''', (
                    reconciliation_result['extended_clusters_count'],
                    reconciliation_result['cycles_count'],
                    job_id,
                    request.json['alignment'],
                ))

            return jsonify(reconciliation_result)
        else:
            abort(400)
    else:
        clustering_result = cluster_csv(csv_filepath, job_id, request.json['alignment'])

        try:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                INSERT INTO clusterings
                (clustering_id, job_id, alignment, clustering_type, clusters_count)
                VALUES (%s, %s, %s, %s, %s)
                ''', (
                    clustering_result['file_name'],
                    job_id,
                    request.json['alignment'],
                    request.json.get('clustering_type', 'default'),
                    clustering_result['clusters_count'],
                ))
        except psycopg2.IntegrityError:
            pass

        return jsonify(clustering_result)


@app.route('/job/<job_id>/clusters/<clustering_id>')
def clusters(job_id, clustering_id):
    clusters = {}
    clusters_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f'{clustering_id}-1.txt.gz')

    if request.args.get('association'):
        reconciled_id = re.sub("Cluster", "Reconciled", clustering_id)
        reconciled = f'{reconciled_id}_{hasher(request.args.get("association"))}'
        extended_filename_base = F"{clustering_id}_ExtendedBy_{splitext(request.args.get('association'))[0]}_{hasher(reconciled)}"
        extended_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f"{extended_filename_base}-1.txt.gz")
        cycles_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f"{extended_filename_base}-2.txt.gz")
    else:
        extended_data = []
        cycles_data = []

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


@app.route('/job/<job_id>/cluster/<clustering_id>/<cluster_id>/graph', methods=['POST'])
def get_cluster_graph_data(job_id, clustering_id, cluster_id):
    cluster_data = request.json['cluster_data'] \
        if 'cluster_data' in request.json \
        else get_cluster_data(clustering_id, cluster_id)
    associations = request.json['associations'] if 'associations' in request.json else None
    properties = request.json['properties'] if 'properties' in request.json else None
    mapping_label = run_query("SELECT alignment FROM clusterings WHERE clustering_id = %s", (clustering_id,))[0]
    sub_clusters = f'Reconciled_{hasher(job_id)}_{mapping_label}_{hasher(associations)}'
    get_cluster = request.json.get('get_cluster', True)
    get_cluster_compact = request.json.get('get_cluster_compact', True)
    get_reconciliation = request.json.get('get_reconciliation', True) if associations else False

    specifications = {
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
        "properties": properties,
    }

    return jsonify({
        'cluster_graph': plot(specs=specifications, activated=True) if get_cluster else None,
        'cluster_graph_compact': plot_compact(specs=specifications, community_only=True,
                                              activated=True) if get_cluster_compact else None,
        'reconciliation_graph': plot_reconciliation(specs=specifications,
                                                    activated=True)[1] if get_reconciliation else None,
    })


@app.route('/properties', methods=['POST'])
def properties():
    resources = request.json['resources'] if 'resources' in request.json else None
    targets = request.json['targets'] if 'targets' in request.json else None

    return jsonify(get_values_for(resources, targets))


@app.route('/server_status/')
def status():
    status_process = subprocess.run(['python', '/app/status.py'], capture_output=True, text=True)
    return status_process.stdout.replace('\n', '<br>')
