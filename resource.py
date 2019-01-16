from .datasets_config import DatasetsConfig
from .filter_function import FilterFunction
from .helpers import hash_string, PropertyField
from psycopg2 import sql as psycopg2_sql


class Resource:
    def __init__(self, resource_data, config):
        self.__data = resource_data
        self.config = config

        collection = DatasetsConfig().dataset(self.dataset_id).collection(self.collection_id)
        self.cached_view = collection.limit_view_name(self.limit, True) if self.limit > -1 else collection.view_name

    @property
    def additional_properties(self):
        additional_properties = []
        additional_properties_hashes = []

        if 'additional_properties' in self.__data:
            for additional_property in self.__data['additional_properties']:
                additional_property['label'] = hash_string(additional_property['label'])
                additional_property = PropertyField(additional_property, self.label, True)
                if additional_property.hash not in additional_properties_hashes:
                    additional_properties.append(additional_property)

        related = []
        for relation in self.related:
            if isinstance(relation, list):
                related += relation
            else:
                related.append(relation)

        for relation in related:
            related_resource = self.config.get_resource_by_label(hash_string(relation['resource']))
            additional_properties += related_resource.additional_properties

        return additional_properties

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

    def r_get_filter_sql(self, filter_obj):
        if filter_obj['type'] in ['AND', 'OR']:
            filter_sqls = map(self.r_get_filter_sql, filter_obj['conditions'])
            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' %s ' % filter_obj['type']).join(filter_sqls))

        return FilterFunction(filter_obj, self.label).sql

    @property
    def group_by_sql(self):
        aggregate_labels = [additional_property.hash for additional_property in self.additional_properties
                            if additional_property.is_aggregate]

        if len(aggregate_labels) == 0:
            return psycopg2_sql.SQL('')

        group_fields = [psycopg2_sql.Identifier(self.label) + psycopg2_sql.SQL('.uri')]
        group_fields += [psycopg2_sql.Identifier(matching_field.hash) for matching_field in self.matching_fields
                         if matching_field.hash not in aggregate_labels]

        return psycopg2_sql.SQL('\nGROUP BY ') + psycopg2_sql.SQL(', ').join(group_fields)

    @property
    def matching_fields(self):
        matching_fields = self.additional_properties
        matching_fields_hashes = [matching_field.hash for matching_field in matching_fields]
        for match in self.config.matches:
            match_matching_fields = match.get_matching_fields(self.label)
            for match_matching_field in match_matching_fields:
                if match_matching_field not in matching_fields_hashes:
                    matching_fields_hashes.append(match_matching_field)
                    matching_fields.append(match_matching_fields[match_matching_field])

        return matching_fields

    @property
    def matching_fields_sql(self):
        matching_fields_sqls = [psycopg2_sql.SQL('{}.uri').format(psycopg2_sql.Identifier(self.label))]

        for matching_field in self.matching_fields:
            matching_fields_sqls.append(psycopg2_sql.SQL('{matching_field} AS {name}')
                                        .format(matching_field=matching_field.sql,
                                                name=psycopg2_sql.Identifier(matching_field.hash)))

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
