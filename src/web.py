import os
import uuid
import decimal
import datetime
import psycopg2
import functools

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask.json import JSONEncoder
from flask_compress import Compress

from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata

from werkzeug.routing import BaseConverter, ValidationError

from ll.job.export import Export
from ll.job.job import Job, Validation
from ll.util.config_db import fetch_one

from ll.util.hasher import hash_string
from ll.util.logging import config_logger

from ll.data.collection import Collection
from ll.data.timbuctoo_datasets import TimbuctooDatasets


class FixedJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(FixedJSONEncoder, self).default(obj)


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
app.config.update(
    OIDC_REDIRECT_URI=os.environ.get('APP_DOMAIN', 'http://localhost') + '/oidc_redirect',
    SECRET_KEY=os.environ.get('SECRET_KEY', uuid.uuid4().hex),
    COMPRESS_MIMETYPES=['text/html', 'text/css', 'text/plain', 'text/csv', 'text/turtle',
                        'application/json', 'application/javascript', 'application/trig'],
)
app.json_encoder = FixedJSONEncoder
app.url_map.converters['job'] = JobConverter
app.url_map.converters['type'] = TypeConverter

CORS(app)
Compress(app)

auth = OIDCAuthentication({'default': ProviderConfiguration(
    issuer=os.environ['OIDC_SERVER'],
    client_metadata=ClientMetadata(
        client_id=os.environ['OIDC_CLIENT_ID'],
        client_secret=os.environ['OIDC_CLIENT_SECRET'])
)}, app) if 'OIDC_SERVER' in os.environ and len(os.environ['OIDC_SERVER']) > 0 else None


def authenticated(func):
    return auth.oidc_auth('default').oidc_decorator(func) if auth else func


def with_job(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'job' in kwargs:
            job = kwargs['job']
        elif request.json and 'job_id' in request.json:
            job = Job(request.json['job_id'])
        else:
            return jsonify({'result': 'error', 'error': 'Please specify a job id'}), 400

        kwargs['job'] = job
        if not job.data:
            return jsonify({'result': 'error', 'error': f"Job with id '{job.job_id}' not found"}), 404

        return func(*args, **kwargs)

    return wrapper


def with_spec(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        spec = kwargs['job'].get_spec_by_id(kwargs['id'], kwargs['type'])
        if not spec:
            return jsonify({'result': 'error',
                            'error': f"Spec with type '{kwargs['type']}' and id '{kwargs['id']}' not found"}), 404

        return func(*args, **kwargs)

    return wrapper


def with_entity_type_selection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not kwargs['job'].get_entity_type_selection_by_id(kwargs['id']):
            return jsonify({'result': 'error',
                            'error': f"Entity-type selection with id '{kwargs['id']}' not found"}), 404

        return func(*args, **kwargs)

    return wrapper


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/datasets')
@authenticated
def datasets():
    if not request.args.get('endpoint'):
        return jsonify({'result': 'error', 'error': 'Please apply the GraphQL endpoint'}), 400

    return jsonify(TimbuctooDatasets(request.args.get('endpoint')).datasets)


@app.route('/datasets/update', methods=['POST'])
@authenticated
def datasets_update():
    if not request.form.get('endpoint'):
        return jsonify({'result': 'error', 'error': 'Please apply the GraphQL endpoint'}), 400

    TimbuctooDatasets(request.form.get('endpoint')).update()
    return jsonify({'result': 'updated'})


@app.route('/downloads')
@authenticated
def downloads():
    return jsonify(Collection.download_status())


@app.route('/download')
@authenticated
def start_download():
    if not request.args.get('endpoint'):
        return jsonify({'result': 'error', 'error': 'Please apply the GraphQL endpoint'}), 400
    if not request.args.get('dataset_id'):
        return jsonify({'result': 'error', 'error': 'Please apply the Timbuctoo dataset id'}), 400
    if not request.args.get('collection_id'):
        return jsonify({'result': 'error', 'error': 'Please apply the Timbuctoo collection id'}), 400

    collection = Collection(request.args.get('endpoint'),
                            request.args.get('dataset_id'), request.args.get('collection_id'))
    collection.start_download()

    return jsonify({'result': 'ok'})


@app.route('/stopwords/<dictionary>')
@authenticated
def stopwords(dictionary):
    if dictionary not in ['arabic', 'azerbaijani', 'danish', 'dutch', 'dutch_names', 'english', 'finnish', 'french',
                          'german', 'greek', 'hungarian', 'indonesian', 'italian', 'kazakh', 'nepali', 'norwegian',
                          'portuguese', 'romanian', 'russian', 'slovene', 'spanish', 'swedish', 'tajik', 'turkish']:
        return jsonify({'result': 'error', 'error': 'Please specify a valid dictionary key'}), 400

    return jsonify(fetch_one('SELECT get_stopwords(%s)', (dictionary,))[0])


@app.route('/job/create', methods=['POST'])
@authenticated
def job_create():
    if not request.json.get('job_title'):
        return jsonify({'result': 'error', 'error': 'Please specify a title for this new job'}), 400
    if not request.json.get('job_description'):
        return jsonify({'result': 'error', 'error': 'Please specify a description for this new job'}), 400

    job_id = hash_string(request.json['job_title'] + request.json['job_description'])
    job = Job(job_id)

    created = False
    while not created:
        try:
            job.create_job(request.json['job_title'], request.json['job_description'],
                           request.json['job_link'] if 'job_link' in request.json
                                                       and len(request.json['job_link'].strip()) > 0 else None)
            created = True
        except:
            job_id = hash_string(uuid.uuid4().hex)
            job = Job(job_id)

    return jsonify({'result': 'created', 'job_id': job_id})


@app.route('/job/update', methods=['POST'])
@authenticated
@with_job
def job_update(job):
    entity_type_selections, linkset_specs, lens_specs, views, errors = job.update_data(request.json)

    if len(errors) > 0:
        return jsonify({
            'result': 'error',
            'job_id': job.job_id,
            'errors': [str(error) for error in errors],
            'entity_type_selections': [entity_type_selection['id'] for entity_type_selection in entity_type_selections],
            'linkset_specs': [linkset_spec['id'] for linkset_spec in linkset_specs],
            'lens_specs': [lens_spec['id'] for lens_spec in lens_specs],
            'views': [[view['id'], view['type']] for view in views],
        }), 400

    return jsonify({
        'result': 'updated',
        'job_id': job.job_id,
        'entity_type_selections': [entity_type_selection['id'] for entity_type_selection in entity_type_selections],
        'linkset_specs': [linkset_spec['id'] for linkset_spec in linkset_specs],
        'lens_specs': [lens_spec['id'] for lens_spec in lens_specs],
        'views': [[view['id'], view['type']] for view in views],
    })


@app.route('/job/<job:job>')
@authenticated
@with_job
def job_data(job):
    return jsonify({
        'job_id': job.data['job_id'],
        'job_title': job.data['job_title'],
        'job_description': job.data['job_description'],
        'job_link': job.data['job_link'],
        'entity_type_selections': job.data['entity_type_selections_form_data'],
        'linkset_specs': job.data['linkset_specs_form_data'],
        'lens_specs': job.data['lens_specs_form_data'],
        'views': job.data['views_form_data'],
        'created_at': job.data['created_at'],
        'updated_at': job.data['updated_at']
    })


@app.route('/job/<job:job>/linksets')
@authenticated
@with_job
def job_linksets(job):
    return jsonify(job.linksets)


@app.route('/job/<job:job>/lenses')
@authenticated
@with_job
def job_lenses(job):
    return jsonify(job.lenses)


@app.route('/job/<job:job>/clusterings')
@authenticated
@with_job
def job_clusterings(job):
    return jsonify(job.clusterings)


@app.route('/job/<job:job>/run/<type:type>/<int:id>', methods=['POST'])
@authenticated
@with_job
@with_spec
def run_spec(job, type, id):
    try:
        restart = 'restart' in request.json and request.json['restart'] is True
        job.run_linkset(id, restart) if type == 'linkset' else job.run_lens(id, restart)
        return jsonify({'result': 'ok'})
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'}), 400


@app.route('/job/<job:job>/run_clustering/<type:type>/<int:id>', methods=['POST'])
@authenticated
@with_job
@with_spec
def run_clustering(job, type, id):
    try:
        job.run_clustering(id, type)
        return jsonify({'result': 'ok'})
    except psycopg2.errors.UniqueViolation:
        return jsonify({'result': 'exists'}), 400


@app.route('/job/<job:job>/sql/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def sql(job, type, id):
    from flask import Response
    from ll.job.matching_sql import MatchingSql
    from ll.job.lens_sql import LensSql

    job_sql = MatchingSql(job, id) if type == 'linkset' else LensSql(job, id)
    return Response(job_sql.sql_string, mimetype='text/plain')


@app.route('/job/<job:job>/kill/<type:type>/<int:id>', methods=['POST'])
@authenticated
@with_job
@with_spec
def kill_spec(job, type, id):
    job.kill_linkset(id) if type == 'linkset' else job.kill_lens(id)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/kill_clustering/<type:type>/<int:id>', methods=['POST'])
@authenticated
@with_job
@with_spec
def kill_clustering(job, type, id):
    job.kill_clustering(id, type)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/<type:type>/<int:id>', methods=['DELETE'])
@authenticated
@with_job
@with_spec
def delete(job, type, id):
    lens_uses = job.spec_lens_uses(id, type)
    if len(lens_uses) > 0:
        return jsonify({'result': 'error', 'lens_uses': lens_uses}), 400

    job.delete(id, type)
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/entity_type_selection_total/<int:id>')
@authenticated
@with_job
@with_entity_type_selection
def entity_type_selection_total(job, id):
    return jsonify(job.get_entity_type_selection_sample_total(id))


@app.route('/job/<job:job>/links_totals/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def links_totals(job, type, id):
    return jsonify(job.get_links_totals(id, type,
                                        cluster_id=request.args.get('cluster_id'),
                                        min_strength=request.args.get('min', type=float),
                                        max_strength=request.args.get('max', type=float)))


@app.route('/job/<job:job>/entity_type_selection/<int:id>')
@authenticated
@with_job
@with_entity_type_selection
def entity_type_selection_sample(job, id):
    return jsonify(job.get_entity_type_selection_sample(id,
                                                        invert=request.args.get('invert', default=False) == 'true',
                                                        limit=request.args.get('limit', type=int),
                                                        offset=request.args.get('offset', 0, type=int)))


@app.route('/job/<job:job>/links/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def links(job, type, id):
    links = [link for link in job.get_links(id, type,
                                            with_properties='multiple',
                                            validation_filter=Validation.get(request.args.getlist('valid')),
                                            cluster_id=request.args.get('cluster_id'),
                                            min_strength=request.args.get('min', type=float),
                                            max_strength=request.args.get('max', type=float),
                                            limit=request.args.get('limit', type=int),
                                            offset=request.args.get('offset', 0, type=int))]
    return jsonify(links)


@app.route('/job/<job:job>/clusters/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def clusters(job, type, id):
    clusters = [{
        'id': cluster['id'],
        'size': cluster['size'],
        'links': cluster['links'],
        'values': cluster['values'],
        'reconciled': False,
        'extended': False,
    } for cluster in job.get_clusters(id, type,
                                      with_properties='multiple',
                                      limit=request.args.get('limit', type=int),
                                      offset=request.args.get('offset', 0, type=int))]

    return jsonify(clusters)


@app.route('/job/<job:job>/validate/<type:type>/<int:id>', methods=['POST'])
@authenticated
@with_job
@with_spec
def validate_link(job, type, id):
    source = request.json.get('source')
    target = request.json.get('target')
    cluster_id = request.json.get('cluster_id')
    validation = Validation.get(request.json.get('validation', []))
    valid = request.json.get('valid')

    job.validate_link(id, type, valid, validation_filter=validation, cluster_id=cluster_id, link=(source, target))
    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/cluster/<type:type>/<int:id>/<cluster_id>/graph')
@authenticated
@with_job
@with_spec
def get_cluster_graph_data(job, type, id, cluster_id):
    return jsonify(job.visualize(id, type, cluster_id))


@app.route('/job/<job:job>/csv/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def export_to_csv(job, type, id):
    export = Export(job, type, id)

    validation_filter = Validation.get(request.args.getlist('valid'))
    export_generator = export.csv_export_generator(validation_filter)

    return Response(export_generator, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=' + type + '_' + str(id) + '.csv'})


@app.route('/job/<job:job>/rdf/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def export_to_rdf(job, type, id):
    export = Export(job, type, id)

    link_pred_namespace = request.args.get('link_pred_namespace')
    link_pred_shortname = request.args.get('link_pred_shortname')
    export_metadata = request.args.get('export_metadata', default=True) == 'true'
    export_link_metadata = request.args.get('export_link_metadata', default=True) == 'true'
    export_linkset = request.args.get('export_linkset', default=True) == 'true'
    rdf_star = request.args.get('rdf_star', default=False) == 'true'
    use_graphs = request.args.get('use_graphs', default=True) == 'true'
    creator = request.args.get('creator')
    publisher = request.args.get('publisher')
    validation_filter = Validation.get(request.args.getlist('valid'))

    export_generator = export.rdf_export_generator(
        link_pred_namespace, link_pred_shortname, export_metadata, export_link_metadata,
        export_linkset, rdf_star, use_graphs, creator, publisher, validation_filter)

    mimetype = 'application/trig' if use_graphs else 'text/turtle'
    extension = '.trig' if use_graphs else '.ttl'

    return Response(export_generator, mimetype=mimetype,
                    headers={'Content-Disposition': 'attachment; filename=' + type + '_' + str(id) + extension})


if __name__ == '__main__':
    app.run()
