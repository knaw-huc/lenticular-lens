from psycopg import sql

from ll.elem.matching_method import MatchingMethod
from ll.elem.matching_extract import MatchingExtract

from ll.util.helpers import flatten, get_yaml_from_file


class Linkset:
    _logic_ops = get_yaml_from_file('logic_ops')

    def __init__(self, data, job):
        self._data = data
        self._job = job

    @property
    def id(self):
        return self._data['id']

    @property
    def label(self):
        return self._data['label']

    @property
    def description(self):
        return self._data['description']

    @property
    def matching(self):
        return self._data['matching']

    @property
    def use_counter(self):
        return self._data.get('use_counter', True)

    @property
    def matching_methods(self):
        return self.with_matching_methods_recursive(lambda condition: flatten(condition['children']))

    @property
    def matching_extract(self):
        return [MatchingExtract(extract_data, self._job, self.id, int(ets_id))
                for ets_id, extract_data in self._data['extract']['elements'].items()]

    @property
    def all_props(self):
        # Add matching method props
        props = {(ets, prop.prop_original)
                 for matching_method in self.matching_methods
                 for ets, props_ets in (matching_method.sources | matching_method.targets).items()
                 for prop in props_ets}

        # Add intermediate props
        props = props.union({(ets, prop.prop_original)
                             for matching_method in self.matching_methods
                             for ets, props_ets in matching_method.intermediates.items()
                             for prop in (props_ets['source'] + props_ets['target'])
                             if matching_method.is_intermediate})

        # Add extract props
        return props.union({(matching_extract.entity_type_selection, prop)
                            for matching_extract in self.matching_extract
                            for prop in (matching_extract.sources |
                                         matching_extract.targets | matching_extract.strengths)})

    @property
    def entity_type_selections(self):
        return self.sources.union(self.targets)

    @property
    def all_entity_type_selections(self):
        return self.entity_type_selections.union(self.intermediates).union(self.referenced_entity_type_selections)

    @property
    def sources(self):
        return {self._job.get_entity_type_selection_by_id(ets_id) for ets_id in self._data['sources']}

    @property
    def targets(self):
        return {self._job.get_entity_type_selection_by_id(ets_id) for ets_id in self._data['targets']}

    @property
    def intermediates(self):
        return set(self.with_matching_methods_recursive(
            lambda condition: flatten(condition['children']),
            lambda mm: [self._job.get_entity_type_selection_by_id(ets_id)
                        for ets_id in mm['matching_method'].intermediates.keys()]
        ))

    @property
    def referenced_entity_type_selections(self):
        return set().union(*[extract.referenced_entity_type_selections for extract in self.matching_extract])

    @property
    def methods_similarity_fields_sqls(self):
        return [sql.Composed([
            sql.Identifier(match_method.field_name),
            sql.SQL(' jsonb') if match_method.is_list_match else sql.SQL(' numeric[]')
        ]) for match_method in self.matching_methods if match_method.similarity_sql]

    @property
    def extract_similarity_fields_sqls(self):
        return [sql.SQL('{} numeric[]').format(sql.Identifier(match_extract.field_name))
                for match_extract in self.matching_extract if match_extract.strengths]

    @property
    def similarity_fields_sqls(self):
        return self.methods_similarity_fields_sqls + self.extract_similarity_fields_sqls

    @property
    def similarity_joins_sqls(self):
        return [sql.SQL('CROSS JOIN LATERAL jsonb_to_record(sim.{}) AS {}'
                        '(scores numeric[], size integer)').format(
            sql.Identifier(match_method.field_name),
            sql.Identifier('sim_' + match_method.field_name)
        ) for match_method in self.matching_methods if match_method.similarity_sql and match_method.is_list_match]

    @property
    def similarity_logic_ops_sql(self):
        if self.matching == 'matching':
            return self.with_matching_methods_recursive(
                lambda condition: self._logic_ops_for_condition(condition),
                lambda mm: mm['matching_method'].similarity_logic_ops_sql
            )

        return self._logic_ops_for(self._data['extract']['s_norm'],
                                   [match_extract.similarity_logic_ops_sql for match_extract in self.matching_extract
                                    if match_extract.similarity_logic_ops_sql])

    @property
    def similarity_logic_ops_sql_per_threshold(self):
        def with_logic_ops(condition):
            logic_ops = self._logic_ops_for_condition(condition)
            if condition['threshold']:
                per_threshold.append((condition['threshold'], logic_ops))

            return logic_ops

        per_threshold = []
        self.with_matching_methods_recursive(
            lambda condition: with_logic_ops(condition),
            lambda mm: mm['matching_method'].similarity_logic_ops_sql
        )

        if self.matching == 'extract' and self._data['extract']['threshold']:
            per_threshold.append((self._data['extract']['threshold'], self.similarity_logic_ops_sql))

        return per_threshold

    def get_extract_fields(self, keys=None):
        if not isinstance(keys, list):
            keys = ['sources', 'targets', 'strengths']

        return {
            match_extract.entity_type_selection.id: set().union(*[getattr(match_extract, key) for key in keys])
            for match_extract in self.matching_extract
        }

    def get_matching_fields(self, keys=None):
        if not isinstance(keys, list):
            keys = ['sources', 'targets', 'intermediates']

        # Regroup properties by entity-type selection instead of by method
        ets_properties = {}
        for matching_method in self.matching_methods:
            for key in keys:
                for ets_id, properties in getattr(matching_method, key).items():
                    for property in (properties['source'] + properties['target']) \
                            if key == 'intermediates' else properties:
                        self._set_field(ets_id, property, matching_method, ets_properties)

        return ets_properties

    def with_matching_methods_recursive(self, with_conditions, with_matching_method=None):
        return self._r_matching_methods(self._data['methods'], with_conditions, with_matching_method)

    def _r_matching_methods(self, methods_obj, with_conditions, with_matching_method, id='', depth=0, index=1):
        if 'type' in methods_obj:
            type = methods_obj['type']
            operator = type if type == 'and' or type == 'or' else \
                'and' if type in ['minimum_t_norm', 'product_t_norm', 'lukasiewicz_t_norm',
                                  'drastic_t_norm', 'nilpotent_minimum', 'hamacher_product'] else 'or'
            fuzzy = type if type != 'and' and type != 'or' else \
                'minimum_t_norm' if type == 'and' else 'maximum_s_norm'

            threshold = methods_obj['threshold']
            conditions = [self._r_matching_methods(condition, with_conditions, with_matching_method,
                                                   id + str(idx), depth + 1, idx + 1)
                          for idx, condition in enumerate(methods_obj['conditions'])]

            return with_conditions({
                'children': conditions,
                'operator': operator,
                'fuzzy': fuzzy,
                'threshold': threshold,
                'depth': depth,
                'index': index,
            }) if with_conditions else conditions

        matching_method = MatchingMethod(methods_obj, self._job, self.id, id)
        return with_matching_method({'matching_method': matching_method,
                                     'depth': depth,
                                     'index': index}) if with_matching_method else matching_method

    @staticmethod
    def _set_field(ets_id, property, matching_method, ets_properties):
        if ets_id not in ets_properties:
            ets_properties[ets_id] = {}

        if matching_method.field_name not in ets_properties[ets_id]:
            ets_properties[ets_id][matching_method.field_name] = {
                'matching_method': matching_method,
                'properties': set()
            }

        props = ets_properties[ets_id][matching_method.field_name]['properties']
        props.add(property)

    @staticmethod
    def _logic_ops_for_condition(condition):
        return Linkset._logic_ops_for(condition['fuzzy'], [sim_sql for sim_sql in condition['children'] if sim_sql])

    @staticmethod
    def _logic_ops_for(logic_ops_key, similarity_sqls):
        if not similarity_sqls:
            return sql.SQL('NULL')

        sim_sql = similarity_sqls.pop()
        while similarity_sqls:
            sim_sql = sql.SQL('{function}({a}, {b})').format(
                function=sql.SQL(Linkset._logic_ops[logic_ops_key]['sql']),
                a=sim_sql,
                b=similarity_sqls.pop()
            )

        return sim_sql
