from ll.util.config_db import db_conn
from ll.data.timbuctoo import Timbuctoo
from psycopg2 import extras as psycopg2_extras


class TimbuctooDatasets:
    def __init__(self, graphql_uri, hsid):
        self.graphql_uri = graphql_uri
        self.hsid = hsid
        self.__datasets = None

    @property
    def datasets(self):
        if not self.__datasets:
            timbuctoo_data = Timbuctoo(self.graphql_uri, self.hsid).datasets
            database_data = self.datasets_from_database()
            self.__datasets = self.combine(timbuctoo_data, database_data)

        return self.__datasets

    def datasets_from_database(self):
        with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM timbuctoo_tables WHERE graphql_endpoint = %s', (self.graphql_uri,))

            datasets = {}
            for table in cur:
                if not table['dataset_id'] in datasets:
                    datasets[table['dataset_id']] = {
                        'name': table['dataset_name'],
                        'title': table['title'],
                        'description': table['description'],
                        'collections': {},
                    }

                datasets[table['dataset_id']]['collections'][table['collection_id']] = {
                    'title': table['collection_title'],
                    'total': table['total'],
                    'properties': {
                        column_info['name']: {
                            'shortenedUri': column_info['shortenedUri'],
                            'isInverse': column_info['isInverse'],
                            'isList': column_info['isList'],
                            'isValueType': column_info['isValueType'],
                            'isLink': column_info['isLink'],
                            'density': column_info['density'],
                            'referencedCollections': column_info['referencedCollections']
                        } for column_info in table['columns'].values()
                    },
                }

            return datasets

    @staticmethod
    def combine(timbuctoo_data, database_data):
        combined = timbuctoo_data.copy()
        for dataset, dataset_data in database_data.items():
            if dataset not in combined:
                combined[dataset] = dataset_data.copy()
            else:
                for collection, collection_data in dataset_data['collections'].items():
                    if collection not in combined[dataset]['collections']:
                        combined[dataset]['collections'][collection] = database_data.copy()

        return combined
