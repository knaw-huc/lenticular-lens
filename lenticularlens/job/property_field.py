from psycopg import sql
from rdflib import URIRef

from lenticularlens.data.entity_type import EntityType
from lenticularlens.util.n3_helpers import pred_val, rdfs_sequence
from lenticularlens.util.hasher import hash_string_min, column_name_hash

from lenticularlens.namespaces.void_plus import VoidPlus
from lenticularlens.namespaces.shared_ontologies import Namespaces as NS


class PropertyField:
    def __init__(self, data, entity_type_selection=None, entity_type=None, transformers=None):
        self._data = data if isinstance(data, list) else [data]

        self._entity_type: EntityType = entity_type_selection.entity_type if entity_type_selection else entity_type
        if not self._entity_type:
            raise Exception('Property field should have either an entity-type selection or an entity-type')

        self._transformers = transformers if transformers else []
        self._alias = entity_type_selection.alias if entity_type_selection \
            else hash_string_min(self._entity_type.table_name)

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
    def extended_prop_label(self):
        return hash_string_min(self.resource_label + '.' + column_name_hash(self.prop_name)) + '_extended'

    @property
    def is_list(self):
        if not self._intermediate_property_path:
            if self.prop_name in self._entity_type.properties:
                return self._entity_type.properties[self.prop_name].is_list

            return False

        if self.prop_name == 'uri':
            return False

        return self._intermediate_property_path[-1]['to_entity_type'].properties[self.prop_name].is_list

    @property
    def sql(self):
        property_sql = self.get_property_sql(self.resource_label, self.prop_name, self._extend and self.is_list)

        for transformer in self._transformers:
            template_sql = sql.SQL(transformer['sql_template'])
            sql_parameters = {key: sql.Literal(value) for (key, value) in transformer['parameters'].items()}
            property_sql = template_sql.format(property=property_sql, **sql_parameters)

        return property_sql

    @property
    def prefix_mappings(self):
        property_prefix_mappings = {}
        prefix_mappings = self._property_entity_type.dataset.prefix_mappings

        for prop_in_path in self._intermediate_property_path:
            prop = prop_in_path['property']

            short_uri = prop_in_path['from_entity_type'].properties[prop].shortened_uri
            prefix = short_uri.split(':')[0] if ':' in short_uri else None
            if prefix and prefix not in property_prefix_mappings and prefix in prefix_mappings:
                property_prefix_mappings[prefix] = prefix_mappings[prefix]

            prefix, prefix_uri = prop_in_path['to_entity_type'].prefix_info
            if prefix and prefix not in property_prefix_mappings:
                property_prefix_mappings[prefix] = prefix_uri

        short_uri = self._property_entity_type.properties[self.prop_name].shortened_uri
        prefix = short_uri.split(':')[0] if ':' in short_uri else None
        if prefix and prefix not in property_prefix_mappings and prefix in prefix_mappings:
            property_prefix_mappings[prefix] = prefix_mappings[prefix]

        prefix, prefix_uri = self._property_entity_type.prefix_info
        if prefix and prefix not in property_prefix_mappings:
            property_prefix_mappings[prefix] = prefix_uri

        return property_prefix_mappings

    def n3(self, ns_manager, end=False, line=True, tabs=1):
        if len(self._data) == 1:
            property = self._entity_type.properties[self.prop_name]['uri'] \
                if self.prop_name != 'uri' else f'{VoidPlus.resource}uri'
            value = URIRef(property).n3(ns_manager)
        else:
            urirefs = []
            for prop_in_path in self._intermediate_property_path:
                urirefs.append(URIRef(prop_in_path['from_entity_type'].properties[prop_in_path['property']]['uri']
                                      if prop_in_path['property'] != 'uri'
                                      else f'{VoidPlus.resource}uri').n3(ns_manager))
                urirefs.append(URIRef(prop_in_path['to_entity_type'].entity_type.uri).n3(ns_manager))

            urirefs.append(URIRef(self._property_entity_type.properties[self.prop_name]['uri']
                                  if self.prop_name != 'uri' else f'{VoidPlus.resource}uri').n3(ns_manager))

            value = rdfs_sequence(urirefs, tabs=tabs)

        return pred_val(NS.VoID.property, value, end=end, line=line, tabs=tabs)

    def add_joins(self, joins):
        cur_resource = self._alias
        for prop_in_path in self._intermediate_property_path:
            next_table_name = prop_in_path['to_entity_type'].table_name
            next_resource = prop_in_path['alias']
            is_list = prop_in_path['from_entity_type'].properties[prop_in_path['property']].is_list

            if is_list:
                extended_prop_alias = self.get_extended_property_alias(cur_resource, prop_in_path['property'])
                joins.add_join(sql.SQL(
                    'LEFT JOIN unnest({alias}.{column_name}) ' +
                    'AS {column_name_expanded} ON true'
                ).format(
                    alias=sql.Identifier(cur_resource),
                    column_name=sql.Identifier(column_name_hash(prop_in_path['property'])),
                    column_name_expanded=sql.Identifier(extended_prop_alias)
                ), extended_prop_alias)

            lhs = self.get_property_sql(cur_resource, prop_in_path['property'], is_list)
            rhs = self.get_property_sql(next_resource, 'uri')

            joins.add_join(sql.SQL('LEFT JOIN entity_types_data.{target} AS {alias} \nON {lhs} = {rhs}').format(
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
                column_name=sql.Identifier(column_name_hash(self.prop_name)),
                column_name_expanded=sql.Identifier(self.extended_prop_label)
            ), self.extended_prop_label)

    @property
    def entity_types_required(self):
        return set([prop_in_path['to_entity_type'] for prop_in_path in self._intermediate_property_path])

    @property
    def is_downloaded(self):
        if not self._entity_type.is_downloaded:
            return False

        for prop_in_path in self._intermediate_property_path:
            if not prop_in_path['to_entity_type'] or not prop_in_path['to_entity_type'].is_downloaded:
                return False

        return True

    @property
    def hash(self):
        if not self._hash:
            self._hash = hash_string_min((
                self.resource_label,
                column_name_hash(self.prop_name),
                self._extend,
                self._transformers
            ))

        return self._hash

    @property
    def _property_entity_type(self):
        if not self._intermediate_property_path:
            return self._entity_type

        return self._intermediate_property_path[-1]['to_entity_type']

    @property
    def _intermediate_property_path(self):
        if not self._prop_path:
            self._prop_path = []
            path = self._entity_type.table_name

            prev_entity_type = self._entity_type
            data = [(self._data[i], self._data[i + 1], self._data[i + 3] if i + 3 < len(self._data) else None)
                    for i in range(0, len(self._data) - 2, 2)]
            for (prop, entity_type_id, next_entity_type_id) in data:
                entity_type = prev_entity_type.get_entity_type(entity_type_id)
                next_entity_type = entity_type.get_entity_type(next_entity_type_id) \
                    if entity_type and next_entity_type_id else None
                path += f'[{entity_type.table_name}_{prop}_{next_entity_type.table_name}]' if next_entity_type \
                    else f'[{entity_type.table_name}_{prop}]' if entity_type else ''

                self._prop_path.append({
                    'from_entity_type_id': entity_type_id,
                    'from_entity_type': prev_entity_type,
                    'to_entity_type_id': next_entity_type_id,
                    'to_entity_type': entity_type,
                    'alias': hash_string_min(path) if path else None,
                    'property': prop
                })

                prev_entity_type = entity_type
                if not entity_type:
                    break

        return self._prop_path

    @staticmethod
    def get_extended_property_alias(resource, prop):
        return hash_string_min(resource + '.' + column_name_hash(prop)) + '_extended'

    @staticmethod
    def get_property_sql(resource, prop, extend=False):
        absolute_property = [PropertyField.get_extended_property_alias(resource, prop)] \
            if extend else [resource, column_name_hash(prop)]
        return sql.SQL('.').join(map(sql.Identifier, absolute_property))

    def __eq__(self, other):
        return isinstance(other, PropertyField) and self.hash == other.hash

    def __hash__(self):
        return hash(self.hash)
