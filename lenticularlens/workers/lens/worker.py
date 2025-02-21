from lenticularlens.workers.worker import Worker
from lenticularlens.workers.lens.job import LensJob


class LensWorker(Worker):
    def __init__(self):
        super().__init__('lenses',  """
            SELECT *
            FROM lenses ls
            WHERE ls.status = 'waiting'
            ORDER BY ls.requested_at
            LIMIT 1
        """)

    def _create_job(self):
        self._job = LensJob(job_id=self._job_data['job_id'], id=self._job_data['spec_id'])

    def _update_status(self, cur):
        cur.execute("""
            UPDATE lenses
            SET status = 'running', processing_at = now()
            WHERE job_id = %s AND spec_id = %s
        """, (self._job_data['job_id'], self._job_data['spec_id']))
