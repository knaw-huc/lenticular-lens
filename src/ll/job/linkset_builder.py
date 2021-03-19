from uuid import uuid4
from psycopg2 import sql

from ll.job.links_filter import LinksFilter
from ll.job.query_builder import QueryBuilder

from ll.util.config_db import db_conn, fetch_many
from ll.util.hasher import hash_string_min
from ll.util.helpers import get_pagination_sql


class LinksetBuilder:
    def __init__(self, schema, table_name, spec, view):
        self._schema = schema
        self._table_name = table_name
        self._spec = spec
        self._view = view

        self._limit = None
        self._offset = None
        self._links_filter = LinksFilter()

    def apply_paging(self, limit, offset):
        self._limit = limit
        self._offset = offset

    def apply_links_filter(self, links_filter):
        self._links_filter = links_filter

    def get_links_generator(self, with_properties='none'):
        values = self._linkset_values(with_properties == 'single') if self._view and with_properties != 'none' else None

        with db_conn() as conn, conn.cursor(name=uuid4().hex) as cur:
            cur.execute(sql.SQL(
                'SELECT links.source_uri, links.source_collections, '
                '       links.target_uri, links.target_collections, '
                '       link_order, cluster_id, valid, computed_similarity '
                'FROM {schema}.{view_name} AS links '
                '{sim_fields_sql} '
                'CROSS JOIN LATERAL coalesce({sim_logic_ops_sql}, 1) AS computed_similarity '
                '{where_sql} '
                'ORDER BY sort_order ASC {limit_offset}'
            ).format(
                schema=sql.Identifier(self._schema),
                view_name=sql.Identifier(self._table_name),
                sim_fields_sql=self._sim_fields_sql,
                sim_logic_ops_sql=self._spec.similarity_logic_ops_sql,
                where_sql=self._links_filter.sql(),
                limit_offset=sql.SQL(get_pagination_sql(self._limit, self._offset))
            ))

            for link in fetch_many(cur):
                yield {
                    'source': link[0],
                    'source_collections': link[1],
                    'source_values': values[link[0]] if values and link[0] in values else None,
                    'target': link[2],
                    'target_collections': link[3],
                    'target_values': values[link[2]] if values and link[2] in values else None,
                    'link_order': link[4],
                    'cluster_id': link[5],
                    'valid': link[6],
                    'similarity': link[7]
                }

    def get_total_links(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL(
                'SELECT valid, count(*) AS valid_count '
                'FROM {schema}.{view_name} AS links '
                '{where_sql} '
                'GROUP BY valid'
            ).format(
                schema=sql.Identifier(self._schema),
                view_name=sql.Identifier(self._table_name),
                where_sql=self._links_filter.sql()
            ))

            return {row[0]: row[1] for row in cur.fetchall()}

    def get_clusters_generator(self, with_properties='none'):
        values = self._cluster_values(with_properties == 'single') if self._view and with_properties != 'none' else None

        with db_conn() as conn, conn.cursor(name=uuid4().hex) as cur:
            cur.execute(sql.SQL(
                'SELECT ls.cluster_id, count(DISTINCT nodes.uri) AS size, count(ls.*) / 2 AS links {nodes_sql} '
                'FROM {schema}.{view_name} AS ls '
                'CROSS JOIN LATERAL (VALUES (ls.source_uri), (ls.target_uri)) AS nodes(uri) '
                'GROUP BY ls.cluster_id '
                'ORDER BY size DESC, ls.cluster_id {limit_offset}'
            ).format(
                nodes_sql=sql.SQL(', array_agg(DISTINCT nodes.uri) AS nodes_arr' if with_properties != 'none' else ''),
                schema=sql.Identifier(self._schema),
                view_name=sql.Identifier(self._table_name),
                limit_offset=sql.SQL(get_pagination_sql(self._limit, self._offset))
            ))

            for cluster in fetch_many(cur):
                cluster_values = {}
                if values:
                    for uri, uri_values in values.items():
                        if uri in cluster[3]:
                            for prop_value in uri_values:
                                key = prop_value['graphql_endpoint'] + '_' + \
                                      prop_value['dataset_id'] + '_' + \
                                      prop_value['collection_id'] + '_' + \
                                      prop_value['property'][-1]

                                if key not in cluster_values:
                                    cluster_values[key] = {
                                        'graphql_endpoint': prop_value['graphql_endpoint'],
                                        'dataset_id': prop_value['dataset_id'],
                                        'collection_id': prop_value['collection_id'],
                                        'property': prop_value['property'],
                                        'values': set()
                                    }

                                cluster_values[key]['values'].update(prop_value['values'])

                yield {
                    'id': cluster[0],
                    'size': cluster[1],
                    'links': cluster[2],
                    'values': [{
                        'graphql_endpoint': cluster_value['graphql_endpoint'],
                        'dataset_id': cluster_value['dataset_id'],
                        'collection_id': cluster_value['collection_id'],
                        'property': cluster_value['property'],
                        'values': list(cluster_value['values'])
                    } for key, cluster_value in cluster_values.items()] if values else None
                }

    @property
    def _sim_fields_sql(self):
        if self._spec.similarity_fields:
            return sql.SQL('CROSS JOIN LATERAL jsonb_to_record(similarity) AS sim({})') \
                .format(sql.SQL(', ').join([sql.SQL('{} numeric[]').format(sql.Identifier(sim_field))
                                            for sim_field in self._spec.similarity_fields]))

        return sql.SQL('')

    def _linkset_values(self, single_value=False):
        query_builder = QueryBuilder()

        for (collection, properties) in self._view.properties_per_collection.items():
            query_builder.add_linkset_query(
                self._schema, self._table_name, collection.graphql_endpoint,
                collection.dataset_id, collection.collection_id,
                hash_string_min(collection.table_name), collection.table_name, properties,
                condition=self._links_filter.sql(), limit=self._limit, offset=self._offset, single_value=single_value)

        return query_builder.run_queries_single_value() if single_value else query_builder.run_queries()

    def _cluster_values(self, single_value=False):
        query_builder = QueryBuilder()

        for (collection, properties) in self._view.properties_per_collection.items():
            query_builder.add_cluster_query(
                self._schema, self._table_name, collection.graphql_endpoint,
                collection.dataset_id, collection.collection_id,
                hash_string_min(collection.table_name), collection.table_name, properties,
                limit=self._limit, offset=self._offset, single_value=single_value)

        return query_builder.run_queries_single_value() if single_value else query_builder.run_queries()
