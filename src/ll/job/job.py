from json import dumps
from uuid import uuid4

from psycopg2 import extras, sql
from psycopg2.extensions import AsIs

from ll.job.joins import Joins
from ll.job.transformer import transform
from ll.job.validation import Validation
from ll.job.links_filter import LinksFilter
from ll.job.query_builder import QueryBuilder
from ll.job.visualize import get_visualization
from ll.job.linkset_builder import LinksetBuilder

from ll.elem.view import View
from ll.elem.lens import Lens
from ll.elem.linkset import Linkset
from ll.elem.entity_type_selection import EntityTypeSelection

from ll.util.helpers import get_sql_empty
from ll.util.config_db import db_conn, fetch_one


class Job:
    def __init__(self, job_id):
        self.job_id = job_id
        self._data = None
        self._entity_type_selections = None
        self._linkset_specs = None
        self._lens_specs = None
        self._views = None

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
    def views(self):
        if not self._views:
            self._views = list(map(lambda view: View(view, self), self.data['views']))

        return self._views

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

    def spec(self, id, type):
        return self.linkset(id) if type == 'linkset' else self.lens(id)

    def clustering(self, id, type):
        return fetch_one('SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = %s',
                         (self.job_id, id, type), dict=True)

    def create_job(self, title, description, link):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jobs (job_id, job_title, job_description, job_link) 
                VALUES (%s, %s, %s, %s)
            """, (self.job_id, title, description, link))

    def update_data(self, data):
        entity_type_selections_form_data = \
            data['entity_type_selections'] if 'entity_type_selections' in data \
                else self.data['entity_type_selections_form_data']
        linkset_specs_form_data = \
            data['linkset_specs'] if 'linkset_specs' in data else self.data['linkset_specs_form_data']
        lens_specs_form_data = data['lens_specs'] if 'lens_specs' in data else self.data['lens_specs_form_data']
        views_form_data = data['views'] if 'views' in data else self.data['views_form_data']

        data_updated = {
            'job_title': data['job_title'].strip() \
                if 'job_title' in data else self.data['job_title'],
            'job_description': data['job_description'].strip() \
                if 'job_description' in data else self.data['job_description'],
            'job_link': data['job_link'].strip() \
                if 'job_link' in data and data['job_link']
                   and data['job_link'].strip() != '' else self.data['job_link'],
            'entity_type_selections_form_data': dumps(entity_type_selections_form_data),
            'linkset_specs_form_data': dumps(linkset_specs_form_data),
            'lens_specs_form_data': dumps(lens_specs_form_data),
            'views_form_data': dumps(views_form_data)
        }

        (entity_type_selections, linkset_specs, lens_specs, views, errors) = \
            transform(entity_type_selections_form_data, linkset_specs_form_data, lens_specs_form_data, views_form_data)

        data_updated['entity_type_selections'] = dumps(entity_type_selections)
        data_updated['linkset_specs'] = dumps(linkset_specs)
        data_updated['lens_specs'] = dumps(lens_specs)
        data_updated['views'] = dumps(views)

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE jobs SET (%s) = ROW %s, updated_at = now() WHERE job_id = %s'), (
                AsIs(', '.join(data_updated.keys())),
                tuple(data_updated.values()),
                self.job_id
            ))

        return entity_type_selections, linkset_specs, lens_specs, views, errors

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

    def run_clustering(self, id, type, clustering_type='default'):
        clustering = self.clustering(id, type)

        with db_conn() as conn, conn.cursor() as cur:
            if clustering:
                cur.execute(sql.SQL("""
                    UPDATE clusterings 
                    SET status = %s, kill = false, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND spec_id = %s AND spec_type = %s
                """), ('waiting', self.job_id, id, type))
            else:
                cur.execute(sql.SQL("""
                    INSERT INTO clusterings (job_id, spec_id, spec_type, clustering_type, status, kill, requested_at) 
                    VALUES (%s, %s, %s, %s, %s, false, now())
                """), (self.job_id, id, type, clustering_type, 'waiting'))

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

    def validate_link(self, id, type, valid, validation_filter=Validation.ALL, cluster_id=None, link=(None, None)):
        links_filter = LinksFilter()
        links_filter.filter_on_validation(validation_filter)
        links_filter.filter_on_cluster(cluster_id)
        links_filter.filter_on_link(link[0], link[1])

        with db_conn() as conn, conn.cursor() as cur:
            if type == 'lens':
                temp_table_id = uuid4().hex
                lens = self.get_lens_spec_by_id(id)

                cur.execute(sql.SQL('''
                    CREATE TEMPORARY TABLE {table_name} ON COMMIT DROP AS 
                    SELECT source_uri, target_uri
                    FROM lenses.{lens_table}
                    {filter}
                ''').format(
                    table_name=sql.Identifier(temp_table_id),
                    lens_table=sql.Identifier(self.table_name(id)),
                    filter=links_filter.sql()
                ))

                # If links in a lens are updated, then also update the same links from the originating linksets/lenses
                update_sqls = [
                    sql.SQL('''
                        UPDATE {schema}.{table_name} AS trg
                        SET valid = {valid} 
                        FROM {selection_table_name} AS sel
                        WHERE trg.source_uri = sel.source_uri 
                        AND trg.target_uri = sel.target_uri;
                    ''').format(
                        schema=sql.Identifier(schema),
                        table_name=sql.Identifier(self.table_name(spec.id)),
                        valid=sql.Literal(valid),
                        selection_table_name=sql.Identifier(temp_table_id)
                    )
                    for (schema, selection) in [('linksets', lens.linksets), ('lenses', lens.lenses)]
                    for spec in selection
                ]

                update_sqls.append(sql.SQL('''
                    UPDATE lenses.{table_name} AS lens 
                    SET valid = {valid}
                    FROM {selection_table_name} AS sel
                    WHERE lens.source_uri = sel.source_uri
                    AND lens.target_uri = sel.target_uri;
                ''').format(
                    table_name=sql.Identifier(self.table_name(id)),
                    valid=sql.Literal(valid),
                    selection_table_name=sql.Identifier(temp_table_id)
                ))

                to_exec = sql.Composed(update_sqls)

                cur.execute(to_exec)
            else:
                query = sql.SQL('UPDATE linksets.{} SET valid = %s {}') \
                    .format(sql.Identifier(self.table_name(id)), links_filter.sql())
                cur.execute(query, (valid,))

                # If links in a linkset are updated, then also update the same links from lenses based on this linkset
                # However, if the same link yield different validations among the linksets, then use 'mixed'
                for lens_spec in self.lens_specs:
                    if id in [linkset.id for linkset in lens_spec.linksets]:
                        validities_sql = sql.SQL(' UNION ALL ').join(
                            sql.SQL('''
                                SELECT ls.source_uri, ls.target_uri, ls.valid 
                                FROM linksets.{} AS ls
                                INNER JOIN links_selection AS sel
                                ON ls.source_uri = sel.source_uri
                                AND ls.target_uri = sel.target_uri
                            ''').format(sql.Identifier(self.table_name(linkset.id)))
                            for linkset in lens_spec.linksets
                        )

                        cur.execute(sql.SQL('''
                            WITH links_selection AS (
                                SELECT source_uri, target_uri
                                FROM linksets.{linkset_table}
                                {filter} 
                            )

                            UPDATE lenses.{lens_table} AS lens
                            SET valid = linkset.valid
                            FROM (
                                SELECT source_uri, target_uri, 
                                       CASE WHEN count(DISTINCT valid) > 1 
                                            THEN 'mixed'::link_validity 
                                            ELSE min(valid) END AS valid
                                FROM ({validaties_select}) AS x
                                GROUP BY source_uri, target_uri
                            ) AS linkset
                            WHERE lens.source_uri = linkset.source_uri 
                            AND lens.target_uri = linkset.target_uri 
                        ''').format(
                            linkset_table=sql.Identifier(self.table_name(id)),
                            filter=links_filter.sql(),
                            lens_table=sql.Identifier(self.table_name(lens_spec.id)),
                            validaties_select=validities_sql,
                        ))

    def schema_name(self, id):
        return 'job_' + self.job_id + '_' + str(id)

    def table_name(self, id):
        return self.job_id + '_' + str(id)

    def spec_lens_uses(self, id, type):
        return [lens_spec.id for lens_spec in self.lens_specs
                if (type == 'linkset' and id in lens_spec.linksets)
                or (type == 'lens' and id in lens_spec.lenses)]

    def linkset_has_queued_table_data(self, linkset_id):
        linkset = self.get_linkset_spec_by_id(linkset_id)
        return any(not property.is_downloaded
                   for entity_type_selection in linkset.entity_type_selections
                   for property in entity_type_selection.properties_for_matching(linkset))

    def get_entity_type_selection_by_id(self, id):
        return next((ets for ets in self.entity_type_selections if ets.id == id or ets.alias == id), None)

    def get_linkset_spec_by_id(self, id):
        return next((linkset_spec for linkset_spec in self.linkset_specs if linkset_spec.id == id), None)

    def get_lens_spec_by_id(self, id):
        return next((lens_spec for lens_spec in self.lens_specs if lens_spec.id == id), None)

    def get_view_by_id(self, id, type):
        return next((view for view in self.views if view.id == id and view.type == type), None)

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
            entity_type_selection.graphql_endpoint, entity_type_selection.dataset_id,
            entity_type_selection.collection_id, entity_type_selection.alias,
            entity_type_selection.collection.table_name, filter_properties, selection_properties,
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

        where_sql = entity_type_selection.filters_sql
        if where_sql:
            where_sql = sql.SQL('WHERE {}').format(where_sql)

        return fetch_one(sql.SQL('''
            SELECT count({resource}.uri) AS total
            FROM timbuctoo.{table_name} AS {resource} 
            {joins}
            {condition}
        ''').format(
            resource=sql.Identifier(entity_type_selection.alias),
            table_name=sql.Identifier(entity_type_selection.collection.table_name),
            joins=joins.sql,
            condition=get_sql_empty(where_sql)
        ), dict=True)

    def get_links(self, id, type, validation_filter=Validation.ALL, cluster_id=None, uri=None,
                  min_strength=0, max_strength=1, limit=None, offset=0, with_properties='none'):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter()
        links_filter.filter_on_validation(validation_filter)
        links_filter.filter_on_cluster(cluster_id)
        links_filter.filter_on_uri(uri)
        links_filter.filter_on_min_max_strength(min_strength, max_strength)

        linkset_builder = LinksetBuilder(schema, self.table_name(id), spec, view)
        linkset_builder.apply_links_filter(links_filter)
        linkset_builder.apply_paging(limit, offset)

        return linkset_builder.get_links_generator(with_properties)

    def get_links_totals(self, id, type, cluster_id=None, uri=None, min_strength=0, max_strength=1):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter()
        links_filter.filter_on_cluster(cluster_id)
        links_filter.filter_on_uri(uri)
        links_filter.filter_on_min_max_strength(min_strength, max_strength)

        linkset_builder = LinksetBuilder(schema, self.table_name(id), spec, view)
        linkset_builder.apply_links_filter(links_filter)

        return linkset_builder.get_total_links()

    def get_clusters(self, id, type, limit=None, offset=0, with_properties='none'):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        linkset_builder = LinksetBuilder(schema, self.table_name(id), spec, view)
        linkset_builder.apply_paging(limit, offset)

        return linkset_builder.get_clusters_generator(with_properties)

    def visualize(self, id, type, cluster_id):
        return get_visualization(self, id, type, cluster_id, include_compact=True)
