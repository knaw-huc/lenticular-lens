from io import StringIO
from psycopg import sql, rows

from ll.worker.job import WorkerJob
from ll.util.config_db import conn_pool

from ll.job.job import Job as JobLL
from ll.job.simple_link_clustering import SimpleLinkClustering


class ClusteringJob(WorkerJob):
    def __init__(self, job_id, id, type):
        self._job_id = job_id
        self._id = id
        self._type = type

        self._job = JobLL(job_id)
        self._worker = None

        super().__init__(self.start_clustering)

    def start_clustering(self):
        links = self._job.get_links(self._id, self._type)
        self._worker = SimpleLinkClustering(links)

        data = StringIO()
        for cluster in self._worker.get_clusters():
            for node in cluster['nodes']:
                data.write(f"{cluster['id']}\t{node}\n")
        data.seek(0)

        if not self._killed:
            schema = 'linksets' if self._type == 'linkset' else 'lenses'
            linkset_table_name = self._job.table_name(self._id)
            clusters_table_name = linkset_table_name + '_clusters'
            cluster_hashes_table_name = linkset_table_name + '_cluster_hashes'
            linkset_index_name = linkset_table_name + '_cluster_id_idx'

            with self._db_conn.cursor() as cur:
                cur.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
                cur.execute(sql.SQL('DROP INDEX IF EXISTS {}').format(sql.Identifier(linkset_index_name)))

                cur.execute(sql.SQL('''
                    CREATE TEMPORARY TABLE IF NOT EXISTS {} (
                        id integer NOT NULL, node text NOT NULL
                    ) ON COMMIT DROP
                ''').format(sql.Identifier(clusters_table_name)))

                cur.copy_from(data, clusters_table_name)

                cur.execute(sql.SQL('''
                    CREATE TEMPORARY TABLE IF NOT EXISTS {} ON COMMIT DROP AS
                    SELECT id, substring(md5(array_to_string(ARRAY(
                                   SELECT DISTINCT unnest(array_agg(node)) AS x ORDER BY x
                               ), '')) FOR 15) AS hash_id
                    FROM {}
                    GROUP BY id 
                ''').format(sql.Identifier(cluster_hashes_table_name), sql.Identifier(clusters_table_name)))

                cur.execute(sql.SQL('''
                    UPDATE {} AS linkset
                    SET cluster_id = clusters.id
                    FROM {} AS clusters
                    WHERE linkset.source_uri = clusters.node
                ''').format(sql.Identifier(linkset_table_name), sql.Identifier(clusters_table_name)))

                cur.execute(sql.SQL('''
                    UPDATE {} AS linkset
                    SET cluster_hash_id = cluster_hashes.hash_id
                    FROM {} AS cluster_hashes
                    WHERE linkset.cluster_id = cluster_hashes.id
                ''').format(sql.Identifier(linkset_table_name), sql.Identifier(cluster_hashes_table_name)))

                cur.execute(sql.SQL('CREATE INDEX ON {} USING btree (cluster_id); ANALYZE {};')
                            .format(sql.Identifier(linkset_table_name), sql.Identifier(linkset_table_name)))

    def watch_process(self):
        if not self._worker:
            return

        self._job.update_clustering(self._id, self._type, {
            'status_message': 'Processing found clusters' if self._worker.links_processed else 'Processing links',
            'links_count': self._worker.links_processed,
            'clusters_count': len(self._worker.clusters)
        })

    def watch_kill(self):
        clustering_job = self._job.clustering(self._id, self._type)
        if clustering_job['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        if self._worker:
            self._worker.stop_clustering()

        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        self._job.update_clustering(self._id, self._type, job_data)

    def on_exception(self):
        err_message = str(self._exception)
        self._job.update_clustering(self._id, self._type, {'status': 'failed', 'status_message': err_message})

    def on_finish(self):
        if len(self._worker.clusters) == 0:
            return

        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute(sql.SQL('''
                SELECT (SELECT count(DISTINCT uri) AS size
                        FROM {schema}.{table_name}, 
                        LATERAL (VALUES (source_uri), (target_uri)) AS nodes(uri)) AS resources_size,
                       (SELECT size FROM (
                          SELECT count(DISTINCT uri) AS size
                          FROM {schema}.{table_name}, LATERAL (VALUES (source_uri), (target_uri)) AS nodes(uri)
                          GROUP BY cluster_id
                       ) AS x ORDER BY size ASC LIMIT 1) AS smallest_size,
                       (SELECT size FROM (
                          SELECT count(DISTINCT uri) AS size
                          FROM {schema}.{table_name}, LATERAL (VALUES (source_uri), (target_uri)) AS nodes(uri)
                          GROUP BY cluster_id
                       ) AS x ORDER BY size DESC LIMIT 1) AS largest_size,
                       (SELECT count FROM (
                          SELECT count(cluster_id) AS count
                          FROM {schema}.{table_name}
                          GROUP BY cluster_id
                       ) AS x ORDER BY count ASC LIMIT 1) AS smallest_count,
                       (SELECT count FROM (
                          SELECT count(cluster_id) AS count
                          FROM {schema}.{table_name}
                          GROUP BY cluster_id
                       ) AS x ORDER BY count DESC LIMIT 1) AS largest_count
            ''').format(
                schema=sql.Identifier('linksets' if self._type == 'linkset' else 'lenses'),
                table_name=sql.Identifier(self._job.table_name(self._id)),
            ))

            result = cur.fetchone()
            cur.execute('''
                UPDATE clusterings
                SET links_count = %s, clusters_count = %s, resources_size = %s, smallest_size = %s, largest_size = %s,
                    smallest_count = %s, largest_count = %s, status = %s, status_message = NULL, finished_at = now()
                WHERE job_id = %s AND spec_id = %s AND spec_type = %s
            ''', (self._worker.links_processed, len(self._worker.clusters), result['resources_size'],
                  result['smallest_size'], result['largest_size'], result['smallest_count'], result['largest_count'],
                  'done', self._job_id, self._id, self._type))
