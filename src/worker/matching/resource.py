from psycopg2 import sql as psycopg2_sql

from common.helpers import hash_string
from common.property_field import PropertyField
from common.datasets_config import DatasetsConfig

from worker.matching.filter_function import FilterFunction


class Resource:
    def __init__(self, resource_data, config):
        self.__data = resource_data
        self.config = config

        self.collection = DatasetsConfig().dataset(self.dataset_id).collection(self.collection_id)
        self.view_queued = self.collection.rows_downloaded > -1 \
                           and (self.limit < 0 or self.limit > self.collection.rows_downloaded)

    @property
    def label(self):
        return hash_string(self.__data['label'])

    @property
    def dataset_id(self):
        return self.__data['dataset_id']

    @property
    def collection_id(self):
        return self.__data['collection_id']

    @property
    def filter_sql(self):
        filter_sql = psycopg2_sql.SQL('')

        if 'filter' in self.__data:
            filter_sql = self.r_get_filter_sql(self.__data['filter'])

        return filter_sql

    @property
    def limit(self):
        return self.__data.get('limit', -1)

    @property
    def limit_sql(self):
        random = '\nORDER BY RANDOM()' if self.__data.get('random', False) else ''
        return psycopg2_sql.SQL(') AS x%s\nLIMIT %i' % (random, self.limit)) \
            if self.limit > -1 else psycopg2_sql.SQL('')

    @property
    def matching_fields(self):
        matching_fields = []
        matching_fields_hashes = []

        for match in self.config.matches_to_run:
            match_matching_fields = match.get_matching_fields().get(self.label, {})
            for match_matching_field_label, match_matching_field in match_matching_fields.items():
                for match_matching_field_property in match_matching_field:
                    if match_matching_field_property.hash not in matching_fields_hashes:
                        matching_fields_hashes.append(match_matching_field_property.hash)
                        matching_fields.append(match_matching_field_property)

        return matching_fields

    @property
    def matching_fields_sql(self):
        matching_fields_sqls = [psycopg2_sql.SQL('{}.uri').format(psycopg2_sql.Identifier(self.label))]

        for property_field in self.matching_fields:
            matching_fields_sqls.append(psycopg2_sql.SQL('{matching_field} AS {name}').format(
                matching_field=property_field.sql,
                name=psycopg2_sql.Identifier(property_field.hash)
            ))

        return psycopg2_sql.SQL(',\n       ').join(matching_fields_sqls)

    @property
    def joins_sql(self):
        joins = []
        joins_added = []
        self.get_matching_fields_joins_sql(joins_added, joins)
        return psycopg2_sql.Composed(joins)

    @property
    def where_sql(self):
        where_sql = self.filter_sql
        if where_sql != psycopg2_sql.SQL(''):
            where_sql = psycopg2_sql.SQL('\nWHERE {}').format(where_sql)

        return where_sql

    @property
    def related(self):
        return self.__data['related'] if 'related' in self.__data else []

    def get_matching_fields_joins_sql(self, joins_added, joins):
        for property_field in self.matching_fields:
            if property_field.resource_label == self.label and property_field.is_list \
                    and property_field.absolute_property not in joins_added:
                joins.append(property_field.left_join)
                joins_added.append(property_field.absolute_property)

        for relation in self.related:
            self.r_get_join_sql(self.label, relation, self.matching_fields, joins_added, joins)

    def r_get_filter_sql(self, filter_obj):
        if filter_obj['type'] in ['AND', 'OR']:
            if not filter_obj['conditions']:
                return psycopg2_sql.SQL('')

            filter_sqls = map(self.r_get_filter_sql, filter_obj['conditions'])
            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL('\n %s ' % filter_obj['type']).join(filter_sqls))

        columns = self.config.get_resource_columns(self.label)
        property = PropertyField(filter_obj['property'], parent_label=self.label, columns=columns)

        return FilterFunction(filter_obj, property).sql

    def r_get_join_sql(self, local_resource_name, relation, matching_fields, property_join_added, joins):
        if isinstance(relation, list):
            for sub_relation in relation:
                self.r_get_join_sql(local_resource_name, sub_relation, matching_fields, property_join_added, joins)
            return

        remote_resource_name = hash_string(relation['resource'])
        remote_resource = self.config.get_resource_by_label(remote_resource_name)

        parent_columns = self.config.get_resource_columns(local_resource_name)
        resource_columns = self.config.get_resource_columns(remote_resource_name)

        local_property = PropertyField(relation['local_property'],
                                       parent_label=local_resource_name, columns=parent_columns)
        remote_property = PropertyField(relation['remote_property'],
                                        parent_label=remote_resource_name, columns=resource_columns)

        if local_property.is_list and local_property.absolute_property not in property_join_added:
            joins.append(psycopg2_sql.SQL('\n'))
            joins.append(local_property.left_join)
            property_join_added.append(local_property.absolute_property)

        lhs = local_property.sql
        rhs = remote_property.sql

        extra_filter = remote_resource.filter_sql
        if extra_filter != psycopg2_sql.SQL(''):
            extra_filter = psycopg2_sql.SQL('\nAND ({resource_filter})').format(resource_filter=extra_filter)

        joins.append(psycopg2_sql.SQL('\nLEFT JOIN {resource_view} AS {alias}\nON {lhs} = {rhs}{extra_filter}').format(
            resource_view=psycopg2_sql.Identifier(remote_resource.collection.table_name),
            alias=psycopg2_sql.Identifier(remote_resource_name),
            lhs=lhs, rhs=rhs,
            extra_filter=extra_filter
        ))

        remote_resource.get_matching_fields_joins_sql(property_join_added, joins)
