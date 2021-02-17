from json import dumps
from uuid import uuid4
from enum import IntFlag

from psycopg2 import extras, sql
from psycopg2.extensions import AsIs

from ll.job.joins import Joins
from ll.job.transformer import transform
from ll.job.visualize import get_visualization
from ll.job.query_builder import QueryBuilder

from ll.elem.lens import Lens
from ll.elem.linkset import Linkset
from ll.elem.entity_type_selection import EntityTypeSelection

from ll.util.helpers import get_pagination_sql
from ll.util.config_db import db_conn, fetch_one, fetch_many


class Validation(IntFlag):
    ALL = 31
    ACCEPTED = 16
    REJECTED = 8
    NOT_SURE = 4
    NOT_VALIDATED = 2
    MIXED = 1

    @staticmethod
    def get(valid):
        validation_filter = 0
        for type in valid:
            if type == 'accepted':
                validation_filter |= Validation.ACCEPTED
            if type == 'rejected':
                validation_filter |= Validation.REJECTED
            if type == 'not_sure':
                validation_filter |= Validation.NOT_SURE
            if type == 'not_validated':
                validation_filter |= Validation.NOT_VALIDATED
            if type == 'mixed':
                validation_filter |= Validation.MIXED

        return validation_filter if validation_filter != 0 else Validation.ALL


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
                cur.execute(sql.SQL('DROP TABLE IF EXISTS linksets.{}')
                            .format(sql.Identifier(self.table_name(id))))

            if type == 'lens':
                cur.execute('DELETE FROM lenses WHERE job_id = %s AND spec_id = %s', (self.job_id, id))
                cur.execute(sql.SQL('DROP TABLE IF EXISTS lenses.{}')
                            .format(sql.Identifier(self.table_name(id))))

    def validate_link(self, id, type, source_uri, target_uri, valid):
        with db_conn() as conn, conn.cursor() as cur:
            if type == 'lens':
                lens = self.get_lens_spec_by_id(id)

                query = sql.SQL('UPDATE lenses.{} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                    .format(sql.Identifier(self.table_name(id)))
                cur.execute(query, (valid, source_uri, target_uri))

                for linkset in lens.linksets:
                    query = sql.SQL('UPDATE linksets.{} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                        .format(sql.Identifier(self.table_name(linkset.id)))
                    cur.execute(query, (valid, source_uri, target_uri))
            else:
                query = sql.SQL('UPDATE linksets.{} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                    .format(sql.Identifier(self.table_name(id)))
                cur.execute(query, (valid, source_uri, target_uri))

                for lens_spec in self.lens_specs:
                    if id in [linkset.id for linkset in lens_spec.linksets]:
                        validities_sql = sql.SQL(' UNION ALL ').join(
                            sql.Composed([
                                sql.SQL('SELECT valid '
                                        'FROM linksets.{table} '
                                        'WHERE source_uri = {source_uri} AND target_uri = {target_uri}').format(
                                    table=sql.Identifier(self.table_name(linkset)),
                                    source_uri=sql.Literal(source_uri), target_uri=sql.Literal(target_uri)
                                ) for linkset in lens_spec.linksets if linkset.id != id
                            ])
                        )

                        cur.execute(validities_sql)
                        validities = [result[0] for result in cur.fetchall()]
                        valid_lens = 'mixed' if validities and valid not in validities else valid

                        query = sql.SQL('UPDATE lenses.{} SET valid = %s WHERE source_uri = %s AND target_uri = %s') \
                            .format(sql.Identifier(self.table_name(lens_spec.id)))
                        cur.execute(query, (valid_lens, source_uri, target_uri))

    def schema_name(self, id):
        return 'job_' + self.job_id + '_' + str(id)

    def table_name(self, id):
        return self.job_id + '_' + str(id)

    def spec_lens_uses(self, id, type):
        return [lens_spec.id for lens_spec in self.lens_specs
                if (type == 'linkset' and id in lens_spec.linksets)
                or (type == 'lens' and id in lens_spec.lenses)]

    def linkset_has_queued_table_data(self, linkset_id=None):
        linkset = self.get_linkset_spec_by_id(linkset_id)
        for entity_type_selection in linkset.entity_type_selections:
            for property in entity_type_selection.properties_for_matching(linkset):
                if not property.is_downloaded:
                    return True

        return False

    def get_entity_type_selection_by_id(self, id):
        for entity_type_selection in self.entity_type_selections:
            if entity_type_selection.id == id or entity_type_selection.alias == id:
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

    def get_spec_by_id(self, id, type):
        return self.get_linkset_spec_by_id(id) if type == 'linkset' else self.get_lens_spec_by_id(id)

    def get_entity_type_selection_sample(self, id, invert=False, limit=None, offset=0):
        entity_type_selection = self.get_entity_type_selection_by_id(id)
        if not entity_type_selection:
            return []

        filter_properties = entity_type_selection.filter_properties
        if any(not prop.is_downloaded for prop in filter_properties):
            return []

        selection_properties = entity_type_selection.properties

        query_builder = QueryBuilder()
        query_builder.add_query(
            entity_type_selection.dataset_id, entity_type_selection.collection_id, entity_type_selection.alias,
            entity_type_selection.table_name, filter_properties, selection_properties,
            condition=entity_type_selection.filters_sql, invert=invert, limit=limit, offset=offset)

        return query_builder.run_queries(dict=False)

    def get_entity_type_selection_sample_total(self, id):
        entity_type_selection = self.get_entity_type_selection_by_id(id)
        if not entity_type_selection:
            return {'total': 0}

        filter_properties = entity_type_selection.filter_properties
        if any(not prop.is_downloaded for prop in filter_properties):
            return {'total': 0}

        joins = Joins()
        joins.set_joins_for_props(filter_properties)

        return fetch_one(sql.SQL('''
            SELECT count({resource}.uri) AS total
            FROM timbuctoo.{table_name} AS {resource} 
            {joins}
            {condition}
        ''').format(
            resource=sql.Identifier(entity_type_selection.alias),
            table_name=sql.Identifier(entity_type_selection.table_name),
            joins=joins.sql,
            condition=entity_type_selection.filters_sql
        ), dict=True)

    def get_links(self, id, type, validation_filter=Validation.ALL, cluster_id=None, uri=None,
                  limit=None, offset=0, include_props=False, single_value=False):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)

        validation_filter_sql = []
        if validation_filter < Validation.ALL:
            if Validation.ACCEPTED in validation_filter:
                validation_filter_sql.append('valid = {}'.format("'accepted'"))
            if Validation.REJECTED in validation_filter:
                validation_filter_sql.append('valid = {}'.format("'rejected'"))
            if Validation.NOT_SURE in validation_filter:
                validation_filter_sql.append('valid = {}'.format("'not_sure'"))
            if Validation.NOT_VALIDATED in validation_filter:
                validation_filter_sql.append('valid = {}'.format("'not_validated'"))
            if Validation.MIXED in validation_filter:
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

        sim_fields_sql = sql.SQL('')
        if spec.similarity_fields:
            sim_fields_sql = sql.SQL('CROSS JOIN LATERAL jsonb_to_record(similarity) \nAS sim({})') \
                .format(sql.SQL(', ').join([sql.SQL('{} numeric[]').format(sql.Identifier(sim_field))
                                            for sim_field in spec.similarity_fields]))

        values = None
        if include_props:
            query_builder = QueryBuilder()

            for ets in spec.entity_type_selections:
                query_builder.add_linkset_query(
                    schema, self.table_name(id), ets.dataset_id, ets.collection_id, ets.alias, ets.table_name,
                    ets.filter_properties, ets.properties_for_spec_selection(spec),
                    condition=where_sql, limit=limit, offset=offset, single_value=single_value)

            values = query_builder.run_queries_single_value() if single_value else query_builder.run_queries()

        with db_conn() as conn, conn.cursor(name=uuid4().hex) as cur:
            cur.execute(sql.SQL(
                'SELECT links.source_uri, links.source_collections, '
                '       links.target_uri, links.target_collections, '
                '       link_order, cluster_id, valid, '
                '       coalesce({sim_logic_ops_sql}, 1) AS similarity '
                'FROM {schema}.{view_name} AS links '
                '{sim_fields_sql} '
                '{where_sql} '
                'ORDER BY sort_order ASC {limit_offset}'
            ).format(
                schema=sql.Identifier(schema),
                view_name=sql.Identifier(self.table_name(id)),
                sim_fields_sql=sim_fields_sql,
                sim_logic_ops_sql=spec.similarity_logic_ops_sql,
                where_sql=where_sql,
                limit_offset=sql.SQL(limit_offset_sql)
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

    def get_links_totals(self, id, type, cluster_id=None, uri=None):
        conditions = []
        if cluster_id:
            conditions.append(sql.SQL('cluster_id = {cluster_id}').format(cluster_id=sql.Literal(cluster_id)))
        if uri:
            conditions.append(sql.SQL('(source_uri = {uri} OR target_uri = {uri})').format(uri=sql.Literal(uri)))

        where_sql = sql.SQL('WHERE {}').format(sql.SQL(' AND ').join(conditions)) \
            if len(conditions) > 0 else sql.SQL('')

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('SELECT valid, count(*) AS valid_count '
                                'FROM {schema}.{view_name} AS links '
                                '{where_sql} '
                                'GROUP BY valid').format(
                schema=sql.Identifier('lenses' if type == 'lens' else 'linksets'),
                view_name=sql.Identifier(self.table_name(id)),
                where_sql=where_sql
            ))

            return {row[0]: row[1] for row in cur.fetchall()}

    def get_clusters(self, id, type, limit=None, offset=0, include_props=False):
        spec = self.get_spec_by_id(id, type)
        limit_offset_sql = get_pagination_sql(limit, offset)
        nodes_sql = ', array_agg(DISTINCT nodes.uri) AS nodes_arr' if include_props else ''

        values = None
        if include_props:
            query_builder = QueryBuilder()

            for ets in spec.entity_type_selections:
                query_builder.add_cluster_query(
                    self.table_name(id), ets.dataset_id, ets.collection_id, ets.alias, ets.table_name,
                    ets.filter_properties, ets.properties_for_spec_selection(spec), limit=limit, offset=offset)

            values = query_builder.run_queries()

        with db_conn() as conn, conn.cursor(name=uuid4().hex) as cur:
            cur.execute("""
                 SELECT ls.cluster_id, count(DISTINCT nodes.uri) AS size, count(ls.*) / 2 AS links {}
                 FROM {}."{}" AS ls
                 CROSS JOIN LATERAL (VALUES (ls.source_uri), (ls.target_uri)) AS nodes(uri)
                 GROUP BY ls.cluster_id
                 ORDER BY size DESC, ls.cluster_id 
                 {}
             """.format(nodes_sql, ('lenses' if type == 'lens' else 'linksets'), self.table_name(id), limit_offset_sql))

            for cluster in fetch_many(cur):
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

    def visualize(self, id, type, cluster_id):
        return get_visualization(self, id, type, cluster_id, include_compact=True)
