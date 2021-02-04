from psycopg2 import sql, extras
from collections import defaultdict

from ll.job.joins import Joins
from ll.util.config_db import db_conn
from ll.util.helpers import get_pagination_sql


class QueryBuilder:
    def __init__(self):
        self._queries = []

    def add_query(self, dataset, entity, resource, target, filter_properties, selection_properties,
                  condition=None, invert=False, single_value=False, limit=None, offset=0):
        query = self._create_query(resource, target, filter_properties, selection_properties,
                                   condition=condition, invert=invert, single_value=single_value,
                                   limit=limit, offset=offset)
        if query:
            self._queries.append({
                'dataset': dataset,
                'entity': entity,
                'properties': selection_properties,
                'query': query
            })

    def add_linkset_query(self, schema, linkset, dataset, entity, resource, target, filter_properties,
                          selection_properties, condition=None, single_value=False, limit=None, offset=0):
        linkset_join = self._linkset_join_sql(schema, linkset, resource, condition, limit, offset)
        query = self._create_query(resource, target, filter_properties, selection_properties,
                                   extra_join=linkset_join, single_value=single_value)
        if query:
            self._queries.append({
                'dataset': dataset,
                'entity': entity,
                'properties': selection_properties,
                'query': query
            })

    def add_cluster_query(self, cluster, dataset, entity, resource, target,
                          filter_properties, selection_properties, single_value=False, limit=None, offset=0):
        cluster_join = self._linkset_cluster_join_sql(cluster, resource, limit, offset)
        query = self._create_query(resource, target, filter_properties, selection_properties,
                                   extra_join=cluster_join, single_value=single_value)
        if query:
            self._queries.append({
                'dataset': dataset,
                'entity': entity,
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
                        'dataset': query_info['dataset'],
                        'entity': query_info['entity'],
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
                    if len(values) > 0:
                        property_values[values['uri']] = filtered_values[0]

        return property_values

    @staticmethod
    def _create_query(resource, target, filter_properties, selection_properties,
                      condition=None, extra_join=None, invert=False, single_value=False, limit=None, offset=0):
        filtered_filter_properties = [prop for prop in filter_properties if prop.is_downloaded]
        filtered_selection_properties = [prop for prop in selection_properties if prop.is_downloaded]

        selection_sqls = [sql.SQL('array_agg(DISTINCT {}) AS {}').format(prop.sql, sql.Identifier(prop.hash))
                          for prop in filtered_selection_properties]
        if not selection_sqls:
            return None
        if single_value:
            selection_sqls = [selection_sqls[0]]

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

        return sql.SQL('''
            SELECT {resource}.uri AS uri, {selection}
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
        ''').format(
            resource=sql.Identifier(resource),
            selection=sql.SQL(', ').join(selection_sqls),
            table_name=sql.Identifier(target),
            selection_joins=selection_joins.sql,
            filter_joins=filter_joins.sql,
            condition=condition_sql,
            limit_offset=sql.SQL(get_pagination_sql(limit, offset))
        )

    @staticmethod
    def _linkset_join_sql(schema, linkset, resource, where_sql=None, limit=None, offset=0):
        limit_offset_sql = get_pagination_sql(limit, offset)

        return sql.SQL('''
            INNER JOIN (
                SELECT DISTINCT nodes.uri
                FROM (
                    SELECT links.source_uri, links.target_uri 
                    FROM {schema}.{linkset} AS links
                    {where_sql} 
                    ORDER BY sort_order ASC {limit_offset}
                ) AS ls, LATERAL (VALUES (ls.source_uri), (ls.target_uri)) AS nodes(uri)
            ) AS linkset ON {resource}.uri = linkset.uri
        ''').format(
            schema=sql.Identifier(schema),
            linkset=sql.Identifier(linkset),
            where_sql=where_sql if where_sql else sql.SQL(''),
            limit_offset=sql.SQL(limit_offset_sql),
            resource=sql.Identifier(resource)
        )

    @staticmethod
    def _linkset_cluster_join_sql(table_name, resource, limit=None, offset=0, uri_limit=5):
        return sql.SQL('''
            INNER JOIN (
                SELECT nodes.uri, ROW_NUMBER() OVER (PARTITION BY ls.cluster_id) AS cluster_row_number
                FROM linksets.{linkset} AS ls
                INNER JOIN (
                    SELECT cluster_id
                    FROM linksets.{linkset}
                    CROSS JOIN LATERAL (VALUES (source_uri), (target_uri)) AS nodes(uri)
                    GROUP BY cluster_id
                    ORDER BY count(DISTINCT nodes.uri) DESC, cluster_id ASC
                    {limit_offset}
                ) AS clusters ON ls.cluster_id = clusters.cluster_id
                CROSS JOIN LATERAL (VALUES (source_uri), (target_uri)) AS nodes(uri)
            ) AS linkset 
            ON {resource}.uri = linkset.uri AND linkset.cluster_row_number < {uri_limit}
        ''').format(
            linkset=sql.Identifier(table_name),
            limit_offset=sql.SQL(get_pagination_sql(limit, offset)),
            uri_limit=sql.Literal(uri_limit),
            resource=sql.Identifier(resource)
        )
