from typing import Any, TypedDict

from psycopg import Cursor
from rdflib.query import Result

from lenticularlens.workers.job import WorkerJob
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.prefix_builder import qname
from lenticularlens.data.sparql.sparql import SPARQL
from lenticularlens.data.sparql.entity_type import EntityType


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
            classes_data = sparql.get_explicit_classes(only_classes=False)
            classes += self.get_classes_data(classes_data)
        except Exception:
            try:
                classes_data = sparql.get_explicit_classes(only_classes=True)
                for class_info in classes_data:
                    class_uri = str(class_info.get('class'))
                    try:
                        classes_data = sparql.get_class_counts(class_uri)
                        classes += self.get_classes_data(classes_data, class_uri)
                    except Exception:
                        classes.append(ClassInfo(class_uri=class_uri, label=None, total=0))
            except Exception:
                pass

        try:
            untyped_resources = sparql.get_untyped_resources()
            classes += self.get_classes_data(untyped_resources)
        except Exception:
            pass

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
    def get_classes_data(classes_data: Result, class_uri: str | None = None) -> list[ClassInfo]:
        classes = []
        for class_data in classes_data:
            class_uri = class_uri or str(class_data.get('class'))
            label = str(class_data.get('label')) if class_data.get('label') else None
            total = int(class_data.get('count'))

            classes.append(ClassInfo(class_uri=class_uri, label=label, total=total))

        return classes
