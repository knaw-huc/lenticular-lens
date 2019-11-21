import time
import random
import psycopg2

from enum import IntFlag
from decimal import Decimal

from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
from psycopg2.extensions import AsIs

from ll.job.job_config import JobConfig

from ll.data.collection import Collection
from ll.data.query import get_property_values

from ll.util.config_db import db_conn, execute_query, run_query
from ll.util.helpers import hash_string, hasher, get_pagination_sql


class ExportLinks(IntFlag):
    ALL = 7
    ACCEPTED = 4
    DECLINED = 2
    NOT_VALIDATED = 1


def get_job_data(job_id):
    return run_query('SELECT * FROM reconciliation_jobs WHERE job_id = %s', (job_id,), dict=True)


def get_job_alignments(job_id):
    return execute_query({
        'query': "SELECT * FROM alignments WHERE job_id = %s",
        'parameters': (job_id,)
    }, {'cursor_factory': psycopg2_extras.RealDictCursor})


def get_job_alignment(job_id, alignment):
    return run_query('SELECT * FROM alignments WHERE job_id = %s AND alignment = %s', (job_id, alignment), dict=True)


def get_job_clusterings(job_id):
    return execute_query({
        'query': "SELECT * FROM clusterings WHERE job_id = %s",
        'parameters': (job_id,)
    }, {'cursor_factory': psycopg2_extras.RealDictCursor})


def get_job_clustering(job_id, alignment):
    return run_query('SELECT * FROM clusterings WHERE job_id = %s AND alignment = %s', (job_id, alignment), dict=True)


def get_value_targets(job_id, alignment, downloaded_only=True):
    def is_downloaded(dataset_id, collection_id):
        return any(download['dataset_id'] == dataset_id and download['collection_id'] == collection_id
                   for download in downloaded)

    job_data = get_job_data(job_id)
    value_targets = next((mapping['value_targets'] for mapping in job_data['mappings'] if mapping['id'] == alignment))

    if not downloaded_only:
        return value_targets

    new_value_targets = []
    downloaded = Collection.download_status()['downloaded']

    for value_target in value_targets:
        graph = value_target['graph']
        new_graph_data = []

        for data_of_entity in value_target['data']:
            entity_type = data_of_entity['entity_type']

            if is_downloaded(graph, entity_type):
                new_properties = []
                for properties in data_of_entity['properties']:
                    if len(properties) == 1 or all(is_downloaded(graph, entity) for entity in properties[1::2]):
                        new_properties.append(properties)

                if len(new_properties) > 0:
                    new_graph_data.append({'entity_type': entity_type, 'properties': new_properties})

        if len(new_graph_data) > 0:
            new_value_targets.append({'graph': graph, 'data': new_graph_data})

    return new_value_targets


def get_links(job_id, alignment, export_links=ExportLinks.ALL, cluster_id=None,
              limit=None, offset=0, include_props=False):
    linkset_table = 'linkset_' + job_id + '_' + str(alignment)
    limit_offset_sql = get_pagination_sql(limit, offset)

    values = None
    if include_props:
        targets = get_value_targets(job_id, alignment)
        if targets:
            values = get_property_values(targets, linkset_table_name=linkset_table, cluster_id=cluster_id,
                                         limit=limit, offset=offset)

    cluster_sql = 'cluster_id = %s' if cluster_id else ''
    export_links_sql = []
    if export_links < ExportLinks.ALL and ExportLinks.ACCEPTED in export_links:
        export_links_sql.append('valid = true')
    if export_links < ExportLinks.ALL and ExportLinks.DECLINED in export_links:
        export_links_sql.append('valid = false')
    if export_links < ExportLinks.ALL and ExportLinks.NOT_VALIDATED in export_links:
        export_links_sql.append('valid IS NULL')

    where_sql = ''
    if cluster_id and export_links < ExportLinks.ALL:
        where_sql = 'WHERE {} AND ({})'.format(cluster_sql, ' OR '.join(export_links_sql))
    elif cluster_id:
        where_sql = 'WHERE {}'.format(cluster_sql)
    elif export_links < ExportLinks.ALL:
        where_sql = 'WHERE {}'.format(' OR '.join(export_links_sql))

    query = 'SELECT source_uri, target_uri, strengths, cluster_id, valid FROM {} {} {}' \
        .format(linkset_table, where_sql, limit_offset_sql)

    with db_conn() as conn, conn.cursor() as cur:
        cur.itersize = 10000
        cur.execute(query, (cluster_id,) if cluster_id else None)

        for link in cur:
            yield {
                'source': link[0],
                'source_values': values[link[0]] if values else None,
                'target': link[1],
                'target_values': values[link[1]] if values else None,
                'strengths': [float(strength) if isinstance(strength, Decimal) else strength for strength in link[2]],
                'cluster_id': link[3],
                'valid': link[4]
            }


def get_clusters(job_id, alignment, limit=None, offset=0, include_props=False):
    linkset_table = 'linkset_' + job_id + '_' + str(alignment)
    clusters_table = 'clusters_' + job_id + '_' + str(alignment)
    limit_offset_sql = get_pagination_sql(limit, offset)

    values = None
    if include_props:
        targets = get_value_targets(job_id, alignment)
        if targets:
            values = get_property_values(targets, linkset_table_name=linkset_table, clusters_table_name=clusters_table,
                                         limit=limit, offset=offset)

    with db_conn() as conn, conn.cursor() as cur:
        cur.itersize = 10000

        if values:
            cur.execute("""
                SELECT clusters.id, clusters.size, clusters.links, 
                       ARRAY_AGG(DISTINCT links.source_uri) || ARRAY_AGG(DISTINCT links.target_uri) AS nodes
                FROM {} AS clusters
                LEFT JOIN {} AS links ON clusters.id = links.cluster_id
                GROUP BY clusters.id
                ORDER BY clusters.size DESC {}
            """.format(clusters_table, linkset_table, limit_offset_sql))
        else:
            cur.execute('SELECT id, size, links FROM {} ORDER BY size DESC {}'.format(clusters_table, limit_offset_sql))

        for cluster in cur:
            cluster_values = {}
            cluster_keys = {}

            if values:
                for uri, uri_values in values.items():
                    if uri in cluster[3]:
                        for prop_value in uri_values:
                            key = prop_value['dataset'] + '_' + prop_value['property']

                            if key not in cluster_values:
                                cluster_values[key] = {
                                    'dataset': prop_value['dataset'],
                                    'property': prop_value['property'],
                                    'values': set()
                                }

                            if key not in cluster_keys:
                                cluster_keys[key] = 0

                            cluster_prop_values = prop_value['values'][:5]
                            cluster_keys[key] = cluster_keys[key] + len(cluster_prop_values)

                            if cluster_keys[key] < 5:
                                cluster_values[key]['values'].update(cluster_prop_values)

            yield {
                'id': cluster[0],
                'size': cluster[1],
                'links': cluster[2],
                'values': [{
                    'dataset': cluster_value['dataset'],
                    'property': cluster_value['property'],
                    'values': list(cluster_value['values'])
                } for key, cluster_value in cluster_values.items()] if values else None
            }


def get_cluster(job_id, alignment, cluster_id):
    linkset_table = 'linkset_' + job_id + '_' + str(alignment)
    links = execute_query({
        'query': f'SELECT source_uri, target_uri, strengths FROM {linkset_table} WHERE cluster_id = %s',
        'parameters': (cluster_id,)
    })

    all_links = []
    strengths = {}
    nodes = []
    for link in links:
        source = '<' + link[0] + '>'
        target = '<' + link[1] + '>'

        current_link = (source, target) if source < target else (target, source)
        link_hash = "key_{}".format(str(hasher(current_link)).replace("-", "N"))

        all_links.append([source, target])
        strengths[link_hash] = link[2]

        if source not in nodes:
            nodes.append(source)
        if target not in nodes:
            nodes.append(target)

    return {'links': all_links, 'strengths': strengths, 'nodes': nodes}


def get_resource_sample(job_id, resource_label, limit=None, offset=0, total=False):
    job_data = get_job_data(job_id)
    job_config = JobConfig('job_id', job_data['resources'], job_data['mappings'])

    resource_label = hash_string(resource_label)
    resource = job_config.get_resource_by_label(resource_label)
    if not resource:
        return []

    selection = psycopg2_sql.SQL('count(*) AS total') if total else resource.properties_sql
    order_limit = psycopg2_sql.SQL('' if total else 'ORDER BY uri ' + get_pagination_sql(limit, offset))

    with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
        cur.execute(psycopg2_sql.SQL("""
            SELECT {selection}
            FROM {table_name} AS {view_name} {joins} {wheres} 
            {order_limit}; 
        """).format(
            selection=selection,
            table_name=psycopg2_sql.Identifier(resource.table_name),
            view_name=psycopg2_sql.Identifier(resource.label),
            joins=resource.joins_related_sql,
            wheres=resource.where_sql,
            order_limit=order_limit,
        ))

        return cur.fetchone() if total else cur.fetchall()


def update_job_data(job_id, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn:
                with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                    if run_query('SELECT 1 FROM reconciliation_jobs WHERE job_id = %s', (job_id,)):
                        query = psycopg2_sql.SQL(
                            "UPDATE reconciliation_jobs SET ({}) = ROW %s, updated_at = NOW() WHERE job_id = %s"
                        ).format(psycopg2_sql.SQL(', '.join(job_data.keys())))
                        cur.execute(query, (tuple(job_data.values()), job_id))
                    else:
                        cur.execute(psycopg2_sql.SQL("INSERT INTO reconciliation_jobs (job_id, %s) VALUES %s"),
                                    (AsIs(', '.join(job_data.keys())), tuple([job_id] + list(job_data.values()))))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break


def update_alignment_job(job_id, alignment, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    psycopg2_sql.SQL("UPDATE alignments SET ({}) = ROW %s WHERE job_id = %s AND alignment = %s")
                        .format(psycopg2_sql.SQL(', '.join(job_data.keys()))),
                    (tuple(job_data.values()), job_id, alignment))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break


def update_clustering_job(job_id, alignment, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        psycopg2_sql.SQL("UPDATE clusterings SET ({}) = ROW %s WHERE job_id = %s AND alignment = %s")
                            .format(
                            psycopg2_sql.SQL(', '.join(job_data.keys()))),
                        (tuple(job_data.values()), job_id, alignment))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break
