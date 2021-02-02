import re

from inspect import cleandoc
from psycopg2 import sql as psycopg2_sql

from ll.util.helpers import get_json_from_file
from ll.data.property_field import PropertyField
from ll.job.matching_method_property import MatchingMethodProperty


class MatchingMethod:
    _matching_methods = get_json_from_file('matching_methods.json')

    def __init__(self, data, job, linkset_id, id):
        self._data = data
        self._job = job

        self.field_name = 'm' + str(linkset_id) + '_' + id

        self.method_name = data['method_name']
        self._method_config = data['method_config']
        if self.method_name in self._matching_methods:
            self._method_info = self._matching_methods[self.method_name]
        else:
            raise NameError('Matching method %s is not defined' % self.method_name)

        self._method_sim_name = data['method_sim_name']
        self._method_sim_config = data['method_sim_config']
        self._method_sim_normalized = data['method_sim_normalized']
        self._method_sim_info = self._matching_methods[self._method_sim_name] \
            if self._method_sim_name in self._matching_methods else {}

        self._t_conorm = data['t_conorm']
        self._threshold = data['threshold']

        self.is_list_match = data['list_matching']['threshold'] > 0 or data['list_matching']['unique_threshold'] > 0
        self._list_threshold = data['list_matching']['threshold']
        self._list_unique_threshold = data['list_matching']['unique_threshold']
        self._list_is_percentage = data['list_matching']['is_percentage']
        self._list_unique_is_percentage = data['list_matching']['unique_is_percentage']

        self._sources, self._targets, self._intermediates = None, None, None

    @property
    def sql(self):
        if 'field' in self._method_info and not self._method_sim_name:
            template = '{source_norm} = {target_norm}'
        else:
            template = self._condition_template
            if template:
                if self._match_template:
                    template = re.sub(r'{match}', self._match_template, template)
                if self._similarity_template:
                    template = re.sub(r'{similarity}', self._similarity_template, template)
            else:
                template = self._match_template

        if self._method_sim_name and not self._method_sim_normalized:
            template = '{source_norm} = {target_norm} AND ' + template

        template = self._update_template_fields(template)

        return self._sql(template, list_check=True) if template else None

    @property
    def similarity_sql(self):
        return self._sql(self._similarity_template, list_check=False) if self._similarity_template else None

    @property
    def similarity_logic_ops_sql(self):
        if self.similarity_sql:
            return psycopg2_sql.SQL('logic_ops({operation}, sim.{field})').format(
                operation=psycopg2_sql.Literal(self._t_conorm),
                field=psycopg2_sql.Identifier(self.field_name)
            )

        return None

    @property
    def similarity_threshold_sql(self):
        if self.similarity_logic_ops_sql and self._threshold:
            return psycopg2_sql.SQL('{similarity} >= {threshold}').format(
                similarity=self.similarity_logic_ops_sql,
                threshold=psycopg2_sql.Literal(self._threshold)
            )

        return None

    @property
    def index_sql(self):
        if self.is_list_match:
            return None

        index_sqls = [psycopg2_sql.SQL('CREATE INDEX ON target USING btree ({});')
                          .format(psycopg2_sql.Identifier(self.field_name))]

        if self._method_info.get('field'):
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING btree ({});')
                              .format(psycopg2_sql.Identifier(self.field_name + '_norm')))

        for before_index in [method_info['before_index'] for method_info in [self._method_info, self._method_sim_info]
                             if 'before_index' in method_info]:
            index_sqls.append(psycopg2_sql.SQL(before_index).format(
                target=psycopg2_sql.Identifier(self.field_name),
                target_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
                **self._sql_parameters
            ))

        for index in [method_info['index'] for method_info in [self._method_info, self._method_sim_info]
                      if 'index' in method_info]:
            index_sqls.append(psycopg2_sql.SQL('CREATE INDEX ON target USING {};').format(
                psycopg2_sql.SQL(index).format(
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
    def _match_template(self):
        if 'match' in self._method_info:
            template = self._method_info['match']
        elif 'field' in self._method_info and 'match' in self._method_sim_info:
            template = self._method_sim_info['match']
            if self._method_sim_normalized:
                template = re.sub(r'{source}', '{source_norm}', template)
                template = re.sub(r'{target}', '{target_norm}', template)
        else:
            return None

        return self._update_template_fields(template)

    @property
    def _similarity_template(self):
        if 'similarity' in self._method_info:
            template = self._method_info['similarity']
        elif 'field' in self._method_info and 'similarity' in self._method_sim_info:
            template = self._method_sim_info['similarity']
            if self._method_sim_normalized:
                template = re.sub(r'{source}', '{source_norm}', template)
                template = re.sub(r'{target}', '{target_norm}', template)
        else:
            return None

        return self._update_template_fields(template)

    @property
    def _condition_template(self):
        if 'condition' in self._method_info:
            return self._method_info['condition']

        if 'condition' in self._method_sim_info:
            return self._method_sim_info['condition']

        return None

    @property
    def _sql_parameters(self):
        return {key: psycopg2_sql.Literal(value)
                for (key, value) in {**self._method_config, **self._method_sim_config}.items()}

    def _update_template_fields(self, template):
        if self.is_list_match:
            template = re.sub(r'{source}', 'src_org', template)
            template = re.sub(r'{target}', 'trg_org', template)
            template = re.sub(r'{source_norm}', 'src_norm', template)
            template = re.sub(r'{target_norm}', 'trg_norm', template)
        else:
            template = re.sub(r'{source}', 'source.{field_name}', template)
            template = re.sub(r'{target}', 'target.{field_name}', template)
            template = re.sub(r'{source_norm}', 'source.{field_name_norm}', template)
            template = re.sub(r'{target_norm}', 'target.{field_name_norm}', template)

        template = re.sub(r'{source_intermediate}', 'source.{field_name_intermediate}', template)
        template = re.sub(r'{target_intermediate}', 'target.{field_name_intermediate}', template)

        return template

    def _sql(self, template, list_check=True):
        if self.is_list_match:
            from_sql = \
                'FROM unnest(source.{field_name}, source.{field_name_norm}) ' \
                'WITH ORDINALITY AS src(src_org, src_norm, src_idx)' \
                    if self._method_info.get('field') else \
                    'FROM unnest(source.{field_name}) WITH ORDINALITY AS src(src_org, src_idx)'
            join_sql = \
                'JOIN unnest(target.{field_name}, target.{field_name_norm}) ' \
                'WITH ORDINALITY AS trg(trg_org, trg_norm, trg_idx)' \
                    if self._method_info.get('field') else \
                    'JOIN unnest(target.{field_name}) WITH ORDINALITY AS trg(trg_org, trg_idx)'

            if list_check:
                template = cleandoc(f'''	
                    match_array_meets_size(ARRAY(
                        SELECT ARRAY['src' || src_idx, 'trg' || trg_idx]
                        {from_sql}
                        {join_sql}
                        ON {template}
                    ), source.{{field_name}}, target.{{field_name}}, 
                       {{list_threshold}}, {{list_threshold_is_perc}}, 
                       {{list_unique_threshold}}, {{list_unique_threshold_is_perc}})
                ''')
            else:
                template = cleandoc(f'''	
                    ARRAY(
                        SELECT {template}
                        {from_sql}
                        CROSS {join_sql}
                    )
                ''')

        return psycopg2_sql.SQL(template).format(
            field_name=psycopg2_sql.Identifier(self.field_name),
            field_name_norm=psycopg2_sql.Identifier(self.field_name + '_norm'),
            field_name_intermediate=psycopg2_sql.Identifier(self.field_name + '_intermediate'),
            list_threshold=psycopg2_sql.Literal(self._list_threshold),
            list_threshold_is_perc=psycopg2_sql.Literal(self._list_is_percentage),
            list_unique_threshold=psycopg2_sql.Literal(self._list_unique_threshold),
            list_unique_threshold_is_perc=psycopg2_sql.Literal(self._list_unique_is_percentage),
            **self._sql_parameters
        )

    def _get_properties(self, key):
        properties = {}
        for entity_type_selection, fields in self._data[key].items():
            field_type = self._method_info.get('field_type')
            field_type_info = {
                'type': field_type,
                'parameters': {'format': self._method_config['format'] if field_type == 'date' else {}}
            }

            properties[entity_type_selection] = \
                [MatchingMethodProperty(field, self._job, field_type_info,
                                        self._method_info.get('field'), self._method_config)
                 for field in fields]

        return properties
