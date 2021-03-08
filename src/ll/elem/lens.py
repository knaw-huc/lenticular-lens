from psycopg2 import sql
from collections import defaultdict

from ll.job.property_field import PropertyField
from ll.util.helpers import flatten, get_json_from_file


class Lens:
    _logic_ops = get_json_from_file('logic_ops.json')

    def __init__(self, data, job):
        self._data = data
        self._job = job
        self._specs = None

    @property
    def id(self):
        return self._data['id']

    @property
    def label(self):
        return self._data['label'].strip()

    @property
    def description(self):
        return self._data['description'].strip()

    @property
    def properties(self):
        props = defaultdict(set)
        for prop in self._data['properties']:
            ets_id = prop['entity_type_selection']
            props[ets_id].add(PropertyField(prop['property'], self._job.get_entity_type_selection_by_id(ets_id)))

        return props

    @property
    def linksets(self):
        return set(self.with_lenses_recursive(
            lambda left, right, type, t_conorm, threshold, only_left: flatten([left, right]),
            lambda spec, id, type: spec if type == 'linkset' else list(spec.linksets)
        ))

    @property
    def lenses(self):
        return set(self.with_lenses_recursive(
            lambda left, right, type, t_conorm, threshold, only_left: flatten([left, right]),
            lambda spec, id, type: list(spec) + spec.lenses if type == 'lens' else None
        ))

    @property
    def entity_type_selections(self):
        return {ets for linkset in self.linksets for ets in linkset.entity_type_selections}

    @property
    def similarity_fields(self):
        return {field_name for linkset in self.linksets for field_name in linkset.similarity_fields}

    @property
    def similarity_logic_ops_sql(self):
        return self.with_lenses_recursive(
            lambda left, right, type, t_conorm, threshold, only_left: self._logic_ops_for_condition(
                left, right, only_left, t_conorm),
            lambda spec, id, type: spec.similarity_logic_ops_sql
        )

    @property
    def similarity_logic_ops_sql_per_threshold(self):
        def with_logic_ops(threshold, left, right, only_left, t_conorm):
            logic_ops = self._logic_ops_for_condition(left, right, only_left, t_conorm)
            if threshold:
                per_threshold.append((threshold, logic_ops))

            return logic_ops

        per_threshold = []
        self.with_lenses_recursive(
            lambda left, right, type, t_conorm, threshold, only_left: with_logic_ops(
                threshold, left, right, only_left, t_conorm),
            lambda spec, id, type: spec.similarity_logic_ops_sql
        )

        return per_threshold

    def with_lenses_recursive(self, with_conditions, with_spec=None):
        return self._r_lenses(self._data['specs'], with_conditions, with_spec)

    def _r_lenses(self, lens_obj, with_conditions, with_spec):
        if 'type' in lens_obj and 'elements' in lens_obj:
            type = lens_obj['type'].lower()
            t_conorm = 'MAXIMUM_T_CONORM' if lens_obj['t_conorm'] == '' else lens_obj['t_conorm']
            threshold = lens_obj['threshold'] if lens_obj['t_conorm'] != '' else 0
            only_left = type == 'difference' or type.startswith('in_set')

            left = self._r_lenses(lens_obj['elements'][0], with_conditions, with_spec)
            right = self._r_lenses(lens_obj['elements'][1], with_conditions, with_spec)

            return with_conditions(left, right, type, t_conorm, threshold, only_left)

        id = lens_obj['id']
        type = lens_obj['type']
        spec = self._job.get_spec_by_id(id, type)
        return with_spec(spec, id, type) if with_spec else spec

    @staticmethod
    def _logic_ops_for_condition(left, right, only_left, t_conorm):
        if only_left or right == sql.SQL('NULL'):
            return left

        if left == sql.SQL('NULL'):
            return right

        return sql.SQL('{function}({a}, {b})').format(
            function=sql.SQL(Lens._logic_ops[t_conorm]['sql']),
            a=left,
            b=right
        )
