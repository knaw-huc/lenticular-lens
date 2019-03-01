from config_db import db_conn, run_query
from helpers import hash_string
import json
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
import psycopg2
import random
import requests
import time


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


def fetchGraphQl(query, variables):
    tn = 0
    while True:
        try:
            response = requests.post(graphql_uri, json={
                "query": query,
                "variables": variables
            }, timeout=60)
            response.raise_for_status()
            result = response.json()
            if "errors" in result and len(result["errors"]) > 0:
                raise RuntimeError('Graphql query returned an error: ', result["errors"])
            return result["data"]
        except requests.RequestException as e:
            print('Error while trying to get data from Timbuctoo: ' + str(e))
            tn += 1
            print('Waiting to retry...')
            time.sleep((2 ** tn) + (random.randint(0, 1000) / 1000))
            print('Retry %i...' % tn)
        except RuntimeError as e:
            print(e)
            print('Query was: %s' % query)
            return False


def initColumns():
    def get_column_info(column_info):
        result = {"name": column_info["name"], "VALUE": False, "LIST": False, "LINK": False, "URI": False, }
        if column_info["isValueType"]:
            result["VALUE"] = True
        if column_info["isList"]:
            result["LIST"] = True
        if len(column_info["referencedCollections"]["items"]) > 0:
            result["LINK"] = True
        return result

    introspection_result = fetchGraphQl("""
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
        "id": job['dataset_id'],
        "collId": job['collection_id']
    })
    if introspection_result["dataSetMetadata"] is None:
        raise ValueError("The dataset name '" + job['dataset_id'] + "' is not available, use one of",
                         ", ".join([x["dataSetId"] for x in introspection_result["dataSetMetadataList"]]))
    if introspection_result["dataSetMetadata"]["collection"] is None:
        raise ValueError("The collection name '" + job['collection_id'] + "' is not available, use one of", ", ".join(
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
    column_info = {hash_string(name): data for name, data in column_info.items()}
    column_info['uri'] = column_info[hash_string('uri')]
    return {
        'columns': column_info,
        'collection_id': introspection_result["dataSetMetadata"]["collection"]["collectionListId"],
    }


if __name__ == '__main__':
    graphql_uri = 'https://goldenagents.jauco.nl/v5/graphql'
    rows_per_page = 500
    n1 = 0

    while True:
        job = None
        total_insert = 0
        try:
            with db_conn() as conn:
                print('Looking for new Timbuctoo job...')

                job = None
                while not job:
                    with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                        cur.execute("LOCK TABLE timbuctoo_tables IN ACCESS EXCLUSIVE MODE;")
                        cur.execute("""
                            SELECT *
                            FROM timbuctoo_tables
                            WHERE update_start_time IS NULL
                            OR (
                                (update_finish_time IS NULL OR update_finish_time < update_start_time)
                                AND update_start_time < now() - interval '2 minutes'
                                AND (last_push_time IS NULL OR last_push_time < now() - interval '2 minutes')
                            )
                            ORDER BY create_time
                            LIMIT 1;""")

                        job = cur.fetchone()
                        n1 = 0

                        if not job:
                            conn.commit()
                            time.sleep(2)

                start_message = 'Job for table %s ' % job['table_name']
                start_message += 'started.' if job['update_start_time'] is None\
                    else 'resumed at cursor %s.' % job['next_page']
                print(start_message)

                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE timbuctoo_tables SET update_start_time = now() WHERE "table_name" = %s',
                        (job['table_name'],)
                    )
                conn.commit()
                n1 = 0

                introspection_data = initColumns()

                cursor = job['next_page']
                while True:
                    query = """
                                query fetch($cursor: ID) {{
                                    dataSets {{
                                        {dataset} {{
                                            {list_id}(cursor: $cursor, count: {count}) {{
                                                nextCursor
                                                items {{
                                                    {columns}
                                                }}
                                            }}
                                        }}
                                    }}
                                }}
                            """.format(
                        dataset=job['dataset_id'],
                        list_id=introspection_data['collection_id'],
                        count=rows_per_page,
                        columns="\n".join([introspection_data['columns'][name]["name"] + format_query(introspection_data['columns'][name]) for name in introspection_data['columns']]))

                    query_result = fetchGraphQl(query, {'cursor': cursor})
                    if not query_result:
                        job = None
                        break

                    query_result = query_result["dataSets"][job['dataset_id']][introspection_data['collection_id']]

                    results = []
                    for item in query_result["items"]:
                        # Property names can be too long for column names in Postgres, so make them shorter
                        # We use hashing, because that keeps the column names unique and uniform
                        result = {hash_string(name.lower()): extract_value(item[name]) for name in item}
                        # Add non-hashed column 'uri'
                        result['uri'] = result[hash_string('uri')]

                        results.append(result)

                    with conn.cursor() as cur:
                        cur.execute("LOCK TABLE timbuctoo_tables IN ACCESS EXCLUSIVE MODE;")
                        # Check if the data we have is still the data that is expected to be inserted
                        cur.execute('''
                        SELECT 1
                            FROM timbuctoo_tables
                            WHERE "table_name" = %(table_name)s
                            AND (
                                    (
                                        %(next_page)s IS NULL AND next_page IS NULL
                                        AND (update_finish_time IS NULL OR update_finish_time < update_start_time)
                                    )
                                    OR
                                    (
                                        %(next_page)s IS NOT NULL AND next_page = %(next_page)s
                                    )
                                )
                        ''', {'table_name': job['table_name'], 'next_page': cursor})
                        if cur.fetchone() != (1,):
                            print('This is weird... Someone else updated the job for table %s while I was fetching data.' % job['table_name'])
                            conn.commit()
                            break

                    # Check rows count
                    with conn.cursor() as cur:
                        cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}').format(
                            psycopg2_sql.Identifier(job['table_name'])
                        ))
                        table_rows = cur.fetchone()[0]
                    if table_rows != job['rows_count'] + total_insert:
                        print('ERROR: Table %s has %i rows, expected %i. Quitting job.' % (
                            job['table_name'],
                            table_rows,
                            job['rows_count'] + total_insert
                        ))
                        conn.commit()
                        break

                    if len(results) > 0:
                        columns_sql = psycopg2_sql.SQL(', ').join(
                            [psycopg2_sql.Identifier(key) for key in results[0].keys()]
                        )
                        for result in results:
                            with conn.cursor() as cur:
                                cur.execute(psycopg2_sql.SQL('INSERT INTO {} ({}) VALUES %s').format(
                                    psycopg2_sql.Identifier(job['table_name']),
                                    columns_sql,
                                ), (tuple(result.values()),))

                    total_insert += len(results)
                    print('Inserted %i new rows into table %s.' % (total_insert, job['table_name']))
                    with conn.cursor() as cur:
                        cur.execute('''
                        UPDATE timbuctoo_tables
                        SET last_push_time = now(), next_page = %s, rows_count = %s
                        WHERE "table_name" = %s
                        ''', (query_result['nextCursor'], table_rows + len(results), job['table_name'])
                        )

                    conn.commit()
                    cursor = query_result['nextCursor']

                    if cursor is None:
                        print('Job for table %s finished.' % job['table_name'])
                        run_query(
                            'UPDATE timbuctoo_tables SET update_finish_time = now() WHERE "table_name" = %s',
                            (job['table_name'],)
                        )

                        break

        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            n1 += 1
            print('Database error: %s' % e)
            print('Waiting to retry...')
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
            print('Retry %i...' % n1)

            continue
