import time
import random
import psycopg2

from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
from psycopg2.extensions import AsIs

from common.helpers import hasher, get_pagination_sql
from common.config_db import db_conn, execute_query, run_query
from common.ll.DataAccess.PostgreSQL.Query import get_values_for


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


def get_value_targets(job_id, alignment):
    job_data = get_job_data(job_id)
    return next((mapping['value_targets'] for mapping in job_data['mappings'] if mapping['id'] == alignment), [])


def get_links(job_id, alignment, cluster_id=None, limit=None, offset=0, include_props=False):
    linkset_table = 'linkset_' + job_id + '_' + str(alignment)
    limit_offset_sql = get_pagination_sql(limit, offset)

    values = None
    if include_props:
        targets = get_value_targets(job_id, alignment)
        values = get_values_for(targets, linkset_table_name=linkset_table, cluster_id=cluster_id,
                                limit=limit, offset=offset)

    where_sql = 'WHERE cluster_id = %s' if cluster_id else ''
    query = 'SELECT source_uri, target_uri, strength, cluster_id, valid FROM {} {} {}' \
        .format(linkset_table, where_sql, limit_offset_sql)

    with db_conn() as conn, conn.cursor() as cur:
        cur.itersize = 10000
        cur.execute(query, (cluster_id,) if cluster_id else None)

        for link in cur:
            yield {
                'source': link[0],
                'source_values': values[link[0]] if include_props else None,
                'target': link[1],
                'target_values': values[link[1]] if include_props else None,
                'strength': link[2],
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
        values = get_values_for(targets, linkset_table_name=linkset_table, clusters_table_name=clusters_table,
                                limit=limit, offset=offset)

    with db_conn() as conn, conn.cursor() as cur:
        cur.itersize = 10000
        cur.execute('SELECT id, size, links, nodes FROM {} ORDER BY size DESC {}'
                    .format(clusters_table, limit_offset_sql))

        for cluster in cur:
            cluster_values = {}
            if include_props:
                for uri, uri_values in values.items():
                    if '<' + uri + '>' in cluster[3]:
                        for prop_value in uri_values:
                            key = prop_value['dataset'] + '_' + prop_value['property']
                            if key not in cluster_values:
                                cluster_values[key] = {
                                    'dataset': prop_value['dataset'],
                                    'property': prop_value['property'],
                                    'values': set()
                                }
                            cluster_values[key]['values'].update(prop_value['values'])

            yield {
                'id': cluster[0],
                'size': cluster[1],
                'links': cluster[2],
                'values': [{
                    'dataset': cluster_value['dataset'],
                    'property': cluster_value['property'],
                    'values': list(cluster_value['values'])
                } for key, cluster_value in cluster_values.items()] if include_props else None
            }


def get_cluster(job_id, alignment, cluster_id):
    linkset_table = 'linkset_' + job_id + '_' + str(alignment)
    links = execute_query({
        'query': f'SELECT source_uri, target_uri, strength FROM {linkset_table} WHERE cluster_id = %s',
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
        strengths[link_hash] = [link[2]]

        if source not in nodes:
            nodes.append(source)
        if target not in nodes:
            nodes.append(target)

    return {'links': all_links, 'strengths': strengths, 'nodes': nodes}


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
