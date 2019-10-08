import time
import threading

from os.path import join

from common.helpers import hasher
from common.config_db import db_conn
from common.job_alignment import update_clustering_job, get_links

import common.ll.Clustering.SimpleLinkClustering as Cls
from common.ll.Clustering.SimpleLinkClustering import simple_csv_link_clustering

from psycopg2 import sql as psycopg2_sql

from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR


class ClusteringJob:
    def __init__(self, job_id, alignment, association_file):
        self.job_id = job_id
        self.alignment = alignment
        self.association_file = association_file

    def run(self):
        thread = threading.Thread(target=self.start_clustering)
        thread.start()

        while thread.is_alive():
            time.sleep(1)

    def kill(self):
        update_clustering_job(self.job_id, self.alignment, {'status': 'waiting'})

    def start_clustering(self):
        if self.association_file:
            reconciliation_result = self.cluster_reconciliation_csv()

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                UPDATE clusterings
                SET extended_count = %s, cycles_count = %s, status = %s, finished_at = now()
                WHERE job_id = %s AND alignment = %s
                ''', (reconciliation_result['extended_clusters_count'], reconciliation_result['cycles_count'],
                      'done', self.job_id, self.alignment))
        else:
            clusters = self.cluster_csv()

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                    UPDATE clusterings
                    SET clusters_count = %s, status = %s, finished_at = now()
                    WHERE job_id = %s AND alignment = %s
                ''', (len(clusters), 'done', self.job_id, self.alignment))

    def cluster_csv(self):
        links = get_links(self.job_id, self.alignment)
        clusters = simple_csv_link_clustering(links, activated=True)

        linkset_table_name = 'linkset_' + self.job_id + '_' + str(self.alignment)
        cluster_table_name = 'clusters_' + self.job_id + '_' + str(self.alignment)

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('DROP TABLE IF EXISTS {} CASCADE')
                        .format(psycopg2_sql.Identifier(cluster_table_name)))

            cur.execute(psycopg2_sql.SQL("""
                CREATE TABLE {} (
                    id text primary key,
                    size integer not null,
                    links integer not null,
                    nodes text[] not null
                )
            """).format(psycopg2_sql.Identifier(cluster_table_name)))

            for cluster in clusters:
                cluster_info = clusters[cluster]

                cur.execute(
                    psycopg2_sql.SQL('INSERT INTO {} (id, size, links, nodes) VALUES (%s, %s, %s, %s)')
                        .format(psycopg2_sql.Identifier(cluster_table_name)),
                    (cluster, len(cluster_info['nodes']), len(cluster_info['links']), cluster_info['nodes'])
                )

                link_sqls = []
                for link in cluster_info['links']:
                    link_sqls.append(psycopg2_sql.SQL('(source_uri = {source} AND target_uri = {target})').format(
                        source=psycopg2_sql.Literal(link[0].replace('<', '').replace('>', '')),
                        target=psycopg2_sql.Literal(link[1].replace('<', '').replace('>', ''))
                    ))

                    link_sqls.append(psycopg2_sql.SQL('(source_uri = {target} AND target_uri = {source})').format(
                        source=psycopg2_sql.Literal(link[0].replace('<', '').replace('>', '')),
                        target=psycopg2_sql.Literal(link[1].replace('<', '').replace('>', ''))
                    ))

                cur.execute(psycopg2_sql.SQL('UPDATE {linkset} SET cluster_id = {cluster_id} WHERE {links}').format(
                    linkset=psycopg2_sql.Identifier(linkset_table_name),
                    cluster_id=psycopg2_sql.Literal(cluster),
                    links=psycopg2_sql.SQL(' OR ').join(link_sqls)
                ))

            conn.commit()

        return clusters

    def cluster_reconciliation_csv(self):
        filename = f'Reconciled_{hasher(self.job_id)}_{self.alignment}_{hasher(self.association_file)}'
        serialised = f'Cluster_{hasher(self.job_id)}_{self.alignment}'

        return Cls.extend_cluster(
            serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=serialised,
            csv_association_file=join(CSV_ASSOCIATIONS_DIR, self.association_file), save_in=CLUSTER_SERIALISATION_DIR,
            reconciled_name=filename, condition_30=True, activated=True)
