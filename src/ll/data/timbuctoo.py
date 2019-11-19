import sys
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Timbuctoo:
    def __init__(self, graphql_uri, hsid):
        self.graphql_uri = graphql_uri
        self.hsid = hsid

    def fetch_graph_ql(self, query, variables=None):
        try:
            response = requests.post(self.graphql_uri, json={
                'query': query,
                'variables': variables
            }, headers={'Authorization': self.hsid} if self.hsid else {}, timeout=60, verify=False)
            response.raise_for_status()

            result = response.json()
            if 'errors' in result and len(result['errors']) > 0:
                raise RuntimeError('Graphql query returned an error: ', result['errors'])

            return result["data"]
        except requests.exceptions.ConnectionError as e:
            print(e, file=sys.stderr)

    @property
    def datasets(self):
        datasets_data = self.fetch_graph_ql("""
            {
                dataSetMetadataList(promotedOnly: false, publishedOnly: false) {
                    dataSetId
                    dataSetName
                    published
                    title { value }
                    description { value }
                    collectionList {
                        items {
                            collectionId
                            total
                            properties {
                                items {
                                    name
                                    isList
                                    isValueType
                                    density
                                    referencedCollections {
                                        items
                                    }
                                }
                            }
                        }
                    }
                }
            }""")

        datasets = {}
        for dataset in datasets_data['dataSetMetadataList']:
            dataset_id = dataset['dataSetId']
            dataset_name = dataset['dataSetName']

            dataset_title = dataset['title']['value'] \
                if dataset['title'] and dataset['title']['value'] else dataset_name

            dataset_description = dataset['description']['value'] \
                if dataset['description'] and dataset['description']['value'] else None

            datasets[dataset_id] = {
                'published': dataset['published'],
                'name': dataset_name,
                'title': dataset_title,
                'description': dataset_description,
                'collections': {},
            }

            for collection in dataset['collectionList']['items']:
                collection_id = collection['collectionId']
                if collection_id != 'tim_unknown':
                    datasets[dataset_id]['collections'][collection_id] = {
                        'total': collection['total'],
                        'downloaded': False,
                        'properties': {
                            'uri': {
                                'name': 'uri',
                                'isList': False,
                                'isValueType': False,
                                'isLink': False,
                                'density': 100,
                                'referencedCollections': []
                            }
                        }
                    }

                    for collection_property in collection['properties']['items']:
                        property_name = collection_property['name']

                        referenced_collections = collection_property['referencedCollections']['items']
                        referenced_collections_filtered = \
                            list(filter(lambda ref_col: ref_col != 'tim_unknown', referenced_collections))

                        datasets[dataset_id]['collections'][collection_id]['properties'][property_name] = {
                            'name': property_name,
                            'isList': collection_property['isList'],
                            'isValueType': collection_property['isValueType'],
                            'isLink': len(referenced_collections) > 0,
                            'density': collection_property['density'],
                            'referencedCollections': referenced_collections_filtered,
                        }

        return datasets
