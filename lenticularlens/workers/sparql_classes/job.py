from lenticularlens.workers.job import WorkerJob
from lenticularlens.util.config_db import conn_pool
from lenticularlens.data.sparql.sparql import SPARQL
from lenticularlens.data.sparql.entity_type import EntityType


class SPARQLClassesJob(WorkerJob):
    def __init__(self, dataset_id, sparql_endpoint):
        self._dataset_id = dataset_id
        self._sparql_endpoint = sparql_endpoint

        super().__init__(self.run_sparql_query)

    def run_sparql_query(self):
        sparql = SPARQL(self._sparql_endpoint)
        classes_data = sparql.get_classes()

        with conn_pool.connection() as conn, conn.cursor() as cur:
            if classes_data:
                for class_data in classes_data:
                    class_uri = str(class_data.get('class'))
                    table_name = EntityType.create_table_name(self._sparql_endpoint, class_uri)

                    label = str(class_data.get('label')) if class_data.get('label') else None
                    total = int(class_data.get('count'))

                    cur.execute('''
                        INSERT INTO entity_types (dataset_id, entity_type_id, "table_name", label,
                                                  uri, shortened_uri, total, status, create_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'waiting', now())
                    ''', (self._dataset_id, class_uri, table_name, label, class_uri, class_uri, total))

                cur.execute("UPDATE sparql SET status = 'finished' WHERE dataset_id = %s", (self._dataset_id,))
            else:
                cur.execute("UPDATE sparql SET status = 'failed' WHERE dataset_id = %s", (self._dataset_id,))

    def on_exception(self):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE sparql SET status = 'failed' WHERE dataset_id = %s", (self._dataset_id,))

    def on_kill(self, reset):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE sparql SET status = 'waiting' WHERE dataset_id = %s", (self._dataset_id,))
