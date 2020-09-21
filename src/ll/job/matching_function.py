import re
import json

from inspect import cleandoc
from psycopg2 import sql as psycopg2_sql

from ll.data.property_field import PropertyField
from ll.util.helpers import hash_string, get_json_from_file


class MatchingFunction:
    _transformers = get_json_from_file('transformers.json')
    _matching_functions = get_json_from_file('matching_functions.json')
    _similarity_functions = get_json_from_file('similarity_functions.json')

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

        if self._method_info['requires_similarity_template']:
            if self._method_sim_name in self._similarity_functions:
                self._method_sim_info = self._similarity_functions[self._method_sim_name]
            else:
                self._method_sim_normalized = True
                self._method_sim_info = {
                    'sql_template': '{source} = {target}',
                    'similarity': None,
                    'before_index': None,
                    'index_using': None
                }
        elif self.method_name in self._similarity_functions:
            self._method_sim_name = self.method_name
            self._method_sim_info = self._similarity_functions[self.method_name]
        else:
            self._method_sim_info = {
                'sql_template': None,
                'similarity': None,
                'before_index': None,
                'index_using': None
            }

        self._t_conorm = function_obj['t_conorm']
        self.list_threshold = function_obj['list_threshold']
        self._list_threshold_unit = function_obj['list_threshold_unit']

    @property
    def sql(self):
        method_template = self._method_info['sql_template']
        method_sim_template = self._method_sim_info['sql_template'] \
            if self.method_name != self._method_sim_name else None
        template = self._template(method_template, method_sim_template, False, self._method_sim_normalized)

        if self.list_threshold > 0:
            list_threshold = psycopg2_sql.Literal(self.list_threshold) if self._list_threshold_unit == 'matches' else \
                psycopg2_sql.SQL('greatest(cardinality(source.{field_name}), ' +
                                 'cardinality(target.{field_name})) * {threshold}').format(
                    field_name=psycopg2_sql.Identifier(self.field_name),
                    threshold=psycopg2_sql.Literal(self.list_threshold / 100)
                )

            return psycopg2_sql.SQL(cleandoc('''
                cardinality(ARRAY(
                    SELECT 1
                    FROM unnest(source.{field_name}) AS src
                    JOIN unnest(target.{field_name}) AS trg
                    ON ''' + template + '''
                )) >= {list_threshold}
            ''')).format(
                field_name=psycopg2_sql.Identifier(self.field_name),
                field_name_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                list_threshold=list_threshold,
                **self._sql_parameters
            )

        return psycopg2_sql.SQL(template).format(
            field_name=psycopg2_sql.Identifier(self.field_name),
            field_name_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
            **self._sql_parameters
        )

    @property
    def similarity_sql(self):
        if not self._method_sim_info['similarity']:
            return None

        method_template = self._method_info['sql_template'] \
            if self.method_name != self._method_sim_name else None
        method_sim_template = self._method_sim_info['similarity']
        template = self._template(method_template, method_sim_template, True, self._method_sim_normalized)

        if self.list_threshold > 0:
            return psycopg2_sql.SQL(cleandoc('''
                logic_ops({t_conorm}, ARRAY(
                    SELECT ''' + template + '''
                    FROM unnest(source.{field_name}) AS src
                    CROSS JOIN unnest(target.{field_name}) AS trg
                ))
            ''')).format(
                t_conorm=psycopg2_sql.Literal(self._t_conorm),
                field_name=psycopg2_sql.Identifier(self.field_name),
                field_name_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                **self._sql_parameters
            )

        return psycopg2_sql.SQL(template).format(
            field_name=psycopg2_sql.Identifier(self.field_name),
            field_name_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
            **self._sql_parameters
        )

    @property
    def index_sql(self):
        if not self._method_info['index_using'] and not self._method_sim_info['index_using']:
            return None

        index_sqls = []

        if self._method_info['before_index']:
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                psycopg2_sql.SQL(self._method_info['before_index']).format(
                    target=psycopg2_sql.Identifier(self.field_name),
                    target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                    **self._sql_parameters
                )
            ))

        if self._method_sim_info['before_index'] and self.method_name != self._method_sim_name:
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                psycopg2_sql.SQL(self._method_sim_info['before_index']).format(
                    target=psycopg2_sql.Identifier(self.field_name),
                    target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                    **self._sql_parameters
                )
            ))

        if self._method_info['index_using']:
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                psycopg2_sql.SQL(self._method_info['index_using']).format(
                    target=psycopg2_sql.Identifier(self.field_name),
                    target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                    **self._sql_parameters
                )
            ))

            if self._method_sim_info['index_using'] and self.method_name != self._method_sim_name:
                index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                    psycopg2_sql.SQL(self._method_info['index_using']).format(
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

    def _template(self, matching_template, similarity_template, is_similarity=False, similarity_over_normalized=False):
        if matching_template:
            matching_template = re.sub(r'{source_intermediate}', 'source.{field_name_intermediate}', matching_template)
            matching_template = re.sub(r'{target_intermediate}', 'target.{field_name_intermediate}', matching_template)

        if similarity_template:
            if matching_template:
                matching_template_source = re.sub(r'{field}', '{source}', matching_template)
                matching_template_target = re.sub(r'{field}', '{target}', matching_template)

                if similarity_over_normalized:
                    template = similarity_template
                    template = re.sub(r'{source}', matching_template_source, template)
                    template = re.sub(r'{target}', matching_template_target, template)
                elif is_similarity:
                    template = similarity_template
                else:
                    template = '{match_source} = {match_target} AND {similarity_match}'.format(
                        match_source=matching_template_source,
                        match_target=matching_template_target,
                        similarity_match=similarity_template
                    )
            else:
                template = similarity_template
        else:
            template = matching_template

        if self.list_threshold:
            template = re.sub(r'{source}', 'src', template)
            template = re.sub(r'{target}', 'trg', template)
        else:
            template = re.sub(r'{source}', 'source.{field_name}', template)
            template = re.sub(r'{target}', 'target.{field_name}', template)

        return template

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
