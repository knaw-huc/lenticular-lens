from psycopg2 import sql as psycopg2_sql

from ll.data.joins import Joins
from ll.data.collection import Collection
from ll.data.property_field import PropertyField

from ll.util.helpers import hash_string
from ll.job.filter_function import FilterFunction


class Resource:
    def __init__(self, resource_data, job):
        self._data = resource_data
        self._job = job

        graphql = resource_data['dataset']['timbuctoo_graphql']
        hsid = resource_data['dataset']['timbuctoo_hsid'] if not resource_data['dataset']['published'] else None
        dataset_id = self._data['dataset']['dataset_id']
        collection_id = self._data['dataset']['collection_id']

        collection = Collection(graphql, hsid, dataset_id, collection_id)
        self.table_name = collection.table_name
        self.columns = collection.columns
        self.view_queued = collection.rows_downloaded > -1 \
                           and (self.limit < 0 or self.limit > collection.rows_downloaded)

    @property
    def dataset_id(self):
        return self._data['dataset']['dataset_id']

    @property
    def collection_id(self):
        return self._data['dataset']['collection_id']

    @property
    def label(self):
        return hash_string(self._data['label'])

    @property
    def properties(self):
        return self._data['properties']

    @property
    def filter_sql(self):
        return self._r_get_filter_sql(self._data['filter']) \
            if 'filter' in self._data and self._data['filter'] else psycopg2_sql.SQL('')

    @property
    def limit(self):
        return self._data.get('limit', -1)

    @property
    def limit_sql(self):
        random = '\nORDER BY RANDOM()' if self._data.get('random', False) else ''
        return psycopg2_sql.SQL(') AS x%s\nLIMIT %i' % (random, self.limit)) \
            if self.limit > -1 else psycopg2_sql.SQL('')

    @property
    def related(self):
        return self._data['related'] if 'related' in self._data else []

    @property
    def where_sql(self):
        where_sql = self.filter_sql
        if where_sql != psycopg2_sql.SQL(''):
            where_sql = psycopg2_sql.SQL('WHERE {}').format(where_sql)

        return where_sql

    def fields(self, match):
        return self._get_fields(match, only_matching_fields=False)

    def matching_fields(self, match):
        return self._get_fields(match, only_matching_fields=True)

    def matching_fields_sql(self, match):
        matching_fields_sqls = [psycopg2_sql.SQL('{}.uri').format(psycopg2_sql.Identifier(self.label))]

        for property_field in self.matching_fields(match):
            matching_fields_sqls.append(psycopg2_sql.SQL('{matching_field} AS {name}').format(
                matching_field=property_field.sql,
                name=psycopg2_sql.Identifier(property_field.hash)
            ))

        return psycopg2_sql.SQL(',\n       ').join(matching_fields_sqls)

    def joins(self, match):
        joins = Joins()
        self.set_joins_sql(match, joins, fields=True, related=True)
        return joins

    def related_joins(self, match):
        joins = Joins()
        self.set_joins_sql(match, joins, fields=False, related=True)
        return joins

    def set_joins_sql(self, match, joins, fields=True, related=True):
        if fields:
            for property_field in self.fields(match):
                if property_field.is_list:
                    joins.add_join(property_field.left_join, property_field.extended_prop_label)

        if related:
            for relation in self.related:
                self._r_get_join_sql(match, relation, joins, fields, related)

    def _get_fields(self, match, only_matching_fields=True):
        matching_fields = []
        matching_fields_hashes = []

        match_fields = match.get_fields(only_matching_fields=only_matching_fields)
        match_resource_fields = match_fields.get(self.label, {})

        for match_field_label, match_field in match_resource_fields.items():
            for match_field_property in match_field:
                if match_field_property.hash not in matching_fields_hashes:
                    matching_fields_hashes.append(match_field_property.hash)
                    matching_fields.append(match_field_property)

        return matching_fields

    def _r_get_filter_sql(self, filter_obj):
        if filter_obj['type'] in ['AND', 'OR']:
            if not filter_obj['conditions']:
                return psycopg2_sql.SQL('')

            filter_sqls = map(self._r_get_filter_sql, filter_obj['conditions'])
            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL('\n %s ' % filter_obj['type']).join(filter_sqls))

        property = PropertyField(filter_obj['property'], parent_label=self.label, columns=self.columns)

        return FilterFunction(filter_obj, property).sql

    def _r_get_join_sql(self, match, relation, joins, fields, related):
        if isinstance(relation, list):
            for sub_relation in relation:
                self._r_get_join_sql(match, sub_relation, joins, fields, related)
            return

        remote_resource_name = hash_string(relation['resource'])
        remote_resource = self._job.get_resource_by_label(remote_resource_name)

        local_property = PropertyField(relation['local_property'],
                                       parent_label=self.label, columns=self.columns)
        remote_property = PropertyField(relation['remote_property'],
                                        parent_label=remote_resource_name, columns=remote_resource.columns)

        if local_property.is_list:
            joins.add_join(local_property.left_join, local_property.extended_prop_label)

        lhs = local_property.sql
        rhs = remote_property.sql

        extra_filter = remote_resource.filter_sql
        if extra_filter != psycopg2_sql.SQL(''):
            extra_filter = psycopg2_sql.SQL('\nAND ({resource_filter})').format(resource_filter=extra_filter)

        joins.add_join(
            psycopg2_sql.SQL('LEFT JOIN {resource_view} AS {alias}\nON {lhs} = {rhs}{extra_filter}').format(
                resource_view=psycopg2_sql.Identifier(remote_resource.table_name),
                alias=psycopg2_sql.Identifier(remote_resource_name),
                lhs=lhs, rhs=rhs,
                extra_filter=extra_filter
            ), remote_resource_name)

        remote_resource.set_joins_sql(match, joins, fields, related)
