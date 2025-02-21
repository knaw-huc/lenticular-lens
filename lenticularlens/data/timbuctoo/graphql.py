import urllib3
import requests
import logging

from math import floor
from typing import Dict
from cachetools import cachedmethod, TTLCache

from lenticularlens.data.dataset_info import Dataset, EntityType, Property

log = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GraphQL:
    cache = TTLCache(maxsize=5, ttl=300)

    known_endpoints = {
        'https://repository.goldenagents.org/graphql': 'ga',
        'https://repository.goldenagents.org/v5/graphql': 'ga',
        'https://repository.huygens.knaw.nl/graphql': 'huygens',
        'https://repository.huygens.knaw.nl/v5/graphql': 'huygens',
        'https://data.anansi.clariah.nl/graphql': 'clariah',
        'https://data.anansi.clariah.nl/v5/graphql': 'clariah',
    }

    def __init__(self, graphql_uri):
        self._graphql_uri = graphql_uri

    def fetch(self, query, variables=None, timeout=60):
        try:
            response = requests.post(self._graphql_uri, json={
                'query': query,
                'variables': variables
            }, timeout=timeout, verify=False)
            response.raise_for_status()

            result = response.json()
            if 'errors' in result and len(result['errors']) > 0:
                raise Exception('Graphql query returned an error: ', result['errors'])

            return result['data']
        except Exception as e:
            log.error(e, exc_info=True)

    @property
    @cachedmethod(lambda self: self.cache, key=lambda self: self._graphql_uri)
    def datasets(self) -> Dict[str, Dataset]:
        datasets_data = self.fetch("""
            {
                dataSetMetadataList(promotedOnly: false, publishedOnly: false) {
                    uri
                    dataSetId
                    dataSetName                    
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
            }""", timeout=10)

        datasets = {}
        if not datasets_data:
            return datasets

        for dataset in datasets_data['dataSetMetadataList']:
            dataset_id = dataset['dataSetId']
            dataset_name = dataset['dataSetName']

            dataset_title = dataset['title']['value'] \
                if dataset['title'] and dataset['title']['value'] else dataset_name

            dataset_description = dataset['description']['value'] \
                if dataset['description'] and dataset['description']['value'] else None

            prefix_mapping = {prefixMapping['prefix']: prefixMapping['uri']
                              for prefixMapping in dataset['prefixMappings']}

            datasets[dataset_id] = Dataset(
                type='timbuctoo',
                title=dataset_title,
                description=dataset_description,
                graphql_endpoint=self._graphql_uri,
                timbuctoo_id=dataset_id,
                prefix_mapping=prefix_mapping
            )

            for collection in dataset['collectionList']['items']:
                collection_id = collection['collectionId']
                collection_title = collection['title']['value'] \
                    if collection['title'] and collection['title']['value'] else None

                if collection_id != 'tim_unknown':
                    datasets[dataset_id].entity_types[collection_id] = EntityType(
                        id=collection_id,
                        label=collection_title,
                        uri=collection['uri'],
                        shortened_uri=collection['shortenedUri'],
                        total=collection['total'],
                        downloaded=False
                    )

                    for collection_property in collection['properties']['items']:
                        property_name = collection_property['name']

                        referenced_collections = collection_property['referencedCollections']['items']
                        referenced_collections_filtered = \
                            list(filter(lambda ref_col: ref_col != 'tim_unknown', referenced_collections))

                        uri = collection_property['uri']
                        short_uri = collection_property['shortenedUri']

                        entities_size = datasets[dataset_id].entity_types[collection_id].total
                        rows_count = floor(entities_size * collection_property['density'])

                        datasets[dataset_id].entity_types[collection_id].properties[property_name] = Property(
                            id=property_name,
                            uri=uri,
                            shortened_uri=short_uri,
                            rows_count=rows_count,
                            referenced=referenced_collections_filtered,
                            is_link=len(referenced_collections) > 0,
                            is_list=collection_property['isList'],
                            is_inverse=collection_property['isInverse'],
                            is_value_type=collection_property['isValueType']
                        )

        return datasets
