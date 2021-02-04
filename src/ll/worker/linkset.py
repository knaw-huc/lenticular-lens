import time

from psycopg2 import sql as psycopg2_sql, ProgrammingError

from ll.job.job import Job
from ll.job.matching_sql import MatchingSql

from ll.worker.job import WorkerJob
from ll.util.config_db import db_conn


class LinksetJob(WorkerJob):
    def __init__(self, job_id, id):
        self._job_id = job_id
        self._id = id

        self._job = None
        self._matching_sql = None
        self._distinct_counts = {}

        self.reset()
        super().__init__(self.run_generated_sql)

    def reset(self):
        self._job = Job(self._job_id)
        self._matching_sql = MatchingSql(self._job, self._id)

    def run(self):
        download_status_set = False
        while self._job.linkset_has_queued_table_data(self._id) and not self._killed:
            if not download_status_set:
                self._job.update_linkset(self._id, {'status': 'downloading'})
                download_status_set = True

            time.sleep(1)
            self.reset()

        super().run()

    def run_generated_sql(self):
        if not self._killed:
            self.process_sql(self._matching_sql.generate_schema_sql())

        if not self._killed:
            self._status = 'Generating entity-type selections'
            self.process_sql(self._matching_sql.generate_entity_type_selection_sql())

        if not self._killed:
            self._status = 'Generating source entities'
            self.process_sql(self._matching_sql.generate_match_source_sql())

        if not self._killed:
            self._status = 'Generating target entities'
            self.process_sql(self._matching_sql.generate_match_target_sql())

        if not self._killed:
            self._status = 'Generating indexes'
            self.process_sql(self._matching_sql.generate_match_index_and_sequence_sql())

        if not self._killed:
            self._status = 'Looking for links'
            self.process_sql(self._matching_sql.generate_match_linkset_sql())

        if not self._killed:
            self._status = 'Finishing'
            self.process_sql(self._matching_sql.generate_match_linkset_finish_sql())

    def process_sql(self, sql):
        with self._db_conn.cursor() as cur:
            cur.execute(sql)
            self._db_conn.commit()

    def watch_process(self):
        data = {'status_message': self._status}

        with db_conn() as conn, conn.cursor() as cur:
            self.get_sequence_count(conn, cur, 'linkset_count', data, 'links_count')
            self.get_distinct_count(conn, cur, 'source', data, 'distinct_sources_count')
            self.get_distinct_count(conn, cur, 'target', data, 'distinct_targets_count')

        self._job.update_linkset(self._id, data)

    def get_sequence_count(self, conn, cur, sequence, data, key):
        try:
            cur.execute(psycopg2_sql.SQL('SELECT is_called, last_value FROM {linkset_schema}.{sequence}').format(
                linkset_schema=psycopg2_sql.Identifier(self._job.schema_name(self._id)),
                sequence=psycopg2_sql.Identifier(sequence)
            ))

            seq = cur.fetchone()
            if seq[0]:
                data[key] = seq[1]
        except ProgrammingError:
            pass
        finally:
            conn.commit()

    def get_distinct_count(self, conn, cur, table, data, key):
        try:
            if table not in self._distinct_counts:
                cur.execute(psycopg2_sql.SQL('SELECT count(DISTINCT uri) FROM {linkset_schema}.{table_name}').format(
                    linkset_schema=psycopg2_sql.Identifier(self._job.schema_name(self._id)),
                    table_name=psycopg2_sql.Identifier(table)
                ))
                self._distinct_counts[table] = cur.fetchone()[0]
                data[key] = self._distinct_counts[table]
        except ProgrammingError:
            pass
        finally:
            conn.commit()

    def watch_kill(self):
        linkset = self._job.linkset(self._id)
        if linkset['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        self._job.update_linkset(self._id, job_data)

        self.cleanup()

    def on_exception(self):
        err_message = str(self._exception)
        self._job.update_linkset(self._id, {'status': 'failed', 'status_message': err_message})

        self.cleanup()

    def on_finish(self):
        self.watch_process()

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('''
                SELECT  (SELECT count(*) FROM linksets.{linkset_table}) AS links_count,
                        (SELECT count(DISTINCT uri) FROM {linkset_schema}.source) AS sources_count,
                        (SELECT count(DISTINCT uri) FROM {linkset_schema}.target) AS targets_count,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT source_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT target_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS linkset_sources_count,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT target_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT source_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS linkset_targets_count
            ''').format(
                linkset_table=psycopg2_sql.Identifier(self._job.table_name(self._id)),
                linkset_schema=psycopg2_sql.Identifier(self._job.schema_name(self._id)),
            ))

            result = cur.fetchone()

            links = result[0]
            sources = result[1]
            targets = result[2]
            linkset_sources = result[3]
            linkset_targets = result[4]

            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(self._job.schema_name(self._id))))

            cur.execute("UPDATE linksets "
                        "SET status = %s, status_message = null, distinct_links_count = %s, "
                        "distinct_sources_count = %s, distinct_targets_count = %s, "
                        "distinct_linkset_sources_count = %s, distinct_linkset_targets_count = %s, "
                        "finished_at = now() "
                        "WHERE job_id = %s AND spec_id = %s",
                        ('done', links, sources, targets, linkset_sources, linkset_targets, self._job_id, self._id))

            if links == 0:
                cur.execute(psycopg2_sql.SQL('DROP TABLE linksets.{} CASCADE')
                            .format(psycopg2_sql.Identifier(self._job.table_name(self._id))))
            else:
                cur.execute("SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'",
                            (self._job_id, self._id))
                clustering = cur.fetchone()

                if clustering:
                    query = psycopg2_sql.SQL("""
                        UPDATE clusterings 
                        SET status = %s, kill = false, requested_at = now(), processing_at = null, finished_at = null
                        WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'
                    """)

                    cur.execute(query, ('waiting', self._job_id, self._id))
                else:
                    query = psycopg2_sql.SQL("""
                        INSERT INTO clusterings 
                        (job_id, spec_id, spec_type, clustering_type, association_file, status, kill, requested_at) 
                        VALUES (%s, %s, 'linkset', %s, %s, %s, false, now())
                    """)

                    cur.execute(query, (self._job_id, self._id, 'default', None, 'waiting'))

    def cleanup(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(psycopg2_sql.Identifier(self._job.schema_name(self._id))))
