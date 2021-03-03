import urllib3
import requests
import logging

log = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Timbuctoo:
    def __init__(self, graphql_uri, hsid=None):
        self._graphql_uri = graphql_uri
        self._hsid = hsid

    def fetch_graph_ql(self, query, variables=None):
        try:
            response = requests.post(self._graphql_uri, json={
                'query': query,
                'variables': variables
            }, headers={'Authorization': self._hsid} if self._hsid else {}, timeout=60, verify=False)
            response.raise_for_status()

            result = response.json()
            if 'errors' in result and len(result['errors']) > 0:
                raise Exception('Graphql query returned an error: ', result['errors'])

            return result['data']
        except Exception as e:
            log.error(e, exc_info=True)

    @property
    def datasets(self):
        datasets_data = self.fetch_graph_ql("""
            {
                dataSetMetadataList(promotedOnly: false, publishedOnly: false) {
                    uri
                    dataSetId
                    dataSetName
                    published
                    title { value }
                    description { value }
                    prefixMappings {
                        prefix
                        uri
                    }
                    collectionList {
                        items {
                            uri
                            collectionId
                            shortenedUri
                            title { value }
                            total
                            properties {
                                items {
                                    uri
                                    name
                                    shortenedUri
                                    isInverse
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

            prefix_mapping = {prefixMapping['prefix']: prefixMapping['uri']
                              for prefixMapping in dataset['prefixMappings']}

            datasets[dataset_id] = {
                'uri': dataset['uri'],
                'published': dataset['published'],
                'name': dataset_name,
                'title': dataset_title,
                'description': dataset_description,
                'prefixMappings': prefix_mapping,
                'collections': {},
            }

            for collection in dataset['collectionList']['items']:
                collection_id = collection['collectionId']
                collection_title = collection['title']['value'] \
                    if collection['title'] and collection['title']['value'] else None

                if collection_id != 'tim_unknown':
                    datasets[dataset_id]['collections'][collection_id] = {
                        'uri': collection['uri'],
                        'title': collection_title,
                        'shortenedUri': collection['shortenedUri'],
                        'total': collection['total'],
                        'downloaded': False,
                        'properties': {}
                    }

                    for collection_property in collection['properties']['items']:
                        property_name = collection_property['name']

                        referenced_collections = collection_property['referencedCollections']['items']
                        referenced_collections_filtered = \
                            list(filter(lambda ref_col: ref_col != 'tim_unknown', referenced_collections))

                        uri = collection_property['uri']
                        short_uri = collection_property['shortenedUri']

                        prefix = short_uri[:short_uri.index(':')] if uri != short_uri and ':' in short_uri else None
                        prefix_uri = prefix_mapping[prefix] if prefix and prefix in prefix_mapping else None

                        datasets[dataset_id]['collections'][collection_id]['properties'][property_name] = {
                            'uri': uri,
                            'name': property_name,
                            'shortenedUri': short_uri,
                            'isInverse': collection_property['isInverse'],
                            'isList': collection_property['isList'],
                            'isValueType': collection_property['isValueType'],
                            'isLink': len(referenced_collections) > 0,
                            'density': collection_property['density'],
                            'referencedCollections': referenced_collections_filtered,
                            'prefix': prefix,
                            'prefixUri': prefix_uri,
                        }

        return datasets
