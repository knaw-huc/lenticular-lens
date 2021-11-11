from inspect import cleandoc
from collections import defaultdict

from psycopg2 import sql, extras

from ll.job.joins import Joins
from ll.util.config_db import db_conn
from ll.util.helpers import get_pagination_sql


class QueryBuilder:
    def __init__(self):
        self._queries = []

    def add_query(self, graphql_endpoint, dataset_id, collection_id, resource, target,
                  filter_properties, selection_properties,
                  condition=None, invert=False, single_value=False, limit=None, offset=0):
        query = self.create_query(resource, target, filter_properties, selection_properties,
                                  condition=condition, invert=invert, single_value=single_value,
                                  limit=limit, offset=offset)
        if query:
            self._queries.append({
                'graphql_endpoint': graphql_endpoint,
                'dataset_id': dataset_id,
                'collection_id': collection_id,
                'properties': selection_properties,
                'query': query
            })

    def run_queries(self, dict=True):
        property_values = defaultdict(list) if dict else []
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            for query_info in self._queries:
                cur.execute(query_info['query'])
                for values in cur:
                    prop_and_values = [{
                        'graphql_endpoint': query_info['graphql_endpoint'],
                        'dataset_id': query_info['dataset_id'],
                        'collection_id': query_info['collection_id'],
                        'property': property.property_path,
                        'values': list(filter(None, values[property.hash])) if property.hash in values else []
                    } for property in query_info['properties']]

                    if dict:
                        property_values[values['uri']] = prop_and_values
                    else:
                        property_values.append({'uri': values['uri'], 'properties': prop_and_values})

        return property_values

    def run_queries_single_value(self):
        property_values = defaultdict(list)
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            for query_info in self._queries:
                cur.execute(query_info['query'])
                for values in cur:
                    key = [key for key in values.keys() if key != 'uri'][0]
                    filtered_values = list(filter(None, values[key]))
                    if len(filtered_values) > 0:
                        property_values[values['uri']] = filtered_values[0]

        return property_values

    @staticmethod
    def create_query(resource, target, filter_properties=None, selection_properties=None,
                     condition=None, extra_join=None, invert=False, single_value=False, limit=None, offset=0):
        filtered_filter_properties = [prop for prop in filter_properties if prop.is_downloaded] \
            if filter_properties else []
        filtered_selection_properties = [prop for prop in selection_properties if prop.is_downloaded] \
            if selection_properties else []

        selection_sqls = QueryBuilder.get_selection_sqls(filtered_selection_properties, single_value)
        selection_sql = sql.Composed([sql.SQL(', '), sql.SQL(', ').join(selection_sqls)]) \
            if selection_sqls else sql.SQL('')

        condition_sql = sql.SQL('')
        if condition and condition != sql.SQL(''):
            condition_sql = sql.SQL('WHERE {}').format(condition) if not invert \
                else sql.SQL('WHERE NOT ({})').format(condition)
        elif invert:
            condition_sql = sql.SQL('WHERE 1 != 1')

        filter_joins, selection_joins = Joins(), Joins()
        filter_joins.set_joins_for_props(filtered_filter_properties)
        selection_joins.set_joins_for_props(filtered_selection_properties)

        if extra_join:
            filter_joins.add_join(extra_join, 'extra')

        if limit or offset:
            return sql.SQL(cleandoc('''
                SELECT {resource}.uri AS uri {selection}
                FROM timbuctoo.{table_name} AS {resource} 
                {selection_joins}
                WHERE {resource}.uri IN (
                    SELECT {resource}.uri
                    FROM timbuctoo.{table_name} AS {resource}
                    {filter_joins}
                    {condition}
                    GROUP BY {resource}.uri
                    ORDER BY {resource}.uri ASC {limit_offset}
                )
                GROUP BY {resource}.uri
                ORDER BY {resource}.uri
            ''')).format(
                resource=sql.Identifier(resource),
                selection=selection_sql,
                table_name=sql.Identifier(target),
                selection_joins=selection_joins.sql,
                filter_joins=filter_joins.sql,
                condition=condition_sql,
                limit_offset=sql.SQL(get_pagination_sql(limit, offset))
            )

        selection_joins.merge(filter_joins)

        return sql.SQL(cleandoc('''
            SELECT {resource}.uri AS uri {selection}
            FROM timbuctoo.{table_name} AS {resource} 
            {joins}
            {condition}
            GROUP BY {resource}.uri
        ''')).format(
            resource=sql.Identifier(resource),
            selection=selection_sql,
            table_name=sql.Identifier(target),
            joins=selection_joins.sql,
            condition=condition_sql,
            limit_offset=sql.SQL(get_pagination_sql(limit, offset))
        )

    @staticmethod
    def get_selection_sqls(properties, single_value=False):
        selection_sqls = [sql.SQL('array_agg(DISTINCT {prop_sql}) AS {id_sql}').format(
            prop_sql=prop.sql,
            id_sql=sql.Identifier(prop.hash)
        ) for prop in properties]

        if not selection_sqls:
            return None

        if single_value:
            return [selection_sqls[0]]

        return selection_sqls
