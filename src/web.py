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

from ll.util.hasher import hash_string
from ll.util.logging import config_logger
from ll.util.stopwords import get_stopwords

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
        elif request.values and 'job_id' in request.values:
            job = Job(request.values['job_id'])
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


@app.route('/job/<job:job>/update_temp/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def update_temp(job, type, id):
    from temp_update import temp_update

    temp_update(job, type, id)
    return jsonify({'result': 'done'})


@app.route('/datasets')
@authenticated
def datasets():
    if not request.values.get('endpoint'):
        return jsonify({'result': 'error', 'error': 'Please apply the GraphQL endpoint'}), 400

    return jsonify(TimbuctooDatasets(request.values.get('endpoint')).datasets)


@app.route('/datasets/update', methods=['POST'])
@authenticated
def datasets_update():
    if not request.values.get('endpoint'):
        return jsonify({'result': 'error', 'error': 'Please apply the GraphQL endpoint'}), 400

    TimbuctooDatasets(request.values.get('endpoint')).update()
    return jsonify({'result': 'updated'})


@app.route('/downloads')
@authenticated
def downloads():
    return jsonify(Collection.download_status())


@app.route('/download')
@authenticated
def start_download():
    if not request.values.get('endpoint'):
        return jsonify({'result': 'error', 'error': 'Please apply the GraphQL endpoint'}), 400
    if not request.values.get('dataset_id'):
        return jsonify({'result': 'error', 'error': 'Please apply the Timbuctoo dataset id'}), 400
    if not request.values.get('collection_id'):
        return jsonify({'result': 'error', 'error': 'Please apply the Timbuctoo collection id'}), 400

    collection = Collection(request.values.get('endpoint'),
                            request.values.get('dataset_id'), request.values.get('collection_id'))
    collection.start_download()

    return jsonify({'result': 'ok'})


@app.route('/stopwords/<dictionary>')
@authenticated
def stopwords(dictionary):
    try:
        return jsonify(get_stopwords(dictionary))
    except:
        return jsonify({'result': 'error', 'error': 'Please specify a valid dictionary key'}), 400


@app.route('/job/create', methods=['POST'])
@authenticated
def job_create():
    if not request.values.get('job_title'):
        return jsonify({'result': 'error', 'error': 'Please specify a title for this new job'}), 400
    if not request.values.get('job_description'):
        return jsonify({'result': 'error', 'error': 'Please specify a description for this new job'}), 400

    job_id = hash_string(request.values['job_title'] + request.values['job_description'])
    job = Job(job_id)

    created = False
    while not created:
        try:
            job_link = request.values['job_link'] if 'job_link' in request.values \
                                                     and len(request.values['job_link'].strip()) > 0 else None
            job.create_job(request.values['job_title'], request.values['job_description'], job_link)
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
        restart = 'restart' in request.values and request.values['restart'] == 'true'
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
    return jsonify(job.get_links_totals(id, type, **get_data_retrieval_params([
        'with_view_filters', 'uris', 'cluster_ids', 'min_strength', 'max_strength'])))


@app.route('/job/<job:job>/clusters_totals/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def clusters_totals(job, type, id):
    return jsonify(job.get_clusters_totals(id, type, **get_data_retrieval_params([
        'with_view_filters', 'uris', 'cluster_ids', 'min_strength', 'max_strength',
        'min_size', 'max_size', 'min_count', 'max_count'])))


@app.route('/job/<job:job>/entity_type_selection/<int:id>')
@authenticated
@with_job
@with_entity_type_selection
def entity_type_selection_sample(job, id):
    return jsonify(job.get_entity_type_selection_sample(
        id, invert=(request.values.get('invert', default=False) == 'true'), **get_paging_params()))


@app.route('/job/<job:job>/links/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def links(job, type, id):
    return jsonify(list(job.get_links(id, type, **get_data_retrieval_params([
        'with_view_filters', 'with_view_properties', 'validation_filter', 'uris', 'cluster_ids',
        'min_strength', 'max_strength', 'sort']), **get_paging_params())))


@app.route('/job/<job:job>/clusters/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def clusters(job, type, id):
    return jsonify(list(job.get_clusters(id, type, **get_data_retrieval_params([
        'with_view_filters', 'with_view_properties', 'include_nodes', 'uris', 'cluster_ids',
        'min_strength', 'max_strength', 'min_size', 'max_size', 'min_count', 'max_count', 'sort'
    ]), **get_paging_params())))


@app.route('/job/<job:job>/validate/<type:type>/<int:id>', methods=['POST'])
@authenticated
@with_job
@with_spec
def validate_link(job, type, id):
    job.validate_link(id, type, request.values.get('validation'), **get_data_retrieval_params([
        'with_view_filters', 'validation_filter', 'uris', 'cluster_ids', 'link', 'min_strength', 'max_strength']))

    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/motivate/<type:type>/<int:id>', methods=['POST'])
@authenticated
@with_job
@with_spec
def motivate_link(job, type, id):
    job.motivate_link(id, type, request.values.get('motivation'), **get_data_retrieval_params([
        'with_view_filters', 'validation_filter', 'uris', 'cluster_ids', 'link', 'min_strength', 'max_strength']))

    return jsonify({'result': 'ok'})


@app.route('/job/<job:job>/cluster/<type:type>/<int:id>/<int:cluster_id>/graph')
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

    validation_filter = Validation.get(request.values.getlist('valid'))
    export_generator = export.csv_export_generator(validation_filter)

    return Response(export_generator, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=' + type + '_' + str(id) + '.csv'})


@app.route('/job/<job:job>/rdf/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def export_to_rdf(job, type, id):
    export = Export(job, type, id)

    link_pred_namespace = request.values.get('link_pred_namespace')
    link_pred_shortname = request.values.get('link_pred_shortname')
    export_metadata = request.values.get('export_metadata', default=True) == 'true'
    export_linkset = request.values.get('export_linkset', default=True) == 'true'
    reification = request.values.get('reification', default='none')
    use_graphs = request.values.get('use_graphs', default=True) == 'true'
    creator = request.values.get('creator')
    publisher = request.values.get('publisher')
    validation_filter = Validation.get(request.values.getlist('valid'))

    export_generator = export.rdf_export_generator(
        link_pred_namespace, link_pred_shortname, export_metadata, export_linkset,
        reification, use_graphs, creator, publisher, validation_filter)

    mimetype = 'application/trig' if use_graphs else 'text/turtle'
    extension = '.trig' if use_graphs else '.ttl'

    return Response(export_generator, mimetype=mimetype,
                    headers={'Content-Disposition': 'attachment; filename=' + type + '_' + str(id) + extension})


def get_paging_params():
    offset = request.values.get('offset', default=0, type=int)
    limit = request.values.get('limit', type=int)

    return {'offset': offset, 'limit': limit}


def get_data_retrieval_params(whitelist):
    data_retrieval_params = dict()

    if 'with_view_filters' in whitelist:
        data_retrieval_params['with_view_filters'] = request.values.get('apply_filters', default=True) == 'true'
    if 'with_view_properties' in whitelist:
        data_retrieval_params['with_view_properties'] = request.values.get('with_view_properties', default='multiple')
        if data_retrieval_params['with_view_properties'] not in ['none', 'single', 'multiple']:
            data_retrieval_params['with_view_properties'] = 'multiple'
    if 'include_nodes' in whitelist:
        data_retrieval_params['include_nodes'] = request.values.get('include_nodes', default=False) == 'true'

    if 'validation_filter' in whitelist:
        data_retrieval_params['validation_filter'] = Validation.get(request.values.getlist('valid'))
    if 'uris' in whitelist:
        data_retrieval_params['uris'] = request.values.getlist('uri')
    if 'cluster_ids' in whitelist:
        data_retrieval_params['cluster_ids'] = request.values.getlist('cluster_id', type=int)
    if 'link' in whitelist:
        data_retrieval_params['link'] = (request.values.get('source'), request.values.get('target'))

    if 'min_strength' in whitelist:
        data_retrieval_params['min_strength'] = request.values.get('min', type=float)
    if 'max_strength' in whitelist:
        data_retrieval_params['max_strength'] = request.values.get('max', type=float)

    if 'min_size' in whitelist:
        data_retrieval_params['min_size'] = request.values.get('min_size', type=int)
    if 'max_size' in whitelist:
        data_retrieval_params['max_size'] = request.values.get('max_size', type=int)

    if 'min_count' in whitelist:
        data_retrieval_params['min_count'] = request.values.get('min_count', type=int)
    if 'max_count' in whitelist:
        data_retrieval_params['max_count'] = request.values.get('max_count', type=int)

    if 'sort' in whitelist:
        data_retrieval_params['sort'] = request.values.get('sort')

    return data_retrieval_params


if __name__ == '__main__':
    app.run()
