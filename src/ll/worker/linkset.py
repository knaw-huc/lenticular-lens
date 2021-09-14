import time

from psycopg2 import sql, extras, ProgrammingError

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
        self._last_status = None
        self._is_downloading = False
        self._counts = {}

        self.reset()
        super().__init__(self.run_matching)

    def reset(self):
        self._job = Job(self._job_id)
        self._matching_sql = MatchingSql(self._job, self._id)

    def run_matching(self):
        while self._job.linkset_has_queued_table_data(self._id) and not self._killed:
            self._is_downloading = True
            self._status = 'Downloading required data'

            time.sleep(1)
            self.reset()

        self._is_downloading = False
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
        cur_status = self._status
        data = {
            'status': 'downloading' if self._is_downloading else 'running',
            'status_message': cur_status
        } if cur_status and self._last_status != cur_status else {}

        if cur_status and not self._is_downloading:
            with db_conn() as conn, conn.cursor() as cur:
                self.get_sequence_count(conn, cur, 'linkset_count', data, 'links_progress')
                self.get_count(conn, cur, 'source', data, 'sources_count')
                self.get_count(conn, cur, 'target', data, 'targets_count')

        if data:
            self._job.update_linkset(self._id, data)

        self._last_status = cur_status

    def get_sequence_count(self, conn, cur, sequence, data, key):
        try:
            cur.execute(sql.SQL('SELECT is_called, last_value FROM {linkset_schema}.{sequence}').format(
                linkset_schema=sql.Identifier(self._job.schema_name(self._id)),
                sequence=sql.Identifier(sequence)
            ))

            seq = cur.fetchone()
            if seq[0]:
                data[key] = seq[1]
        except ProgrammingError:
            pass
        finally:
            conn.commit()

    def get_count(self, conn, cur, table, data, key):
        try:
            if table not in self._counts:
                cur.execute(sql.SQL('SELECT count(DISTINCT uri) FROM {linkset_schema}.{table_name}').format(
                    linkset_schema=sql.Identifier(self._job.schema_name(self._id)),
                    table_name=sql.Identifier(table)
                ))
                self._counts[table] = cur.fetchone()[0]
                data[key] = self._counts[table]
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

        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql.SQL('''
                SELECT  (SELECT count(*) FROM linksets.{linkset_table}) AS links,
                        (SELECT count(DISTINCT uri) FROM {linkset_schema}.source) AS sources,
                        (SELECT count(DISTINCT uri) FROM {linkset_schema}.target) AS targets,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT uri FROM {linkset_schema}.source
                            UNION ALL
                            SELECT uri FROM {linkset_schema}.target
                         ) AS uris) AS entities,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT source_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT target_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS linkset_sources,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT target_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'source_target' OR link_order = 'both'
                            UNION ALL
                            SELECT source_uri AS uri FROM linksets.{linkset_table} 
                            WHERE link_order = 'target_source' OR link_order = 'both'
                        ) AS uris) AS linkset_targets,
                        (SELECT count(DISTINCT uris.uri) FROM (
                            SELECT source_uri AS uri FROM linksets.{linkset_table} 
                            UNION ALL
                            SELECT target_uri AS uri FROM linksets.{linkset_table}
                        ) AS uris) AS linkset_entities
            ''').format(
                linkset_table=sql.Identifier(self._job.table_name(self._id)),
                linkset_schema=sql.Identifier(self._job.schema_name(self._id)),
            ))

            result = cur.fetchone()
            cur.execute(sql.SQL('DROP SCHEMA {} CASCADE')
                        .format(sql.Identifier(self._job.schema_name(self._id))))

            cur.execute("UPDATE linksets "
                        "SET status = %s, status_message = null, links_count = %s, "
                        "sources_count = %s, targets_count = %s, entities_count = %s, "
                        "linkset_sources_count = %s, linkset_targets_count = %s, linkset_entities_count = %s, "
                        "finished_at = now() "
                        "WHERE job_id = %s AND spec_id = %s",
                        ('done', result['links'], result['sources'], result['targets'], result['entities'],
                         result['linkset_sources'], result['linkset_targets'], result['linkset_entities'],
                         self._job_id, self._id))

            if result['links'] == 0:
                cur.execute(sql.SQL('DROP TABLE linksets.{} CASCADE')
                            .format(sql.Identifier(self._job.table_name(self._id))))
            else:
                cur.execute("SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'",
                            (self._job_id, self._id))
                clustering = cur.fetchone()

                query = """
                    UPDATE clusterings 
                    SET status = 'waiting', kill = false, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'
                """ if clustering else """
                    INSERT INTO clusterings 
                    (job_id, spec_id, spec_type, clustering_type, status, kill, requested_at) 
                    VALUES (%s, %s, 'linkset', 'default', 'waiting', false, now())
                """

                cur.execute(query, (self._job_id, self._id))

    def cleanup(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE')
                        .format(sql.Identifier(self._job.schema_name(self._id))))
