from lenticularlens.workers.worker import Worker
from lenticularlens.workers.sparql_properties.job import SPARQLPropertiesJob

class SPARQLPropertiesWorker(Worker):
    def __init__(self):
        super().__init__('entity_types', """
            SELECT *
            FROM entity_types
            INNER JOIN sparql
            ON entity_types.dataset_id = sparql.dataset_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM entity_type_properties
                WHERE entity_type_properties.dataset_id = entity_types.dataset_id
                  AND entity_type_properties.entity_type_id = entity_types.entity_type_id
            )
            AND entity_types.status = 'waiting'
            ORDER BY create_time
            LIMIT 1
        """)

    def _create_job(self):
        self._job = SPARQLPropertiesJob(dataset_id=self._job_data['dataset_id'],
                                        entity_type_id=self._job_data['entity_type_id'],
                                        sparql_endpoint=self._job_data['sparql_endpoint'])

    def _update_status(self, cur):
        cur.execute("UPDATE entity_types SET status = 'running' "
                    "WHERE dataset_id = %s AND entity_type_id = %s",
                    (self._job_data['dataset_id'], self._job_data['entity_type_id']))
