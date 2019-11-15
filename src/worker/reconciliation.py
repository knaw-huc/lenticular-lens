from os.path import join

from common.helpers import hasher
from common.config_db import db_conn
from common.job_alignment import get_job_clustering, update_clustering_job

import common.ll.Clustering.SimpleLinkClustering as Cls

from worker.job import Job

# TODO: Paths
# from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
# from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
CSV_ASSOCIATIONS_DIR = ''
CLUSTER_SERIALISATION_DIR = ''


class ReconciliationJob(Job):
    def __init__(self, job_id, alignment, association_file):
        self.job_id = job_id
        self.alignment = alignment
        self.association_file = association_file

        self.result = None

        super().__init__(self.start_reconciliation)

    def start_reconciliation(self):
        filename = f'Reconciled_{hasher(self.job_id)}_{self.alignment}_{hasher(self.association_file)}'
        serialised = f'Cluster_{hasher(self.job_id)}_{self.alignment}'

        self.result = Cls.extend_cluster(
            serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=serialised,
            csv_association_file=join(CSV_ASSOCIATIONS_DIR, self.association_file), save_in=CLUSTER_SERIALISATION_DIR,
            reconciled_name=filename, condition_30=True, activated=True)

    def watch_process(self):
        pass

    def watch_kill(self):
        clustering_job = get_job_clustering(self.job_id, self.alignment)
        if clustering_job['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        update_clustering_job(self.job_id, self.alignment, job_data)

    def on_exception(self):
        err_message = str(self.exception)
        update_clustering_job(self.job_id, self.alignment, {'status': 'failed', 'status_message': err_message})

    def on_finish(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('''
                UPDATE clusterings
                SET extended_count = %s, cycles_count = %s, status = %s, finished_at = now()
                WHERE job_id = %s AND alignment = %s
            ''', (self.result['extended_clusters_count'], self.result['cycles_count'], 'done',
                  self.job_id, self.alignment))
