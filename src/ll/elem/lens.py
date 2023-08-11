from psycopg import sql
from inspect import cleandoc

from ll.util.helpers import flatten, get_yaml_from_file


class Lens:
    _logic_ops = get_yaml_from_file('logic_ops')

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
    def threshold(self):
        return self._data['specs']['threshold'] if 0 < self._data['specs']['threshold'] < 1 else None

    @property
    def operators(self):
        lens_operators = set()
        self.with_lenses_recursive(
            lambda elem: lens_operators.add(elem['type']),
            lambda spec: lens_operators.update(spec['spec'].operators) if spec['type'] == 'lens' else set()
        )
        return lens_operators

    @property
    def linksets(self):
        return set(self.with_lenses_recursive(
            lambda elem: flatten([elem['left'], elem['right']]),
            lambda spec: spec['spec'] if spec['type'] == 'linkset' else list(spec['spec'].linksets)
        ))

    @property
    def lenses(self):
        return set(self.with_lenses_recursive(
            lambda elem: flatten([elem['left'], elem['right']]),
            lambda spec: [spec['spec']] + list(spec['spec'].lenses) if spec['type'] == 'lens' else None
        ))

    @property
    def entity_type_selections(self):
        return {ets for linkset in self.linksets for ets in linkset.entity_type_selections}

    @property
    def all_entity_type_selections(self):
        return {ets for linkset in self.linksets for ets in linkset.all_entity_type_selections}

    @property
    def sources(self):
        return {ets for linkset in self.linksets for ets in linkset.sources}

    @property
    def targets(self):
        return {ets for linkset in self.linksets for ets in linkset.targets}

    @property
    def matching_methods(self):
        return [matching_method for linkset in self.linksets for matching_method in linkset.matching_methods]

    @property
    def all_props(self):
        return set(all_props for linkset in self.linksets for all_props in linkset.all_props)

    @property
    def similarity_logic_ops_sql(self):
        return self.with_lenses_recursive(
            lambda elem: self._logic_ops_for_condition(elem),
            lambda spec: spec['spec'].similarity_logic_ops_sql
        )

    @property
    def similarity_logic_ops_sql_per_threshold(self):
        def with_logic_ops(elem):
            logic_ops = self._logic_ops_for_condition(elem)
            if elem['threshold']:
                per_threshold.append((elem['threshold'], logic_ops))

            return logic_ops

        per_threshold = []
        self.with_lenses_recursive(
            lambda elem: with_logic_ops(elem),
            lambda spec: spec['spec'].similarity_logic_ops_sql
        )

        return per_threshold

    def with_lenses_recursive(self, with_conditions, with_spec=None, depth=0, index=1):
        return self._r_lenses(self._data['specs'], with_conditions, with_spec, depth, index)

    def _r_lenses(self, lens_obj, with_conditions, with_spec, depth=0, index=1):
        if 'type' in lens_obj and 'elements' in lens_obj:
            type = lens_obj['type'].lower()
            s_norm = 'maximum_s_norm' if lens_obj['s_norm'] == '' else lens_obj['s_norm']
            threshold = lens_obj['threshold'] if lens_obj['s_norm'] != '' else 0
            only_left = type == 'difference' or type.startswith('in_set')

            left = self._r_lenses(lens_obj['elements'][0], with_conditions, with_spec, depth + 1, 1)
            right = self._r_lenses(lens_obj['elements'][1], with_conditions, with_spec, depth + 1, 2)

            return with_conditions({
                'left': left,
                'right': right,
                'type': type,
                's_norm': s_norm,
                'threshold': threshold,
                'only_left': only_left,
                'depth': depth,
                'index': index,
            })

        id = lens_obj['id']
        type = lens_obj['type']
        spec = self._job.get_spec_by_id(id, type)

        return with_spec({
            'spec': spec,
            'id': id,
            'type': type,
            'depth': depth,
            'index': index
        }) if with_spec else spec

    @staticmethod
    def _logic_ops_for_condition(elem):
        if elem['only_left'] or elem['right'] == sql.SQL('NULL'):
            return elem['left']

        if elem['left'] == sql.SQL('NULL'):
            return elem['right']

        return sql.SQL(cleandoc('''
            CASE WHEN {a} IS NULL THEN {b} 
                 WHEN {b} IS NULL THEN {a}
                 ELSE {function}({a}, {b}) END        
        ''')).format(
            function=sql.SQL(Lens._logic_ops[elem['s_norm']]['sql']),
            a=elem['left'],
            b=elem['right']
        )
