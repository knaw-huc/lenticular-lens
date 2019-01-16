import json
import random
import requests
from time import monotonic as timer, sleep


def fetchGraphQl(graphql_uri, query, variables=None):
    response = requests.post(graphql_uri, json={
        "query": query,
        "variables": variables
    })
    response.raise_for_status()
    result = response.json()
    if "errors" in result and len(result["errors"]) > 0:
        raise RuntimeError('Graphql query returned an error: ', result["errors"])
    return result["data"]


class Timbuctoo:
    def __init__(self):
        self.graphql_uri = 'https://goldenagents.jauco.nl/v5/graphql'

    def json_to_file(self, filename):
        file = open(filename, 'w')

        json.dump(self.datasets, file, indent=2)

        file.close()

    @property
    def datasets(self):
        datasets_data = fetchGraphQl(self.graphql_uri, """
            {
                dataSetMetadataList(promotedOnly: false, publishedOnly: false) {
                    dataSetId,
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
            datasets[dataset_id] = {}
            for collection in dataset['collectionList']['items']:
                collection_id = collection['collectionId']
                datasets[dataset_id][collection_id] = {}
                collection['properties']['items'] += [
                    {"name": "uri", 'isValueType': False, 'isList': False},
                    {"name": "title", 'isValueType': True, 'isList': False},
                    {"name": "description", 'isValueType': True, 'isList': False},
                    {"name": "image", 'isValueType': True, 'isList': False}
                ]
                for collection_property in collection['properties']['items']:
                    property_name = collection_property['name']
                    datasets[dataset_id][collection_id][property_name] = {}
                    for property_property_key, property_property_value in collection_property.items():
                        if property_property_key == 'name':
                            continue
                        if property_property_key == 'referencedCollections':
                            property_property_value = property_property_value['items']
                        datasets[dataset_id][collection_id][property_name][property_property_key] = property_property_value

        return datasets

    @property
    def introspection_result(self):
        return fetchGraphQl(self.timbuctoo_uri, """
            query($id: ID!, $collId: ID!) {
                dataSetMetadata(dataSetId: $id) {
                    collection(collectionId: $collId) {
                        collectionListId
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
                    collectionList {
                        items {
                            collectionId
                        }
                    }
                }
                dataSetMetadataList(promotedOnly: false, publishedOnly: false) {
                    dataSetId
                }
            }
        """, {
            "id": self.dataset,
            "collId": self.typename
        })

    def initColumns(self, columns):
        def get_column_info(column_info):
            result = {"name": column_info["name"], "VALUE": False, "LIST": False, "LINK": False, "URI": False, }
            if column_info["isValueType"]:
                result["VALUE"] = True
            if column_info["isList"]:
                result["LIST"] = True
            if len(column_info["referencedCollections"]["items"]) > 0:
                result["LINK"] = True
            return result

        introspection_result = self.introspection_result
        if introspection_result["dataSetMetadata"] is None:
            raise ValueError("The datasetname '" + self.dataset + "' is not available, use one of",
                             ", ".join([x["dataSetId"] for x in introspection_result["dataSetMetadataList"]]))
        if introspection_result["dataSetMetadata"]["collection"] is None:
            raise ValueError("The collection name '" + self.typename + "' is not available, use one of", ", ".join(
                [x["collectionId"] for x in introspection_result["dataSetMetadata"]["collectionList"]["items"]]))
        column_info = {
            "uri": {
                "name": "uri",
                "LIST": False,
                "LINK": False,
                "VALUE": False,
                "URI": True,
            },
            "title": {
                "name": "title",
                "LIST": False,
                "LINK": False,
                "VALUE": True,
                "URI": False,
            },
            "description": {
                "name": "description",
                "LIST": False,
                "LINK": False,
                "VALUE": True,
                "URI": False,
            },
            "image": {
                "name": "image",
                "LIST": False,
                "LINK": False,
                "VALUE": True,
                "URI": False,
            },
            **{x["name"].lower(): get_column_info(x) for x in
               introspection_result["dataSetMetadata"]["collection"]["properties"]["items"]}
        }
        for column in columns:
            if column not in column_info:
                raise ValueError("The column '" + column + "' is not available, use one of", ", ".join(column_info))
        self.columns = column_info
        self.list_id = introspection_result["dataSetMetadata"]["collection"]["collectionListId"]

    def fetchData(self, columnLimit):
        curToken = None

        def format_query(column_info):
            result = ""
            if column_info["URI"]:
                return ""
            else:
                if column_info["VALUE"]:
                    result = "... on Value { value type } "
                if column_info["LINK"]:
                    result += "... on Entity { uri }"  # It might be both a value and a link
            if column_info["LIST"]:
                result = "items { " + result + " }"
            return "{ " + result + " }"

        def extract_value(value):
            if isinstance(value, str) or value == None:
                return value
            if "items" in value and value["items"] != None:
                return json.dumps([extract_value(item) for item in value["items"]])
            if "value" in value:
                return value["value"]
            if "uri" in value:
                return value["uri"]

        query = """
            query fetch($cursor: ID) {{
                dataSets {{
                    {dataset} {{
                    {list_id}(cursor: $cursor, count: 20) {{
                        nextCursor
                        items {{
                            {columns}
                        }}
                    }}
                    }}
                }}
            }}
        """.format(dataset=self.dataset, list_id=self.list_id, columns="\n".join(
            [self.columns[name]["name"] + format_query(self.columns[name]) for name in self.columns if
             name in columnLimit]))
        page = 0
        start = timer()
        while True:
            n = 0
            try:
                query_result = fetchGraphQl(query, {
                    "cursor": curToken
                })["dataSets"][self.dataset][self.list_id]
                page += 1
                print("Fetched page {page}, {elapsed} seconds elapsed".format(page=page,
                                                                              elapsed=round(timer() - start, 1)))
                for item in query_result["items"]:
                    result = {name.lower(): extract_value(item[name]) for name in item}
                    yield result
                if query_result["nextCursor"] == None:
                    break
                else:
                    curToken = query_result["nextCursor"]
            except (ConnectionError, TimeoutError):
                n += 1
                sleep((2 ** n) + (random.randint(0, 1000) / 1000))