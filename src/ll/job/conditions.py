from psycopg2 import sql as psycopg2_sql
from ll.job.matching_mehod import MatchingMethod


class Conditions:
    def __init__(self, data, type, job, linkset_id, id_pref=''):
        self._data = data
        self._type = type
        self._job = job
        self._linkset_id = linkset_id
        self._id_pref = id_pref

        self._conditions = None
        self._operator = type if type == 'AND' or type == 'OR' else \
            'AND' if type in ['MINIMUM_T_NORM', 'PRODUCT_T_NORM', 'LUKASIEWICZ_T_NORM',
                              'DRASTIC_T_NORM', 'NILPOTENT_MINIMUM', 'HAMACHER_PRODUCT'] else 'OR'
        self._fuzzy = type if type != 'AND' and type != 'OR' else \
            'MINIMUM_T_NORM' if type == 'AND' else 'MAXIMUM_T_CONORM'

    @property
    def similarity_fields(self):
        return [match_method.field_name for match_method in self._matching_methods if match_method.similarity_sql]

    @property
    def index_sql(self):
        index_sqls = [matching_method.index_sql
                      for matching_method in self._matching_methods
                      if matching_method.index_sql]

        return psycopg2_sql.SQL('\n').join(index_sqls) if index_sqls else None

    @property
    def conditions_sql(self):
        condition_sqls = [condition.sql if isinstance(condition, MatchingMethod) else condition.conditions_sql
                          for condition in self._conditions_list]

        return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' %s ' % self._operator).join(condition_sqls))

    @property
    def similarity_fields_agg_sql(self):
        fields = {}
        fields_added = []

        for match_func in self._matching_methods:
            if match_func.similarity_sql:
                name = match_func.field_name

                # Add source and target values; if not done already
                if name not in fields_added:
                    fields_added.append(name)
                    fields[name] = match_func.similarity_sql

        fields_sql = [psycopg2_sql.SQL('{}, array_agg(DISTINCT {})').format(psycopg2_sql.Literal(name), sim)
                      for name, sim in fields.items()]

        return psycopg2_sql.SQL('jsonb_build_object({})').format(psycopg2_sql.SQL(', ').join(fields_sql)) \
            if fields_sql else psycopg2_sql.SQL('NULL::jsonb')

    @property
    def similarity_logic_ops_sql(self):
        similarity_sqls = []
        for condition in self._conditions_list:
            if isinstance(condition, MatchingMethod):
                if condition.similarity_logic_ops_sql:
                    similarity_sqls.append(condition.similarity_logic_ops_sql)
            else:
                similarity_sqls.append(condition.similarity_logic_ops_sql)

        if not similarity_sqls:
            return psycopg2_sql.SQL('NULL')

        sim_sql = similarity_sqls.pop()
        while similarity_sqls:
            sim_sql = psycopg2_sql.SQL('logic_ops({operation}, {a}, {b})').format(
                operation=psycopg2_sql.Literal(self._type),
                a=sim_sql,
                b=similarity_sqls.pop()
            )

        return sim_sql

    @property
    def similarity_threshold_sqls(self):
        return [match_method.similarity_threshold_sql
                for match_method in self._matching_methods
                if match_method.similarity_threshold_sql]

    @property
    def update_keys_mm(self):
        return self._matching_methods

    def get_fields(self, keys=None, only_matching_fields=True):
        if not isinstance(keys, list):
            keys = ['sources', 'targets', 'intermediates']

        # Regroup properties by entity-type selection instead of by method
        ets_properties = {}
        for matching_method in self._matching_methods:
            for key in keys:
                for internal_id, properties in getattr(matching_method, key).items():
                    if key == 'sources' or key == 'targets':
                        for property in properties:
                            self._set_field(internal_id, property, matching_method,
                                            ets_properties, only_matching_fields)
                    else:
                        self._set_field(internal_id, properties['source'], matching_method,
                                        ets_properties, only_matching_fields)
                        self._set_field(internal_id, properties['target'], matching_method,
                                        ets_properties, only_matching_fields)

        return ets_properties

    @property
    def _conditions_list(self):
        if not self._conditions:
            self._conditions = [
                Conditions(item['conditions'], item['type'], self._job, self._linkset_id, self._id_pref + str(idx))
                if 'conditions' in item and 'type' in item else
                MatchingMethod(item, self._job, self._linkset_id, self._id_pref + str(idx))
                for idx, item in enumerate(self._data)
            ]

        return self._conditions

    @property
    def _matching_methods(self):
        matching_methods = []
        for condition in self._conditions_list:
            if isinstance(condition, MatchingMethod):
                matching_methods.append(condition)
            else:
                matching_methods += condition._matching_methods

        return matching_methods

    @staticmethod
    def _set_field(internal_id, property, matching_method, ets_properties, only_matching_fields):
        ets_internal_id = internal_id if only_matching_fields \
            else property.prop_original.entity_type_selection_internal_id

        if ets_internal_id not in ets_properties:
            ets_properties[ets_internal_id] = {}

        if matching_method.field_name not in ets_properties[ets_internal_id]:
            ets_properties[ets_internal_id][matching_method.field_name] = {
                'matching_method': matching_method,
                'properties': []
            }

        props = ets_properties[ets_internal_id][matching_method.field_name]['properties']
        props.append(property)
