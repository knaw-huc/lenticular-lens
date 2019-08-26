import random
import requests
import sys
from time import sleep
from common.helpers import hash_string

class Timbuctoo:
    def __init__(self):
        self.graphql_uri = 'https://goldenagents.jauco.nl/v5/graphql'

    def fetchGraphQl(self, query, variables=None):
        n = 0
        while True:
            try:
                response = requests.post(self.graphql_uri, json={
                    "query": query,
                    "variables": variables
                }, timeout=60)
                response.raise_for_status()
                result = response.json()
                if "errors" in result and len(result["errors"]) > 0:
                    raise RuntimeError('Graphql query returned an error: ', result["errors"])
                return result["data"]
            except requests.exceptions.ConnectionError as e:
                n += 1
                print(e, file=sys.stderr)
                print('Waiting to retry...', file=sys.stderr)
                sleep((2 ** n) + (random.randint(0, 1000) / 1000))
                print('Retry %i' % n, file=sys.stderr)

    @property
    def datasets(self):
        datasets_data = self.fetchGraphQl("""
            {
                dataSetMetadataList(promotedOnly: false, publishedOnly: false) {
                    dataSetId,
                    title { value },
                    collectionList {
                        items {
                            collectionId,
                            properties {
                                items {
                                    name
                                    isValueType
                                    isList
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
            dataset_title = dataset['title']['value'] if dataset['title'] and dataset['title']['value'] else dataset_id.split('__')[1]
            datasets[dataset_id] = {"title": dataset_title, "collections": {}}
            for collection in dataset['collectionList']['items']:
                collection_id = collection['collectionId']
                datasets[dataset_id]['collections'][collection_id] = {}
                collection['properties']['items'] += [
                    {"name": "uri", 'isValueType': False, 'isList': False},
                    {"name": "title", 'isValueType': True, 'isList': False},
                    {"name": "description", 'isValueType': True, 'isList': False},
                    {"name": "image", 'isValueType': True, 'isList': False}
                ]
                for collection_property in collection['properties']['items']:
                    property_name = collection_property['name']
                    datasets[dataset_id]['collections'][collection_id][property_name] = {}
                    for property_property_key, property_property_value in collection_property.items():
                        if property_property_key == 'referencedCollections':
                            property_property_value = property_property_value['items']
                        datasets[dataset_id]['collections'][collection_id][property_name][property_property_key] = property_property_value

        return datasets

    @staticmethod
    def columns(datasets):
        def get_column_info(column_info):
            result = {"name": column_info["name"], "VALUE": False, "LIST": False, "LINK": False, "URI": False}
            if column_info["isValueType"]:
                result["VALUE"] = True
            if column_info["isList"]:
                result["LIST"] = True
            if "referencedCollections" in column_info and len(column_info["referencedCollections"]) > 0:
                result["LINK"] = True
                result["REF"] = column_info["referencedCollections"]
            return result

        column_info = {hash_string(col_name.lower()): get_column_info(col_info)
                       for col_name, col_info in datasets.items()}
        column_info[hash_string('uri')]['URI'] = True

        return column_info
