import re
import json

from psycopg2 import sql as psycopg2_sql
from ll.data.property_field import PropertyField
from ll.util.helpers import hash_string, get_json_from_file


class MatchingFunction:
    _transformers = get_json_from_file('transformers.json')
    _matching_functions = get_json_from_file('matching_functions.json')

    def __init__(self, function_obj, job):
        self._data = function_obj
        self._job = job
        self._sources = []
        self._targets = []
        self._intermediates = []

        self.field_name = hash_string(json.dumps(function_obj))

        self.method_name = function_obj['method_name']
        self._method_config = function_obj['method_config']
        if self.method_name in self._matching_functions:
            self._method_info = self._matching_functions[self.method_name]
        else:
            raise NameError('Matching function %s is not defined' % self.method_name)

        self._method_sim_name = function_obj['method_sim_name']
        self._method_sim_config = function_obj['method_sim_config']
        self._method_sim_normalized = function_obj['method_sim_normalized']
        self._method_sim_info = self._matching_functions[self._method_sim_name] \
            if self._method_sim_name in self._matching_functions else {}

        self._t_conorm = function_obj['t_conorm']
        self.list_threshold = function_obj['list_threshold']
        self._list_threshold_unit = function_obj['list_threshold_unit']

    @property
    def join_condition_sql(self):
        if 'match' in self._method_info and 'condition' not in self._method_info:
            template = self._method_info['match']
        elif 'field' in self._method_info and not self._method_sim_normalized:
            template = '{source} = {target}'.format(
                source=re.sub(r'{field}', '{source}', self._method_info['field']),
                target=re.sub(r'{field}', '{target}', self._method_info['field'])
            )
        else:
            return None

        template = re.sub(r'{source}', 'source.{field_name}', template)
        template = re.sub(r'{target}', 'target.{field_name}', template)
        template = re.sub(r'{source_intermediate}', 'source.{field_name_intermediate}', template)
        template = re.sub(r'{target_intermediate}', 'target.{field_name_intermediate}', template)

        return psycopg2_sql.SQL(template).format(
            field_name=psycopg2_sql.Identifier(self.field_name),
            field_name_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
            **self._sql_parameters
        )

    @property
    def match_conditions_sql(self):
        if 'condition' in self._method_info:
            template = self._method_info['condition']
        elif 'condition' in self._method_sim_info:
            template = self._method_sim_info['condition']
        else:
            return None

        template = re.sub(r'{similarity}', '{field_name}', template)

        return psycopg2_sql.SQL(template).format(
            field_name=psycopg2_sql.Identifier(self.field_name + '_similarity'),
            **self._sql_parameters
        )

    @property
    def similarity_sql(self):
        if 'similarity' in self._method_info:
            template = self._method_info['similarity']
        elif 'field' in self._method_info and 'similarity' in self._method_sim_info:
            template = self._method_sim_info['similarity']
            if self._method_sim_normalized:
                template = template.format(
                    source=re.sub(r'{field}', '{source}', self._method_info['field']),
                    target=re.sub(r'{field}', '{target}', self._method_info['field'])
                )
        else:
            return None

        template = re.sub(r'{source}', 'source.{field_name}', template)
        template = re.sub(r'{target}', 'target.{field_name}', template)

        return psycopg2_sql.SQL(template).format(
            field_name=psycopg2_sql.Identifier(self.field_name),
            field_name_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
            **self._sql_parameters
        )

    @property
    def similarity_grouping_sql(self):
        if self.similarity_sql:
            return psycopg2_sql.SQL('logic_ops({operation}, array_agg({field}))').format(
                operation=psycopg2_sql.Literal(self._t_conorm),
                field=psycopg2_sql.Identifier(self.field_name + '_similarity')
            )

        return None

    @property
    def index_sql(self):
        if 'index' not in self._method_info and 'index' not in self._method_sim_info:
            return None

        index_sqls = []

        if 'before_index' in self._method_info:
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                psycopg2_sql.SQL(self._method_info['before_index']).format(
                    target=psycopg2_sql.Identifier(self.field_name),
                    target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                    **self._sql_parameters
                )
            ))

        if 'before_index' in self._method_sim_info:
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                psycopg2_sql.SQL(self._method_sim_info['before_index']).format(
                    target=psycopg2_sql.Identifier(self.field_name),
                    target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                    **self._sql_parameters
                )
            ))

        if 'index' in self._method_info:
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                psycopg2_sql.SQL(self._method_info['index']).format(
                    target=psycopg2_sql.Identifier(self.field_name),
                    target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                    **self._sql_parameters
                )
            ))

            if 'index' in self._method_sim_info:
                index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                    psycopg2_sql.SQL(self._method_info['index']).format(
                        target=psycopg2_sql.Identifier(self.field_name),
                        target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                        **self._sql_parameters
                    )
                ))

        return psycopg2_sql.SQL('\n').join(index_sqls)

    @property
    def sources(self):
        if not self._sources:
            self._sources = self._get_properties('sources')

        return self._sources

    @property
    def targets(self):
        if not self._targets:
            self._targets = self._get_properties('targets')

        return self._targets

    @property
    def intermediates(self):
        if not self._intermediates:
            self._intermediates = {}
            if self.method_name == 'INTERMEDIATE':
                self._intermediates[self._method_config['entity_type_selection']] = {
                    'source': PropertyField(self._method_config['intermediate_source'], job=self._job),
                    'target': PropertyField(self._method_config['intermediate_target'], job=self._job)
                }

        return self._intermediates

    @property
    def _sql_parameters(self):
        return {key: psycopg2_sql.Literal(value)
                for (key, value) in {**self._method_config, **self._method_sim_config}.items()}

    def _get_properties(self, key):
        properties = {}
        for entity_type_selection, fields in self._data[key].items():
            properties[entity_type_selection] = []
            for field in fields:
                field_transformers = field.get('transformers', [])

                for transformer in field_transformers:
                    if transformer['name'] in self._transformers:
                        transformer['transformer_info'] = self._transformers[transformer['name']]
                    else:
                        raise NameError('Transformer %s is not defined' % transformer['name'])

                property_field = PropertyField(field['property'], job=self._job, transformers=field_transformers)
                properties[entity_type_selection].append(property_field)

        return properties
