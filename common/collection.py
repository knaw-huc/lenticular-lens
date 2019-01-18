from config_db import db_conn, run_query, table_exists
from helpers import hash_string
from psycopg2 import sql as psycopg2_sql


class Collection:
    def __init__(self, dataset_id, collection_id, columns):
        self.collection_id = collection_id
        self.dataset_id = dataset_id
        self.graph_columns = columns

    def create_foreign_table(self, name):
        run_query(psycopg2_sql.SQL("""
        CREATE FOREIGN TABLE IF NOT EXISTS {table_name} (
            {columns}
        ) SERVER timbuctoo OPTIONS (
            dataset %(dataset_id)s,
            collectionid %(collection_id)s
        );
        """)
            .format(
            table_name=psycopg2_sql.Identifier(name),
            columns=self.columns_sql,
        ), {'dataset_id': self.dataset_id, 'collection_id': self.collection_id})

    def create_cached_view(self, limit=None):
        original_table = self.view_name if limit and self.has_cached_view else self.sql_name
        limit_string = 'LIMIT %s' if limit else ''
        if limit and self.has_cached_view:
            limit_string = 'ORDER BY RANDOM() ' + limit_string

        run_query(psycopg2_sql.SQL("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {limit_view_name} AS
                SELECT * FROM {original_view_name}
                %s
                ;
                """ % limit_string).format(
            limit_view_name=psycopg2_sql.Identifier(self.limit_view_name(limit) + '_full'),
            original_view_name=psycopg2_sql.Identifier(original_table)),
            (limit,))

        conn = db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.attname,
                   pg_catalog.format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
              JOIN pg_class t on a.attrelid = t.oid
              JOIN pg_namespace s on t.relnamespace = s.oid
            WHERE a.attnum > 0 
              AND NOT a.attisdropped
              AND t.relname = %s
              AND s.nspname = 'public'
            ORDER BY a.attnum;
        """, (self.limit_view_name(limit) + '_full',))

        column_sqls = []
        for column in cur:
            column_sql = psycopg2_sql.Identifier(column[0])
            if column[1] == 'jsonb':
                column_sql = psycopg2_sql.SQL('jsonb_array_elements_text({}) AS {}').format(column_sql, column_sql)
            column_sqls.append(column_sql)
        conn.close()

        run_query(psycopg2_sql.SQL("""
            CREATE OR REPLACE VIEW {view_name} AS
            SELECT {columns}
            FROM {materialized_view}
            ;
        """).format(
            view_name=psycopg2_sql.Identifier(self.limit_view_name(limit)),
            columns=psycopg2_sql.SQL(',\n').join(column_sqls),
            materialized_view=psycopg2_sql.Identifier(self.limit_view_name(limit) + '_full'),
        ))

    def limit_view_name(self, limit, create_if_not_exists=False):
        view_name = self.sql_name + '_limit_' + str(limit) if limit else self.get_view_name(False)

        if limit and create_if_not_exists and not table_exists(view_name):
            self.create_cached_view(limit)

        return view_name

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
    def has_cached_view(self):
        return table_exists(self.get_view_name(False))

    @property
    def sql_name(self):
        sql_name = hash_string(self.dataset_id + self.collection_id)
        if not table_exists(sql_name):
            self.create_foreign_table(sql_name)

        return sql_name

    def get_view_name(self, create_if_not_exists=True):
        view_name = self.sql_name + '_cached'
        if create_if_not_exists and not table_exists(view_name):
            self.create_cached_view()

        return view_name

    view_name = property(get_view_name)
