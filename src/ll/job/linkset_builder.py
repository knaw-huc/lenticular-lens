from uuid import uuid4
from inspect import cleandoc

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
            cur.execute(self.get_total_links_sql(with_view_filters))

            return {
                'accepted': 0,
                'rejected': 0,
                'uncertain': 0,
                'unchecked': 0,
                'disputed': 0,
                **{row[0]: row[1] for row in cur.fetchall()}
            }

    def get_total_links_sql(self, with_view_filters=False):
        return sql.SQL(cleandoc('''
            {linkset_cte}
            
            SELECT valid, count(*) AS valid_count 
            FROM linkset
            GROUP BY valid
        ''')).format(linkset_cte=self.get_linkset_cte_sql(with_view_filters=with_view_filters,
                                                          apply_paging=False, include_linkset_uris=False))

    def get_total_clusters(self, with_view_filters=False):
        return fetch_one(self.get_total_clusters_sql(with_view_filters), dict=True)

    def get_total_clusters_sql(self, with_view_filters=False):
        return sql.SQL(cleandoc('''
            {linkset_cte}
            
            SELECT count(cluster_id) AS total, array_agg(cluster_id) AS cluster_ids
            FROM (
                SELECT cluster_id
                FROM linkset, LATERAL (VALUES (linkset.source_uri), (linkset.target_uri)) AS nodes(uri)
                GROUP BY cluster_id
                {having_sql}
            ) AS x
        ''')).format(
            linkset_cte=self.get_linkset_cte_sql(with_view_filters=with_view_filters,
                                                 apply_paging=False, include_linkset_uris=False),
            having_sql=self._clusters_filter.sql()
        )

    def get_links_generator(self, with_view_properties='none', with_view_filters=False):
        is_single_value = with_view_properties == 'single'
        use_properties = bool(with_view_properties != 'none' and self._view.properties_per_collection)

        with db_conn() as conn, conn.cursor(name=uuid4().hex, cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(self.get_links_generator_sql(with_view_properties, with_view_filters))

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
                    'source_values': self._get_values(link, check_key='source_uri',
                                                      is_single_value=is_single_value) if use_properties else None,
                    'target_values': self._get_values(link, check_key='target_uri',
                                                      is_single_value=is_single_value) if use_properties else None,
                    'cluster_id': link['cluster_id'],
                    'cluster_hash_id': link['cluster_hash_id'],
                    'valid': link['valid'],
                    'similarity': link['similarity'],
                    'motivation': link['motivation']
                }

    def get_links_generator_sql(self, with_view_properties='none', with_view_filters=False):
        is_single_value = with_view_properties == 'single'
        use_properties = bool(with_view_properties != 'none' and self._view.properties_per_collection)

        selection_sql = get_sql_empty(self._selection_props_sql(is_single_value),
                                      flag=use_properties, prefix=sql.SQL(', \n'), add_new_line=False)

        props_joins_sql = get_sql_empty(self._properties_join_sql(
            sql.SQL('IN (linkset.source_uri, linkset.target_uri)'), is_single_value), flag=use_properties)

        group_by_sql = get_sql_empty(sql.SQL(
            'GROUP BY source_uri, target_uri, link_order, source_collections, target_collections, '
            'source_intermediates, target_intermediates, cluster_id, cluster_hash_id, valid, similarity, motivation'),
            flag=use_properties, add_new_line=False)

        return sql.SQL(cleandoc('''
            {linkset_cte}
            
            SELECT source_uri, target_uri, link_order, source_collections, target_collections, 
                   source_intermediates, target_intermediates, cluster_id, cluster_hash_id, 
                   valid, similarity, motivation 
                   {selection_sql}
            FROM linkset
            {props_joins_sql}
            {group_by_sql}
        ''')).format(
            linkset_cte=self.get_linkset_cte_sql(with_view_filters=with_view_filters),
            selection_sql=selection_sql,
            props_joins_sql=props_joins_sql,
            group_by_sql=group_by_sql
        )

    def get_clusters_generator(self, with_view_properties='none', with_view_filters=False, include_nodes=False):
        is_single_value = with_view_properties == 'single'
        use_properties = bool(with_view_properties != 'none' and self._view.properties_per_collection)

        with db_conn() as conn, conn.cursor(name=uuid4().hex, cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(self.get_clusters_generator_sql(with_view_properties, with_view_filters, include_nodes))

            for cluster in fetch_many(cur):
                yield {
                    'id': cluster['cluster_id'],
                    'hash_id': cluster['cluster_hash_id'],
                    'size': cluster['size'],
                    'links': {
                        'accepted': 0,
                        'rejected': 0,
                        'uncertain': 0,
                        'unchecked': 0,
                        'disputed': 0,
                        **cluster['links']
                    },
                    'reconciled': False,
                    'extended': False,
                    'nodes': cluster['nodes'] if include_nodes else None,
                    'values': self._get_values(cluster, is_single_value=is_single_value,
                                               max_values=10) if use_properties else None
                }

    def get_clusters_generator_sql(self, with_view_properties='none', with_view_filters=False, include_nodes=False):
        is_single_value = with_view_properties == 'single'
        use_properties = bool(with_view_properties != 'none' and self._view.properties_per_collection)

        selection_sql = get_sql_empty(self._cluster_selection_props_sql,
                                      flag=use_properties, prefix=sql.SQL(', \n'), add_new_line=False)
        if include_nodes:
            selection_sql = sql.Composed([selection_sql, sql.SQL(', all_nodes AS nodes')])

        props_joins_sql = get_sql_empty(self._properties_join_sql(
            sql.SQL('IN (nodes_limited)'), single_value=is_single_value, include_unnest=True), flag=use_properties)

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

        return sql.SQL(cleandoc('''
            {linkset_cte}
            
            SELECT cluster_id, cluster_hash_id, size, links {selection_sql} 
            FROM (
                SELECT cluster_id, cluster_hash_id, 
                       array_agg(DISTINCT nodes) AS all_nodes, count(DISTINCT nodes) AS size, 
                       jsonb_object_agg(valid, valid_count) AS links, sum(valid_count) AS total_links
                FROM (
                    SELECT cluster_id, cluster_hash_id, 
                           array_agg(nodes.uri) AS all_nodes, valid, count(valid) / 2 AS valid_count
                    FROM linkset, LATERAL (VALUES (linkset.source_uri), (linkset.target_uri)) AS nodes(uri)
                    GROUP BY cluster_id, cluster_hash_id, valid
                ) AS x, unnest(all_nodes) AS nodes
                GROUP BY cluster_id, cluster_hash_id
                {having_sql}
                {sort_sql} {limit_offset}
            ) AS clusters
            LEFT JOIN unnest(all_nodes[0:50]) AS nodes_limited ON true
            {props_joins_sql}
            GROUP BY cluster_id, cluster_hash_id, all_nodes, size, links, total_links
            {sort_sql}
        ''')).format(
            linkset_cte=self.get_linkset_cte_sql(with_view_filters=with_view_filters, apply_paging=False),
            selection_sql=selection_sql,
            having_sql=self._clusters_filter.sql(),
            limit_offset=sql.SQL(get_pagination_sql(self._limit, self._offset)),
            props_joins_sql=props_joins_sql,
            sort_sql=sort_sql,
        )

    def get_linkset_cte_sql(self, with_view_filters=False, apply_paging=True,
                            apply_sorting=True, include_linkset_uris=True):
        use_filters = bool(with_view_filters and self._view.filters_per_collection)

        filter_laterals_sql = get_sql_empty(self._filter_laterals_sql, flag=use_filters)
        where_sql = self._links_filter.sql(additional_filter=self._additional_filter_sql if use_filters else None)

        sort_sql = sql.SQL('ORDER BY sort_order ASC')
        if apply_sorting and self._sort_desc is not None:
            sort_sql = sql.SQL('ORDER BY similarity {}, sort_order ASC') \
                .format(sql.SQL('DESC') if self._sort_desc else sql.SQL('ASC'))

        limit_offset_sql = get_sql_empty(sql.SQL(get_pagination_sql(self._limit, self._offset)), flag=apply_paging)

        include_linkset_uris_sql = get_sql_empty(sql.SQL(cleandoc('''
            , linkset_uris AS (
                SELECT DISTINCT nodes.uri
                FROM linkset, LATERAL (VALUES (linkset.source_uri), (linkset.target_uri)) AS nodes(uri)
            )
        ''')), flag=include_linkset_uris)

        return sql.SQL(cleandoc('''
            WITH linkset AS (
                SELECT source_uri, target_uri, link_order, source_collections, target_collections, 
                       source_intermediates, target_intermediates, cluster_id, cluster_hash_id, 
                       valid, similarity, motivation
                FROM {schema}.{view_name} AS linkset
                {filter_laterals_sql}
                {where_sql} 
                {sort_sql} {limit_offset_sql}
            ) {include_linkset_uris_sql} 
        ''')).format(
            schema=sql.Identifier(self._schema),
            view_name=sql.Identifier(self._table_name),
            filter_laterals_sql=filter_laterals_sql,
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
    def _filter_laterals_sql(self):
        sqls = []
        for collection in self._collections:
            filter_properties = self._view.filters_properties_per_collection[collection] \
                if collection in self._view.filters_per_collection else None

            condition = sql.SQL('{}.uri IN (linkset.source_uri, linkset.target_uri)') \
                .format(sql.Identifier(collection.alias))
            if collection in self._view.filters_per_collection:
                condition = sql.SQL('{} AND {}').format(condition, self._view.filters_sql_per_collection[collection])

            sqls.append(sql.SQL(cleandoc('''
                LATERAL (
                    {resource_query}
                ) AS {resource}
            ''')).format(
                resource_query=QueryBuilder.create_query(
                    collection.alias, collection.table_name,
                    filter_properties=filter_properties,
                    condition=condition),
                resource=sql.Identifier(collection.alias),
            ))

        if sqls:
            return sql.Composed([sql.SQL(',\n'), sql.SQL(',\n').join(sqls)])

        return sql.SQL('')

    def _selection_props_sql(self, single_value=True):
        prop_selection_sqls = [
            (sql.SQL('{}.{}').format(sql.Identifier(collection.alias), sql.Identifier(prop.hash)),
             sql.Identifier(collection.alias + '_' + prop.hash))
            for collection in self._view.properties_per_collection
            for (idx, prop) in enumerate(self._view.properties_per_collection.get(collection))
            if not single_value or idx == 0
        ]

        prop_selection_sqls = [sql.SQL('jsonb_agg({}) AS {}').format(selection_sql[0], selection_sql[1])
                               for selection_sql in prop_selection_sqls]

        uri_selection_sqls = [
            (sql.SQL('{}.uri').format(sql.Identifier(collection.alias)),
             sql.Identifier(collection.alias + '_uri'))
            for collection in self._view.properties_per_collection
        ]

        uri_selection_sqls = [sql.SQL('array_agg({}) AS {}').format(selection_sql[0], selection_sql[1])
                              for selection_sql in uri_selection_sqls]

        return sql.SQL(', \n').join(prop_selection_sqls + uri_selection_sqls)

    def _properties_join_sql(self, uri_match_sql, single_value=True, include_unnest=False):
        join_sqls = []

        for collection in self._collections:
            if collection in self._view.properties_per_collection:
                resource_query_condition = sql.SQL('{}.uri {}').format(sql.Identifier(collection.alias), uri_match_sql)
                resource_query = QueryBuilder.create_query(
                    collection.alias, collection.table_name,
                    condition=resource_query_condition,
                    selection_properties=self._view.properties_per_collection[collection],
                    single_value=single_value)

                join_sqls.append(sql.SQL(cleandoc('''
                    LEFT JOIN LATERAL (
                        {resource_query}
                    ) AS {resource} ON true
                ''')).format(resource_query=resource_query, resource=sql.Identifier(collection.alias)))

                if include_unnest:
                    for prop in self._view.properties_per_collection.get(collection):
                        join_sqls.append(sql.SQL('LEFT JOIN unnest({resource}.{property}) '
                                                 'AS {extended_property} ON true ').format(
                            resource=sql.Identifier(collection.alias),
                            property=sql.Identifier(prop.hash),
                            extended_property=sql.Identifier(collection.alias + '_' + prop.hash + '_extended'),
                        ))

        return sql.SQL('\n').join(join_sqls)

    def _get_values(self, source, check_key=None, is_single_value=False, max_values=None):
        all_values = []

        for collection in self._view.properties_per_collection:
            for (idx, prop) in enumerate(self._view.properties_per_collection.get(collection)):
                uri_key = collection.alias + '_uri'
                if (not is_single_value or idx == 0) and (not check_key or (source[check_key] in source[uri_key])):
                    values = source[collection.alias + '_' + prop.hash]
                    if check_key:
                        values = values[source[uri_key].index(source[check_key])]

                    values = list(filter(None, values))
                    if max_values or is_single_value:
                        values = values[:(max_values or 1)]

                    all_values.append({
                        'graphql_endpoint': collection.graphql_endpoint,
                        'dataset_id': collection.dataset_id,
                        'collection_id': collection.collection_id,
                        'property': prop.property_path,
                        'values': values
                    })

        return all_values

    @staticmethod
    def create(schema, table_name, spec, view,
               links_filter=None, clusters_filter=None, sort=None, cluster_sort=None, offset=0, limit=None):
        linkset_builder = LinksetBuilder(schema, table_name, spec, view)

        if links_filter:
            linkset_builder.apply_links_filter(links_filter)
        if clusters_filter:
            linkset_builder.apply_clusters_filter(clusters_filter)
        if sort:
            linkset_builder.apply_sorting(sort.lower() == 'desc')
        if cluster_sort and (cluster_sort.lower() in ['size_asc', 'size_desc', 'count_asc', 'count_desc']):
            linkset_builder.apply_cluster_sorting(cluster_sort.lower())
        if offset > 0 or limit:
            linkset_builder.apply_paging(limit, offset)

        return linkset_builder
