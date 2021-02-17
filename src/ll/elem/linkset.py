from psycopg2 import sql
from collections import defaultdict

from ll.job.property_field import PropertyField
from ll.elem.matching_method import MatchingMethod
from ll.util.helpers import flatten, get_json_from_file


class Linkset:
    _logic_ops = get_json_from_file('logic_ops.json')

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
    def threshold(self):
        return self._data['threshold']

    @property
    def is_association(self):
        return self._data.get('is_association', False)

    @property
    def use_counter(self):
        return self._data.get('use_counter', True)

    @property
    def properties(self):
        props = defaultdict(set)
        for prop in self._data['properties']:
            ets_id = prop['entity_type_selection']
            props[ets_id].add(PropertyField(prop['property'], self._job.get_entity_type_selection_by_id(ets_id)))

        return props

    @property
    def matching_methods(self):
        return self.with_matching_methods_recursive(lambda c, operator, fuzzy: flatten(c))

    @property
    def entity_type_selections(self):
        return self.sources.union(self.targets).union(self.intermediates)

    @property
    def sources(self):
        return {self._job.get_entity_type_selection_by_id(ets_id) for ets_id in self._data['sources']}

    @property
    def targets(self):
        return {self._job.get_entity_type_selection_by_id(ets_id) for ets_id in self._data['targets']}

    @property
    def intermediates(self):
        return {self._job.get_entity_type_selection_by_id(ets_id) for ets_id in self._data['intermediates']}

    @property
    def similarity_fields(self):
        return {match_method.field_name for match_method in self.matching_methods if match_method.similarity_sql}

    @property
    def similarity_logic_ops_sql(self):
        def logic_ops_for_condition(sqls, fuzzy):
            similarity_sqls = [sim_sql for sim_sql in sqls if sim_sql]
            if not similarity_sqls:
                return sql.SQL('NULL')

            sim_sql = similarity_sqls.pop()
            while similarity_sqls:
                sim_sql = sql.SQL('{function}({a}, {b})').format(
                    function=sql.SQL(self._logic_ops[fuzzy]['sql']),
                    a=sim_sql,
                    b=similarity_sqls.pop()
                )

            return sim_sql

        return self.with_matching_methods_recursive(
            lambda sqls, operator, fuzzy: logic_ops_for_condition(sqls, fuzzy),
            lambda matching_method: matching_method.similarity_logic_ops_sql
        )

    def get_fields(self, keys=None):
        if not isinstance(keys, list):
            keys = ['sources', 'targets', 'intermediates']

        # Regroup properties by entity-type selection instead of by method
        ets_properties = {}
        for matching_method in self.matching_methods:
            for key in keys:
                for ets_id, properties in getattr(matching_method, key).items():
                    if key == 'sources' or key == 'targets':
                        for property in properties:
                            self._set_field(ets_id, property, matching_method, ets_properties)
                    else:
                        self._set_field(ets_id, properties['source'], matching_method, ets_properties)
                        self._set_field(ets_id, properties['target'], matching_method, ets_properties)

        return ets_properties

    def with_matching_methods_recursive(self, with_conditions, with_matching_method=None):
        return self._r_matching_methods(self._data['methods'], with_conditions, with_matching_method)

    def _r_matching_methods(self, methods_obj, with_conditions, with_matching_method, id=''):
        if 'type' in methods_obj:
            type = methods_obj['type']
            operator = type if type == 'AND' or type == 'OR' else \
                'AND' if type in ['MINIMUM_T_NORM', 'PRODUCT_T_NORM', 'LUKASIEWICZ_T_NORM',
                                  'DRASTIC_T_NORM', 'NILPOTENT_MINIMUM', 'HAMACHER_PRODUCT'] else 'OR'
            fuzzy = type if type != 'AND' and type != 'OR' else \
                'MINIMUM_T_NORM' if type == 'AND' else 'MAXIMUM_T_CONORM'

            conditions = [self._r_matching_methods(condition, with_conditions, with_matching_method, id + str(idx))
                          for idx, condition in enumerate(methods_obj['conditions'])]

            return with_conditions(conditions, operator, fuzzy) if with_conditions else conditions

        matching_method = MatchingMethod(methods_obj, self._job, self.id, id)
        return with_matching_method(matching_method) if with_matching_method else matching_method

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
