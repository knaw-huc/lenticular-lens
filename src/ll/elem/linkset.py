from psycopg import sql

from ll.elem.matching_method import MatchingMethod
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
    def use_counter(self):
        return self._data.get('use_counter', True)

    @property
    def matching_methods(self):
        return self.with_matching_methods_recursive(lambda condition: flatten(condition['children']))

    @property
    def all_props(self):
        props = {(ets, prop.prop_original)
                 for matching_method in self.matching_methods
                 for ets, props_ets in (matching_method.sources | matching_method.targets).items()
                 for prop in props_ets}

        return props.union({(ets, prop.prop_original)
                            for matching_method in self.matching_methods
                            for ets, props_ets in matching_method.intermediates.items()
                            for prop in (props_ets['source'] + props_ets['target'])
                            if matching_method.is_intermediate})

    @property
    def entity_type_selections(self):
        return self.sources.union(self.targets)

    @property
    def all_entity_type_selections(self):
        return self.entity_type_selections.union(self.intermediates)

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
    def similarity_logic_ops_sql(self):
        return self.with_matching_methods_recursive(
            lambda condition: self._logic_ops_for_condition(condition, self._logic_ops),
            lambda mm: mm['matching_method'].similarity_logic_ops_sql
        )

    @property
    def similarity_logic_ops_sql_per_threshold(self):
        def with_logic_ops(condition):
            logic_ops = self._logic_ops_for_condition(condition, self._logic_ops)
            if condition['threshold']:
                per_threshold.append((condition['threshold'], logic_ops))

            return logic_ops

        per_threshold = []
        self.with_matching_methods_recursive(
            lambda condition: with_logic_ops(condition),
            lambda mm: mm['matching_method'].similarity_logic_ops_sql
        )

        return per_threshold

    def get_fields(self, keys=None):
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
    def _logic_ops_for_condition(condition, logic_ops):
        similarity_sqls = [sim_sql for sim_sql in condition['children'] if sim_sql]
        if not similarity_sqls:
            return sql.SQL('NULL')

        sim_sql = similarity_sqls.pop()
        while similarity_sqls:
            sim_sql = sql.SQL('{function}({a}, {b})').format(
                function=sql.SQL(logic_ops[condition['fuzzy']]['sql']),
                a=sim_sql,
                b=similarity_sqls.pop()
            )

        return sim_sql
