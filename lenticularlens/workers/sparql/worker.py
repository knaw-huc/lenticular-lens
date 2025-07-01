from lenticularlens.workers.worker import Worker
from lenticularlens.workers.sparql.job import SPARQLJob


class SPARQLWorker(Worker):
    def __init__(self):
        super().__init__('entity_types', """
            SELECT *
            FROM entity_types
            INNER JOIN sparql 
            ON entity_types.dataset_id = sparql.dataset_id
            WHERE entity_types.status = 'downloadable'
            AND (
                update_start_time IS NULL
                OR (
                    (update_finish_time IS NULL OR update_finish_time < update_start_time)
                    AND update_start_time < now() - interval '2 minutes'
                    AND (last_push_time IS NULL OR last_push_time < now() - interval '2 minutes')
                )
            )
            ORDER BY create_time
            LIMIT 1
        """)

    def _create_job(self):
        self._job = SPARQLJob(table_name=self._job_data['table_name'],
                              sparql_endpoint=self._job_data['sparql_endpoint'],
                              entity_type_id=self._job_data['entity_type_id'],
                              cursor=self._job_data['cursor'],
                              rows_count=self._job_data['rows_count'],
                              rows_per_page=1000)

    def _update_status(self, cur):
        cur.execute("""
            UPDATE entity_types
            SET update_start_time = now() 
            WHERE "table_name" = %s
        """, (self._job_data['table_name'],))
