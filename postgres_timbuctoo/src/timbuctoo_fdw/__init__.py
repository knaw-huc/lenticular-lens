import random

import requests
from itertools import takewhile
from multicorn import ForeignDataWrapper
import json
from time import monotonic as timer, sleep


def hash_string(to_hash):
    import hashlib

    return hashlib.md5(to_hash.encode('utf-8')).hexdigest()


def fetchGraphQl(graphql_uri, query, variables):
    response = requests.post(graphql_uri, json={
        "query": query,
        "variables": variables
    })
    response.raise_for_status()
    result = response.json()
    if "errors" in result and len(result["errors"]) > 0:
        raise RuntimeError('Graphql query returned an error: ', result["errors"])
    return result["data"]

class TimTable:
    def __init__(self, dataset, typename, columns):
        self.timbuctoo_uri = 'https://goldenagents.jauco.nl/v5/graphql'
        self.dataset = dataset
        self.typename = typename
        self.initColumns(columns)
        
    def initColumns(self, columns):
        def get_column_info(column_info):
            result = {"name": column_info["name"], "VALUE": False, "LIST": False, "LINK": False, "URI": False,}
            if column_info["isValueType"]:
                result["VALUE"] = True
            if column_info["isList"]:
                result["LIST"] = True
            if len(column_info["referencedCollections"]["items"]) > 0:
                result["LINK"] = True
            return result

        introspection_result = fetchGraphQl(self.timbuctoo_uri, """
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
        if introspection_result["dataSetMetadata"] == None:
            raise ValueError("The dataset name '" + self.dataset +  "' is not available, use one of", ", ".join([x["dataSetId"] for x in introspection_result["dataSetMetadataList"]]))
        if introspection_result["dataSetMetadata"]["collection"] == None:
            raise ValueError("The collection name '" + self.typename +  "' is not available, use one of", ", ".join([x["collectionId"] for x in introspection_result["dataSetMetadata"]["collectionList"]["items"]]))
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
            **{x["name"].lower(): get_column_info(x) for x in introspection_result["dataSetMetadata"]["collection"]["properties"]["items"]}
        }
        column_info = {hash_string(name): data for name, data in column_info.items()}
        column_info['uri'] = column_info[hash_string('uri')]
        for column in columns:
            if column.lower() not in column_info:
                raise ValueError("The column '" + column +  "' is not available, use one of", ", ".join(column_info))
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
                    result += "... on Entity { uri }" #It might be both a value and a link
            if column_info["LIST"]:
                result = "items { " + result + " }"
            return "{ " + result + " }"
        def extract_value(value):
            if isinstance(value, str) or value == None:
                return value
            if "items" in value and value["items"] != None:
                return json.dumps([ extract_value(item) for item in value["items"]])
            if "value" in value:
                return value["value"]
            if "uri" in value:
                return value["uri"]

        query = """
            query fetch($cursor: ID) {{
                dataSets {{
                    {dataset} {{
                    {list_id}(cursor: $cursor, count: 500) {{
                        nextCursor
                        items {{
                            {columns}
                        }}
                    }}
                    }}
                }}
            }}
        """.format(dataset=self.dataset, list_id=self.list_id, columns="\n".join([self.columns[name]["name"] + format_query(self.columns[name]) for name in self.columns if name in columnLimit]))

        def expand_lists(records, depth=None):
            if not depth:
                depth = 1
            expanded_records = []
            for record in records:
                for field, value in record.items():
                    if not isinstance(value, str) and value is not None and "items" in value and value["items"] is not None:
                        if len(value["items"]) == 0:
                            record[field] = None
                        else:
                            for expanded_value in value["items"]:
                                record[field] = expanded_value
                                expanded_records.append({k: v for k, v in record.items()})
                            records = expand_lists(expanded_records, depth + 1)

            return records

        page = 0
        start = timer()
        while True:
            n = 0
            try:
                query_result = fetchGraphQl(self.timbuctoo_uri, query, {
                    "cursor": curToken
                })["dataSets"][self.dataset][self.list_id]
                page += 1
                print("Fetched page {page}, {elapsed} seconds elapsed".format(page=page, elapsed=round(timer() - start, 1)), flush=True)
                for item in query_result["items"]:
                    result = {hash_string(name.lower()): extract_value(item[name]) for name in item}
                    result['uri'] = result[hash_string('uri')]
                    yield result

                if query_result["nextCursor"] == None:
                    break
                else:
                    curToken = query_result["nextCursor"]
            except (ConnectionError, TimeoutError):
                print('Error. Retrying...', flush=True)
                n += 1
                sleep((2 ** n) + (random.randint(0, 1000) / 1000))


class TimbuctooForeignDataWrapper(ForeignDataWrapper):
    def __init__(self, options, columns):
        super().__init__(options, columns)
        self.executor = TimTable(options["dataset"], options["collectionid"], [key for key in columns])

    def execute(self, quals, columns):
        yield from self.executor.fetchData([key for key in columns])

if __name__ == "__main__":
    cols = ["schema_deathplace", "schema_birthplace", "tim_pred_nameslist", "schema_birthdate"]
    myObj = TimTable("http://repository.huygens.knaw.nl/v5/graphql", "u74ccc032adf8422d7ea92df96cd4783f0543db3b__dwc", "dwc_col_Persons", cols)
    i = 0
    for item in myObj.fetchData(cols):
        i += 1
        if i > 35:
            break
        print(item)