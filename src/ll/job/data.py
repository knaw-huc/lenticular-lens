from json import dumps
from enum import IntFlag
from uuid import uuid4

from psycopg2 import extras, sql
from psycopg2.extensions import AsIs

from ll.job.lens import Lens
from ll.job.linkset import Linkset
from ll.job.entity_type_selection import EntityTypeSelection
from ll.job.transformer import transform

from ll.data.collection import Collection
from ll.data.query import get_property_values, get_property_values_queries, get_property_values_for_query, \
    create_query_for_properties, create_count_query_for_properties, \
    get_linkset_join_sql, get_linkset_cluster_join_sql, get_table_info

from ll.util.config_db import db_conn, fetch_one
from ll.util.helpers import hasher, get_pagination_sql


class Validation(IntFlag):
    ALL = 15
    ACCEPTED = 8
    REJECTED = 4
    NOT_VALIDATED = 2
    MIXED = 1


class Job:
    def __init__(self, job_id):
        self.job_id = job_id
        self._data = None
        self._entity_type_selections = None
        self._linkset_specs = None
        self._lens_specs = None

    @property
    def data(self):
        if not self._data:
            self._data = fetch_one('SELECT * FROM jobs WHERE job_id = %s', (self.job_id,), dict=True)

        return self._data

    @property
    def entity_type_selections(self):
        if not self._entity_type_selections:
            self._entity_type_selections = list(map(lambda entity_type_selection:
                                                    EntityTypeSelection(entity_type_selection, self),
                                                    self.data['entity_type_selections']))

        return self._entity_type_selections

    @property
    def linkset_specs(self):
        if not self._linkset_specs:
            self._linkset_specs = list(
                map(lambda linkset_spec: Linkset(linkset_spec, self), self.data['linkset_specs']))

        return self._linkset_specs

    @property
    def lens_specs(self):
        if not self._lens_specs:
            self._lens_specs = list(map(lambda lens_spec: Lens(lens_spec, self), self.data['lens_specs']))

        return self._lens_specs

    @property
    def linksets(self):
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM linksets WHERE job_id = %s', (self.job_id,))
            return cur.fetchall()

    @property
    def lenses(self):
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM lenses WHERE job_id = %s', (self.job_id,))
            return cur.fetchall()

    @property
    def clusterings(self):
        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM clusterings WHERE job_id = %s', (self.job_id,))
            return cur.fetchall()

    def linkset(self, id):
        return fetch_one('SELECT * FROM linksets WHERE job_id = %s AND spec_id = %s',
                         (self.job_id, id), dict=True)

    def lens(self, id):
        return fetch_one('SELECT * FROM lenses WHERE job_id = %s AND spec_id = %s',
                         (self.job_id, id), dict=True)

    def clustering(self, id, type):
        return fetch_one('SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = %s',
                         (self.job_id, id, type), dict=True)

    def update_data(self, data):
        if 'entity_type_selections' in data and 'linkset_specs' in data and 'lens_specs' in data:
            (entity_type_selections, linkset_specs, lens_specs) \
                = transform(data['entity_type_selections'], data['linkset_specs'], data['lens_specs'])

            data['entity_type_selections_form_data'] = dumps(data['entity_type_selections'])
            data['linkset_specs_form_data'] = dumps(data['linkset_specs'])
            data['lens_specs_form_data'] = dumps(data['lens_specs'])
            data['entity_type_selections'] = dumps(entity_type_selections)
            data['linkset_specs'] = dumps(linkset_specs)
            data['lens_specs'] = dumps(lens_specs)
        else:
            entity_type_selections = []
            linkset_specs = []
            lens_specs = []

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("""
                INSERT INTO jobs (job_id, %s) VALUES %s
                ON CONFLICT (job_id) DO 
                UPDATE SET (%s) = ROW %s, updated_at = NOW()
            """), (
                AsIs(', '.join(data.keys())),
                tuple([self.job_id] + list(data.values())),
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
            ))

        return entity_type_selections, linkset_specs, lens_specs

    def update_linkset(self, id, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE linksets SET (%s) = ROW %s WHERE job_id = %s AND spec_id = %s'), (
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
                self.job_id,
                id
            ))

    def update_lens(self, id, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE lenses SET (%s) = ROW %s WHERE job_id = %s AND spec_id = %s'), (
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
                self.job_id,
                id
            ))

    def update_clustering(self, id, type, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE clusterings SET (%s) = ROW %s '
                                'WHERE job_id = %s AND spec_id = %s AND spec_type = %s'), (
                            AsIs(', '.join(data.keys())),
                            tuple(data.values()),
                            self.job_id,
                            id,
                            type
                        ))

    def run_linkset(self, id, restart=False):
        with db_conn() as conn, conn.cursor() as cur:
            if restart:
                cur.execute(sql.SQL("DELETE FROM linksets WHERE job_id = %s AND spec_id = %s"),
                            (self.job_id, id))
                cur.execute(sql.SQL("DELETE FROM clusterings "
                                    "WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'"),
                            (self.job_id, id))

            cur.execute(sql.SQL("INSERT INTO linksets (job_id, spec_id, status, kill, requested_at) "
                                "VALUES (%s, %s, %s, false, now())"), (self.job_id, id, 'waiting'))

    def run_lens(self, id, restart=False):
        with db_conn() as conn, conn.cursor() as cur:
            if restart:
                cur.execute(sql.SQL("DELETE FROM lenses WHERE job_id = %s AND spec_id = %s"),
                            (self.job_id, id))
                cur.execute(sql.SQL("DELETE FROM clusterings "
                                    "WHERE job_id = %s AND spec_id = %s AND spec_type = 'lens'"),
                            (self.job_id, id))

            cur.execute(sql.SQL("INSERT INTO lenses (job_id, spec_id, status, kill, requested_at) "
                                "VALUES (%s, %s, %s, false, now())"), (self.job_id, id, 'waiting'))

    def run_clustering(self, id, type, association_file, clustering_type='default'):
        clustering = self.clustering(id, type)

        with db_conn() as conn, conn.cursor() as cur:
            if clustering:
                cur.execute(sql.SQL("""
                    UPDATE clusterings 
                    SET association_file = %s, status = %s, 
                        kill = false, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND spec_id = %s AND spec_type = %s
                """), (association_file, 'waiting', self.job_id, id, type))
            else:
                cur.execute(sql.SQL("""
                    INSERT INTO clusterings (job_id, spec_id, spec_type, clustering_type, association_file, 
                                             status, kill, requested_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, false, now())
                """), (self.job_id, id, type, clustering_type, association_file, 'waiting'))

    def kill_linkset(self, id):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('UPDATE linksets SET kill = true WHERE job_id = %s AND spec_id = %s',
                        (self.job_id, id))

    def kill_lens(self, id):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('UPDATE lenses SET kill = true WHERE job_id = %s AND spec_id = %s',
                        (self.job_id, id))

    def kill_clustering(self, id, type):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('UPDATE clusterings SET kill = true WHERE job_id = %s AND spec_id = %s AND spec_type = %s',
                        (self.job_id, id, type))

    def delete(self, id, type):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('DELETE FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = %s',
                        (self.job_id, id, type))

            if type == 'linkset':
                cur.execute('DELETE FROM linksets WHERE job_id = %s AND spec_id = %s', (self.job_id, id))
                cur.execute(sql.SQL('DROP TABLE IF EXISTS {}').format(sql.Identifier(self.linkset_table_name(id))))

            if type == 'lens':
                cur.execute('DELETE FROM lenses WHERE job_id = %s AND spec_id = %s', (self.job_id, id))
                cur.execute(sql.SQL('DROP TABLE IF EXISTS {}').format(sql.Identifier(self.lens_table_name(id))))

    def validate_link(self, id, type, source_uri, target_uri, valid):
        linksets = set() if type == 'lens' else {id}
        lenses = set() if type == 'linkset' else {id}

        lenses_tmp = [] if type == 'linkset' else [id]
        while lenses_tmp:
            lens = self.get_lens_spec_by_id(lenses_tmp[0])
            linksets = linksets.union(lens.linksets)
            lenses = lenses.union(lens.lenses)

            lenses_tmp += lens.lenses
            lenses_tmp.remove(lens.id)

        with db_conn() as conn, conn.cursor() as cur:
            for linkset_id in linksets:
                query = sql.SQL('UPDATE {} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                    .format(sql.Identifier(self.linkset_table_name(linkset_id)))
                cur.execute(query, (valid, source_uri, target_uri))

            if type == 'lens':
                query = sql.SQL('UPDATE {} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                    .format(sql.Identifier(self.lens_table_name(id)))
                cur.execute(query, (valid, source_uri, target_uri))
            else:
                for lens_spec in self.lens_specs:
                    if linkset_id in lens_spec.linksets:
                        validities_sql = sql.SQL(' UNION ALL ').join(
                            sql.Composed([
                                sql.SQL('SELECT valid FROM {table} '
                                        'WHERE source_uri = {source_uri} AND target_uri = {target_uri}').format(
                                    table=sql.Identifier(self.linkset_table_name(linkset)),
                                    source_uri=sql.Literal(source_uri), target_uri=sql.Literal(target_uri)
                                ) for linkset in lens_spec.linksets if linkset != linkset_id
                            ])
                        )

                        cur.execute(validities_sql)
                        validities = [result[0] for result in cur.fetchall()]
                        valid_lens = 'mixed' if validities and valid not in validities else valid

                        query = sql.SQL('UPDATE {} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                            .format(sql.Identifier(self.lens_table_name(lens_spec.id)))
                        cur.execute(query, (valid_lens, source_uri, target_uri))

    def properties_for_entity_type_selection(self, entity_type_selection, downloaded_only=True):
        return self._properties(entity_type_selection.dataset_id, entity_type_selection.properties,
                                None, downloaded_only)

    def value_targets_for_properties(self, properties, downloaded_only=True):
        return self._value_targets(properties, downloaded_only)

    def linkset_schema_name(self, id):
        return 'job_' + self.job_id + '_' + str(id)

    def linkset_table_name(self, id):
        return 'linkset_' + self.job_id + '_' + str(id)

    def lens_table_name(self, id):
        return 'lens_' + self.job_id + '_' + str(id)

    def entity_type_selections_required_for_linkset(self, id):
        linkset_spec = self.get_linkset_spec_by_id(id)

        to_add = linkset_spec.entity_type_selections
        to_run = []

        added = []
        while to_add:
            ets_to_add = to_add[0]

            if ets_to_add not in added:
                for ets in self.entity_type_selections:
                    if ets.internal_id == ets_to_add:
                        to_run.append(ets)
                        to_add.remove(ets_to_add)
                        added.append(ets_to_add)
            else:
                to_add.remove(ets_to_add)

        return to_run

    def spec_lens_uses(self, id, type):
        return [lens_spec.id for lens_spec in self.lens_specs
                if (type == 'linkset' and id in lens_spec.linksets)
                or (type == 'lens' and id in lens_spec.lenses)]

    def has_queued_entity_type_selections(self, id=None):
        ets = self.entity_type_selections_required_for_linkset(id) if id else self.entity_type_selections
        for entity_type_selection in ets:
            if entity_type_selection.view_queued:
                return True

        return False

    def get_entity_type_selection_by_id(self, id):
        for entity_type_selection in self.entity_type_selections:
            if entity_type_selection.id == id:
                return entity_type_selection

        return None

    def get_entity_type_selection_by_internal_id(self, internal_id):
        for entity_type_selection in self.entity_type_selections:
            if entity_type_selection.internal_id == internal_id:
                return entity_type_selection

        return None

    def get_linkset_spec_by_id(self, id):
        for linkset_spec in self.linkset_specs:
            if linkset_spec.id == id:
                return linkset_spec

        return None

    def get_lens_spec_by_id(self, id):
        for lens_spec in self.lens_specs:
            if lens_spec.id == id:
                return lens_spec

        return None

    def get_entity_type_selection_sample(self, id, invert=False, limit=None, offset=0):
        entity_type_selection = self.get_entity_type_selection_by_id(id)
        if not entity_type_selection:
            return []

        properties = self.properties_for_entity_type_selection(entity_type_selection)
        if not properties:
            return []

        table_info = get_table_info(entity_type_selection.dataset_id, entity_type_selection.collection_id)
        query = create_query_for_properties(entity_type_selection.dataset_id, entity_type_selection.internal_id,
                                            table_info['table_name'], table_info['columns'], properties,
                                            joins=entity_type_selection.joins(),
                                            condition=entity_type_selection.filter_sql,
                                            invert=invert, limit=limit, offset=offset)

        return get_property_values_for_query(query, None, properties, dict=False)

    def get_entity_type_selection_sample_total(self, id):
        entity_type_selection = self.get_entity_type_selection_by_id(id)
        if not entity_type_selection:
            return {'total': 0}

        table_info = get_table_info(entity_type_selection.dataset_id, entity_type_selection.collection_id)
        query = create_count_query_for_properties(entity_type_selection.internal_id, table_info['table_name'],
                                                  joins=entity_type_selection.joins(),
                                                  condition=entity_type_selection.filter_sql)

        return fetch_one(query, dict=True)

    def get_links(self, id, type, validation_filter=Validation.ALL, cluster_id=None, uri=None,
                  limit=None, offset=0, include_props=False):
        view_name = sql.Identifier(self.linkset_table_name(id)) \
            if type == 'linkset' else sql.Identifier(self.lens_table_name(id))

        validation_filter_sql = []
        if validation_filter < Validation.ALL and Validation.ACCEPTED in validation_filter:
            validation_filter_sql.append('valid = {}'.format("'accepted'"))
        if validation_filter < Validation.ALL and Validation.REJECTED in validation_filter:
            validation_filter_sql.append('valid = {}'.format("'rejected'"))
        if validation_filter < Validation.ALL and Validation.NOT_VALIDATED in validation_filter:
            validation_filter_sql.append('valid = {}'.format("'not_validated'"))
        if validation_filter < Validation.ALL and Validation.MIXED in validation_filter:
            validation_filter_sql.append('valid = {}'.format("'mixed'"))

        conditions = []
        if cluster_id:
            conditions.append(sql.SQL('cluster_id = {cluster_id}').format(cluster_id=sql.Literal(cluster_id)))
        if uri:
            conditions.append(sql.SQL('(source_uri = {uri} OR target_uri = {uri})').format(uri=sql.Literal(uri)))
        if len(validation_filter_sql) > 0:
            conditions.append(sql.SQL('(' + ' OR '.join(validation_filter_sql) + ')'))

        limit_offset_sql = get_pagination_sql(limit, offset)
        where_sql = sql.SQL('WHERE {}').format(sql.SQL(' AND ').join(conditions)) \
            if len(conditions) > 0 else sql.SQL('')

        values = None
        if include_props:
            properties = self.get_lens_spec_by_id(id).properties \
                if type == 'lens' else self.get_linkset_spec_by_id(id).properties
            targets = self.value_targets_for_properties(properties)
            if targets:
                joins = get_linkset_join_sql(view_name, where_sql, limit, offset)
                queries = get_property_values_queries(targets, joins=joins)
                values = get_property_values(queries, dict=True)

        with db_conn() as conn, conn.cursor(name=uuid4().hex) as cur:
            # TODO: Removed 'similarities' for now
            cur.execute(sql.SQL('SELECT links.source_uri, links.target_uri, link_order, '
                                '       similarity, cluster_id, valid '
                                'FROM {view_name} AS links '
                                '{where_sql} '
                                'ORDER BY sort_order ASC {limit_offset}').format(
                view_name=view_name,
                where_sql=where_sql,
                limit_offset=sql.SQL(limit_offset_sql)
            ))

            while True:
                links = cur.fetchmany(size=2000)
                if not links:
                    break

                for link in links:
                    yield {
                        'source': link[0],
                        'source_values': values[link[0]] if values and link[0] in values else None,
                        'target': link[1],
                        'target_values': values[link[1]] if values and link[1] in values else None,
                        'link_order': link[2],
                        'similarity': link[3] if link[3] else 1,
                        #'similarities': link[4] if link[4] else {},
                        'cluster_id': link[4],
                        'valid': link[5]
                    }

    def get_links_totals(self, id, type, cluster_id=None, uri=None):
        view_name = sql.Identifier(self.linkset_table_name(id)) \
            if type == 'linkset' else sql.Identifier(self.lens_table_name(id))

        conditions = []
        if cluster_id:
            conditions.append(sql.SQL('cluster_id = {cluster_id}').format(cluster_id=sql.Literal(cluster_id)))
        if uri:
            conditions.append(sql.SQL('(source_uri = {uri} OR target_uri = {uri})').format(uri=sql.Literal(uri)))

        where_sql = sql.SQL('WHERE {}').format(sql.SQL(' AND ').join(conditions)) \
            if len(conditions) > 0 else sql.SQL('')

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('SELECT valid, count(*) AS valid_count '
                                'FROM {view_name} AS links '
                                '{where_sql} '
                                'GROUP BY valid').format(
                view_name=view_name,
                where_sql=where_sql
            ))

            return {row[0]: row[1] for row in cur.fetchall()}

    def get_clusters(self, id, type, limit=None, offset=0, include_props=False):
        linkset_table = self.linkset_table_name(id) if type == 'linkset' else self.lens_table_name(id)
        limit_offset_sql = get_pagination_sql(limit, offset)
        nodes_sql = ', array_agg(DISTINCT nodes.uri) AS nodes_arr' if include_props else ''

        values = None
        if include_props:
            properties = self.get_lens_spec_by_id(id).properties if type == 'lens' \
                else self.get_linkset_spec_by_id(id).properties
            targets = self.value_targets_for_properties(properties)
            if targets:
                joins = get_linkset_cluster_join_sql(linkset_table, limit, offset)
                queries = get_property_values_queries(targets, joins=joins)
                values = get_property_values(queries, dict=True)

        with db_conn() as conn, conn.cursor(name=uuid4().hex) as cur:
            cur.execute("""
                 SELECT ls.cluster_id, COUNT(DISTINCT nodes.uri) AS size, COUNT(ls.*) / 2 AS links {}
                 FROM {} AS ls
                 CROSS JOIN LATERAL (VALUES (ls.source_uri), (ls.target_uri)) AS nodes(uri)
                 GROUP BY ls.cluster_id
                 ORDER BY size DESC, ls.cluster_id ASC
                 {}
             """.format(nodes_sql, linkset_table, limit_offset_sql))

            while True:
                clusters = cur.fetchmany(size=2000)
                if not clusters:
                    break

                for cluster in clusters:
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

    def cluster(self, id, type, cluster_id=None, uri=None):
        all_links = []
        strengths = {}
        nodes = []

        for link in self.get_links(id, type, cluster_id=cluster_id, uri=uri):
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
    def _value_targets(properties, downloaded_only=True):
        value_targets = []
        downloaded = Collection.download_status()['downloaded']

        for prop in properties:
            graph = prop['graph']
            new_graph_data = []

            for data_of_entity in prop['data']:
                entity_type = data_of_entity['entity_type']

                if not downloaded_only or Job._is_downloaded(downloaded, graph, entity_type):
                    new_properties = Job._properties(graph, data_of_entity['properties'], downloaded, downloaded_only)
                    if len(new_properties) > 0:
                        new_graph_data.append({'entity_type': entity_type, 'properties': new_properties})

            if len(new_graph_data) > 0:
                value_targets.append({'graph': graph, 'data': new_graph_data})

        return value_targets

    @staticmethod
    def _properties(graph, properties, downloaded=None, downloaded_only=True):
        downloaded = Collection.download_status()['downloaded'] if downloaded is None else downloaded

        new_properties = []
        for props in properties:
            props = [prop for prop in props if prop != '__value__' and prop != '']

            if len(props) > 0 and (not downloaded_only or len(props) == 1
                                   or all(Job._is_downloaded(downloaded, graph, entity) for entity in props[1::2])):
                new_properties.append(props)

        return new_properties

    @staticmethod
    def _is_downloaded(downloaded, dataset_id, collection_id):
        return any(download['dataset_id'] == dataset_id and download['collection_id'] == collection_id
                   for download in downloaded)
