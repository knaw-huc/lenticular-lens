import re

from psycopg2 import sql
from inspect import cleandoc

from ll.util.hasher import hash_string_min
from ll.util.helpers import get_json_from_file, flatten
from ll.elem.matching_method_property import MatchingMethodProperty


class MatchingMethod:
    _logic_ops = get_json_from_file('logic_ops.json')
    _matching_methods = get_json_from_file('matching_methods.json')

    def __init__(self, data, job, linkset_id, id):
        self._data = data
        self._job = job

        self.field_name = 'm' + str(linkset_id) + '_' + id

        self.method_name = data['method']['name']
        self.method_config = data['method']['config']
        if self.method_name in self._matching_methods:
            self.method_info = self._matching_methods[self.method_name]
        else:
            raise NameError('Matching method %s is not defined' % self.method_name)

        self.method_sim_name = data['sim_method']['name']
        self.method_sim_config = data['sim_method']['config']
        self.method_sim_normalized = data['sim_method']['normalized']
        self.method_sim_info = self._matching_methods[self.method_sim_name] \
            if self.method_sim_name in self._matching_methods else {}

        self.t_norm = data['fuzzy']['t_norm']
        self.s_norm = data['fuzzy']['s_norm']
        self.threshold = data['fuzzy']['threshold'] \
            if self.method_info['is_similarity_method'] or \
               ('is_similarity_method' in self.method_sim_info and self.method_sim_info['is_similarity_method']) else 0

        self.list_threshold = data['list_matching']['threshold']
        self.list_is_percentage = data['list_matching']['is_percentage']

        self._sources, self._targets, self._intermediates = None, None, None

    @property
    def is_intermediate(self):
        return self.method_name == 'intermediate'

    @property
    def is_list_match(self):
        return self.list_threshold > 0

    @property
    def sql(self):
        return self._sql(self._full_matching_template, self._similarity_template, match_sql=True)

    @property
    def config_hash(self):
        return hash_string_min(self._data)

    @property
    def similarity_sql(self):
        return self._sql(self._full_matching_template, self._similarity_template, match_sql=False) \
            if self._similarity_template else None

    @property
    def similarity_logic_ops_sql(self):
        if self.similarity_sql:
            sub_template = 'unnest({target}.{field}) AS x'
            if self.is_list_match:
                sub_template = '(SELECT {t_norm_func}(x) ' \
                               'FROM combinations({target}.scores, {target}.size) AS c, unnest(c) AS x ' \
                               'GROUP BY c) AS scores(x)'

            return sql.SQL(f'(SELECT {{s_norm_func}}(x) FROM {sub_template})').format(
                t_norm_func=sql.SQL(self._logic_ops[self.t_norm]['sql_agg']),
                s_norm_func=sql.SQL(self._logic_ops[self.s_norm]['sql_agg']),
                target=sql.Identifier(('sim_' + self.field_name) if self.is_list_match else 'sim'),
                field=sql.Identifier(self.field_name)
            )

        return None

    @property
    def similarity_threshold_sql(self):
        if self.similarity_logic_ops_sql and self.threshold:
            return sql.SQL('{similarity} >= {threshold}').format(
                similarity=self.similarity_logic_ops_sql,
                threshold=sql.Literal(self.threshold)
            )

        return None

    @property
    def index_sql(self):
        if self.is_list_match:
            return None

        index_sqls = [sql.SQL('CREATE INDEX ON target USING btree ({});')
                          .format(sql.Identifier(self.field_name))]

        if self.method_info.get('field'):
            index_sqls.append(sql.SQL('CREATE INDEX ON target USING btree ({});')
                              .format(sql.Identifier(self.field_name + '_norm')))

        for before_index in [method_info['before_index'] for method_info in [self.method_info, self.method_sim_info]
                             if 'before_index' in method_info]:
            index_sqls.append(sql.SQL(before_index).format(
                target=sql.Identifier(self.field_name),
                target_intermediate=sql.Identifier(self.field_name + '_intermediate'),
                **self._sql_parameters
            ))

        for index in [method_info['index'] for method_info in [self.method_info, self.method_sim_info]
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
                ets_id = int(self.method_config['entity_type_selection'])
                self._intermediates[ets_id] = {
                    'source': [self._get_property(prop, ets_id, property_only=True)
                               for prop in self.method_config['intermediate_source']],
                    'target': [self._get_property(prop, ets_id, property_only=True)
                               for prop in self.method_config['intermediate_target']]
                }

        return self._intermediates

    @property
    def sources_props(self):
        return set(flatten(list(self.sources.values())))

    @property
    def targets_props(self):
        return set(flatten(list(self.targets.values())))

    @property
    def source_intermediates_props(self):
        return set(flatten([x['source'] for x in self.intermediates.values()]))

    @property
    def target_intermediates_props(self):
        return set(flatten([x['target'] for x in self.intermediates.values()]))

    @property
    def sources_hash(self):
        return hash_string_min((self.config_hash, sorted([prop.hash for prop in self.sources_props])))

    @property
    def targets_hash(self):
        return hash_string_min((self.config_hash, sorted([prop.hash for prop in self.targets_props])))

    @property
    def source_intermediates_hash(self):
        return hash_string_min((self.config_hash, sorted([prop.hash for prop in self.source_intermediates_props])))

    @property
    def target_intermediates_hash(self):
        return hash_string_min((self.config_hash, sorted([prop.hash for prop in self.target_intermediates_props])))

    @property
    def _match_template(self):
        if 'match' in self.method_info:
            template = self.method_info['match']
        elif 'field' in self.method_info and 'match' in self.method_sim_info:
            template = self.method_sim_info['match']
            if self.method_sim_normalized:
                template = re.sub(r'{source}', '{source_norm}', template)
                template = re.sub(r'{target}', '{target_norm}', template)
        else:
            return None

        return self._update_template_fields(template)

    @property
    def _similarity_template(self):
        if 'similarity' in self.method_info:
            template = self.method_info['similarity']
        elif 'field' in self.method_info and 'similarity' in self.method_sim_info:
            template = self.method_sim_info['similarity']
            if self.method_sim_normalized:
                template = re.sub(r'{source}', '{source_norm}', template)
                template = re.sub(r'{target}', '{target_norm}', template)
        else:
            return None

        return self._update_template_fields(template)

    @property
    def _condition_template(self):
        if 'condition' in self.method_info:
            return self.method_info['condition']

        if 'condition' in self.method_sim_info:
            return self.method_sim_info['condition']

        return None

    @property
    def _full_matching_template(self):
        if 'field' in self.method_info and not self.method_sim_name:
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

        if self.method_sim_name and not self.method_sim_normalized:
            template = '{source_norm} = {target_norm} AND ' + template

        return self._update_template_fields(template)

    @property
    def _sql_parameters(self):
        return {key: sql.Literal(value)
                for (key, value) in {**self.method_config, **self.method_sim_config}.items()}

    def transformers(self, key):
        return self._data[key].get('transformers', [])

    def props(self, key):
        return self.sources_props if key == 'sources' else self.targets_props

    def intermediates_props(self, key):
        return self.source_intermediates_props if key == 'sources' else self.target_intermediates_props

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
            source_fields_sqls = ['source.{field_name}']
            source_alias_sqls = ['src_org']
            if self.method_info.get('field'):
                source_fields_sqls.append('source.{field_name_norm}')
                source_alias_sqls.append('src_norm')

            target_fields_sqls = ['target.{field_name}']
            target_alias_sqls = ['trg_org']
            if self.method_info.get('field'):
                target_fields_sqls.append('target.{field_name_norm}')
                target_alias_sqls.append('trg_norm')

            list_threshold_match_template = '{list_threshold}'
            list_threshold_similarity_template = '{list_threshold}'
            if self.list_is_percentage:
                list_threshold_match_template = \
                    'array_perc_size(source.{field_name}, target.{field_name}, {list_threshold})'
                list_threshold_similarity_template = \
                    'array_perc_size(max(source.{field_name}), max(target.{field_name}), ' \
                    '{list_threshold})'

            new_match_template = cleandoc(f'''	
                match_array_meets_size(ARRAY(
                    SELECT ARRAY['src' || src_idx, 'trg' || trg_idx]
                    FROM unnest({','.join(source_fields_sqls)}) WITH ORDINALITY AS src({','.join(source_alias_sqls)}, src_idx)
                    JOIN unnest({','.join(target_fields_sqls)}) WITH ORDINALITY AS trg({','.join(target_alias_sqls)}, trg_idx)
                    ON {match_template}
                ), {list_threshold_match_template})
            ''')

            new_similarity_template = cleandoc(f'''	
                jsonb_build_object('scores', ARRAY(
                    SELECT DISTINCT {similarity_template}
                    FROM unnest({','.join([f'array_agg({field_sql}) FILTER (WHERE cardinality({field_sql}) > 0)' for field_sql in source_fields_sqls])}) AS src({','.join(source_alias_sqls)})
                    JOIN unnest({','.join([f'array_agg({field_sql}) FILTER (WHERE cardinality({field_sql}) > 0)' for field_sql in target_fields_sqls])}) AS trg({','.join(target_alias_sqls)})
                    ON {match_template}
                ), 'size', {list_threshold_similarity_template})
            ''')
        else:
            new_similarity_template = f'array_agg(DISTINCT {new_similarity_template})'

        return sql.SQL(new_match_template if match_sql else new_similarity_template).format(
            field_name=sql.Identifier(self.field_name),
            field_name_norm=sql.Identifier(self.field_name + '_norm'),
            field_name_intermediate=sql.Identifier(self.field_name + '_intermediate'),
            list_threshold=sql.Literal(self.list_threshold),
            list_threshold_is_perc=sql.Literal(self.list_is_percentage),
            **self._sql_parameters
        )

    def _get_properties(self, key):
        return {int(ets_id): [self._get_property(field, int(ets_id), key=key) for field in fields]
                for ets_id, fields in self._data[key]['properties'].items()}

    def _get_property(self, field, ets_id, key=None, property_only=False):
        field_type = self.method_info.get('field_type')
        field_type_info = {
            'type': field_type,
            'parameters': {'format': self.method_config.get('format', 'YYYY-MM-DD') if field_type == 'date' else {}}
        }

        property = field if property_only else field['property']
        apply_transformers = bool(key and not property_only)
        method_transformers = self.transformers(key) if apply_transformers else []
        property_transformers = field.get('transformers', []) if apply_transformers else []
        property_transformer_first = field.get('property_transformer_first', False) if apply_transformers else False

        return MatchingMethodProperty(property, ets_id, self._job, apply_transformers,
                                      method_transformers, property_transformers, property_transformer_first,
                                      field_type_info, self.method_info.get('field'), self.method_config)

    @staticmethod
    def get_similarity_fields_sqls(matching_methods):
        lateral_joins_sqls = []
        similarity_fields_sqls = []

        for match_method in matching_methods:
            if match_method.similarity_sql:
                similarity_fields_sqls.append(sql.Composed([
                    sql.Identifier(match_method.field_name),
                    sql.SQL(' jsonb') if match_method.is_list_match else sql.SQL(' numeric[]')
                ]))

                if match_method.is_list_match:
                    lateral_joins_sqls.append(sql.SQL('CROSS JOIN LATERAL jsonb_to_record(sim.{}) AS {}'
                                                      '(scores numeric[], size integer)').format(
                        sql.Identifier(match_method.field_name),
                        sql.Identifier('sim_' + match_method.field_name),
                    ))

        if similarity_fields_sqls:
            lateral_joins_sqls.insert(0, sql.SQL('CROSS JOIN LATERAL jsonb_to_record(similarities) AS sim({})').format(
                sql.SQL(', ').join(similarity_fields_sqls)
            ))

        return lateral_joins_sqls
