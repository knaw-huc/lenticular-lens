from lenticularlens.workers.worker import Worker
from lenticularlens.workers.sparql_classes.job import SPARQLClassesJob

class SPARQLClassesWorker(Worker):
    def __init__(self):
        super().__init__('sparql', """
            SELECT *
            FROM sparql
            WHERE status = 'waiting'
            LIMIT 1
        """)

    def _create_job(self):
        self._job = SPARQLClassesJob(dataset_id=self._job_data['dataset_id'],
                                     sparql_endpoint=self._job_data['sparql_endpoint'])

    def _update_status(self, cur):
        cur.execute("UPDATE sparql SET status = 'running' WHERE dataset_id = %s", (self._job_data['dataset_id'],))
