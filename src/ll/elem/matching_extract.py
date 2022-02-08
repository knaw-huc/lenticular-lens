from psycopg2 import sql

from ll.job.property_field import PropertyField

from ll.util.helpers import get_yaml_from_file
from ll.util.db_functions import get_transformers


class MatchingExtract:
    _logic_ops = get_yaml_from_file('logic_ops')
    _transformers_info = get_transformers()

    def __init__(self, data, job, linkset_id, ets_id):
        self._data = data
        self._job = job
        self._ets_id = ets_id

        self.field_name = 'e' + str(linkset_id) + '_' + str(ets_id)

    @property
    def threshold(self):
        return self._data['threshold']

    @property
    def entity_type_selection(self):
        return self._job.get_entity_type_selection_by_id(self._ets_id)

    @property
    def referenced_entity_type_selections(self):
        return set(self._job.get_entity_type_selection_by_id(int(entity_type_selection))
                   for entity_type_selection in self._data['entity_type_selections'])

    @property
    def sources(self):
        return {PropertyField(property, entity_type_selection=self.entity_type_selection)
                for property in self._data['sources']}

    @property
    def targets(self):
        return {PropertyField(property, entity_type_selection=self.entity_type_selection)
                for property in self._data['targets']}

    @property
    def strengths(self):
        return {PropertyField(property, entity_type_selection=self.entity_type_selection, transformers=[{
            'sql_template': self._transformers_info['to_numeric_immutable']['sql_template'],
            'parameters': {}
        }]) for property in self._data['strengths']}

    @property
    def similarity_logic_ops_sql(self):
        if self._data['strengths']:
            return sql.SQL('(SELECT {s_norm_func}(x) FROM unnest(sim.{field}) AS x)').format(
                s_norm_func=sql.SQL(self._logic_ops[self._data['s_norm']]['sql_agg']),
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
