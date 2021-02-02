from psycopg2 import sql as psycopg2_sql

from ll.data.collection import Collection
from ll.data.property_field import PropertyField

from ll.util.hasher import hash_string_min
from ll.job.filter_function import FilterFunction


class EntityTypeSelection:
    def __init__(self, data, job):
        self._data = data
        self._job = job

        graphql = data['dataset']['timbuctoo_graphql']
        hsid = data['dataset']['timbuctoo_hsid'] if not data['dataset']['published'] else None
        dataset_id = self._data['dataset']['dataset_id']
        collection_id = self._data['dataset']['collection_id']

        self.collection = Collection(graphql, hsid, dataset_id, collection_id)
        self.table_name = self.collection.table_name
        self.columns = self.collection.columns

    @property
    def id(self):
        return self._data['id']

    @property
    def alias(self):
        return hash_string_min(self.id)

    @property
    def dataset_id(self):
        return self._data['dataset']['dataset_id']

    @property
    def collection_id(self):
        return self._data['dataset']['collection_id']

    @property
    def dataset_label(self):
        return self.collection.table_data

    @property
    def limit(self):
        return self._data.get('limit', -1)

    @property
    def properties(self):
        return [PropertyField(property, self) for property in self._data['properties']]

    @property
    def filter_properties(self):
        return [filter.property_field for filter in self.filters]

    @property
    def filters(self):
        return self._r_get_filters(self._data['filter']) if 'filter' in self._data and self._data['filter'] else []

    @property
    def filter_sql(self):
        return self._r_get_filter_sql(self._data['filter']) \
            if 'filter' in self._data and self._data['filter'] else psycopg2_sql.SQL('')

    @property
    def where_sql(self):
        where_sql = self.filter_sql
        if where_sql != psycopg2_sql.SQL(''):
            where_sql = psycopg2_sql.SQL('WHERE {}').format(where_sql)

        return where_sql

    @property
    def limit_sql(self):
        random = '\nORDER BY RANDOM()' if self._data.get('random', False) else ''
        return psycopg2_sql.SQL(') AS x%s\nLIMIT %i' % (random, self.limit)) \
            if self.limit > -1 else psycopg2_sql.SQL('')

    def prepare_sql(self, linkset_spec):
        prepare_sql = [matching_method_prop.prepare_sql
                       for matching_method_prop in self.get_fields(linkset_spec)
                       if matching_method_prop.prepare_sql]

        if prepare_sql:
            return psycopg2_sql.SQL('\n').join(prepare_sql)

        return None

    def matching_fields_sql(self, linkset_spec):
        matching_fields_sqls = [psycopg2_sql.SQL('{}.uri').format(psycopg2_sql.Identifier(self.alias))]

        for matching_method_prop in self.get_fields(linkset_spec):
            for property_field in [matching_method_prop.prop_original, matching_method_prop.prop_normalized]:
                if property_field:
                    matching_fields_sqls.append(psycopg2_sql.SQL('{matching_field} AS {name}').format(
                        matching_field=property_field.sql,
                        name=psycopg2_sql.Identifier(property_field.hash)
                    ))

        return psycopg2_sql.SQL(',\n       ').join(matching_fields_sqls)

    def properties_for_spec_selection(self, spec):
        return spec.properties.get(self.id, [])

    def properties_for_matching(self, linkset_spec):
        return self.filter_properties + \
               [matching_method_prop.prop_original for matching_method_prop in self.get_fields(linkset_spec)]

    def get_fields(self, linkset_spec):
        match_fields = linkset_spec.get_fields()
        match_ets_fields = match_fields.get(str(self.id), {})

        return list(dict.fromkeys([match_field_property
                                   for match_field_label, match_field in match_ets_fields.items()
                                   for match_field_property in match_field['properties']]))

    def _r_get_filters(self, filter_obj):
        if filter_obj['type'] in ['AND', 'OR']:
            filters = []
            for condition in filter_obj['conditions']:
                condition_filters = self._r_get_filters(condition)
                if isinstance(condition_filters, list):
                    filters += condition_filters
                else:
                    filters.append(condition_filters)

            return filters

        return FilterFunction(filter_obj, PropertyField(filter_obj['property'], self))

    def _r_get_filter_sql(self, filter_obj):
        if filter_obj['type'] in ['AND', 'OR']:
            if not filter_obj['conditions']:
                return psycopg2_sql.SQL('')

            filter_sqls = map(self._r_get_filter_sql, filter_obj['conditions'])
            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL('\n%s ' % filter_obj['type']).join(filter_sqls))

        return FilterFunction(filter_obj, PropertyField(filter_obj['property'], self)).sql
