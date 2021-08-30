from psycopg2 import sql
from rdflib import URIRef

from ll.util.n3_helpers import pred_val, rdfs_sequence
from ll.util.hasher import hash_string_min, column_name_hash

from ll.namespaces.void_plus import VoidPlus
from ll.namespaces.shared_ontologies import Namespaces as NS


class PropertyField:
    def __init__(self, data, entity_type_selection=None, collection=None, transformers=None):
        self._data = data if isinstance(data, list) else [data]

        self._collection = entity_type_selection.collection if entity_type_selection else collection
        if not self._collection:
            raise Exception('Property field should have either an entity-type selection or a collection')

        self._transformers = transformers if transformers else []
        self._alias = entity_type_selection.alias if entity_type_selection \
            else hash_string_min(self._collection.table_name)

        self._extend = True
        self._hash = None
        self._prop_path = None

    def no_extend(self):
        self._extend = False

    @property
    def property_path(self):
        return self._data

    @property
    def resource_label(self):
        if not self._intermediate_property_path:
            return self._alias

        return self._intermediate_property_path[-1]['alias']

    @property
    def prop_name(self):
        return self._data[-1]

    @property
    def prop_label(self):
        return column_name_hash(self.prop_name)

    @property
    def extended_prop_label(self):
        return hash_string_min(self.resource_label + '.' + self.prop_label) + '_extended'

    @property
    def is_list(self):
        if not self._intermediate_property_path:
            if self.prop_label in self._collection.columns:
                return self._collection.columns[self.prop_label]['isList']

            return False

        if self.prop_label == 'uri':
            return False

        return self._intermediate_property_path[-1]['to_collection'].columns[self.prop_label]['isList']

    @property
    def sql(self):
        property_sql = self.get_property_sql(self.resource_label, self.prop_label, self._extend and self.is_list)

        for transformer in self._transformers:
            template_sql = sql.SQL(transformer['sql_template'])
            sql_parameters = {key: sql.Literal(value) for (key, value) in transformer['parameters'].items()}
            property_sql = template_sql.format(property=property_sql, **sql_parameters)

        return property_sql

    @property
    def prefix_mappings(self):
        property_prefix_mappings = {}
        for prop_in_path in self._intermediate_property_path:
            prop = prop_in_path['property']

            prefix = prop_in_path['from_collection'].columns[prop].get('prefix')
            if prefix and prefix not in property_prefix_mappings:
                property_prefix_mappings[prefix] = prop_in_path['from_collection'].columns[prop]['prefixUri']

            prefix, prefix_uri = prop_in_path['to_collection'].prefix_info
            if prefix and prefix not in property_prefix_mappings:
                property_prefix_mappings[prefix] = prefix_uri

        prefix = self._property_collection.columns[self.prop_label].get('prefix') if self.prop_label != 'uri' else None
        if prefix and prefix not in property_prefix_mappings:
            property_prefix_mappings[prefix] = self._property_collection.columns[self.prop_label]['prefixUri']

        prefix, prefix_uri = self._property_collection.prefix_info
        if prefix and prefix not in property_prefix_mappings:
            property_prefix_mappings[prefix] = prefix_uri

        return property_prefix_mappings

    def n3(self, ns_manager, end=False, line=True, tabs=1):
        if len(self._data) == 1:
            property = self._collection.columns[self.prop_label]['uri'] \
                if self.prop_label != 'uri' else f'{VoidPlus.resource}uri'
            value = URIRef(property).n3(ns_manager)
        else:
            urirefs = []
            for prop_in_path in self._intermediate_property_path:
                urirefs.append(URIRef(prop_in_path['from_collection'].columns[prop_in_path['property']]['uri']
                                      if prop_in_path['property'] != 'uri'
                                      else f'{VoidPlus.resource}uri').n3(ns_manager))
                urirefs.append(URIRef(prop_in_path['to_collection'].table_data['collection_uri']).n3(ns_manager))

            urirefs.append(URIRef(self._property_collection.columns[self.prop_label]['uri']
                                  if self.prop_label != 'uri' else f'{VoidPlus.resource}uri').n3(ns_manager))

            value = rdfs_sequence(urirefs, tabs=tabs)

        return pred_val(NS.VoID.property, value, end=end, line=line, tabs=tabs)

    def add_joins(self, joins):
        cur_resource = self._alias
        for prop_in_path in self._intermediate_property_path:
            next_table_name = prop_in_path['to_collection'].table_name
            next_resource = prop_in_path['alias']
            is_list = prop_in_path['from_collection'].columns[prop_in_path['property']]['isList']

            if is_list:
                extended_prop_alias = self.get_extended_property_alias(cur_resource, prop_in_path['property'])
                joins.add_join(sql.SQL(
                    'LEFT JOIN unnest({alias}.{column_name}) ' +
                    'AS {column_name_expanded} ON true'
                ).format(
                    alias=sql.Identifier(cur_resource),
                    column_name=sql.Identifier(prop_in_path['property']),
                    column_name_expanded=sql.Identifier(extended_prop_alias)
                ), extended_prop_alias)

            lhs = self.get_property_sql(cur_resource, prop_in_path['property'], is_list)
            rhs = self.get_property_sql(next_resource, 'uri')

            joins.add_join(sql.SQL('LEFT JOIN timbuctoo.{target} AS {alias} \nON {lhs} = {rhs}').format(
                target=sql.Identifier(next_table_name),
                alias=sql.Identifier(next_resource),
                lhs=lhs, rhs=rhs
            ), next_resource)

            cur_resource = next_resource

        if self.is_list:
            joins.add_join(sql.SQL(
                'LEFT JOIN unnest({alias}.{column_name}) ' +
                'AS {column_name_expanded} ON true'
            ).format(
                alias=sql.Identifier(self.resource_label),
                column_name=sql.Identifier(self.prop_label),
                column_name_expanded=sql.Identifier(self.extended_prop_label)
            ), self.extended_prop_label)

    @property
    def collections_required(self):
        return set([prop_in_path['to_collection'].collection_id for prop_in_path in self._prop_path])

    @property
    def is_downloaded(self):
        if not self._collection.is_downloaded:
            return False

        for prop_in_path in self._intermediate_property_path:
            if not prop_in_path['to_collection'].is_downloaded:
                return False

        return True

    @property
    def hash(self):
        if not self._hash:
            self._hash = \
                hash_string_min((self.resource_label, self.prop_label, self._extend, self.is_list, self._transformers))

        return self._hash

    @property
    def _property_collection(self):
        if not self._intermediate_property_path:
            return self._collection

        return self._intermediate_property_path[-1]['to_collection']

    @property
    def _intermediate_property_path(self):
        if not self._prop_path:
            self._prop_path = []
            path = self._collection.table_name

            prev_collection = self._collection
            for (prop, collection_id) in [(self._data[i], self._data[i + 1]) for i in range(0, len(self._data) - 2, 2)]:
                collection = prev_collection.get_collection_by_id(collection_id)
                path += f'[{collection.table_name}_{prop}]'

                self._prop_path.append({
                    'from_collection': prev_collection,
                    'to_collection': collection,
                    'alias': hash_string_min(path),
                    'property': column_name_hash(prop)
                })

                prev_collection = collection

        return self._prop_path

    @staticmethod
    def get_extended_property_alias(resource, prop):
        return hash_string_min(resource + '.' + prop) + '_extended'

    @staticmethod
    def get_property_sql(resource, prop, extend=False):
        absolute_property = [PropertyField.get_extended_property_alias(resource, prop)] \
            if extend else [resource, prop]
        return sql.SQL('.').join(map(sql.Identifier, absolute_property))

    def __eq__(self, other):
        return isinstance(other, PropertyField) and self.hash == other.hash

    def __hash__(self):
        return hash(self.hash)
