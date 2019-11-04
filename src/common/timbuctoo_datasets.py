from common.config_db import db_conn
from common.timbuctoo import Timbuctoo
from common.dataset import Dataset

import psycopg2

from psycopg2 import extras as psycopg2_extras


class TimbuctooDatasets:
    def __init__(self, graphql_uri, hsid):
        self.graphql_uri = graphql_uri
        self.hsid = hsid

        try:
            timbuctoo_data = Timbuctoo(graphql_uri, hsid).datasets
            database_data = self.datasets_from_database()

            combined = timbuctoo_data.copy()
            for dataset, dataset_data in database_data.items():
                if dataset not in combined:
                    combined[dataset] = dataset_data.copy()
                else:
                    for collection, collection_data in dataset_data['collections'].items():
                        if collection not in combined[dataset]['collections']:
                            combined[dataset]['collections'][collection] = database_data.copy()
                        else:
                            combined[dataset]['collections'][collection]['downloaded'] = True

            self.__datasets = combined
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            print('Database error')

    @property
    def datasets(self):
        return self.__datasets

    def dataset(self, dataset_id):
        dataset_info = self.__datasets[dataset_id]
        return Dataset(self.graphql_uri, self.hsid, dataset_id, dataset_info['name'], dataset_info['title'],
                       dataset_info['description'], dataset_info['collections'])

    def collection(self, dataset_id, collection_id):
        dataset = self.dataset(dataset_id)
        return dataset.collection(collection_id)

    def datasets_from_database(self):
        datasets = {}

        with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM timbuctoo_tables WHERE graphql_endpoint = %s', (self.graphql_uri,))

            for table in cur:
                if not table['dataset_id'] in datasets:
                    datasets[table['dataset_id']] = {
                        'name': table['dataset_name'],
                        'title': table['title'],
                        'description': table['description'],
                        'collections': {},
                    }

                datasets[table['dataset_id']]['collections'][table['collection_id']] = {
                    'total': table['total'],
                    'downloaded': True,
                    'properties': {
                        column_info['name']: {
                            'isList': column_info['isList'],
                            'isValueType': column_info['isValueType'],
                            'isLink': column_info['isLink'],
                            'density': column_info['density'],
                            'referencedCollections': column_info['referencedCollections']
                        } for column_info in table['columns'].values()
                    },
                }

        return datasets
