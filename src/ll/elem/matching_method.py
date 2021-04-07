import re

from psycopg2 import sql
from inspect import cleandoc

from ll.util.helpers import get_json_from_file
from ll.elem.matching_method_property import MatchingMethodProperty


class MatchingMethod:
    _logic_ops = get_json_from_file('logic_ops.json')
    _matching_methods = get_json_from_file('matching_methods.json')

    def __init__(self, data, job, linkset_id, id):
        self._data = data
        self._job = job

        self.field_name = 'm' + str(linkset_id) + '_' + id

        self.method_name = data['method']['name']
        self._method_config = data['method']['config']
        if self.method_name in self._matching_methods:
            self._method_info = self._matching_methods[self.method_name]
        else:
            raise NameError('Matching method %s is not defined' % self.method_name)

        self.method_sim_name = data['sim_method']['name']
        self._method_sim_config = data['sim_method']['config']
        self._method_sim_normalized = data['sim_method']['normalized']
        self._method_sim_info = self._matching_methods[self.method_sim_name] \
            if self.method_sim_name in self._matching_methods else {}

        self._t_conorm = data['fuzzy']['t_conorm']
        self._threshold = data['fuzzy']['threshold']

        self._list_threshold = data['list_matching']['threshold']
        self._list_is_percentage = data['list_matching']['is_percentage']

        self._sources, self._targets, self._intermediates = None, None, None

    @property
    def is_intermediate(self):
        return self.method_name == 'INTERMEDIATE'

    @property
    def is_list_match(self):
        return self._list_threshold > 0

    @property
    def sql(self):
        return self._sql(self._full_matching_template, self._similarity_template, match_sql=True)

    @property
    def similarity_sql(self):
        return self._sql(self._full_matching_template, self._similarity_template, match_sql=False) \
            if self._similarity_template else None

    @property
    def similarity_logic_ops_sql(self):
        if self.similarity_sql:
            return sql.SQL('(SELECT {function}(x) FROM unnest(sim.{field}) AS x)').format(
                function=sql.SQL(self._logic_ops[self._t_conorm]['sql_agg']),
                field=sql.Identifier(self.field_name)
            )

        return None

    @property
    def similarity_threshold_sql(self):
        if self.similarity_logic_ops_sql and self._threshold:
            return sql.SQL('{similarity} >= {threshold}').format(
                similarity=self.similarity_logic_ops_sql,
                threshold=sql.Literal(self._threshold)
            )

        return None

    @property
    def index_sql(self):
        if self.is_list_match:
            return None

        index_sqls = [sql.SQL('CREATE INDEX ON target USING btree ({});')
                          .format(sql.Identifier(self.field_name))]

        if self._method_info.get('field'):
            index_sqls.append(sql.SQL('CREATE INDEX ON target USING btree ({});')
                              .format(sql.Identifier(self.field_name + '_norm')))

        for before_index in [method_info['before_index'] for method_info in [self._method_info, self._method_sim_info]
                             if 'before_index' in method_info]:
            index_sqls.append(sql.SQL(before_index).format(
                target=sql.Identifier(self.field_name),
                target_intermediate=sql.Identifier(self.field_name + '_intermediate'),
                **self._sql_parameters
            ))

        for index in [method_info['index'] for method_info in [self._method_info, self._method_sim_info]
                      if 'index' in method_info]:
            index_sqls.append(sql.SQL('CREATE INDEX ON target USING {};').format(
                sql.SQL(index).format(
                    target=sql.Identifier(self.field_name),
                    target_intermediate=sql.Identifier(self.field_name + '_intermediate'),
                    **self._sql_parameters
                )
            ))

        return sql.SQL('\n').join(index_sqls)

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
            if self.is_intermediate:
                ets_id = int(self._method_config['entity_type_selection'])
                self._intermediates[ets_id] = {
                    'source': [self._get_property(prop, ets_id, property_only=True)
                               for prop in self._method_config['intermediate_source']],
                    'target': [self._get_property(prop, ets_id, property_only=True)
                               for prop in self._method_config['intermediate_target']]
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
    def _full_matching_template(self):
        if 'field' in self._method_info and not self.method_sim_name:
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

        if self.method_sim_name and not self._method_sim_normalized:
            template = '{source_norm} = {target_norm} AND ' + template

        return self._update_template_fields(template)

    @property
    def _sql_parameters(self):
        return {key: sql.Literal(value)
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

    def _sql(self, match_template, similarity_template, match_sql=True):
        new_match_template = match_template
        new_similarity_template = similarity_template

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

            new_match_template = cleandoc(f'''	
                match_array_meets_size(ARRAY(
                    SELECT ARRAY['src' || src_idx, 'trg' || trg_idx]
                    {from_sql}
                    {join_sql}
                    ON {match_template}
                ), source.{{field_name}}, target.{{field_name}}, {{list_threshold}}, {{list_threshold_is_perc}})
            ''')

            new_similarity_template = cleandoc(f'''	
                ARRAY(
                    SELECT {similarity_template}
                    {from_sql}
                    {join_sql}
                    ON {match_template}
                )
            ''')

        return sql.SQL(new_match_template if match_sql else new_similarity_template).format(
            field_name=sql.Identifier(self.field_name),
            field_name_norm=sql.Identifier(self.field_name + '_norm'),
            field_name_intermediate=sql.Identifier(self.field_name + '_intermediate'),
            list_threshold=sql.Literal(self._list_threshold),
            list_threshold_is_perc=sql.Literal(self._list_is_percentage),
            **self._sql_parameters
        )

    def _get_properties(self, key):
        return {int(ets_id): [self._get_property(field, int(ets_id), key=key) for field in fields]
                for ets_id, fields in self._data[key]['properties'].items()}

    def _get_property(self, field, ets_id, key=None, property_only=False):
        field_type = self._method_info.get('field_type')
        field_type_info = {
            'type': field_type,
            'parameters': {'format': self._method_config['format'] if field_type == 'date' else {}}
        }

        property = field if property_only else field['property']

        transformers = []
        if key and not property_only:
            transformers = self._data[key].get('transformers', []).copy()
            if field['property_transformer_first']:
                transformers = field.get('transformers', []).copy() + transformers
            else:
                transformers = transformers + field.get('transformers', []).copy()

        return MatchingMethodProperty(property, transformers, ets_id, self._job, field_type_info,
                                      self._method_info.get('field'), self._method_config)
