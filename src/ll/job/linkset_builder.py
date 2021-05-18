from uuid import uuid4
from psycopg2 import sql, extras

from ll.job.query_builder import QueryBuilder
from ll.job.links_filter import LinksFilter
from ll.job.clusters_filter import ClustersFilter

from ll.util.config_db import db_conn, fetch_many, fetch_one
from ll.util.helpers import get_pagination_sql, get_sql_empty, flatten


class LinksetBuilder:
    def __init__(self, schema, table_name, spec, view):
        self._schema = schema
        self._table_name = table_name
        self._spec = spec
        self._view = view

        self._limit = None
        self._offset = 0
        self._sort_desc = None
        self._cluster_sort_type = None

        self._links_filter = LinksFilter()
        self._clusters_filter = ClustersFilter()

    def apply_paging(self, limit, offset):
        self._limit = limit
        self._offset = offset

    def apply_sorting(self, sort_desc):
        self._sort_desc = sort_desc

    def apply_cluster_sorting(self, sort_type):
        self._cluster_sort_type = sort_type

    def apply_links_filter(self, links_filter):
        self._links_filter = links_filter

    def apply_clusters_filter(self, clusters_filter):
        self._clusters_filter = clusters_filter

    def get_total_links(self, with_view_filters=False):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('''
                {linkset_cte}
                
                SELECT valid, count(*) AS valid_count 
                FROM linkset
                GROUP BY valid
            ''').format(
                linkset_cte=self.get_linkset_cte_sql(
                    with_view_filters=with_view_filters, apply_paging=False, include_linkset_uris=False)
            ))

            return {
                'accepted': 0,
                'rejected': 0,
                'not_sure': 0,
                'not_validated': 0,
                'mixed': 0,
                **{row[0]: row[1] for row in cur.fetchall()}
            }

    def get_total_clusters(self, with_view_filters=False):
        return fetch_one(sql.SQL('''
            {linkset_cte}
            
            SELECT count(*) AS total
            FROM (
                SELECT cluster_id
                FROM linkset, LATERAL (VALUES (linkset.source_uri), (linkset.target_uri)) AS nodes(uri)
                GROUP BY cluster_id
                {having_sql}
            ) AS x
        ''').format(
            linkset_cte=self.get_linkset_cte_sql(
                with_view_filters=with_view_filters, apply_paging=False, include_linkset_uris=False),
            having_sql=self._clusters_filter.sql()
        ), dict=True)

    def get_links_generator(self, with_view_properties='none', with_view_filters=False):
        is_single_value = with_view_properties == 'single'
        use_properties = bool(with_view_properties != 'none' and self._view.properties_per_collection)

        selection_sql = get_sql_empty(self._selection_props_sql(is_single_value),
                                      flag=use_properties, prefix=sql.SQL(', \n'), add_new_line=False)

        props_joins_sql = get_sql_empty(self._properties_join_sql(
            sql.SQL('IN (linkset.source_uri, linkset.target_uri)'), is_single_value), flag=use_properties)

        with db_conn() as conn, conn.cursor(name=uuid4().hex, cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql.SQL('''
                {linkset_cte}
                
                SELECT source_uri, target_uri, link_order, source_collections, target_collections, 
                       source_intermediates, target_intermediates, cluster_id, valid, similarity 
                       {selection_sql}
                FROM linkset
                {props_joins_sql}
            ''').format(
                linkset_cte=self.get_linkset_cte_sql(with_view_filters=with_view_filters),
                selection_sql=selection_sql,
                props_joins_sql=props_joins_sql
            ))

            for link in fetch_many(cur):
                yield {
                    'source': link['source_uri'],
                    'target': link['target_uri'],
                    'link_order': link['link_order'],
                    'source_collections': link['source_collections'],
                    'target_collections': link['target_collections'],
                    'source_intermediates': flatten(list(link['source_intermediates'].values())) if link[
                        'source_intermediates'] else None,
                    'target_intermediates': flatten(list(link['target_intermediates'].values())) if link[
                        'source_intermediates'] else None,
                    'source_values': self._get_values(link, is_source=True,
                                                      is_single_value=is_single_value) if use_properties else None,
                    'target_values': self._get_values(link, is_source=False,
                                                      is_single_value=is_single_value) if use_properties else None,
                    'cluster_id': link['cluster_id'],
                    'valid': link['valid'],
                    'similarity': link['similarity']
                }

    def get_clusters_generator(self, with_view_properties='none', with_view_filters=False):
        is_single_value = with_view_properties == 'single'
        use_properties = bool(with_view_properties != 'none' and self._view.properties_per_collection)

        selection_sql = get_sql_empty(self._cluster_selection_props_sql,
                                      flag=use_properties, prefix=sql.SQL(', \n'), add_new_line=False)

        props_joins_sql = get_sql_empty(self._properties_join_sql(
            sql.SQL('= ANY (all_nodes)'), is_single_value, include_unnest=True), flag=use_properties)

        sort_sql = sql.SQL('ORDER BY cluster_id')
        if self._cluster_sort_type is not None:
            if self._cluster_sort_type == 'size_asc' or self._cluster_sort_type == 'size_desc':
                sort_sql = sql.SQL('ORDER BY size {}, cluster_id {}') \
                    .format(sql.SQL('ASC') if self._cluster_sort_type == 'size_asc' else sql.SQL('DESC'),
                            sql.SQL('DESC') if self._cluster_sort_type == 'size_asc' else sql.SQL('ASC'))
            else:
                sort_sql = sql.SQL('ORDER BY total_links {}, cluster_id {}') \
                    .format(sql.SQL('ASC') if self._cluster_sort_type == 'count_asc' else sql.SQL('DESC'),
                            sql.SQL('DESC') if self._cluster_sort_type == 'count_asc' else sql.SQL('ASC'))

        with db_conn() as conn, conn.cursor(name=uuid4().hex, cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql.SQL('''
                {linkset_cte}
                
                SELECT cluster_id, size, links {selection_sql} 
                FROM (
                    SELECT cluster_id, array_agg(nodes) AS all_nodes, count(DISTINCT nodes) AS size, 
                           jsonb_object_agg(valid, valid_count) AS links, sum(valid_count) AS total_links
                    FROM (
                        SELECT cluster_id, array_agg(nodes.uri) AS all_nodes, valid, count(valid) / 2 AS valid_count
                        FROM linkset, LATERAL (VALUES (linkset.source_uri), (linkset.target_uri)) AS nodes(uri)
                        GROUP BY cluster_id, valid
                    ) AS x, unnest(all_nodes) AS nodes
                    GROUP BY cluster_id
                    {having_sql}
                    {sort_sql} {limit_offset}
                ) AS clusters
                {props_joins_sql}
                GROUP BY cluster_id, size, links, total_links
                {sort_sql}
            ''').format(
                linkset_cte=self.get_linkset_cte_sql(with_view_filters=with_view_filters, apply_paging=False),
                selection_sql=selection_sql,
                having_sql=self._clusters_filter.sql(),
                limit_offset=sql.SQL(get_pagination_sql(self._limit, self._offset)),
                props_joins_sql=props_joins_sql,
                sort_sql=sort_sql,
            ))

            for cluster in fetch_many(cur):
                yield {
                    'id': cluster['cluster_id'],
                    'size': cluster['size'],
                    'links': cluster['links'],
                    'values': self._get_values(cluster, include_check=False, is_single_value=is_single_value,
                                               max_values=10) if use_properties else None
                }

    def get_linkset_cte_sql(self, with_view_filters=False, apply_paging=True,
                            apply_sorting=True, include_linkset_uris=True):
        use_filters = bool(with_view_filters and self._view.filters_per_collection)

        filter_joins_sql = get_sql_empty(self._filter_join_sql, flag=use_filters)
        where_sql = self._links_filter.sql(additional_filter=self._additional_filter_sql if use_filters else None)

        sort_sql = sql.SQL('ORDER BY sort_order ASC')
        if apply_sorting and self._sort_desc is not None:
            sort_sql = sql.SQL('ORDER BY similarity {}, sort_order ASC') \
                .format(sql.SQL('DESC') if self._sort_desc else sql.SQL('ASC'))

        limit_offset_sql = get_sql_empty(sql.SQL(get_pagination_sql(self._limit, self._offset)), flag=apply_paging)

        include_linkset_uris_sql = get_sql_empty(sql.SQL('''
            , linkset_uris AS (
                SELECT DISTINCT nodes.uri
                FROM linkset, LATERAL (VALUES (linkset.source_uri), (linkset.target_uri)) AS nodes(uri)
            )
        '''), flag=include_linkset_uris)

        return sql.SQL('''
            WITH linkset AS (
                SELECT source_uri, target_uri, link_order, source_collections, target_collections, 
                       source_intermediates, target_intermediates, cluster_id, valid, similarity
                FROM {schema}.{view_name} AS linkset
                {filter_joins_sql}
                {where_sql} 
                {sort_sql} {limit_offset_sql}
            ) {include_linkset_uris_sql} 
        ''').format(
            schema=sql.Identifier(self._schema),
            view_name=sql.Identifier(self._table_name),
            filter_joins_sql=filter_joins_sql,
            where_sql=where_sql,
            sort_sql=sort_sql,
            limit_offset_sql=limit_offset_sql,
            include_linkset_uris_sql=include_linkset_uris_sql,
        )

    @property
    def _collections(self):
        return set(ets.collection for ets in self._spec.entity_type_selections)

    @property
    def _selection_resource_uris_sql(self):
        return sql.SQL(', \n').join([
            sql.SQL('{}.uri AS {}').format(
                sql.Identifier(collection.alias),
                sql.Identifier(collection.alias + '_uri'))
            for collection in self._collections
        ])

    @property
    def _cluster_selection_props_sql(self):
        return sql.SQL(', \n').join(
            [sql.SQL('array_agg(DISTINCT {}) AS {}').format(
                sql.Identifier(collection.alias + '_' + prop.hash + '_extended'),
                sql.Identifier(collection.alias + '_' + prop.hash))
                for collection in self._view.properties_per_collection
                for prop in self._view.properties_per_collection.get(collection)]
        )

    @property
    def _additional_filter_sql(self):
        return sql.SQL(' AND ').join(
            [sql.SQL('{} IN ({})').format(
                sql.Identifier(target),
                sql.SQL(', ').join([
                    sql.SQL('{}.{}').format(sql.Identifier(collection.alias), sql.Identifier('uri'))
                    for collection in self._collections
                ])) for target in ['source_uri', 'target_uri']])

    @property
    def _filter_join_sql(self):
        sqls = []
        for collection in self._collections:
            if collection in self._view.filters_per_collection:
                sqls.append(sql.SQL('''
                    LEFT JOIN (
                        {resource_query}
                    ) AS {resource}
                    ON {resource}.uri IN (linkset.source_uri, linkset.target_uri)
                ''').format(
                    resource_query=QueryBuilder.create_query(
                        collection.alias, collection.table_name,
                        filter_properties=self._view.filters_properties_per_collection[collection],
                        condition=self._view.filters_sql_per_collection[collection]),
                    resource=sql.Identifier(collection.alias),
                ))
            else:
                sqls.append(sql.SQL('''
                    LEFT JOIN timbuctoo.{table_name} AS {resource}
                    ON {resource}.uri IN (linkset.source_uri, linkset.target_uri)
                ''').format(
                    table_name=sql.Identifier(collection.table_name),
                    resource=sql.Identifier(collection.alias),
                ))

        return sql.Composed(sqls)

    def _selection_props_sql(self, single_value=True):
        prop_selection_sqls = [
            sql.SQL('{}.{} AS {}').format(
                sql.Identifier(collection.alias),
                sql.Identifier(prop.hash),
                sql.Identifier(collection.alias + '_' + prop.hash))
            for collection in self._view.properties_per_collection
            for (idx, prop) in enumerate(self._view.properties_per_collection.get(collection))
            if not single_value or idx == 0
        ]

        uri_selection_sqls = [
            sql.SQL('{}.uri AS {}').format(
                sql.Identifier(collection.alias),
                sql.Identifier(collection.alias + '_uri'))
            for collection in self._view.properties_per_collection
        ]

        return sql.SQL(', \n').join(prop_selection_sqls + uri_selection_sqls)

    def _properties_join_sql(self, uri_match_sql, single_value=True, include_unnest=False):
        sqls = []
        for collection in self._collections:
            if collection in self._view.properties_per_collection:
                sqls.append(sql.SQL('''
                    LEFT JOIN (
                        {resource_query}
                    ) AS {resource}
                    ON {resource}.uri {uri_match_sql}
                ''').format(
                    resource_query=QueryBuilder.create_query(
                        collection.alias, collection.table_name,
                        condition=sql.SQL('{}.uri IN (SELECT uri FROM linkset_uris)')
                            .format(sql.Identifier(collection.alias)),
                        selection_properties=self._view.properties_per_collection[collection],
                        single_value=single_value),
                    resource=sql.Identifier(collection.alias),
                    uri_match_sql=uri_match_sql,
                ))

                if include_unnest:
                    for prop in self._view.properties_per_collection.get(collection):
                        sqls.append(sql.SQL('LEFT JOIN unnest({resource}.{property}) '
                                            'AS {extended_property} ON true ').format(
                            resource=sql.Identifier(collection.alias),
                            property=sql.Identifier(prop.hash),
                            extended_property=sql.Identifier(collection.alias + '_' + prop.hash + '_extended'),
                        ))

        return sql.Composed(sqls)

    def _get_values(self, source, include_check=True, is_source=True, is_single_value=False, max_values=None):
        return [{
            'graphql_endpoint': collection.graphql_endpoint,
            'dataset_id': collection.dataset_id,
            'collection_id': collection.collection_id,
            'property': prop.property_path,
            'values': list(filter(None, source[collection.alias + '_' + prop.hash]))[:(max_values or 1)]
            if max_values or is_single_value else list(filter(None, source[collection.alias + '_' + prop.hash]))}
            for collection in self._view.properties_per_collection
            for (idx, prop) in enumerate(self._view.properties_per_collection.get(collection))
            if (not is_single_value or idx == 0) and
               (not include_check
                or (source[collection.alias + '_uri'] == source['source_uri' if is_source else 'target_uri']))
        ]
