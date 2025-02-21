from psycopg import sql

from lenticularlens.job.property_field import PropertyField
from lenticularlens.elem.filter_function import FilterFunction
from lenticularlens.elem.dataset_reference import DatasetReference

from lenticularlens.util.helpers import flatten


class View:
    def __init__(self, data, job):
        self._data = data
        self._job = job

    @property
    def id(self):
        return self._data['id']

    @property
    def type(self):
        return self._data['type']

    @property
    def all_props(self):
        return self.properties.union(self.filter_properties)

    @property
    def properties(self):
        return set(prop for entity_type_props in self.properties_per_entity_type.values() for prop in entity_type_props)

    @property
    def properties_per_entity_type(self):
        properties = dict()
        for dataset_props in self._data['properties']:
            entity_type = DatasetReference(dataset_props['dataset']).entity_type
            properties[entity_type] = list(dict.fromkeys([PropertyField(prop, entity_type=entity_type)
                                                          for prop in dataset_props['properties']]))

        return properties

    @property
    def filters(self):
        return set(filter
                   for entity_type_filters in self.filters_per_entity_type.values()
                   for filter in entity_type_filters)

    @property
    def filter_properties(self):
        return set(prop for filter_props in self.filters_properties_per_entity_type.values() for prop in filter_props)

    @property
    def filters_properties_per_entity_type(self):
        return {entity_type: {filter.property_field for filter in filters}
                for (entity_type, filters) in self.filters_per_entity_type.items()}

    @property
    def filters_per_entity_type(self):
        return self._with_filters_per_entity_type(lambda c, type: flatten(c))

    @property
    def filters_sql_per_entity_type(self):
        return self._with_filters_per_entity_type(
            lambda conds, type: sql.SQL('({})').format(sql.SQL('\n%s ' % type).join(conds)),
            lambda filter_func: filter_func.sql
        )

    @property
    def prefix_mappings(self):
        return self._data['prefix_mappings']

    def _with_filters_per_entity_type(self, with_conditions, with_filter_function=None):
        filters = dict()
        for dataset_filter in self._data['filters']:
            if dataset_filter['filter']:
                entity_type = DatasetReference(dataset_filter['dataset']).entity_type
                filters[entity_type] = self._r_filters(dataset_filter['filter'], entity_type,
                                                       with_conditions, with_filter_function)

        return filters

    def _r_filters(self, filter_obj, entity_type, with_conditions, with_filter_function=None):
        if 'type' in filter_obj and filter_obj['type'] in ['and', 'or']:
            conditions = [self._r_filters(condition, entity_type, with_conditions, with_filter_function)
                          for condition in filter_obj['conditions']]
            return with_conditions(conditions, filter_obj['type']) if with_conditions else conditions

        filter_function = FilterFunction(filter_obj, PropertyField(filter_obj['property'], entity_type=entity_type))
        return with_filter_function(filter_function) if with_filter_function else filter_function
