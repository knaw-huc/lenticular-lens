from lenticularlens.workers.worker import Worker
from lenticularlens.workers.reconciliation.job import ReconciliationJob


class ReconciliationWorker(Worker):
    def __init__(self):
        super().__init__(self, 'clusterings', """
            SELECT *
            FROM clusterings cl
            WHERE cl.status = 'waiting' AND cl.association_file IS NOT NULL AND cl.association_file != ''
            ORDER BY cl.requested_at
            LIMIT 1
        """)

    def _create_job(self):
        self._job = ReconciliationJob(job_id=self._job_data['job_id'], id=self._job_data['spec_id'],
                                      type=self._job_data['spec_type'])

    def _update_status(self, cur):
        cur.execute("""
            UPDATE clusterings
            SET status = 'running', processing_at = now()
            WHERE job_id = %s AND spec_id = %s AND spec_type = %s
        """, (self._job_data['job_id'], self._job_data['spec_id'], self._job_data['spec_type']))
