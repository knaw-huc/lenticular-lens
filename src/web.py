import io
import csv
import psycopg2

from flask import Flask, jsonify, request, abort, make_response
from werkzeug.routing import BaseConverter

from ll.job.data import Job, Validation

from ll.util.logging import config_logger
from ll.util.helpers import hash_string, get_association_files

from ll.data.collection import Collection
from ll.data.timbuctoo_datasets import TimbuctooDatasets

from ll.Clustering.IlnVisualisation import plot, plot_compact, plot_reconciliation


class JobConverter(BaseConverter):
    def to_python(self, job_id):
        return Job(job_id)

    def to_url(self, job):
        return job.job_id


config_logger()

app = Flask(__name__)
app.url_map.converters['job'] = JobConverter


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/datasets')
def datasets():
    return jsonify(TimbuctooDatasets(request.args.get('endpoint'), request.args.get('hsid')).datasets)


@app.route('/downloads')
def downloads():
    return jsonify(Collection.download_status())


@app.route('/download')
def start_download():
    collection = Collection(request.args.get('endpoint'), request.args.get('hsid'),
                            request.args.get('dataset_id'), request.args.get('collection_id'))
    collection.start_download()

    return jsonify({'result': 'ok'})


@app.route('/association_files')
def association_files():
    return jsonify(get_association_files())


@app.route('/job/create/', methods=['POST'])
def job_create():
    job_id = hash_string(request.json['job_title'] + request.json['job_description'])
    job = Job(job_id)

    job.update_data({
        'job_title': request.json['job_title'],
        'job_description': request.json['job_description'],
        'job_link': request.json['job_link'] if 'job_link' in request.json else None,
    })

    return jsonify({'result': 'created', 'job_id': job_id})


@app.route('/job/update/', methods=['POST'])
def job_update():
    job_id = request.json['job_id']
    job = Job(job_id)

    (resources, mappings) = job.update_data({
        'job_title': request.json['job_title'],
        'job_description': request.json['job_description'],
        'job_link': request.json['job_link'],
        'resources': request.json['resources'] if 'resources' in request.json else [],
        'mappings': request.json['mappings'] if 'mappings' in request.json else [],
    })

    return jsonify({
        'result': 'updated',
        'job_id': job_id,
        'resources': [resource['id'] for resource in resources if 'id' in resource],
        'mappings': [mapping['id'] for mapping in mappings if 'id' in mapping]
    })


@app.route('/job/<job:job>')
def job_data(job):
    if job.data:
        return jsonify({
            'job_id': job.data['job_id'],
            'job_title': job.data['job_title'],
            'job_description': job.data['job_description'],
            'job_link': job.data['job_link'],
            'resources': job.data['resources_form_data'],
            'mappings': job.data['mappings_form_data'],
            'created_at': job.data['created_at'],
            'updated_at': job.data['updated_at']
        })

    return abort(404)


@app.route('/job/<job:job>/alignments')
def job_alignments(job):
    job_alignments = job.alignments
    return jsonify(job_alignments if job_alignments else [])


@app.route('/job/<job:job>/clusterings')
def job_clusterings(job):
    job_clusterings = job.clusterings
    return jsonify(job_clusterings if job_clusterings else [])


@app.route('/job/<job:job>/resource/<resource_label>')
def resource_sample(job, resource_label):
    if request.args.get('total', default=False) == 'true':
        return jsonify(job.get_resource_sample_total(resource_label))

    return jsonify(job.get_resource_sample(resource_label,
                                           invert=request.args.get('invert', default=False) == 'true',
                                           limit=request.args.get('limit', type=int),
                                           offset=request.args.get('offset', 0, type=int)))


@app.route('/job/<job:job>/run_alignment/<alignment>', methods=['POST'])
def run_alignment(job, alignment):
    try:
        restart = 'restart' in request.json and request.json['restart'] is True
        job.run_alignment(alignment, restart)
        return jsonify({'result': 'ok'})
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'})


@app.route('/job/<job:job>/run_clustering/<alignment>', methods=['POST'])
def run_clustering(job, alignment):
    association_file = request.json['association_file']
    clustering_type = request.json.get('clustering_type', 'default')
    job.run_clustering(alignment, association_file, clustering_type)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/matching_sql/<alignment>')
def matching_sql(job, alignment):
    from flask import Response
    from ll.job.matching_sql import MatchingSql

    job_sql = MatchingSql(job.config_for_alignment(int(alignment)))
    return Response(job_sql.sql_string, mimetype='application/sql')


@app.route('/job/<job:job>/kill_alignment/<alignment>', methods=['POST'])
def kill_alignment(job, alignment):
    job.kill_alignment(alignment)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/kill_clustering/<alignment>', methods=['POST'])
def kill_clustering(job, alignment):
    job.kill_clustering(alignment)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/alignment_totals/<alignment>')
def linkset_totals(job, alignment):
    return jsonify(job.get_links_totals(int(alignment), cluster_id=request.args.get('cluster_id')))


@app.route('/job/<job:job>/alignment/<alignment>')
def linkset(job, alignment):
    cluster_id = request.args.get('cluster_id')
    validation_filter = validation_filter_helper(request.args)

    links = [link for link in job.get_links(int(alignment), validation_filter=validation_filter, cluster_id=cluster_id,
                                            include_props=True, limit=request.args.get('limit', type=int),
                                            offset=request.args.get('offset', 0, type=int))]
    return jsonify(links)


@app.route('/job/<job:job>/clusters/<alignment>')
def clusters(job, alignment):
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
    for cluster in job.get_clusters(int(alignment), include_props=True,
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

    return jsonify(clusters)


@app.route('/job/<job:job>/validate/<alignment>', methods=['POST'])
def validate_link(job, alignment):
    source = request.json.get('source')
    target = request.json.get('target')
    valid = request.json.get('valid')
    job.validate_link(alignment, source, target, valid)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/cluster/<alignment>/<cluster_id>/graph')
def get_cluster_graph_data(job, alignment, cluster_id):
    cluster_data = job.cluster(alignment, cluster_id=cluster_id)
    clustering = job.clustering(alignment)
    match = job.config.get_match_by_id(int(alignment))
    properties = job.value_targets_for_match(match)

    specifications = {
        "data_store": "POSTGRESQL",
        "sub_clusters": '',
        "associations": clustering['association_file'],
        "serialised": '',
        "cluster_id": cluster_id,
        "cluster_data": cluster_data,
        "properties": properties,
    }

    cluster_graph = plot(specs=specifications, activated=True) \
        if request.args.get('get_cluster', True) else None
    cluster_graph_compact = plot_compact(specs=specifications, community_only=True, activated=True) \
        if request.args.get('get_cluster_compact', True) else None
    reconciliation_graph = plot_reconciliation(specs=specifications, activated=True)[1] \
        if clustering['association_file'] and request.args.get('get_reconciliation', True) else None

    return jsonify({
        'cluster_graph': cluster_graph,
        'cluster_graph_compact': cluster_graph_compact,
        'reconciliation_graph': reconciliation_graph,
    })


@app.route('/job/<job:job>/export/<alignment>/csv')
def export_to_csv(job, alignment):
    stream = io.StringIO()
    writer = csv.writer(stream)

    writer.writerow(['Source URI', 'Target URI', 'Strengths', 'Valid'])
    for link in job.get_links(alignment, validation_filter=validation_filter_helper(request.args)):
        writer.writerow([link['source'], link['target'], link['strengths'], link['valid']])

    output = make_response(stream.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=' + job.job_id + '_' + alignment + '.csv'
    output.headers['Content-Type'] = 'text/csv'

    return output


def validation_filter_helper(args):
    validation_filter = 0
    if args.get('accepted', default=False) == 'true':
        validation_filter |= Validation.ACCEPTED
    if args.get('declined', default=False) == 'true':
        validation_filter |= Validation.DECLINED
    if args.get('not_validated', default=False) == 'true':
        validation_filter |= Validation.NOT_VALIDATED

    return validation_filter if validation_filter != 0 else Validation.ALL


if __name__ == '__main__':
    app.run()
