from psycopg2 import sql

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
    def use_counter(self):
        return self._data.get('use_counter', True)

    @property
    def matching_methods(self):
        return self.with_matching_methods_recursive(lambda c, operator, fuzzy, threshold: flatten(c))

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
        return set(self.with_matching_methods_recursive(
            lambda ets_ids, operator, fuzzy, threshold: flatten(ets_ids),
            lambda matching_method: [self._job.get_entity_type_selection_by_id(ets_id)
                                     for ets_id in matching_method.intermediates.keys()]
        ))

    @property
    def similarity_fields(self):
        return {match_method.field_name for match_method in self.matching_methods if match_method.similarity_sql}

    @property
    def similarity_logic_ops_sql(self):
        return self.with_matching_methods_recursive(
            lambda sqls, operator, fuzzy, threshold: self._logic_ops_for_condition(sqls, fuzzy, self._logic_ops),
            lambda matching_method: matching_method.similarity_logic_ops_sql
        )

    @property
    def similarity_logic_ops_sql_per_threshold(self):
        def with_logic_ops(sqls, fuzzy, threshold):
            logic_ops = self._logic_ops_for_condition(sqls, fuzzy, self._logic_ops)
            if threshold:
                per_threshold.append((threshold, logic_ops))

            return logic_ops

        per_threshold = []
        self.with_matching_methods_recursive(
            lambda sqls, operator, fuzzy, threshold: with_logic_ops(sqls, fuzzy, threshold),
            lambda matching_method: matching_method.similarity_logic_ops_sql
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

    def _r_matching_methods(self, methods_obj, with_conditions, with_matching_method, id=''):
        if 'type' in methods_obj:
            type = methods_obj['type']
            operator = type if type == 'AND' or type == 'OR' else \
                'AND' if type in ['MINIMUM_T_NORM', 'PRODUCT_T_NORM', 'LUKASIEWICZ_T_NORM',
                                  'DRASTIC_T_NORM', 'NILPOTENT_MINIMUM', 'HAMACHER_PRODUCT'] else 'OR'
            fuzzy = type if type != 'AND' and type != 'OR' else \
                'MINIMUM_T_NORM' if type == 'AND' else 'MAXIMUM_T_CONORM'

            threshold = methods_obj['threshold']
            conditions = [self._r_matching_methods(condition, with_conditions, with_matching_method, id + str(idx))
                          for idx, condition in enumerate(methods_obj['conditions'])]

            return with_conditions(conditions, operator, fuzzy, threshold) if with_conditions else conditions

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

    @staticmethod
    def _logic_ops_for_condition(sqls, fuzzy, logic_ops):
        similarity_sqls = [sim_sql for sim_sql in sqls if sim_sql]
        if not similarity_sqls:
            return sql.SQL('NULL')

        sim_sql = similarity_sqls.pop()
        while similarity_sqls:
            sim_sql = sql.SQL('{function}({a}, {b})').format(
                function=sql.SQL(logic_ops[fuzzy]['sql']),
                a=sim_sql,
                b=similarity_sqls.pop()
            )

        return sim_sql
