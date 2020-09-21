from psycopg2 import sql as psycopg2_sql
from ll.job.matching_function import MatchingFunction


class Conditions:
    def __init__(self, data, type, job):
        self._data = data
        self._type = type
        self._job = job

        self._conditions_list = None
        self._operator = 'AND' if type in ['MINIMUM_T_NORM', 'PRODUCT_T_NORM', 'LUKASIEWICZ_T_NORM',
                                           'DRASTIC_T_NORM', 'NILPOTENT_MINIMUM', 'HAMACHER_PRODUCT'] else 'OR'

    @property
    def conditions_list(self):
        if not self._conditions_list:
            self._conditions_list = []
            for idx, item in enumerate(self._data):
                if 'conditions' in item and 'type' in item:
                    self._conditions_list.append(Conditions(item['conditions'], item['type'], self._job))
                else:
                    self._conditions_list.append(MatchingFunction(item, self._job))

        return self._conditions_list

    @property
    def conditions_sql(self):
        filter_sqls = []
        for condition in self.conditions_list:
            if isinstance(condition, MatchingFunction):
                filter_sqls.append(condition.sql)
            else:
                filter_sqls.append(condition.conditions_sql)

        return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' %s ' % self._operator).join(filter_sqls))

    @property
    def similarity_sql(self):
        similarity_sqls = []
        for condition in self.conditions_list:
            if isinstance(condition, MatchingFunction):
                if condition.similarity_sql:
                    similarity_sqls.append(condition.similarity_sql)
            else:
                similarity_sqls.append(condition.similarity_sql)

        if not similarity_sqls:
            return psycopg2_sql.Literal(1)

        sim_sql = similarity_sqls.pop()
        while similarity_sqls:
            sim_sql = psycopg2_sql.SQL('logic_ops({operation}, {a}, {b})').format(
                operation=psycopg2_sql.Literal(self._type),
                a=sim_sql,
                b=similarity_sqls.pop()
            )

        return sim_sql

    @property
    def matching_functions(self):
        matching_functions = []
        for condition in self.conditions_list:
            if isinstance(condition, MatchingFunction):
                matching_functions.append(condition)
            else:
                matching_functions += condition.matching_functions

        return matching_functions
