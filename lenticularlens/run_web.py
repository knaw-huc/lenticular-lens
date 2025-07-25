import os
import json
import uuid
import logging
import decimal
import datetime
import eventlet
import functools
import threading

from flask import Flask, Response, jsonify, session, request, redirect
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_socketio import SocketIO

from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.user_session import UserSession
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata

from psycopg.errors import UniqueViolation
from werkzeug.routing.converters import BaseConverter, ValidationError

from lenticularlens.data.timbuctoo.dataset import Dataset as TimbuctooDataset
from lenticularlens.data.timbuctoo.entity_type import EntityType as TimbuctooEntityType
from lenticularlens.data.sparql.dataset import Dataset as SPARQLDataset
from lenticularlens.data.sparql.entity_type import EntityType as SPARQLEntityType

from lenticularlens.job.user import User
from lenticularlens.job.job import Job, Validation
from lenticularlens.job.lens_sql import LensSql
from lenticularlens.job.matching_sql import MatchingSql
from lenticularlens.job.export import CsvExport, RdfExport

from lenticularlens.util.hasher import hash_string
from lenticularlens.util.stopwords import get_stopwords
from lenticularlens.util.config_db import listen_for_notify
from lenticularlens.util.config_logging import config_logger
from lenticularlens.util.helpers import get_string_from_sql
from lenticularlens.util.admin_tasks import cleanup_jobs, cleanup_downloaded
from lenticularlens.util.db_functions import reset, get_filter_functions, get_matching_methods, get_transformers, \
    get_all_jobs


class FixedDefaultJSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, datetime.date):
            return obj.isoformat()

        return DefaultJSONProvider.default(obj)


class JobConverter(BaseConverter):
    def to_python(self, job_id):
        return Job(job_id)


class TypeConverter(BaseConverter):
    def to_python(self, type):
        if type == 'linkset' or type == 'lens':
            return type
        raise ValidationError()


def emit_database_events():
    q = eventlet.Queue()
    eventlet.spawn(listen_for_notify, q)
    while True:
        notify = q.get()
        if notify.channel == 'extension_update':
            reset()

        ns = '' if (notify.channel == 'extension_update' or
                    notify.channel.startswith('timbuctoo_') or notify.channel.startswith('sparql_')) \
            else json.loads(notify.payload)['job_id']

        socketio.emit(notify.channel, notify.payload, namespace=f'/{ns}')
        log.debug(f'WebSocket emit on /{ns}: {notify.channel} = {notify.payload}')


config_logger()
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    OIDC_REDIRECT_URI=os.environ.get('APP_DOMAIN', 'http://localhost') + '/oidc_redirect',
    SECRET_KEY=os.environ.get('SECRET_KEY', uuid.uuid4().hex),
    COMPRESS_MIMETYPES=['text/html', 'text/css', 'text/plain', 'text/csv', 'text/turtle',
                        'application/json', 'application/javascript', 'application/trig'],
)
app.json = FixedDefaultJSONProvider(app)
app.url_map.converters['job'] = JobConverter
app.url_map.converters['type'] = TypeConverter

CORS(app)

auth = OIDCAuthentication({'default': ProviderConfiguration(
    issuer=os.environ['OIDC_SERVER'],
    client_metadata=ClientMetadata(
        client_id=os.environ['OIDC_CLIENT_ID'],
        client_secret=os.environ['OIDC_CLIENT_SECRET']),
    auth_request_params={'scope': ['openid', 'email', 'profile']},
)}, app) if 'OIDC_SERVER' in os.environ and len(os.environ['OIDC_SERVER']) > 0 else None

enable_logger = os.environ.get('LOG_LEVEL', 'INFO').lower() == 'debug'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*', namespaces='*',
                    logger=enable_logger, engineio_logger=enable_logger)
socketio.start_background_task(emit_database_events)


def authenticated(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if auth:
            user_session = UserSession(session, 'default')
            if user_session.last_authenticated is None:
                return jsonify(result='not_authenticated', error='Please login!'), 401

            if 'persisted' not in session:
                user = User(user_session.userinfo)
                user.persist_data()
                session['persisted'] = True

        return func(*args, **kwargs)

    return wrapper


def admin_task(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'access_token' not in request.values or \
                request.values['access_token'] != os.environ.get('ADMIN_ACCESS_TOKEN'):
            return jsonify(result='not_authenticated', error='No access!'), 401

        return func(*args, **kwargs)

    return wrapper


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
            return jsonify(result='error', error='Please specify a job id'), 400

        kwargs['job'] = job
        if not job.data:
            return jsonify(result='error', error=f"Job with id '{job.job_id}' not found"), 404

        return func(*args, **kwargs)

    return wrapper


def with_spec(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        spec = kwargs['job'].get_spec_by_id(kwargs['id'], kwargs['type'])
        if not spec:
            return jsonify(result='error',
                           error=f"Spec with type '{kwargs['type']}' and id '{kwargs['id']}' not found"), 404

        return func(*args, **kwargs)

    return wrapper


def with_entity_type_selection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not kwargs['job'].get_entity_type_selection_by_id(kwargs['id']):
            return jsonify(result='error',
                           error=f"Entity-type selection with id '{kwargs['id']}' not found"), 404

        return func(*args, **kwargs)

    return wrapper


@app.get('/')
def index():
    return 'Lenticular Lens'


if auth:
    @app.get('/login')
    @auth.oidc_auth('default')
    def login():
        destination = request.values.get('redirect-uri', default='/')
        return redirect(destination)


    @app.get('/user_info')
    @authenticated
    def user_info():
        user_session = UserSession(session, 'default')
        return jsonify(user_session.userinfo)


@app.get('/datasets/timbuctoo/downloads')
@authenticated
def downloads_timbuctoo():
    downloads = TimbuctooDataset.get_downloads()
    return jsonify([download.model_dump() for download in downloads])


@app.get('/datasets/sparql/downloads')
@authenticated
def downloads_sparql():
    downloads = SPARQLDataset.get_downloads()
    return jsonify([download.model_dump() for download in downloads])


@app.get('/datasets/timbuctoo')
@authenticated
def datasets_timbuctoo():
    if not request.values.get('graphql_endpoint'):
        return jsonify(result='error', error='Please apply the GraphQL endpoint'), 400

    datasets = TimbuctooDataset.get_datasets_for_graphql(request.values.get('graphql_endpoint'))
    return jsonify({key: value.model_dump() for key, value in datasets.items()})


@app.get('/datasets/sparql')
@authenticated
def datasets_sparql():
    if not request.values.get('sparql_endpoint'):
        return jsonify(result='error', error='Please apply the SPARQL endpoint'), 400

    datasets = SPARQLDataset.get_datasets_for_sparql(request.values.get('sparql_endpoint'))
    return jsonify({key: value.model_dump() for key, value in datasets.items()})


@app.post('/datasets/sparql/load')
@authenticated
def datasets_sparql_load():
    if not request.values.get('sparql_endpoint'):
        return jsonify(result='error', error='Please apply the SPARQL endpoint'), 400

    SPARQLDataset.load_datasets_for_sparql(request.values.get('sparql_endpoint'))

    return jsonify(result='ok')


@app.post('/datasets/timbuctoo')
@authenticated
def datasets_timbuctoo_download():
    if not request.values.get('graphql_endpoint'):
        return jsonify(result='error', error='Please apply the GraphQL endpoint'), 400
    if not request.values.get('timbuctoo_id'):
        return jsonify(result='error', error='Please apply the Timbuctoo id'), 400
    if not request.values.get('entity_type_id'):
        return jsonify(result='error', error='Please apply the entity type id'), 400

    TimbuctooEntityType.start_download(request.values.get('graphql_endpoint'),
                                       request.values.get('timbuctoo_id'), request.values.get('entity_type_id'))

    return jsonify(result='ok')


@app.post('/datasets/sparql')
@authenticated
def datasets_sparql_download():
    if not request.values.get('sparql_endpoint'):
        return jsonify(result='error', error='Please apply the SPARQL endpoint'), 400
    if not request.values.get('entity_type_id'):
        return jsonify(result='error', error='Please apply the entity type id'), 400

    SPARQLEntityType.start_download(request.values.get('sparql_endpoint'), request.values.get('entity_type_id'))

    return jsonify(result='ok')


@app.get('/stopwords/<dictionary>')
@authenticated
def stopwords(dictionary):
    try:
        return jsonify(get_stopwords(dictionary))
    except:
        return jsonify(result='error', error='Please specify a valid dictionary key'), 400


@app.get('/methods')
@authenticated
def methods():
    filter_functions_info = get_filter_functions()
    matching_methods_info = get_matching_methods()
    transformers_info = get_transformers()

    return jsonify(
        filter_functions=filter_functions_info,
        filter_functions_order=list(filter_functions_info.keys()),
        matching_methods=matching_methods_info,
        matching_methods_order=list(matching_methods_info.keys()),
        transformers=transformers_info,
        transformers_order=list([key for key, item in transformers_info.items() if not item.get('internal', False)]),
    )


@app.get('/job/list')
@authenticated
def job_list():
    return jsonify(get_user().list_jobs() if auth else get_all_jobs())


@app.post('/job/create')
@authenticated
def job_create():
    if not request.values.get('job_title'):
        return jsonify(result='error', error='Please specify a title for this new job'), 400
    if not request.values.get('job_description'):
        return jsonify(result='error', error='Please specify a description for this new job'), 400

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

    if auth:
        get_user().register_job(job_id, 'owner')

    return jsonify(result='created', job_id=job_id)


@app.post('/job/update')
@authenticated
@with_job
def job_update(job):
    entity_type_selections, linkset_specs, lens_specs, views, errors = job.update_data(request.json)

    if len(errors) > 0:
        return jsonify(
            result='error',
            job_id=job.job_id,
            errors=[str(error) for error in errors],
            entity_type_selections=[entity_type_selection['id'] for entity_type_selection in entity_type_selections],
            linkset_specs=[linkset_spec['id'] for linkset_spec in linkset_specs],
            lens_specs=[lens_spec['id'] for lens_spec in lens_specs],
            views=[[view['id'], view['type']] for view in views],
        ), 400

    return jsonify(
        result='updated',
        job_id=job.job_id,
        entity_type_selections=[entity_type_selection['id'] for entity_type_selection in entity_type_selections],
        linkset_specs=[linkset_spec['id'] for linkset_spec in linkset_specs],
        lens_specs=[lens_spec['id'] for lens_spec in lens_specs],
        views=[[view['id'], view['type']] for view in views],
    )


@app.get('/job/<job:job>')
@authenticated
@with_job
def job_data(job):
    if auth and (not job.data['users'] or get_user().user_id not in job.data['users']):
        get_user().register_job(job.data['job_id'], 'shared')

    return jsonify(
        job_id=job.data['job_id'],
        job_title=job.data['job_title'],
        job_description=job.data['job_description'],
        job_link=job.data['job_link'],
        entity_type_selections=job.data['entity_type_selections_form_data'],
        linkset_specs=job.data['linkset_specs_form_data'],
        lens_specs=job.data['lens_specs_form_data'],
        views=job.data['views_form_data'],
        created_at=job.data['created_at'],
        updated_at=job.data['updated_at']
    )


@app.get('/job/<job:job>/linksets')
@authenticated
@with_job
def job_linksets(job):
    return jsonify(job.linksets)


@app.get('/job/<job:job>/lenses')
@authenticated
@with_job
def job_lenses(job):
    return jsonify(job.lenses)


@app.get('/job/<job:job>/clusterings')
@authenticated
@with_job
def job_clusterings(job):
    return jsonify(job.clusterings)


@app.post('/job/<job:job>/run/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def run_spec(job, type, id):
    try:
        restart = 'restart' in request.values and request.values['restart'] == 'true'
        job.run_linkset(id, restart) if type == 'linkset' else job.run_lens(id, restart)
        return jsonify(result='ok')
    except UniqueViolation:
        return jsonify(result='exists'), 400


@app.post('/job/<job:job>/run_clustering/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def run_clustering(job, type, id):
    try:
        job.run_clustering(id, type)
        return jsonify(result='ok')
    except UniqueViolation:
        return jsonify(result='exists'), 400


@app.get('/job/<job:job>/sql/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def sql(job, type, id):
    job_sql = MatchingSql(job, id) if type == 'linkset' else LensSql(job, id)
    return Response(job_sql.sql_string, mimetype='text/plain')


@app.post('/job/<job:job>/kill/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def kill_spec(job, type, id):
    job.kill_linkset(id) if type == 'linkset' else job.kill_lens(id)
    return jsonify(result='ok')


@app.post('/job/<job:job>/kill_clustering/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def kill_clustering(job, type, id):
    job.kill_clustering(id, type)
    return jsonify(result='ok')


@app.delete('/job/<job:job>')
@authenticated
@with_job
def delete_job(job):
    job.delete()
    return jsonify(result='ok')


@app.delete('/job/<job:job>/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def delete_spec(job, type, id):
    lens_uses = job.spec_lens_uses(id, type)
    if len(lens_uses) > 0:
        return jsonify(result='error', lens_uses=lens_uses), 400

    job.delete_spec(id, type)
    return jsonify(result='ok')


@app.get('/job/<job:job>/entity_type_selection_total/<int:id>')
@authenticated
@with_job
@with_entity_type_selection
def entity_type_selection_total(job, id):
    sql_only = request.values.get('sql', default=False) == 'true'
    result = job.get_entity_type_selection_sample_total(id, sql_only=sql_only)

    if sql_only:
        return Response(get_string_from_sql(result), mimetype='text/plain')

    return jsonify(result)


@app.route('/job/<job:job>/links_totals/<type:type>/<int:id>', methods=['GET', 'POST'])
@authenticated
@with_job
@with_spec
def links_totals(job, type, id):
    params = get_data_retrieval_params(['sql', 'with_view_filters', 'uris',
                                        'cluster_ids', 'min_strength', 'max_strength'])
    result = job.get_links_totals(id, type, **params)

    if params['sql_only']:
        return Response(get_string_from_sql(result), mimetype='text/plain')

    return jsonify(result)


@app.route('/job/<job:job>/clusters_totals/<type:type>/<int:id>', methods=['GET', 'POST'])
@authenticated
@with_job
@with_spec
def clusters_totals(job, type, id):
    params = get_data_retrieval_params([
        'sql', 'with_view_filters', 'uris', 'cluster_ids', 'min_strength', 'max_strength',
        'min_size', 'max_size', 'min_count', 'max_count'])
    result = job.get_clusters_totals(id, type, **params)

    if params['sql_only']:
        return Response(get_string_from_sql(result), mimetype='text/plain')

    return jsonify(result)


@app.get('/job/<job:job>/entity_type_selection/<int:id>')
@authenticated
@with_job
@with_entity_type_selection
def entity_type_selection_sample(job, id):
    invert = request.values.get('invert', default=False) == 'true'
    sql_only = request.values.get('sql', default=False) == 'true'
    result = job.get_entity_type_selection_sample(id, invert=invert, sql_only=sql_only, **get_paging_params())

    if sql_only:
        return Response(get_string_from_sql(result), mimetype='text/plain')

    return jsonify(result)


@app.route('/job/<job:job>/links/<type:type>/<int:id>', methods=['GET', 'POST'])
@authenticated
@with_job
@with_spec
def links(job, type, id):
    params = get_data_retrieval_params([
        'sql', 'with_view_filters', 'with_view_properties', 'validation_filter', 'uris',
        'cluster_ids', 'min_strength', 'max_strength', 'sort'])
    result = job.get_links(id, type, **params, **get_paging_params())

    if params['sql_only']:
        return Response(get_string_from_sql(result), mimetype='text/plain')

    return jsonify(list(result))


@app.route('/job/<job:job>/clusters/<type:type>/<int:id>', methods=['GET', 'POST'])
@authenticated
@with_job
@with_spec
def clusters(job, type, id):
    params = get_data_retrieval_params([
        'sql', 'with_view_filters', 'with_view_properties', 'include_nodes', 'uris', 'cluster_ids',
        'min_strength', 'max_strength', 'min_size', 'max_size', 'min_count', 'max_count', 'sort'])
    result = job.get_clusters(id, type, **params, **get_paging_params())

    if params['sql_only']:
        return Response(get_string_from_sql(result), mimetype='text/plain')

    return jsonify(list(result))


@app.post('/job/<job:job>/validate/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def validate_link(job, type, id):
    job.validate_link(id, type, request.values.get('validation'), **get_data_retrieval_params([
        'with_view_filters', 'validation_filter', 'uris', 'cluster_ids', 'link', 'min_strength', 'max_strength']))

    return jsonify(result='ok')


@app.post('/job/<job:job>/motivate/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def motivate_link(job, type, id):
    job.motivate_link(id, type, request.values.get('motivation'), **get_data_retrieval_params([
        'with_view_filters', 'validation_filter', 'uris', 'cluster_ids', 'link', 'min_strength', 'max_strength']))

    return jsonify(result='ok')


@app.get('/job/<job:job>/cluster/<type:type>/<int:id>/<int:cluster_id>/graph')
@authenticated
@with_job
@with_spec
def get_cluster_graph_data(job, type, id, cluster_id):
    return jsonify(job.visualize(id, type, cluster_id))


@app.get('/job/<job:job>/csv/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def export_to_csv(job, type, id):
    export = CsvExport(job, type, id)

    validation_filter = Validation.get(request.values.getlist('valid'))
    export_generator = export.create_generator(validation_filter)

    return Response(export_generator, mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={type}_{job.job_id}_{str(id)}.csv'})


@app.get('/job/<job:job>/rdf/<type:type>/<int:id>')
@authenticated
@with_job
@with_spec
def export_to_rdf(job, type, id):
    export = RdfExport(job, type, id)

    export_linkset = request.values.get('export_linkset', default=True) == 'true'
    export_metadata = request.values.get('export_metadata', default=True) == 'true'
    export_validation_set = request.values.get('export_validation_set', default=True) == 'true'
    export_cluster_set = request.values.get('export_cluster_set', default=True) == 'true'

    validation_filter = Validation.get(request.values.getlist('valid'))

    reification = request.values.get('reification', default='none')

    link_pred_namespace = request.values.get('link_pred_namespace')
    link_pred_shortname = request.values.get('link_pred_shortname')

    creator = request.values.get('creator')
    if auth:
        user_session = UserSession(session, 'default')
        if user_session.last_authenticated is not None and \
                user_session.userinfo and 'nickname' in user_session.userinfo:
            creator = user_session.userinfo['nickname']

    export_generator = export.create_generator(
        link_pred_namespace, link_pred_shortname, export_linkset, export_metadata,
        export_validation_set, export_cluster_set, reification, creator, validation_filter)

    use_graphs = (export_linkset and export_metadata or export_validation_set or export_cluster_set) \
                 or export_validation_set or export_cluster_set
    mimetype = 'application/trig' if use_graphs else 'text/turtle'
    extension = 'trig' if use_graphs else 'ttl'

    return Response(export_generator, mimetype=mimetype,
                    headers={'Content-Disposition': f'attachment; filename={type}_{job.job_id}_{str(id)}.{extension}'})


@app.post('/admin/cleanup_jobs')
@admin_task
def admin_cleanup_jobs():
    threading.Thread(target=cleanup_jobs).start()
    return jsonify(ok=True)


@app.post('/admin/cleanup_downloaded')
@admin_task
def admin_cleanup_downloaded():
    threading.Thread(target=cleanup_downloaded).start()
    return jsonify(ok=True)


def get_user():
    user_session = UserSession(session, 'default')
    return User(user_session.userinfo)


def get_paging_params():
    offset = request.values.get('offset', default=0, type=int)
    limit = request.values.get('limit', type=int)

    return {'offset': offset, 'limit': limit}


def get_data_retrieval_params(whitelist):
    data_retrieval_params = dict()

    if 'sql' in whitelist:
        data_retrieval_params['sql_only'] = request.values.get('sql', default=False) == 'true'

    if 'with_view_filters' in whitelist:
        data_retrieval_params['with_view_filters'] = request.values.get('apply_filters', default=True) == 'true'
    if 'with_view_properties' in whitelist:
        data_retrieval_params['with_view_properties'] = request.values.get('with_properties', default='multiple')
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
    socketio.run(app)
