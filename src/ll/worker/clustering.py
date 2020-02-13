from psycopg2 import sql as psycopg2_sql

from ll.worker.job import Job
from ll.util.config_db import db_conn

from ll.job.data import Job as JobLL
from ll.job.simple_link_clustering import SimpleLinkClustering


class ClusteringJob(Job):
    def __init__(self, job_id, alignment):
        self.job_id = job_id
        self.alignment = alignment

        self.job = JobLL(job_id)
        self.worker = None

        super().__init__(self.start_clustering)

    def start_clustering(self):
        linkset_table_name = self.job.get_linkset_table(self.alignment)
        links = self.job.get_links(self.alignment)

        with self.db_conn.cursor() as cur:
            self.worker = SimpleLinkClustering(links)

            for cluster in self.worker.get_clusters():
                for i in range(0, len(cluster['links']), 1000):
                    link_sqls = [psycopg2_sql.SQL('(source_uri = {source} AND target_uri = {target})').format(
                        source=psycopg2_sql.Literal(link[0]), target=psycopg2_sql.Literal(link[1])
                    ) for link in cluster['links'][i:i + 1000]]

                    cur.execute(psycopg2_sql.SQL('UPDATE {linkset} SET cluster_id = {cluster_id} WHERE {links}').format(
                        linkset=psycopg2_sql.Identifier(linkset_table_name),
                        cluster_id=psycopg2_sql.Literal(cluster['id']),
                        links=psycopg2_sql.SQL(' OR ').join(link_sqls)
                    ))

    def watch_process(self):
        if not self.worker:
            return

        self.job.update_clustering(self.alignment, {
            'status_message': 'Processing found clusters' if self.worker.links_processed else 'Processing links',
            'links_count': self.worker.links_processed,
            'clusters_count': len(self.worker.clusters)
        })

    def watch_kill(self):
        clustering_job = self.job.clustering(self.alignment)
        if clustering_job['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        if self.worker:
            self.worker.stop_clustering()

        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        self.job.update_clustering(self.alignment, job_data)

    def on_exception(self):
        err_message = str(self.exception)
        self.job.update_clustering(self.alignment, {'status': 'failed', 'status_message': err_message})

    def on_finish(self):
        if len(self.worker.clusters) > 0:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                    UPDATE clusterings
                    SET links_count = %s, clusters_count = %s, status = %s, finished_at = now()
                    WHERE job_id = %s AND alignment = %s
                ''', (self.worker.links_processed, len(self.worker.clusters), 'done', self.job_id, self.alignment))
