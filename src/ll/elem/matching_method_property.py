from psycopg2 import sql

from ll.job.property_field import PropertyField
from ll.util.db_functions import get_transformers
from ll.util.hasher import hash_string_min


class MatchingMethodProperty:
    def __init__(self, property, ets_id, job,
                 apply_transformers, method_transformers, property_transformers, property_transformer_first,
                 field_type_info, norm_template, norm_properties):
        self._property = property
        self._ets = job.get_entity_type_selection_by_id(ets_id)
        self._field_type_info = field_type_info
        self._norm_template = norm_template
        self._norm_properties = norm_properties

        self._transformers = []
        if apply_transformers:
            self._transformers = method_transformers.copy()
            if property_transformer_first:
                self._transformers = property_transformers.copy() + method_transformers.copy()
            else:
                self._transformers = method_transformers.copy() + property_transformers.copy()

        self.property_transformers = property_transformers

    @property
    def prop_original(self):
        return PropertyField(self._property, entity_type_selection=self._ets,
                             transformers=self._get_field_transformers(normalized=False))

    @property
    def prop_normalized(self):
        if not self._norm_template:
            return None

        return PropertyField(self._property, entity_type_selection=self._ets,
                             transformers=self._get_field_transformers(normalized=True))

    @property
    def prepare_sql(self):
        prepare_sqls = [
            sql.SQL('SELECT init_dictionary({key}, {dictionary}, {additional});').format(
                key=sql.Literal(hash_string_min((transformer['parameters']['dictionary'],
                                                 transformer['parameters']['additional']))),
                dictionary=sql.Literal(transformer['parameters']['dictionary']),
                additional=sql.SQL('ARRAY[{}]::text[]').format(
                    sql.SQL(', ').join(sql.Literal(additional)
                                       for additional in transformer['parameters']['additional'])
                ),
            )
            for transformer in self._transformers
            if transformer['name'] == 'stopwords'
        ]

        if prepare_sqls:
            return sql.SQL('\n').join(prepare_sqls)

        return None

    def _get_field_transformers(self, normalized=False):
        transformers_info = get_transformers()

        field_transformers = self._transformers.copy()
        for transformer in field_transformers:
            if transformer['name'] in transformers_info:
                transformer['sql_template'] = transformers_info[transformer['name']]['sql_template']

                if transformer['name'] == 'stopwords':
                    transformer['parameters']['key'] = hash_string_min((transformer['parameters']['dictionary'],
                                                                        transformer['parameters']['additional']))
            else:
                raise NameError('Transformer %s is not defined' % transformer['name'])

        if not self._field_type_info['type']:
            field_transformers.append({
                'sql_template': 'lower({property})',
                'parameters': {}
            })
        elif self._field_type_info['type'] == 'number':
            field_transformers.append({
                'sql_template': 'to_numeric_immutable({property})',
                'parameters': {}
            })
        elif self._field_type_info['type'] == 'date':
            field_transformers.append({
                'sql_template': 'to_date_immutable({property}, {format})',
                'parameters': {'format': self._field_type_info['parameters']['format']}
            })

        if normalized:
            field_transformers.append({
                'sql_template': self._norm_template,
                'parameters': self._norm_properties
            })

        return field_transformers

    @property
    def hash(self):
        if self.prop_normalized:
            return hash_string_min((self.prop_original.hash, self.prop_normalized.hash))

        return self.prop_original.hash

    def __eq__(self, other):
        return isinstance(other, MatchingMethodProperty) and self.prop_original == other.prop_original

    def __hash__(self):
        return hash(self.hash)
