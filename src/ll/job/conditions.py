from psycopg2 import sql as psycopg2_sql
from ll.job.matching_mehod import MatchingMethod


class Conditions:
    def __init__(self, data, type, job):
        self._data = data
        self._type = type
        self._job = job

        self._conditions_list = None
        # self._operator = 'AND' if type in ['MINIMUM_T_NORM', 'PRODUCT_T_NORM', 'LUKASIEWICZ_T_NORM',
        #                                    'DRASTIC_T_NORM', 'NILPOTENT_MINIMUM', 'HAMACHER_PRODUCT'] else 'OR'

    @property
    def conditions_list(self):
        if not self._conditions_list:
            self._conditions_list = []
            for idx, item in enumerate(self._data):
                if 'conditions' in item and 'type' in item:
                    self._conditions_list.append(Conditions(item['conditions'], item['type'], self._job))
                else:
                    self._conditions_list.append(MatchingMethod(item, self._job))

        return self._conditions_list

    @property
    def conditions_sql(self):
        condition_sqls = []
        for condition in self.conditions_list:
            if isinstance(condition, MatchingMethod):
                condition_sqls.append(condition.sql)
            else:
                condition_sqls.append(condition.conditions_sql)

        return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' %s ' % self._type).join(condition_sqls))

    # @property
    # def conditions_sql(self):
    #     filter_sqls = []
    #     for condition in self.conditions_list:
    #         if isinstance(condition, MatchingMethod):
    #             match_condition = condition.match_conditions_sql
    #             if match_condition:
    #                 filter_sqls.append(match_condition)
    #
    #             join_condition = condition.join_condition_sql
    #             if join_condition:
    #                 filter_sqls.append(join_condition)
    #         else:
    #             nested_condition = condition.conditions_sql
    #             if nested_condition:
    #                 filter_sqls.append(nested_condition)
    #
    #     if filter_sqls:
    #         return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' \n%s ' % self._operator).join(filter_sqls))
    #
    #     return None

    # @property
    # def similarity_sql(self):
    #     similarity_sqls = []
    #     for condition in self.conditions_list:
    #         if isinstance(condition, MatchingMethod):
    #             if condition.similarity_grouping_sql:
    #                 similarity_sqls.append(condition.similarity_grouping_sql)
    #         else:
    #             similarity_sqls.append(condition.similarity_sql)
    #
    #     if not similarity_sqls:
    #         return psycopg2_sql.Literal(1)
    #
    #     sim_sql = similarity_sqls.pop()
    #     while similarity_sqls:
    #         sim_sql = psycopg2_sql.SQL('logic_ops({operation}, {a}, {b})').format(
    #             operation=psycopg2_sql.Literal(self._type),
    #             a=sim_sql,
    #             b=similarity_sqls.pop()
    #         )
    #
    #     return sim_sql

    # @property
    # def similarity_fields(self):
    #     return {matching_method.field_name + '_similarity': matching_method.similarity_sql
    #             for matching_method in self.matching_methods if matching_method.similarity_sql}

    @property
    def matching_methods(self):
        matching_methods = []
        for condition in self.conditions_list:
            if isinstance(condition, MatchingMethod):
                matching_methods.append(condition)
            else:
                matching_methods += condition.matching_methods

        return matching_methods
