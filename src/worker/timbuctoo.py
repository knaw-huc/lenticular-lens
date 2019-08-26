import time
import json
import threading

from psycopg2 import sql as psycopg2_sql

from common.helpers import hash_string
from common.timbuctoo import Timbuctoo
from common.config_db import db_conn, run_query


class TimbuctooJob:
    def __init__(self, table_name, dataset_id, collection_id, columns, cursor, rows_count, rows_per_page):
        self.table_name = table_name
        self.dataset_id = dataset_id
        self.collection_id = collection_id
        self.columns = columns
        self.cursor = cursor
        self.rows_count = rows_count
        self.rows_per_page = rows_per_page

    @staticmethod
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

    @staticmethod
    def extract_value(value):
        if isinstance(value, str) or value == None:
            return value
        if "items" in value and value["items"] != None:
            return json.dumps([TimbuctooJob.extract_value(item) for item in value["items"]])
        if "value" in value:
            return value["value"]
        if "uri" in value:
            return value["uri"]

    def run(self):
        thread = threading.Thread(target=self.download)
        thread.start()

        while thread.is_alive():
            time.sleep(1)

    def kill(self):
        return

    def download(self):
        total_insert = 0

        while True:
            columns = [self.columns[name]['name'] + self.format_query(self.columns[name]) for name in self.columns]

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
                dataset=self.dataset_id,
                list_id=self.collection_id + 'List',
                count=self.rows_per_page,
                columns="\n".join(columns))

            query_result = Timbuctoo().fetchGraphQl(query, {'cursor': self.cursor})
            if not query_result:
                return

            query_result = query_result["dataSets"][self.dataset_id][self.collection_id + 'List']

            results = []
            for item in query_result["items"]:
                # Property names can be too long for column names in Postgres, so make them shorter
                # We use hashing, because that keeps the column names unique and uniform
                result = {hash_string(name.lower()): self.extract_value(item[name]) for name in item}
                # Add non-hashed column 'uri'
                result['uri'] = result[hash_string('uri')]

                results.append(result)

            with db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("LOCK TABLE timbuctoo_tables IN ACCESS EXCLUSIVE MODE;")

                    # Check if the data we have is still the data that is expected to be inserted
                    cur.execute('''
                        SELECT 1
                        FROM timbuctoo_tables
                        WHERE "table_name" = %(table_name)s
                        AND ((
                            %(next_page)s IS NULL AND next_page IS NULL
                            AND (update_finish_time IS NULL OR update_finish_time < update_start_time)
                        ) OR (
                            %(next_page)s IS NOT NULL AND next_page = %(next_page)s
                        ))
                    ''', {'table_name': self.table_name, 'next_page': self.cursor})
                    if cur.fetchone() != (1,):
                        print('This is weird... Someone else updated the job for table %s while I was fetching data.'
                              % self.table_name)
                        conn.commit()
                        return

                # Check rows count
                with conn.cursor() as cur:
                    cur.execute(psycopg2_sql.SQL('SELECT count(*) FROM {}')
                                .format(psycopg2_sql.Identifier(self.table_name)))
                    table_rows = cur.fetchone()[0]

                if table_rows != self.rows_count + total_insert:
                    print('ERROR: Table %s has %i rows, expected %i. Quitting job.' % (
                        self.table_name, table_rows, self.rows_count + total_insert))
                    conn.commit()
                    return

                if len(results) > 0:
                    columns_sql = psycopg2_sql.SQL(', ').join(
                        [psycopg2_sql.Identifier(key) for key in results[0].keys()])
                    for result in results:
                        with conn.cursor() as cur:
                            cur.execute(psycopg2_sql.SQL('INSERT INTO {} ({}) VALUES %s').format(
                                psycopg2_sql.Identifier(self.table_name),
                                columns_sql,
                            ), (tuple(result.values()),))

                total_insert += len(results)
                print('Inserted %i new rows into table %s.' % (total_insert, self.table_name))

                with conn.cursor() as cur:
                    cur.execute('''
                    UPDATE timbuctoo_tables
                    SET last_push_time = now(), next_page = %s, rows_count = %s
                    WHERE "table_name" = %s
                    ''', (query_result['nextCursor'], table_rows + len(results), self.table_name))

                conn.commit()
                self.cursor = query_result['nextCursor']

                if self.cursor is None:
                    print('Job for table %s finished.' % self.table_name)
                    run_query(
                        'UPDATE timbuctoo_tables SET update_finish_time = now() WHERE "table_name" = %s',
                        (self.table_name,)
                    )
                    return
