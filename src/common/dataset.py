from common.config_db import db_conn
from psycopg2 import extras as psycopg2_extras
from common.collection import Collection


class Dataset:
    def __init__(self, dataset_id, collections):
        self.dataset_id = dataset_id
        self.__collections = collections

    def collection(self, collection_id):
        return Collection(self.dataset_id, collection_id, self.__collections[collection_id])

    @staticmethod
    def datasets():
        datasets = {}

        with db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM timbuctoo_tables')

                for table in cur:
                    if not table['dataset_id'] in datasets:
                        datasets[table['dataset_id']] = {
                            'collections': {},
                            'title': 'No title - ' + table['dataset_id'].split('__', 1)[1]
                        }

                    columns = {}
                    for key, column_info in table['columns'].items():
                        columns[column_info['name']] = {
                            'isList': column_info['LIST'],
                            'isValueType': column_info['VALUE'],
                            'name': column_info['name'],
                        }

                        if 'REF' in column_info:
                            columns[column_info['name']]['referencedCollections'] = column_info['REF']

                    datasets[table['dataset_id']]['collections'][table['collection_id']] = columns

        return datasets
