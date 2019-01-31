from config_db import db_conn, run_query, table_exists
import datetime
from helpers import hash_string
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql


class Collection:
    def __init__(self, dataset_id, collection_id, columns):
        self.collection_id = collection_id
        self.dataset_id = dataset_id
        self.graph_columns = columns

    @property
    def columns_sql(self):
        def column_sql(column_name, column_type):
            return psycopg2_sql.SQL('{col_name} {col_type}').format(
                col_name=psycopg2_sql.Identifier(column_name),
                col_type=psycopg2_sql.Identifier(column_type),
            )

        columns_sqls = []
        for info in self.columns.values():
            if info['name'] == 'uri':
                columns_sqls.append(column_sql('uri', 'text'))

            column_name = hash_string(info['name'])
            column_type = 'jsonb' if info['LIST'] else 'text'
            columns_sqls.append(column_sql(column_name, column_type))

        return psycopg2_sql.SQL(',\n').join(columns_sqls)

    @property
    def expanded_columns_sql(self):
        def column_sql(column_name, column_type):
            sql_string = 'jsonb_array_elements_text({col_name}) as {col_name}' if column_type == 'jsonb'\
                else '{col_name}'

            return psycopg2_sql.SQL(sql_string).format(col_name=psycopg2_sql.Identifier(column_name))

        columns_sqls = []
        for info in self.columns.values():
            if info['name'] == 'uri':
                columns_sqls.append(column_sql('uri', 'text'))

            column_name = hash_string(info['name'])
            column_type = 'jsonb' if info['LIST'] else 'text'
            columns_sqls.append(column_sql(column_name, column_type))

        return psycopg2_sql.SQL(',\n').join(columns_sqls)

    @property
    def columns(self):
        def get_column_info(name, column_info):
            result = {"name": name.lower(), "VALUE": False, "LIST": False, "LINK": False, "URI": False}
            if column_info["isValueType"]:
                result["VALUE"] = True
            if column_info["isList"]:
                result["LIST"] = True
            if "referencedCollections" in column_info and len(column_info["referencedCollections"]) > 0:
                result["LINK"] = True
            return result

        return {
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
            **{col_name.lower(): get_column_info(col_name, col_info) for col_name, col_info in self.graph_columns.items()}
        }

    @property
    def rows_downloaded(self):
        return self.table_data['rows_count']\
            if self.table_data['update_finish_time'] is None or self.table_data['update_finish_time'] < self.table_data['update_start_time']\
            else -1

    @property
    def table_name(self):
        return hash_string(self.dataset_id + self.collection_id)

    @property
    def table_data(self):
        with db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                cur.execute("LOCK TABLE timbuctoo_tables IN ACCESS EXCLUSIVE MODE;")
                cur.execute('SELECT * FROM timbuctoo_tables WHERE dataset_id = %s AND collection_id = %s',
                                   (self.dataset_id, self.collection_id))
                table_data = cur.fetchone()

            if not table_data:
                with conn.cursor() as cur:
                    cur.execute(psycopg2_sql.SQL('CREATE TABLE {} ({})').format(
                        psycopg2_sql.Identifier(self.table_name),
                        self.columns_sql,
                    ))
                with conn.cursor() as cur:
                    cur.execute(psycopg2_sql.SQL('CREATE VIEW {} AS SELECT {} FROM {}').format(
                        psycopg2_sql.Identifier(self.table_name + '_expanded'),
                        self.expanded_columns_sql,
                        psycopg2_sql.Identifier(self.table_name),
                    ))
                with conn.cursor() as cur:
                    cur.execute(
                        '''INSERT INTO timbuctoo_tables
                            ("table_name", dataset_id, collection_id, create_time)
                            VALUES (%s, %s, %s, now())''',
                        (self.table_name, self.dataset_id, self.collection_id))

                conn.commit()

                return self.table_data

        table_data['view_name'] = table_data['table_name'] + '_expanded'

        return table_data

    @property
    def view_name(self):
        return self.table_data['view_name']
