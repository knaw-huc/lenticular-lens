from psycopg2 import sql as psycopg2_sql

from ll.util.helpers import hash_string
from ll.data.collection import Collection
from ll.job.property_field import PropertyField
from ll.job.filter_function import FilterFunction


class Resource:
    def __init__(self, resource_data, config):
        self.__data = resource_data
        self.config = config

        if 'type' not in resource_data['dataset'] or resource_data['dataset']['type'] == 'timbuctoo':
            graphql = resource_data['dataset']['timbuctoo_graphql']
            hsid = resource_data['dataset']['timbuctoo_hsid'] if not resource_data['dataset']['published'] else None
            dataset_id = self.__data['dataset']['dataset_id']
            collection_id = self.__data['dataset']['collection_id']

            collection = Collection(graphql, hsid, dataset_id, collection_id)
            self.table_name = collection.table_name
            self.columns = collection.columns
            self.view_queued = collection.rows_downloaded > -1 \
                               and (self.limit < 0 or self.limit > collection.rows_downloaded)

    @property
    def label(self):
        return hash_string(self.__data['label'])

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
        return self.get_fields(only_matching_fields=True)

    @property
    def fields(self):
        return self.get_fields(only_matching_fields=False)

    @property
    def properties(self):
        if 'filter' in self.__data:
            return self.r_get_filter_properties(self.__data['filter'], [])
        return []

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
    def properties_sql(self):
        properties_sqls = [psycopg2_sql.SQL('{}.uri').format(psycopg2_sql.Identifier(self.label))]

        for property_field in self.properties:
            properties_sqls.append(psycopg2_sql.SQL('{property} AS {name}').format(
                property=property_field.sql,
                name=psycopg2_sql.Identifier(property_field.prop_name)
            ))

        return psycopg2_sql.SQL(',\n       ').join(properties_sqls)

    @property
    def joins_sql(self):
        joins = self.get_fields_joins_sql([], [])
        return psycopg2_sql.Composed(joins)

    @property
    def joins_related_sql(self):
        joins = self.get_fields_joins_sql([], [], fields=False)
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

    def get_fields(self, only_matching_fields=True):
        matching_fields = []
        matching_fields_hashes = []

        match_fields = self.config.match_to_run.get_fields(only_matching_fields=only_matching_fields)
        match_resource_fields = match_fields.get(self.label, {})

        for match_field_label, match_field in match_resource_fields.items():
            for match_field_property in match_field:
                if match_field_property.hash not in matching_fields_hashes:
                    matching_fields_hashes.append(match_field_property.hash)
                    matching_fields.append(match_field_property)

        return matching_fields

    def get_fields_joins_sql(self, joins, joins_added, fields=True, related=True):
        if fields:
            for property_field in self.fields:
                if property_field.is_list and property_field.absolute_property not in joins_added:
                    joins.append(property_field.left_join)
                    joins_added.append(property_field.absolute_property)

        if related:
            for relation in self.related:
                self.r_get_join_sql(relation, joins, joins_added, fields, related)

        return joins

    def r_get_filter_properties(self, filter_obj, properties):
        if 'conditions' in filter_obj:
            for condition in filter_obj['conditions']:
                self.r_get_filter_properties(condition, properties)
        else:
            properties.append(PropertyField(filter_obj['property'], parent_label=self.label, columns=self.columns))

        return properties

    def r_get_filter_sql(self, filter_obj):
        if filter_obj['type'] in ['AND', 'OR']:
            if not filter_obj['conditions']:
                return psycopg2_sql.SQL('')

            filter_sqls = map(self.r_get_filter_sql, filter_obj['conditions'])
            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL('\n %s ' % filter_obj['type']).join(filter_sqls))

        property = PropertyField(filter_obj['property'], parent_label=self.label, columns=self.columns)

        return FilterFunction(filter_obj, property).sql

    def r_get_join_sql(self, relation, joins, property_join_added, fields, related):
        if isinstance(relation, list):
            for sub_relation in relation:
                self.r_get_join_sql(sub_relation, joins, property_join_added, fields, related)
            return

        remote_resource_name = hash_string(relation['resource'])
        remote_resource = self.config.get_resource_by_label(remote_resource_name)

        local_property = PropertyField(relation['local_property'],
                                       parent_label=self.label, columns=self.columns)
        remote_property = PropertyField(relation['remote_property'],
                                        parent_label=remote_resource_name, columns=remote_resource.columns)

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
            resource_view=psycopg2_sql.Identifier(remote_resource.table_name),
            alias=psycopg2_sql.Identifier(remote_resource_name),
            lhs=lhs, rhs=rhs,
            extra_filter=extra_filter
        ))

        remote_resource.get_fields_joins_sql(joins, property_join_added, fields, related)
