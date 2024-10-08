from json import dumps
from inspect import cleandoc
from psycopg import sql, rows

from lenticularlens.job.joins import Joins
from lenticularlens.job.transformer import transform
from lenticularlens.job.validation import Validation
from lenticularlens.job.links_filter import LinksFilter
from lenticularlens.job.query_builder import QueryBuilder
from lenticularlens.job.visualize import get_visualization
from lenticularlens.job.clusters_filter import ClustersFilter
from lenticularlens.job.linkset_builder import LinksetBuilder
from lenticularlens.job.linkset_validator import LinksetValidator

from lenticularlens.elem.view import View
from lenticularlens.elem.lens import Lens
from lenticularlens.elem.linkset import Linkset
from lenticularlens.elem.entity_type_selection import EntityTypeSelection

from lenticularlens.util.helpers import get_sql_empty
from lenticularlens.util.config_db import conn_pool


class Job:
    def __init__(self, job_id, data=None):
        self.job_id = job_id
        self._data = data
        self._entity_type_selections = None
        self._linkset_specs = None
        self._lens_specs = None
        self._views = None

    @property
    def data(self):
        if not self._data:
            with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
                self._data = cur.execute('''
                    SELECT *, (
                        SELECT json_object(array_agg(user_id), array_agg(role)::text[]) 
                        FROM job_users
                        WHERE job_id = %s
                    ) AS users
                    FROM jobs
                    WHERE job_id = %s
                ''', (self.job_id, self.job_id,)).fetchone()

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
            raw_linkset_specs = self.data['linkset_specs'] if self.data['linkset_specs'] else []
            self._linkset_specs = list(map(lambda linkset_spec: Linkset(linkset_spec, self), raw_linkset_specs))

        return self._linkset_specs

    @property
    def lens_specs(self):
        if not self._lens_specs:
            raw_lens_specs = self.data['lens_specs'] if self.data['lens_specs'] else []
            self._lens_specs = list(map(lambda lens_spec: Lens(lens_spec, self), raw_lens_specs))

        return self._lens_specs

    @property
    def views(self):
        if not self._views:
            self._views = list(map(lambda view: View(view, self), self.data['views']))

        return self._views

    @property
    def linksets(self):
        specs = self.linkset_specs
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT * FROM linksets WHERE job_id = %s', (self.job_id,))
            linksets = cur.fetchall()

        return self._include_prefix_mappings_in_results(linksets, specs)

    @property
    def lenses(self):
        specs = self.lens_specs
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT * FROM lenses WHERE job_id = %s', (self.job_id,))
            lenses = cur.fetchall()

        return self._include_prefix_mappings_in_results(lenses, specs)

    @property
    def clusterings(self):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT * FROM clusterings WHERE job_id = %s', (self.job_id,))
            return cur.fetchall()

    def linkset(self, id):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            return cur.execute('SELECT * FROM linksets WHERE job_id = %s AND spec_id = %s',
                               (self.job_id, id)).fetchone()

    def lens(self, id):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            return cur.execute('SELECT * FROM lenses WHERE job_id = %s AND spec_id = %s',
                               (self.job_id, id)).fetchone()

    def spec(self, id, type):
        return self.linkset(id) if type == 'linkset' else self.lens(id)

    def clustering(self, id, type):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            return cur.execute('SELECT * FROM clusterings WHERE job_id = %s AND spec_id = %s AND spec_type = %s',
                               (self.job_id, id, type)).fetchone()

    def create_job(self, title, description, link):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jobs (job_id, job_title, job_description, job_link) 
                VALUES (%s, %s, %s, %s)
            """, (self.job_id, title, description, link))

    def update_data(self, data):
        entity_type_selections_form_data = data['entity_type_selections'] \
            if 'entity_type_selections' in data \
               and data['entity_type_selections'] is not None else self.data['entity_type_selections_form_data'] \
            if 'entity_type_selections_form_data' in self.data \
               and self.data['entity_type_selections_form_data'] is not None else []
        linkset_specs_form_data = data['linkset_specs'] \
            if 'linkset_specs' in data \
               and data['linkset_specs'] is not None else self.data['linkset_specs_form_data'] \
            if 'linkset_specs_form_data' in self.data \
               and self.data['linkset_specs_form_data'] is not None else []
        lens_specs_form_data = data['lens_specs'] \
            if 'lens_specs' in data \
               and data['lens_specs'] is not None else self.data['lens_specs_form_data'] \
            if 'lens_specs_form_data' in self.data \
               and self.data['lens_specs_form_data'] is not None else []
        views_form_data = data['views'] \
            if 'views' in data \
               and data['views'] is not None else self.data['views_form_data'] \
            if 'views_form_data' in self.data \
               and self.data['views_form_data'] is not None else []

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

        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE jobs SET ({}) = ROW ({}), updated_at = now() WHERE job_id = {}').format(
                sql.SQL(', ').join([sql.Identifier(column) for column in data_updated.keys()]),
                sql.SQL(', ').join([sql.Literal(column) for column in data_updated.values()]),
                sql.Literal(self.job_id)
            ))

        return entity_type_selections, linkset_specs, lens_specs, views, errors

    def update_linkset(self, id, data):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE linksets SET ({}) = ROW ({}) WHERE job_id = {} AND spec_id = {}').format(
                sql.SQL(', ').join([sql.Identifier(column) for column in data.keys()]),
                sql.SQL(', ').join([sql.Literal(column) for column in data.values()]),
                sql.Literal(self.job_id),
                sql.Literal(id)
            ))

    def update_lens(self, id, data):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE lenses SET ({}) = ROW ({}) WHERE job_id = {} AND spec_id = {}').format(
                sql.SQL(', ').join([sql.Identifier(column) for column in data.keys()]),
                sql.SQL(', ').join([sql.Literal(column) for column in data.values()]),
                sql.Literal(self.job_id),
                sql.Literal(id)
            ))

    def update_clustering(self, id, type, data):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL('UPDATE clusterings SET ({}) = ROW ({}) '
                                'WHERE job_id = {} AND spec_id = {} AND spec_type = {}').format(
                sql.SQL(', ').join([sql.Identifier(column) for column in data.keys()]),
                sql.SQL(', ').join([sql.Literal(column) for column in data.values()]),
                sql.Literal(self.job_id),
                sql.Literal(id),
                sql.Literal(type)
            ))

    def run_linkset(self, id, restart=False):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            if restart:
                cur.execute("DELETE FROM linksets WHERE job_id = %s AND spec_id = %s", (self.job_id, id))
                cur.execute(("DELETE FROM clusterings "
                             "WHERE job_id = %s AND spec_id = %s AND spec_type = 'linkset'"), (self.job_id, id))

            cur.execute("INSERT INTO linksets (job_id, spec_id, status, kill, requested_at) "
                        "VALUES (%s, %s, %s, false, now())", (self.job_id, id, 'waiting'))

    def run_lens(self, id, restart=False):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            if restart:
                cur.execute("DELETE FROM lenses WHERE job_id = %s AND spec_id = %s", (self.job_id, id))
                cur.execute("DELETE FROM clusterings "
                            "WHERE job_id = %s AND spec_id = %s AND spec_type = 'lens'", (self.job_id, id))

            cur.execute("INSERT INTO lenses (job_id, spec_id, status, kill, requested_at) "
                        "VALUES (%s, %s, %s, false, now())", (self.job_id, id, 'waiting'))

    def run_clustering(self, id, type, clustering_type='default'):
        clustering = self.clustering(id, type)

        with conn_pool.connection() as conn, conn.cursor() as cur:
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
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute('UPDATE linksets SET kill = true WHERE job_id = %s AND spec_id = %s',
                        (self.job_id, id))

    def kill_lens(self, id):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute('UPDATE lenses SET kill = true WHERE job_id = %s AND spec_id = %s',
                        (self.job_id, id))

    def kill_clustering(self, id, type):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute('UPDATE clusterings SET kill = true WHERE job_id = %s AND spec_id = %s AND spec_type = %s',
                        (self.job_id, id, type))

    def delete(self):
        for linkset_spec in self.linkset_specs:
            self.delete_spec(linkset_spec.id, 'linkset')

        for lens_spec in self.lens_specs:
            self.delete_spec(lens_spec.id, 'lens')

        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute('INSERT INTO jobs_deleted '
                        'SELECT * FROM jobs WHERE job_id = %s '
                        'ON CONFLICT (job_id) DO NOTHING', (self.job_id,))
            cur.execute('DELETE FROM jobs WHERE job_id = %s', (self.job_id,))

    def delete_spec(self, id, type):
        with conn_pool.connection() as conn, conn.cursor() as cur:
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

    def validate_link(self, id, type, valid, validation_filter=Validation.ALL, cluster_ids=None, uris=None,
                      min_strength=0, max_strength=1, link=(None, None), with_view_filters=False):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter.create(validation_filter=validation_filter, cluster_ids=cluster_ids, uris=uris,
                                          min_strength=min_strength, max_strength=max_strength, link=link)
        linkset_builder = LinksetBuilder.create(schema, self.table_name(id), spec, view, links_filter=links_filter)

        linkset_validator = LinksetValidator(self, type, spec, linkset_builder, with_view_filters)
        linkset_validator.validate(valid)

    def motivate_link(self, id, type, motivation, validation_filter=Validation.ALL, cluster_ids=None, uris=None,
                      min_strength=0, max_strength=1, link=(None, None), with_view_filters=False):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter.create(validation_filter=validation_filter, cluster_ids=cluster_ids, uris=uris,
                                          min_strength=min_strength, max_strength=max_strength, link=link)
        linkset_builder = LinksetBuilder.create(schema, self.table_name(id), spec, view, links_filter=links_filter)

        linkset_validator = LinksetValidator(self, type, spec, linkset_builder, with_view_filters)
        linkset_validator.add_motivation(motivation)

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
                   for entity_type_selection in linkset.all_entity_type_selections
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

    def get_entity_type_selection_sample(self, id, invert=False, limit=None, offset=0, sql_only=False):
        entity_type_selection = self.get_entity_type_selection_by_id(id)
        if not entity_type_selection or not entity_type_selection.collection.is_downloaded:
            return []

        filter_properties = entity_type_selection.filter_properties
        if any(not prop.is_downloaded for prop in filter_properties):
            return []

        selection_properties = entity_type_selection.properties

        if sql_only:
            return QueryBuilder.create_query(
                entity_type_selection.alias, entity_type_selection.collection.table_name, filter_properties,
                selection_properties, condition=entity_type_selection.filters_sql,
                invert=invert, limit=limit, offset=offset)

        query_builder = QueryBuilder()
        query_builder.add_query(
            entity_type_selection.graphql_endpoint, entity_type_selection.dataset_id,
            entity_type_selection.collection_id, entity_type_selection.alias,
            entity_type_selection.collection.table_name, filter_properties, selection_properties,
            condition=entity_type_selection.filters_sql, invert=invert, limit=limit, offset=offset)

        return query_builder.run_queries(dict=False)

    def get_entity_type_selection_sample_total(self, id, sql_only=False):
        entity_type_selection = self.get_entity_type_selection_by_id(id)
        if not entity_type_selection or not entity_type_selection.collection.is_downloaded:
            return {'total': 0}

        filter_properties = entity_type_selection.filter_properties
        if any(not prop.is_downloaded for prop in filter_properties):
            return {'total': 0}

        joins = Joins()
        joins.set_joins_for_props(filter_properties)

        where_sql = entity_type_selection.filters_sql
        if where_sql:
            where_sql = sql.SQL('WHERE {}').format(where_sql)

        query_sql = sql.SQL(cleandoc('''
            SELECT count(DISTINCT {resource}.uri) AS total
            FROM timbuctoo.{table_name} AS {resource} 
            {joins}
            {condition}
        ''')).format(
            resource=sql.Identifier(entity_type_selection.alias),
            table_name=sql.Identifier(entity_type_selection.collection.table_name),
            joins=joins.sql,
            condition=get_sql_empty(where_sql)
        )

        if sql_only:
            return query_sql

        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            return cur.execute(query_sql).fetchone()

    def get_links(self, id, type, validation_filter=Validation.ALL, cluster_ids=None, uris=None,
                  min_strength=0, max_strength=1, sort=None, limit=None, offset=0,
                  with_view_properties='none', with_view_filters=False, sql_only=False):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter.create(validation_filter=validation_filter, cluster_ids=cluster_ids, uris=uris,
                                          min_strength=min_strength, max_strength=max_strength)
        linkset_builder = LinksetBuilder.create(schema, self.table_name(id), spec, view,
                                                links_filter=links_filter, sort=sort, limit=limit, offset=offset)

        if sql_only:
            return linkset_builder.get_links_generator_sql(with_view_properties, with_view_filters)

        return linkset_builder.get_links_generator(with_view_properties, with_view_filters)

    def get_links_totals(self, id, type, cluster_ids=None, uris=None, min_strength=0, max_strength=1,
                         with_view_filters=False, sql_only=False):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter.create(cluster_ids=cluster_ids, uris=uris,
                                          min_strength=min_strength, max_strength=max_strength)
        linkset_builder = LinksetBuilder.create(schema, self.table_name(id), spec, view, links_filter=links_filter)

        if sql_only:
            return linkset_builder.get_total_links_sql(with_view_filters)

        return linkset_builder.get_total_links(with_view_filters)

    def get_clusters(self, id, type, cluster_ids=None, uris=None, min_strength=0, max_strength=1,
                     min_size=None, max_size=None, min_count=None, max_count=None, sort=None,
                     limit=None, offset=0, with_view_properties='none',
                     with_view_filters=False, include_nodes=False, sql_only=False):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter.create(cluster_ids=cluster_ids, uris=uris,
                                          min_strength=min_strength, max_strength=max_strength)
        clusters_filter = ClustersFilter.create(min_size=min_size, max_size=max_size,
                                                min_count=min_count, max_count=max_count)
        linkset_builder = LinksetBuilder.create(schema, self.table_name(id), spec, view, links_filter=links_filter,
                                                clusters_filter=clusters_filter, cluster_sort=sort,
                                                limit=limit, offset=offset)

        if sql_only:
            return linkset_builder.get_clusters_generator_sql(with_view_properties, with_view_filters, include_nodes)

        return linkset_builder.get_clusters_generator(with_view_properties, with_view_filters, include_nodes)

    def get_clusters_totals(self, id, type, cluster_ids=None, uris=None, min_strength=0, max_strength=1,
                            min_size=0, max_size=None, min_count=None, max_count=None,
                            with_view_filters=False, sql_only=False):
        schema = 'lenses' if type == 'lens' else 'linksets'
        spec = self.get_spec_by_id(id, type)
        view = self.get_view_by_id(id, type)

        links_filter = LinksFilter.create(cluster_ids=cluster_ids, uris=uris,
                                          min_strength=min_strength, max_strength=max_strength)
        clusters_filter = ClustersFilter.create(min_size=min_size, max_size=max_size,
                                                min_count=min_count, max_count=max_count)
        linkset_builder = LinksetBuilder.create(schema, self.table_name(id), spec, view,
                                                links_filter=links_filter, clusters_filter=clusters_filter)

        if sql_only:
            return linkset_builder.get_total_clusters_sql(with_view_filters)

        return linkset_builder.get_total_clusters(with_view_filters)

    def visualize(self, id, type, cluster_id):
        return get_visualization(self, id, type, cluster_id, include_compact=True)

    @staticmethod
    def _include_prefix_mappings_in_results(results, specs):
        try:
            return [{
                **result,
                **{
                    'prefix_mappings': {
                        prefix: uri
                        for (ets, prop) in next(x for x in specs if x.id == result['spec_id']).all_props
                        for prefix, uri in prop.prefix_mappings.items()
                    },
                    'uri_prefix_mappings': {
                        prefix: uri
                        for ets in next(x for x in specs if x.id == result['spec_id']).all_entity_type_selections
                        for prefix, uri in ets.collection.uri_prefix_mappings.items()
                    },
                    'dynamic_uri_prefix_mappings': {
                        prefix: uri
                        for ets in next(x for x in specs if x.id == result['spec_id']).all_entity_type_selections
                        for prefix, uri in ets.collection.dynamic_uri_prefix_mappings.items()
                    }
                }
            } for result in results]
        except:
            return [{
                **result,
                **{
                    'prefix_mappings': {},
                    'uri_prefix_mappings': {},
                    'dynamic_uri_prefix_mappings': {}
                }
            } for result in results]
