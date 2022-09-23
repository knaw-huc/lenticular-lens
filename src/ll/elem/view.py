from psycopg2 import sql

from ll.data.collection import Collection
from ll.job.property_field import PropertyField
from ll.elem.filter_function import FilterFunction

from ll.util.helpers import flatten


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
        return set(prop for collection_props in self.properties_per_collection.values() for prop in collection_props)

    @property
    def properties_per_collection(self):
        properties = dict()
        for dataset_props in self._data['properties']:
            collection = Collection(
                dataset_props['timbuctoo_graphql'],
                dataset_props['dataset_id'],
                dataset_props['collection_id']
            )

            properties[collection] = list(dict.fromkeys([PropertyField(prop, collection=collection)
                                                         for prop in dataset_props['properties']]))

        return properties

    @property
    def filters(self):
        return set(filter for coll_filters in self.filters_per_collection.values() for filter in coll_filters)

    @property
    def filter_properties(self):
        return set(prop for filter_props in self.filters_properties_per_collection.values() for prop in filter_props)

    @property
    def filters_properties_per_collection(self):
        return {collection: {filter.property_field for filter in filters}
                for (collection, filters) in self.filters_per_collection.items()}

    @property
    def filters_per_collection(self):
        return self._with_filters_per_collection(lambda c, type: flatten(c))

    @property
    def filters_sql_per_collection(self):
        return self._with_filters_per_collection(
            lambda conds, type: sql.SQL('({})').format(sql.SQL('\n%s ' % type).join(conds)),
            lambda filter_func: filter_func.sql
        )

    @property
    def prefix_mappings(self):
        return self._data['prefix_mappings']

    def _with_filters_per_collection(self, with_conditions, with_filter_function=None):
        filters = dict()
        for dataset_filter in self._data['filters']:
            if dataset_filter['filter']:
                collection = Collection(
                    dataset_filter['timbuctoo_graphql'],
                    dataset_filter['dataset_id'],
                    dataset_filter['collection_id']
                )

                filters[collection] = self._r_filters(dataset_filter['filter'], collection,
                                                      with_conditions, with_filter_function)

        return filters

    def _r_filters(self, filter_obj, collection, with_conditions, with_filter_function=None):
        if 'type' in filter_obj and filter_obj['type'] in ['and', 'or']:
            conditions = [self._r_filters(condition, collection, with_conditions, with_filter_function)
                          for condition in filter_obj['conditions']]
            return with_conditions(conditions, filter_obj['type']) if with_conditions else conditions

        filter_function = FilterFunction(filter_obj, PropertyField(filter_obj['property'], collection=collection))
        return with_filter_function(filter_function) if with_filter_function else filter_function
