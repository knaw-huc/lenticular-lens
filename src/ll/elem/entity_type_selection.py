from psycopg2 import sql

from ll.data.collection import Collection
from ll.job.property_field import PropertyField
from ll.elem.filter_function import FilterFunction

from ll.util.helpers import flatten
from ll.util.hasher import hash_string_min


class EntityTypeSelection:
    def __init__(self, data, job):
        self._data = data
        self._job = job

        self.graphql_endpoint = self._data['dataset']['timbuctoo_graphql']
        self.dataset_id = self._data['dataset']['dataset_id']
        self.collection_id = self._data['dataset']['collection_id']

        self.collection = Collection(self.graphql_endpoint, self.dataset_id, self.collection_id)

    @property
    def id(self):
        return self._data['id']

    @property
    def label(self):
        return self._data['label'].strip()

    @property
    def description(self):
        return self._data['description'].strip() if 'description' in self._data and self._data['description'] else None

    @property
    def alias(self):
        return hash_string_min(self.id)

    @property
    def limit(self):
        return self._data.get('limit', -1)

    @property
    def random(self):
        return self._data.get('random', False)

    @property
    def properties(self):
        return {PropertyField(property, entity_type_selection=self) for property in self._data['properties']}

    @property
    def filter_properties(self):
        return {filter.property_field for filter in self.filters}

    @property
    def filters(self):
        return self.with_filters_recursive(lambda c, type: flatten(c), default=[])

    @property
    def filters_sql(self):
        return self.with_filters_recursive(
            lambda conds, type: sql.SQL('({})').format(sql.SQL('\n%s ' % type).join(conds)),
            lambda filter_func: filter_func.sql
        )

    def properties_for_matching(self, linkset_spec):
        return self.filter_properties.union(
            matching_method_prop.prop_original for matching_method_prop in self.get_fields(linkset_spec))

    def get_fields(self, linkset_spec):
        match_fields = linkset_spec.get_fields()
        match_ets_fields = match_fields.get(self.id, set())

        return {match_field_property
                for match_field_label, match_field in match_ets_fields.items()
                for match_field_property in match_field['properties']}

    def with_filters_recursive(self, with_conditions, with_filter=None, default=None):
        if 'filter' in self._data and self._data['filter']:
            return self._r_filters(self._data['filter'], with_conditions, with_filter)

        return default

    def _r_filters(self, filter_obj, with_conditions, with_filter_function):
        if 'type' in filter_obj and filter_obj['type'] in ['AND', 'OR']:
            conditions = [self._r_filters(condition, with_conditions, with_filter_function)
                          for condition in filter_obj['conditions']]
            return with_conditions(conditions, filter_obj['type']) if with_conditions else conditions

        filter_function = FilterFunction(filter_obj, PropertyField(filter_obj['property'], entity_type_selection=self))
        return with_filter_function(filter_function) if with_filter_function else filter_function
