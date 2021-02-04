import io
import csv
import decimal
import psycopg2

from flask import Flask, jsonify, request, abort, make_response
from flask_cors import CORS
from flask.json import JSONEncoder

from werkzeug.routing import BaseConverter, ValidationError

from ll.job.job import Job, Validation

from ll.util.hasher import hash_string
from ll.util.logging import config_logger
from ll.util.helpers import get_association_files

from ll.data.collection import Collection
from ll.data.timbuctoo_datasets import TimbuctooDatasets


class DecimalJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to strings.
            return float(obj)
        return super(DecimalJSONEncoder, self).default(obj)


class JobConverter(BaseConverter):
    def to_python(self, job_id):
        return Job(job_id)


class TypeConverter(BaseConverter):
    def to_python(self, type):
        if type == 'linkset' or type == 'lens':
            return type
        raise ValidationError()


config_logger()

app = Flask(__name__)
CORS(app)

app.json_encoder = DecimalJSONEncoder
app.url_map.converters['job'] = JobConverter
app.url_map.converters['type'] = TypeConverter


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/datasets')
def datasets():
    return jsonify(TimbuctooDatasets(request.args.get('endpoint'), request.args.get('hsid')).datasets)


@app.route('/datasets/update', methods=['POST'])
def datasets_update():
    TimbuctooDatasets(request.form.get('endpoint'), request.form.get('hsid')).update()
    return jsonify({'result': 'updated'})


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


@app.route('/job/create', methods=['POST'])
def job_create():
    job_id = hash_string(request.json['job_title'] + request.json['job_description'])
    job = Job(job_id)

    job.update_data({
        'job_title': request.json['job_title'],
        'job_description': request.json['job_description'],
        'job_link': request.json['job_link'] if 'job_link' in request.json else None,
    })

    return jsonify({'result': 'created', 'job_id': job_id})


@app.route('/job/update', methods=['POST'])
def job_update():
    job_id = request.json['job_id']
    job = Job(job_id)

    (entity_type_selections, linkset_specs, lens_specs) = job.update_data({
        key: request.json[key]
        for key in ['job_title', 'job_description', 'job_link', 'entity_type_selections', 'linkset_specs', 'lens_specs']
        if key in request.json
    })

    return jsonify({
        'result': 'updated',
        'job_id': job_id,
        'entity_type_selections': [entity_type_selection['id'] for entity_type_selection in entity_type_selections
                                   if 'id' in entity_type_selection],
        'linkset_specs': [linkset_spec['id'] for linkset_spec in linkset_specs if 'id' in linkset_spec],
        'lens_specs': [lens_spec['id'] for lens_spec in lens_specs if 'id' in lens_spec]
    })


@app.route('/job/<job:job>')
def job_data(job):
    if job.data:
        return jsonify({
            'job_id': job.data['job_id'],
            'job_title': job.data['job_title'],
            'job_description': job.data['job_description'],
            'job_link': job.data['job_link'],
            'entity_type_selections': job.data['entity_type_selections_form_data'],
            'linkset_specs': job.data['linkset_specs_form_data'],
            'lens_specs': job.data['lens_specs_form_data'],
            'created_at': job.data['created_at'],
            'updated_at': job.data['updated_at']
        })

    return abort(404)


@app.route('/job/<job:job>/linksets')
def job_linksets(job):
    job_linksets = job.linksets
    return jsonify(job_linksets if job_linksets else [])


@app.route('/job/<job:job>/lenses')
def job_lenses(job):
    job_lenses = job.lenses
    return jsonify(job_lenses if job_lenses else [])


@app.route('/job/<job:job>/clusterings')
def job_clusterings(job):
    job_clusterings = job.clusterings
    return jsonify(job_clusterings if job_clusterings else [])


@app.route('/job/<job:job>/run_linkset/<int:id>', methods=['POST'])
def run_linkset(job, id):
    try:
        restart = 'restart' in request.json and request.json['restart'] is True
        job.run_linkset(id, restart)
        return jsonify({'result': 'ok'})
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'})


@app.route('/job/<job:job>/run_lens/<int:id>', methods=['POST'])
def run_lens(job, id):
    try:
        restart = 'restart' in request.json and request.json['restart'] is True
        job.run_lens(id, restart)
        return jsonify({'result': 'ok'})
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'})


@app.route('/job/<job:job>/run_clustering/<type:type>/<int:id>', methods=['POST'])
def run_clustering(job, type, id):
    association_file = request.json['association_file']
    clustering_type = request.json.get('clustering_type', 'default')
    job.run_clustering(id, type, association_file, clustering_type)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/sql/<type:type>/<int:id>')
def sql(job, type, id):
    from flask import Response
    from ll.job.matching_sql import MatchingSql
    from ll.job.lens_sql import LensSql

    job_sql = MatchingSql(job, id) if type == 'linkset' else LensSql(job, id)
    return Response(job_sql.sql_string, mimetype='text/plain')


@app.route('/job/<job:job>/kill_linkset/<int:id>', methods=['POST'])
def kill_linkset(job, id):
    job.kill_linkset(id)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/kill_lens/<int:id>', methods=['POST'])
def kill_lens(job, id):
    job.kill_lens(id)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/kill_clustering/<type:type>/<int:id>', methods=['POST'])
def kill_clustering(job, type, id):
    job.kill_clustering(id, type)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/<type:type>/<int:id>', methods=['DELETE'])
def delete(job, type, id):
    lens_uses = job.spec_lens_uses(id, type)
    if len(lens_uses) > 0:
        response = jsonify({'result': 'fail', 'lens_uses': lens_uses})
        response.status_code = 400
        return response

    job.delete(id, type)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/entity_type_selection_total/<int:id>')
def entity_type_selection_total(job, id):
    return jsonify(job.get_entity_type_selection_sample_total(id))


@app.route('/job/<job:job>/links_totals/<type:type>/<int:id>')
def links_totals(job, type, id):
    return jsonify(job.get_links_totals(id, type, cluster_id=request.args.get('cluster_id')))


@app.route('/job/<job:job>/entity_type_selection/<int:id>')
def entity_type_selection_sample(job, id):
    return jsonify(job.get_entity_type_selection_sample(id,
                                                        invert=request.args.get('invert', default=False) == 'true',
                                                        limit=request.args.get('limit', type=int),
                                                        offset=request.args.get('offset', 0, type=int)))


@app.route('/job/<job:job>/links/<type:type>/<int:id>')
def links(job, type, id):
    cluster_id = request.args.get('cluster_id')
    validation_filter = validation_filter_helper(request.args.getlist('valid'))

    links = [link for link in job.get_links(id, type, validation_filter=validation_filter,
                                            cluster_id=cluster_id, include_props=True,
                                            limit=request.args.get('limit', type=int),
                                            offset=request.args.get('offset', 0, type=int))]
    return jsonify(links)


@app.route('/job/<job:job>/clusters/<type:type>/<int:id>')
def clusters(job, type, id):
    extended_data = []
    cycles_data = []

    clusters = []
    for cluster in job.get_clusters(id, type, include_props=True,
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


@app.route('/job/<job:job>/validate/<type:type>/<int:id>', methods=['POST'])
def validate_link(job, type, id):
    source = request.json.get('source')
    target = request.json.get('target')
    valid = request.json.get('valid')
    job.validate_link(id, type, source, target, valid)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/cluster/<type:type>/<int:id>/<cluster_id>/graph')
def get_cluster_graph_data(job, type, id, cluster_id):
    return jsonify(job.visualize(id, type, cluster_id))


@app.route('/job/<job:job>/export/<type:type>/<int:id>/csv')
def export_to_csv(job, type, id):
    stream = io.StringIO()
    writer = csv.writer(stream)

    writer.writerow(['Source URI', 'Target URI', 'Max Strength', 'Valid'])
    for link in job.get_links(id, type, validation_filter=validation_filter_helper(request.args.getlist('valid'))):
        similarity = round(link['similarity'], 3) if link['similarity'] else 1
        writer.writerow([link['source'], link['target'], similarity, link['valid']])

    output = make_response(stream.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=' + job.job_id + '_' + type + '_' + str(id) + '.csv'
    output.headers['Content-Type'] = 'text/csv'

    return output


def validation_filter_helper(valid):
    validation_filter = 0
    for type in valid:
        if type == 'accepted':
            validation_filter |= Validation.ACCEPTED
        if type == 'rejected':
            validation_filter |= Validation.REJECTED
        if type == 'not_validated':
            validation_filter |= Validation.NOT_VALIDATED
        if type == 'mixed':
            validation_filter |= Validation.MIXED

    return validation_filter if validation_filter != 0 else Validation.ALL


if __name__ == '__main__':
    app.run()
