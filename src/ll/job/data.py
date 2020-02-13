from json import dumps
from enum import IntFlag
from decimal import Decimal

from psycopg2 import extras, sql
from psycopg2.extensions import AsIs

from ll.job.job_config import JobConfig
from ll.job.job_transformer import transform

from ll.data.collection import Collection
from ll.data.query import get_property_values, get_property_values_queries, get_property_values_for_query, \
    create_query_for_properties, create_count_query_for_properties, \
    get_linkset_join_sql, get_linkset_cluster_join_sql, get_table_info

from ll.util.config_db import db_conn, fetch_one
from ll.util.helpers import hash_string, hasher, get_pagination_sql


class Validation(IntFlag):
    ALL = 7
    ACCEPTED = 4
    DECLINED = 2
    NOT_VALIDATED = 1


class Job:
    def __init__(self, job_id):
        self.job_id = job_id
        self._data = None

    @property
    def data(self):
        if not self._data:
            self._data = fetch_one('SELECT * FROM reconciliation_jobs WHERE job_id = %s', (self.job_id,), dict=True)

        return self._data

    @property
    def resources(self):
        return self.data['resources']

    @property
    def mappings(self):
        return self.data['mappings']

    @property
    def config(self):
        return JobConfig(self.job_id, self.resources, self.mappings)

    @property
    def alignments(self):
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM alignments WHERE job_id = %s', (self.job_id,))
            return cur.fetchall()

    @property
    def clusterings(self):
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM clusterings WHERE job_id = %s', (self.job_id,))
            return cur.fetchall()

    def config_for_alignment(self, alignment):
        return JobConfig(self.job_id, self.resources, self.mappings, run_match=alignment)

    def alignment(self, alignment):
        return fetch_one('SELECT * FROM alignments WHERE job_id = %s AND alignment = %s',
                         (self.job_id, alignment), dict=True)

    def clustering(self, alignment):
        return fetch_one('SELECT * FROM clusterings WHERE job_id = %s AND alignment = %s',
                         (self.job_id, alignment), dict=True)

    def update_data(self, data):
        if 'resources' in data and 'mappings' in data:
            (resources, mappings) = transform(data['resources'], data['mappings'])

            data['resources_form_data'] = dumps(data['resources'])
            data['mappings_form_data'] = dumps(data['mappings'])
            data['resources'] = dumps(resources)
            data['mappings'] = dumps(mappings)
        else:
            resources = []
            mappings = []

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("""
                INSERT INTO reconciliation_jobs (job_id, %s) VALUES %s
                ON CONFLICT (job_id) DO 
                UPDATE SET (%s) = ROW %s, updated_at = NOW()
            """), (
                AsIs(', '.join(data.keys())),
                tuple([self.job_id] + list(data.values())),
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
            ))

        return resources, mappings

    def update_alignment(self, alignment, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE alignments SET (%s) = ROW %s WHERE job_id = %s AND alignment = %s'), (
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
                self.job_id,
                alignment
            ))

    def update_clustering(self, alignment, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE clusterings SET (%s) = ROW %s WHERE job_id = %s AND alignment = %s'), (
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
                self.job_id,
                alignment
            ))

    def run_alignment(self, alignment, restart=False):
        with db_conn() as conn, conn.cursor() as cur:
            if restart:
                cur.execute(sql.SQL("DELETE FROM alignments WHERE job_id = %s AND alignment = %s"),
                            (self.job_id, alignment))
                cur.execute(sql.SQL("DELETE FROM clusterings WHERE job_id = %s AND alignment = %s"),
                            (self.job_id, alignment))

            cur.execute(sql.SQL("INSERT INTO alignments (job_id, alignment, status, kill, requested_at) "
                                "VALUES (%s, %s, %s, false, now())"), (self.job_id, alignment, 'waiting'))

    def run_clustering(self, alignment, association_file, clustering_type='default'):
        clustering = self.clustering(alignment)

        with db_conn() as conn, conn.cursor() as cur:
            if clustering:
                cur.execute(sql.SQL("""
                    UPDATE clusterings 
                    SET association_file = %s, status = %s, 
                        kill = false, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND alignment = %s
                """), (association_file, 'waiting', self.job_id, alignment))
            else:
                cur.execute(sql.SQL("""
                    INSERT INTO clusterings (job_id, alignment, clustering_type, association_file, 
                                             status, kill, requested_at) 
                    VALUES (%s, %s, %s, %s, %s, false, now())
                """), (self.job_id, alignment, clustering_type, association_file, 'waiting'))

    def kill_alignment(self, alignment):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('UPDATE alignments SET kill = true WHERE job_id = %s AND alignment = %s',
                        (self.job_id, alignment))

    def kill_clustering(self, alignment):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('UPDATE clusterings SET kill = true WHERE job_id = %s AND alignment = %s',
                        (self.job_id, alignment))

    def validate_link(self, alignment, source_uri, target_uri, valid):
        with db_conn() as conn, conn.cursor() as cur:
            query = sql.SQL('UPDATE {} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                .format(sql.Identifier(self.get_linkset_table(alignment)))
            cur.execute(query, (valid, source_uri, target_uri))

    def properties_for_resource(self, resource, downloaded_only=True):
        return self.properties(resource.dataset_id, resource.properties, None, downloaded_only)

    def value_targets_for_match(self, match, downloaded_only=True):
        return self.value_targets(match.properties, downloaded_only)

    def get_linkset_table(self, alignment):
        return 'linkset_' + self.job_id + '_' + str(alignment)

    def get_resource_sample(self, resource_label, invert=False, limit=None, offset=0):
        resource = self.config.get_resource_by_label(hash_string(resource_label))
        if not resource:
            return []

        properties = self.properties_for_resource(resource)
        if not properties:
            return []

        table_info = get_table_info(resource.dataset_id, resource.collection_id)
        query = create_query_for_properties(resource.dataset_id, resource.label,
                                            table_info['table_name'], table_info['columns'], properties,
                                            initial_join=resource.related_joins, condition=resource.filter_sql,
                                            invert=invert, limit=limit, offset=offset)

        return get_property_values_for_query(query, None, properties, dict=False)

    def get_resource_sample_total(self, resource_label):
        resource = self.config.get_resource_by_label(hash_string(resource_label))
        if not resource:
            return {'total': 0}

        table_info = get_table_info(resource.dataset_id, resource.collection_id)
        query = create_count_query_for_properties(resource.label, table_info['table_name'],
                                                  initial_join=resource.related_joins, condition=resource.filter_sql)

        return fetch_one(query, dict=True)

    def get_links(self, alignment, validation_filter=Validation.ALL, cluster_id=None, uri=None,
                  limit=None, offset=0, include_props=False):
        validation_filter_sql = []
        if validation_filter < Validation.ALL and Validation.ACCEPTED in validation_filter:
            validation_filter_sql.append('valid = true')
        if validation_filter < Validation.ALL and Validation.DECLINED in validation_filter:
            validation_filter_sql.append('valid = false')
        if validation_filter < Validation.ALL and Validation.NOT_VALIDATED in validation_filter:
            validation_filter_sql.append('valid IS NULL')

        conditions = []
        if cluster_id:
            conditions.append(sql.SQL('cluster_id = {cluster_id}').format(cluster_id=sql.Literal(cluster_id)))
        if uri:
            conditions.append(sql.SQL('(source_uri = {uri} OR target_uri = {uri})').format(uri=sql.Literal(uri)))
        if len(validation_filter_sql) > 0:
            conditions.append(sql.SQL('(' + ' OR '.join(validation_filter_sql) + ')'))

        linkset_table = self.get_linkset_table(alignment)
        limit_offset_sql = get_pagination_sql(limit, offset)
        where_sql = sql.SQL('WHERE {}').format(sql.SQL(' AND ').join(conditions)) \
            if len(conditions) > 0 else sql.SQL('')

        values = None
        if include_props:
            match = self.config.get_match_by_id(alignment)
            targets = self.value_targets_for_match(match)
            if targets:
                initial_join = get_linkset_join_sql(linkset_table, where_sql, limit, offset)
                queries = get_property_values_queries(targets, initial_join=initial_join)
                values = get_property_values(queries, dict=True)

        with db_conn() as conn, conn.cursor() as cur:
            cur.itersize = 1000
            cur.execute(sql.SQL('SELECT source_uri, target_uri, link_order, similarity, cluster_id, valid '
                                'FROM {linkset} {where_sql} '
                                'ORDER BY sort_order ASC {limit_offset}').format(
                linkset=sql.Identifier(linkset_table),
                where_sql=where_sql,
                limit_offset=sql.SQL(limit_offset_sql)
            ))

            for link in cur:
                yield {
                    'source': link[0],
                    'source_values': values[link[0]] if values else None,
                    'target': link[1],
                    'target_values': values[link[1]] if values else None,
                    'link_order': link[2],
                    'similarity': link[3] if link[3] else {},
                    'cluster_id': link[4],
                    'valid': link[5]
                }

    def get_links_totals(self, alignment, cluster_id=None, uri=None):
        conditions = []
        if cluster_id:
            conditions.append(sql.SQL('cluster_id = {cluster_id}').format(cluster_id=sql.Literal(cluster_id)))
        if uri:
            conditions.append(sql.SQL('(source_uri = {uri} OR target_uri = {uri})').format(uri=sql.Literal(uri)))

        linkset_table = self.get_linkset_table(alignment)
        where_sql = sql.SQL('WHERE {}').format(sql.SQL(' AND ').join(conditions)) \
            if len(conditions) > 0 else sql.SQL('')

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('SELECT valid, count(*) AS valid_count '
                                'FROM {linkset} {where_sql} '
                                'GROUP BY valid')
                        .format(linkset=sql.Identifier(linkset_table), where_sql=where_sql))

            return {'accepted' if row[0] is True else 'declined' if row[0] is False else 'not_validated': row[1]
                    for row in cur.fetchall()}

    def get_clusters(self, alignment, limit=None, offset=0, include_props=False):
        linkset_table = self.get_linkset_table(alignment)
        limit_offset_sql = get_pagination_sql(limit, offset)
        nodes_sql = ', ARRAY_AGG(DISTINCT nodes.uri) AS nodes_arr' if include_props else ''

        values = None
        if include_props:
            match = self.config.get_match_by_id(alignment)
            targets = self.value_targets_for_match(match)
            if targets:
                initial_join = get_linkset_cluster_join_sql(linkset_table, limit, offset)
                queries = get_property_values_queries(targets, initial_join=initial_join)
                values = get_property_values(queries, dict=True)

        with db_conn() as conn, conn.cursor() as cur:
            cur.itersize = 1000
            cur.execute("""
                 SELECT ls.cluster_id, COUNT(DISTINCT nodes.uri) AS size, COUNT(ls.*) / 2 AS links {}
                 FROM {} AS ls
                 CROSS JOIN LATERAL (VALUES (ls.source_uri), (ls.target_uri)) AS nodes(uri)
                 GROUP BY ls.cluster_id
                 ORDER BY size DESC, ls.cluster_id ASC
                 {}
             """.format(nodes_sql, linkset_table, limit_offset_sql))

            for cluster in cur:
                cluster_values = {}
                if values:
                    for uri, uri_values in values.items():
                        if uri in cluster[3]:
                            for prop_value in uri_values:
                                key = prop_value['dataset'] + '_' + prop_value['entity'] \
                                      + '_' + prop_value['property'][-1]

                                if key not in cluster_values:
                                    cluster_values[key] = {
                                        'dataset': prop_value['dataset'],
                                        'entity': prop_value['entity'],
                                        'property': prop_value['property'],
                                        'values': set()
                                    }

                                cluster_values[key]['values'].update(prop_value['values'])

                yield {
                    'id': cluster[0],
                    'size': cluster[1],
                    'links': cluster[2],
                    'values': [{
                        'dataset': cluster_value['dataset'],
                        'entity': cluster_value['entity'],
                        'property': cluster_value['property'],
                        'values': list(cluster_value['values'])
                    } for key, cluster_value in cluster_values.items()] if values else None
                }

    def cluster(self, alignment, cluster_id=None, uri=None):
        all_links = []
        strengths = {}
        nodes = []

        for link in self.get_links(alignment, cluster_id=cluster_id, uri=uri):
            source = '<' + link['source'] + '>'
            target = '<' + link['target'] + '>'

            all_links.append([source, target])
            link_hash = "key_{}".format(str(hasher((source, target))).replace("-", "N"))
            strengths[link_hash] = list(link['similarity'].values())
            if not strengths[link_hash]:
                strengths[link_hash] = [1]

            if source not in nodes:
                nodes.append(source)
            if target not in nodes:
                nodes.append(target)

        return {'links': all_links, 'strengths': strengths, 'nodes': nodes}

    @staticmethod
    def value_targets(properties, downloaded_only=True):
        value_targets = []
        downloaded = Collection.download_status()['downloaded']

        for prop in properties:
            graph = prop['graph']
            new_graph_data = []

            for data_of_entity in prop['data']:
                entity_type = data_of_entity['entity_type']

                if not downloaded_only or Job.is_downloaded(downloaded, graph, entity_type):
                    new_properties = Job.properties(graph, data_of_entity['properties'], downloaded, downloaded_only)
                    if len(new_properties) > 0:
                        new_graph_data.append({'entity_type': entity_type, 'properties': new_properties})

            if len(new_graph_data) > 0:
                value_targets.append({'graph': graph, 'data': new_graph_data})

        return value_targets

    @staticmethod
    def properties(graph, properties, downloaded=None, downloaded_only=True):
        downloaded = Collection.download_status()['downloaded'] if downloaded is None else downloaded

        new_properties = []
        for props in properties:
            props = [prop for prop in props if prop != '__value__' and prop != '']

            if len(props) > 0 and (not downloaded_only or len(props) == 1
                                   or all(Job.is_downloaded(downloaded, graph, entity) for entity in props[1::2])):
                new_properties.append(props)

        return new_properties

    @staticmethod
    def is_downloaded(downloaded, dataset_id, collection_id):
        return any(download['dataset_id'] == dataset_id and download['collection_id'] == collection_id
                   for download in downloaded)
