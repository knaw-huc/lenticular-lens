from os.path import join

from lenticularlens.job.job import Job as JobLL
from lenticularlens.workers.job import WorkerJob
from lenticularlens.util.hasher import hasher
from lenticularlens.util.config_db import conn_pool

import lenticularlens.org.Clustering.SimpleLinkClustering as Cls

# TODO: Paths
# from ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
# from ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
CSV_ASSOCIATIONS_DIR = ''
CLUSTER_SERIALISATION_DIR = ''


class ReconciliationJob(WorkerJob):
    def __init__(self, job_id, id, type, association_file=None):
        self._job_id = job_id
        self._id = id
        self._type = type
        self._association_file = association_file

        self._job = JobLL(job_id)
        self._result = None

        super().__init__(self.start_reconciliation)

    def start_reconciliation(self):
        filename = f'Reconciled_{hasher(self._job_id)}_{self._id}_{hasher(self._association_file)}'
        serialised = f'Cluster_{hasher(self._job_id)}_{self._id}'

        self._result = Cls.extend_cluster(
            serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=serialised,
            csv_association_file=join(CSV_ASSOCIATIONS_DIR, self._association_file), save_in=CLUSTER_SERIALISATION_DIR,
            reconciled_name=filename, condition_30=True, activated=True)

    def watch_process(self):
        pass

    def watch_kill(self):
        clustering_job = self._job.clustering(self._id, self._type)
        if clustering_job['kill']:
            self.kill(reset=False)

    def on_kill(self, reset):
        job_data = {'status': 'waiting'} if reset else {'status': 'failed', 'status_message': 'Killed manually'}
        self._job.update_clustering(self._id, self._type, job_data)

    def on_exception(self):
        err_message = str(self._exception)
        self._job.update_clustering(self._id, self._type, {'status': 'failed', 'status_message': err_message})

    def on_finish(self):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute('''
                UPDATE clusterings
                SET extended_count = %s, cycles_count = %s, status = %s, finished_at = now()
                WHERE job_id = %s AND spec_id = %s AND spec_type = %s
            ''', (self._result['extended_clusters_count'], self._result['cycles_count'], 'done',
                  self._job_id, self._id, self._type))
