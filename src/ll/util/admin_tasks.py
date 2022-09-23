from os import environ
from psycopg2 import extras, sql
from datetime import datetime, timedelta

from ll.job.job import Job
from ll.data.collection import Collection
from ll.util.config_db import db_conn


def cleanup_jobs():
    auto_delete_date = datetime.today() - timedelta(days=int(environ.get('AUTO_DELETE_JOB_DAYS')))
    jobs_query = sql.SQL('''
        SELECT * 
        FROM jobs AS j
        INNER JOIN job_users AS ju
        ON j.job_id = ju.job_id AND ju.role = 'owner'
        INNER JOIN users AS u 
        ON ju.user_id = u.user_id
        WHERE u.auto_delete_data AND j.created_at <= {}
    ''').format(sql.Literal(auto_delete_date))

    for job in jobs_by_query(jobs_query):
        job.delete()


def cleanup_downloaded():
    collections_in_use = set()
    for job in jobs_by_query('SELECT * FROM jobs'):
        for ets in job.entity_type_selections:
            collections_in_use.add(ets.collection)
            for property in ets.all_props:
                collections_in_use = collections_in_use.union(property.collections_required)

        for linkset in job.linkset_specs:
            for property in linkset.all_props:
                collections_in_use = collections_in_use.union(property[1].collections_required)

        for lens in job.lens_specs:
            for property in lens.all_props:
                collections_in_use = collections_in_use.union(property[1].collections_required)

        for view in job.views:
            for property in view.all_props:
                collections_in_use = collections_in_use.union(property.collections_required)

    with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute('SELECT table_name, graphql_endpoint, dataset_id, collection_id FROM timbuctoo_tables')

        for table in cur:
            collection = Collection(table['graphql_endpoint'], table['dataset_id'], table['collection_id'])
            if collection not in collections_in_use:
                cur.execute('DELETE FROM timbuctoo_tables WHERE table_name = %s', table['table_name'])
                cur.execute(sql.SQL('DROP TABLE IF EXISTS timbuctoo.{}').format(sql.Identifier(table['table_name'])))


def jobs_by_query(job_query):
    with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute(job_query)
        return list(map(lambda job_spec: Job(job_spec['job_id'], job_spec), cur.fetchall()))
