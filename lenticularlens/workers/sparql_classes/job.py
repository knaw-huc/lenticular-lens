from logging import getLogger
from typing import Any, TypedDict

from SPARQLWrapper.SmartWrapper import Value
from psycopg import Cursor

from lenticularlens.workers.job import WorkerJob
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.prefix_builder import qname
from lenticularlens.data.sparql.sparql import SPARQL
from lenticularlens.data.sparql.entity_type import EntityType

log = getLogger(__name__)


class ClassInfo(TypedDict):
    class_uri: str
    label: str | None
    total: int


class SPARQLClassesJob(WorkerJob):
    def __init__(self, dataset_id, sparql_endpoint):
        self._dataset_id = dataset_id
        self._sparql_endpoint = sparql_endpoint

        super().__init__(self.run_sparql_query)

    def run_sparql_query(self):
        sparql = SPARQL(self._sparql_endpoint)

        classes = []
        try:
            log.info(f'Try to obtain explicit classes from {self._sparql_endpoint}')
            classes_data = sparql.get_explicit_classes(only_classes=False)
            classes += self.get_classes_data(classes_data)
            log.info(f'Obtained explicit classes from {self._sparql_endpoint}!')
        except Exception:
            try:
                log.info(f'Try to obtain explicit classes only, counts later, from {self._sparql_endpoint}')
                classes_data = sparql.get_explicit_classes(only_classes=True)
                log.info(f'Obtained explicit classes only from {self._sparql_endpoint}!')
                for class_info in classes_data:
                    class_uri = str(class_info.get('class').value)
                    try:
                        log.info(f'Try to obtain counts for {class_uri} from {self._sparql_endpoint}')
                        classes_data = sparql.get_class_counts(class_uri)
                        classes += self.get_classes_data(classes_data, class_uri)
                        log.info(f'Obtained counts for {class_uri} from {self._sparql_endpoint}!')
                    except Exception:
                        classes.append(ClassInfo(class_uri=class_uri, label=None, total=0))
            except Exception:
                pass

        try:
            log.info(f'Try to obtain untyped resources from {self._sparql_endpoint}')
            untyped_resources = sparql.get_untyped_resources()
            classes += self.get_classes_data(untyped_resources)
            log.info(f'Obtained untyped resources from {self._sparql_endpoint}!')
        except Exception:
            classes.append(ClassInfo(class_uri='http://www.w3.org/2000/01/rdf-schema#Resource', label=None, total=0))

        with conn_pool.connection() as conn, conn.cursor() as cur:
            if classes:
                for class_info in classes:
                    self.insert_class_data(class_info, cur)

                cur.execute("UPDATE sparql SET status = 'finished' WHERE dataset_id = %s", (self._dataset_id,))
            else:
                cur.execute("UPDATE sparql SET status = 'failed' WHERE dataset_id = %s", (self._dataset_id,))

    def insert_class_data(self, class_info: ClassInfo, cur: Cursor[Any]):
        table_name = EntityType.create_table_name(self._sparql_endpoint, class_info['class_uri'])
        shortened_uri, _prefix, _name = qname(class_info['class_uri'])

        cur.execute('''
            INSERT INTO entity_types (dataset_id, entity_type_id, "table_name", label,
                                      uri, shortened_uri, total, status, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'waiting', now())
        ''', (self._dataset_id, class_info['class_uri'], table_name, class_info['label'],
              class_info['class_uri'], shortened_uri, class_info['total']))

    def on_exception(self):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE sparql SET status = 'failed' WHERE dataset_id = %s", (self._dataset_id,))

    def on_kill(self, reset):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE sparql SET status = 'waiting' WHERE dataset_id = %s", (self._dataset_id,))

    @staticmethod
    def get_classes_data(classes_data: list[dict[str, Value]], class_uri: str | None = None) -> list[ClassInfo]:
        classes = []
        for class_data in classes_data:
            class_uri = class_uri or str(class_data.get('class').value)
            label = str(class_data.get('label').value) if 'label' in class_data and class_data.get('label').value else None
            total = int(class_data.get('count').value)

            classes.append(ClassInfo(class_uri=class_uri, label=label, total=total))

        return classes
