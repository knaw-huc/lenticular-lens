from common.datasets_config import DatasetsConfig
from jobs_worker.filter_function import FilterFunction
from common.helpers import hash_string, PropertyField, get_absolute_property
from psycopg2 import sql as psycopg2_sql


class Resource:
    def __init__(self, resource_data, config):
        self.__data = resource_data
        self.config = config

        self.collection = DatasetsConfig().dataset(self.dataset_id).collection(self.collection_id)
        self.view_queued = self.collection.rows_downloaded > -1\
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
        random = '\nORDER BY RANDOM()' if self.__data.get('random', True) else ''
        return psycopg2_sql.SQL(') AS x%s\nLIMIT %i' % (random, self.limit)) if self.limit > -1 else psycopg2_sql.SQL('')

    def r_get_filter_sql(self, filter_obj):
        if filter_obj['type'] in ['AND', 'OR']:
            if not filter_obj['conditions']:
                return psycopg2_sql.SQL('')

            filter_sqls = map(self.r_get_filter_sql, filter_obj['conditions'])
            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL('\n %s ' % filter_obj['type']).join(filter_sqls))

        absolute_property = get_absolute_property(filter_obj['property'])
        prop_resource = self.config.get_resource_by_label(absolute_property[0])
        column_info = prop_resource.collection.table_data['columns'][absolute_property[1]]

        return FilterFunction(filter_obj, self.label, column_info['LIST']).sql

    @property
    def matching_fields(self):
        matching_fields = []
        matching_fields_hashes = []

        for match in self.config.matches:
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
            resource = self.config.get_resource_by_label(property_field.resource_label)
            column_info = resource.collection.table_data['columns'][property_field.prop_label]

            matching_fields_sqls.append(psycopg2_sql.SQL('{matching_field} AS {name}').format(
                matching_field=property_field.sql(column_info['LIST']),
                name=psycopg2_sql.Identifier(property_field.hash)
            ))

        return psycopg2_sql.SQL(',\n       ').join(matching_fields_sqls)

    @property
    def where_sql(self):
        where_sql = self.filter_sql
        if where_sql != psycopg2_sql.SQL(''):
            where_sql = psycopg2_sql.SQL('\nWHERE {}').format(where_sql)

        return where_sql

    @property
    def related(self):
        return self.__data['related'] if 'related' in self.__data else []

    @property
    def materialize(self):
        return 'materialize' in self.__data and self.__data['materialize'] is True

    @staticmethod
    def get_matching_fields_sql(matching_fields):
        return ',\n'.join(matching_fields)
