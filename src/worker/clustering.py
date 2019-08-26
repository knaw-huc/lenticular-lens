import time
import threading

from os.path import join

from common.config_db import db_conn
from common.helpers import hasher, update_clustering_job

import common.ll.Clustering.SimpleLinkClustering as Cls
from common.ll.Clustering.SimpleLinkClustering import simple_csv_link_clustering

from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from common.ll.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR


class ClusteringJob:
    def __init__(self, job_id, alignment, association_file, clustering_id, status):
        self.job_id = job_id
        self.alignment = alignment
        self.association_file = association_file
        self.clustering_id = clustering_id
        self.status = status

    def run(self):
        thread = threading.Thread(target=self.start_clustering)
        thread.start()

        while thread.is_alive():
            time.sleep(1)

    def kill(self):
        update_clustering_job(self.job_id, self.alignment, {'status': self.status})

    def start_clustering(self):
        if self.clustering_id and self.association_file:
            reconciliation_result = self.cluster_reconciliation_csv()

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                UPDATE clusterings
                SET extended_count = %s, cycles_count = %s, status = %s, finished_at = now()
                WHERE job_id = %s AND alignment = %s
                ''', (reconciliation_result['extended_clusters_count'], reconciliation_result['cycles_count'],
                      'Finished', self.job_id, self.alignment))
        elif not self.clustering_id and self.association_file:
            clustering_result = self.cluster_csv()
            reconciliation_result = self.cluster_reconciliation_csv()

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                UPDATE clusterings
                SET clustering_id = %s, clusters_count = %s, 
                    extended_count = %s, cycles_count = %s, status = %s, finished_at = now()
                WHERE job_id = %s AND alignment = %s
                ''', (clustering_result['file_name'], clustering_result['clusters_count'],
                      reconciliation_result['extended_clusters_count'], reconciliation_result['cycles_count'],
                      'Finished', self.job_id, self.alignment))
        else:
            clustering_result = self.cluster_csv()

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                UPDATE clusterings
                SET clustering_id = %s, clusters_count = %s, status = %s, finished_at = now()
                WHERE job_id = %s AND alignment = %s
                ''', (clustering_result['file_name'], clustering_result['clusters_count'],
                      'Finished', self.job_id, self.alignment))

    def cluster_csv(self):
        csv_filepath = join(CSV_ALIGNMENTS_DIR, f'alignment_{hasher(self.job_id)}_alignment_{self.alignment}.csv.gz')
        filename = f'Cluster_{hasher(self.job_id)}_{self.alignment}'

        return simple_csv_link_clustering(csv_filepath, CLUSTER_SERIALISATION_DIR, file_name=filename, activated=True)

    def cluster_reconciliation_csv(self):
        filename = f'Reconciled_{hasher(self.job_id)}_{self.alignment}_{hasher(self.association_file)}'
        serialised = f'Cluster_{hasher(self.job_id)}_{self.alignment}'

        return Cls.extend_cluster(
            serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=serialised,
            csv_association_file=join(CSV_ASSOCIATIONS_DIR, self.association_file), save_in=CLUSTER_SERIALISATION_DIR,
            reconciled_name=filename, condition_30=True, activated=True)
