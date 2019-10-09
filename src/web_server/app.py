import json
import subprocess

import psycopg2
from psycopg2 import sql as psycopg2_sql

from flask import Flask, jsonify, request, abort

from common.config_db import run_query
from common.helpers import hash_string, get_association_files
from common.datasets_config import DatasetsConfig
from common.job_alignment import get_job_data, get_job_alignments, get_job_clusterings, \
    get_job_clustering, update_job_data, get_links, get_clusters, get_cluster, get_value_targets

from common.ll.Clustering.IlnVisualisation import plot, plot_compact, plot_reconciliation

app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('core/index.html')


@app.route('/datasets')
def datasets():
    return jsonify(DatasetsConfig().data)


@app.route('/association_files')
def association_files():
    return jsonify(get_association_files())


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


@app.route('/job/<job_id>/alignments')
def job_alignments(job_id):
    job_alignments = get_job_alignments(job_id)
    if job_alignments:
        return jsonify(job_alignments)
    return jsonify([])


@app.route('/job/<job_id>/clusterings')
def job_clusterings(job_id):
    job_clusterings = get_job_clusterings(job_id)
    if job_clusterings:
        return jsonify(job_clusterings)
    return jsonify([])


@app.route('/job/<job_id>/run_alignment/<alignment>', methods=['POST'])
def run_alignment(job_id, alignment):
    if 'restart' in request.json and request.json['restart'] is True:
        query = psycopg2_sql.SQL("DELETE FROM alignments WHERE job_id = %s AND alignment = %s")
        params = (job_id, alignment)
        run_query(query, params)

        query = psycopg2_sql.SQL("DELETE FROM clusterings WHERE job_id = %s AND alignment = %s")
        run_query(query, params)

    try:
        query = psycopg2_sql.SQL(
            "INSERT INTO alignments (job_id, alignment, status, kill, requested_at) VALUES (%s, %s, %s, false, now())")
        params = (job_id, alignment, 'waiting')
        run_query(query, params)
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'})

    return jsonify({'result': 'ok'})


@app.route('/job/<job_id>/kill_alignment/<alignment>', methods=['POST'])
def kill_alignment(job_id, alignment):
    run_query('UPDATE alignments SET kill = true WHERE job_id = %s AND alignment = %s', (job_id, alignment))
    return jsonify({'result': 'ok'})


@app.route('/job/<job_id>/alignment/<alignment>')
def alignment_result(job_id, alignment):
    cluster_id = request.args.get('cluster_id')
    links = [link for link in get_links(job_id, int(alignment), cluster_id=cluster_id, include_props=True,
                                        limit=request.args.get('limit', type=int),
                                        offset=request.args.get('offset', 0, type=int))]
    return jsonify(links)


@app.route('/job/<job_id>/run_clustering/<alignment>', methods=['POST'])
def run_clustering(job_id, alignment):
    try:
        job_clusterings = get_job_clusterings(job_id)
        clustering = next((cl for cl in job_clusterings if cl['alignment'] == alignment), None)

        if clustering:
            query = psycopg2_sql.SQL("""
                UPDATE clusterings 
                SET association_file = %s, status = %s, 
                    requested_at = now(), processing_at = null, finished_at = null
                WHERE job_id = %s AND alignment = %s
                """)
            params = (request.json['association_file'], 'waiting', job_id, alignment)
            run_query(query, params)

            return jsonify({'result': 'ok'})
        else:
            query = psycopg2_sql.SQL("""
                INSERT INTO clusterings (job_id, alignment, clustering_type, association_file, status, requested_at) 
                VALUES (%s, %s, %s, %s, %s, now())
            """)
            params = (job_id, alignment, request.json.get('clustering_type', 'default'),
                      request.json['association_file'], 'waiting')
            run_query(query, params)

            return jsonify({'result': 'ok'})
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'})


@app.route('/job/<job_id>/clusters/<alignment>')
def clusters(job_id, alignment):
    if request.args.get('association'):
        extended_data = []
        cycles_data = []

        # reconciled_id = re.sub("Cluster", "Reconciled", clustering_id)
        # reconciled = f'{reconciled_id}_{hasher(request.args.get("association"))}'
        # extended_filename_base = F"{clustering_id}_ExtendedBy_{splitext(request.args.get('association'))[0]}_{hasher(reconciled)}"
        # extended_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f"{extended_filename_base}-1.txt.gz")
        # cycles_data = pickle_deserializer(CLUSTER_SERIALISATION_DIR, f"{extended_filename_base}-2.txt.gz")
    else:
        extended_data = []
        cycles_data = []

    clusters = []
    for cluster in get_clusters(job_id, int(alignment), include_props=True,
                                limit=request.args.get('limit', type=int),
                                offset=request.args.get('offset', 0, type=int)):
        clusters.append({
            'id': cluster['id'],
            'size': cluster['size'],
            'links': cluster['links'],
            'values': cluster['values'],
            'reconciled': 'yes' if cycles_data and cluster['id'] in cycles_data else 'no',
            'extended': 'yes' if cycles_data and extended_data and
                                 cluster['id'] in cycles_data and cluster['id'] in extended_data else 'no'
        })

    if not clusters:
        response = jsonify(clusters)
        response.status_code = 500
        return response

    return jsonify(clusters)


@app.route('/job/<job_id>/validate/<alignment>', methods=['POST'])
def validate_link(job_id, alignment):
    linkset_table = 'linkset_' + job_id + '_' + str(alignment)

    valid = request.json.get('valid')
    source = request.json.get('source')
    target = request.json.get('target')

    query = psycopg2_sql.SQL('UPDATE {} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
        .format(psycopg2_sql.Identifier(linkset_table))
    run_query(query, (valid, source, target))

    return jsonify({'result': 'ok'})


@app.route('/job/<job_id>/cluster/<alignment>/<cluster_id>/graph')
def get_cluster_graph_data(job_id, alignment, cluster_id):
    cluster_data = get_cluster(job_id, alignment, cluster_id)
    clustering = get_job_clustering(job_id, alignment)
    properties = get_value_targets(job_id, int(alignment))

    specifications = {
        "data_store": "POSTGRESQL",
        "sub_clusters": '',
        "associations": clustering['association_file'],
        "serialised": '',
        "cluster_id": cluster_id,
        "cluster_data": cluster_data,
        "properties": properties,
    }

    return jsonify({
        'cluster_graph': plot(specs=specifications, activated=True) \
            if request.args.get('get_cluster', True) else None,
        'cluster_graph_compact': plot_compact(specs=specifications, community_only=True, activated=True) \
            if request.args.get('get_cluster_compact', True) else None,
        'reconciliation_graph': plot_reconciliation(specs=specifications, activated=True)[1] \
            if clustering['association_file'] and request.args.get('get_reconciliation', True) else None,
    })


@app.route('/server_status/')
def status():
    status_process = subprocess.run(['python', '/app/status.py'], capture_output=True, text=True)
    return status_process.stdout.replace('\n', '<br>')
