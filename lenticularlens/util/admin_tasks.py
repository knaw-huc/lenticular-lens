from os import environ
from psycopg import sql, rows
from datetime import datetime, timedelta

from lenticularlens.job.job import Job
from lenticularlens.util.config_db import conn_pool


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
    entity_types_in_use = set()
    for job in jobs_by_query('SELECT * FROM jobs'):
        for ets in job.entity_type_selections:
            entity_types_in_use.add(ets.entity_type)
            for property in ets.all_props:
                entity_types_in_use = entity_types_in_use.union(property.entity_types_required)

        for linkset in job.linkset_specs:
            for property in linkset.all_props:
                entity_types_in_use = entity_types_in_use.union(property[1].entity_types_required)

        for lens in job.lens_specs:
            for property in lens.all_props:
                entity_types_in_use = entity_types_in_use.union(property[1].entity_types_required)

        for view in job.views:
            for property in view.all_props:
                entity_types_in_use = entity_types_in_use.union(property.entity_types_required)

    in_use = set(map(lambda et: (et.dataset_id, et.entity_type_id), entity_types_in_use))

    with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
        cur.execute('SELECT dataset_id, entity_type_id, table_name FROM entity_types')

        for table in cur:
            if (table['dataset_id'], table['entity_type_id']) not in in_use:
                cur.execute('DELETE FROM entity_types WHERE table_name = %s', table['table_name'])
                cur.execute(
                    sql.SQL('DROP TABLE IF EXISTS entity_types_data.{}').format(sql.Identifier(table['table_name'])))


def jobs_by_query(job_query):
    with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
        cur.execute(job_query)
        return list(map(lambda job_spec: Job(job_spec['job_id'], job_spec), cur.fetchall()))
