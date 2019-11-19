from psycopg2 import sql as psycopg2_sql

from ll.worker.job import Job
from ll.util.config_db import db_conn

from ll.job.simple_link_clustering import SimpleLinkClustering
from ll.job.job_alignment import get_job_clustering, update_clustering_job, get_links


class ClusteringJob(Job):
    def __init__(self, job_id, alignment):
        self.job_id = job_id
        self.alignment = alignment

        self.worker = None

        super().__init__(self.start_clustering)

    def start_clustering(self):
        linkset_table_name = 'linkset_' + self.job_id + '_' + str(self.alignment)
        cluster_table_name = 'clusters_' + self.job_id + '_' + str(self.alignment)

        links = get_links(self.job_id, self.alignment)

        with self.db_conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('DROP TABLE IF EXISTS {} CASCADE')
                        .format(psycopg2_sql.Identifier(cluster_table_name)))

            cur.execute(psycopg2_sql.SQL("""
                CREATE TABLE {} (
                    id text primary key,
                    size integer not null,
                    links integer not null
                )
            """).format(psycopg2_sql.Identifier(cluster_table_name)))

            self.worker = SimpleLinkClustering(links)
            for cluster in self.worker.get_clusters():
                cur.execute(
                    psycopg2_sql.SQL('INSERT INTO {} (id, size, links) VALUES (%s, %s, %s)')
                        .format(psycopg2_sql.Identifier(cluster_table_name)),
                    (cluster['id'], len(cluster['nodes']), len(cluster['links']))
                )

                link_sqls = []
                for link in cluster['links']:
                    link_sqls.append(psycopg2_sql.SQL('(source_uri = {source} AND target_uri = {target})').format(
                        source=psycopg2_sql.Literal(link[0]), target=psycopg2_sql.Literal(link[1])
                    ))

                    link_sqls.append(psycopg2_sql.SQL('(source_uri = {target} AND target_uri = {source})').format(
                        source=psycopg2_sql.Literal(link[0]), target=psycopg2_sql.Literal(link[1])
                    ))

                cur.execute(psycopg2_sql.SQL('UPDATE {linkset} SET cluster_id = {cluster_id} WHERE {links}').format(
                    linkset=psycopg2_sql.Identifier(linkset_table_name),
                    cluster_id=psycopg2_sql.Literal(cluster['id']),
                    links=psycopg2_sql.SQL(' OR ').join(link_sqls)
                ))

            self.db_conn.commit()

    def watch_process(self):
        if not self.worker:
            return

        update_clustering_job(self.job_id, self.alignment, {
            'status_message': 'Processing found clusters' if self.worker.links_processed else 'Processing links',
            'links_count': self.worker.links_processed,
            'clusters_count': len(self.worker.clusters)
        })

    def watch_kill(self):
        clustering_job = get_job_clustering(self.job_id, self.alignment)
        if clustering_job['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        if self.worker:
            self.worker.stop_clustering()

        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        update_clustering_job(self.job_id, self.alignment, job_data)

    def on_exception(self):
        err_message = str(self.exception)
        update_clustering_job(self.job_id, self.alignment, {'status': 'failed', 'status_message': err_message})

    def on_finish(self):
        cluster_table_name = 'clusters_' + self.job_id + '_' + str(self.alignment)

        with db_conn() as conn, conn.cursor() as cur:
            if len(self.worker.clusters) == 0:
                cur.execute(psycopg2_sql.SQL('DROP TABLE IF EXISTS {} CASCADE')
                            .format(psycopg2_sql.Identifier(cluster_table_name)))
            else:
                cur.execute('''
                    UPDATE clusterings
                    SET links_count = %s, clusters_count = %s, status = %s, finished_at = now()
                    WHERE job_id = %s AND alignment = %s
                ''', (self.worker.links_processed, len(self.worker.clusters), 'done', self.job_id, self.alignment))
