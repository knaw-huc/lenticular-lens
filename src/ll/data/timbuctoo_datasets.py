from ll.util.config_db import db_conn
from ll.data.timbuctoo import Timbuctoo
from ll.data.collection import Collection
from psycopg2 import extras as psycopg2_extras


class TimbuctooDatasets:
    def __init__(self, graphql_uri, hsid):
        self._graphql_uri = graphql_uri
        self._hsid = hsid
        self._datasets = None

    @property
    def datasets(self):
        if not self._datasets:
            timbuctoo_data = Timbuctoo(self._graphql_uri, self._hsid).datasets
            database_data = self._datasets_from_database()
            self._datasets = self._combine(timbuctoo_data, database_data)

        return self._datasets

    def update(self):
        timbuctoo_data = Timbuctoo(self._graphql_uri, self._hsid).datasets
        database_data = self._datasets_from_database()

        for dataset_id, dataset_data in database_data.items():
            for collection_id, collection_data in dataset_data['collections'].items():
                if dataset_id in timbuctoo_data and collection_id in timbuctoo_data[dataset_id]['collections']:
                    collection = Collection(self._graphql_uri, self._hsid, dataset_id, collection_id, timbuctoo_data)
                    collection.update()

    def _datasets_from_database(self):
        with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM timbuctoo_tables WHERE graphql_endpoint = %s', (self._graphql_uri,))

            datasets = {}
            for table in cur:
                if not table['dataset_id'] in datasets:
                    datasets[table['dataset_id']] = {
                        'uri': table['dataset_uri'],
                        'name': table['dataset_name'],
                        'title': table['title'],
                        'description': table['description'],
                        'published': table['hsid'] is None,
                        'collections': {},
                    }

                datasets[table['dataset_id']]['collections'][table['collection_id']] = {
                    'uri': table['collection_uri'],
                    'title': table['collection_title'],
                    'shortenedUri': table['collection_shortened_uri'],
                    'total': table['total'],
                    'properties': {
                        column_info['name']: {
                            'uri': column_info.get('uri', None),
                            'shortenedUri': column_info.get('shortenedUri', None),
                            'isInverse': column_info.get('isInverse', False),
                            'isList': column_info.get('isList', False),
                            'isValueType': column_info.get('isValueType', True),
                            'isLink': column_info.get('isLink', False),
                            'density': column_info.get('density', 100),
                            'referencedCollections': column_info.get('referencedCollections', [])
                        } for column_info in table['columns'].values()
                    },
                }

            return datasets

    @staticmethod
    def _combine(timbuctoo_data, database_data):
        combined = timbuctoo_data.copy()
        for dataset, dataset_data in database_data.items():
            if dataset not in combined:
                combined[dataset] = dataset_data.copy()
            else:
                for collection, collection_data in dataset_data['collections'].items():
                    if collection not in combined[dataset]['collections']:
                        combined[dataset]['collections'][collection] = database_data.copy()

        return combined
