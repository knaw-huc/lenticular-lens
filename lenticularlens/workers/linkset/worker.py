from lenticularlens.workers.worker import Worker
from lenticularlens.workers.linkset.job import LinksetJob


class LinksetWorker(Worker):
    def __init__(self):
        super().__init__('linksets', """
            SELECT *
            FROM linksets ls
            WHERE ls.status = 'waiting'
            ORDER BY ls.requested_at
            LIMIT 1
        """)

    def _create_job(self):
        self._job = LinksetJob(job_id=self._job_data['job_id'], id=self._job_data['spec_id'])

    def _update_status(self, cur):
        cur.execute("""
            UPDATE linksets
            SET status = 'running', processing_at = now()
            WHERE job_id = %s AND spec_id = %s
        """, (self._job_data['job_id'], self._job_data['spec_id']))
