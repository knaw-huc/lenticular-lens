from collections import defaultdict

from ll.elem.lens_elements import LensElements
from ll.job.property_field import PropertyField


class Lens:
    def __init__(self, data, job):
        self._data = data
        self._job = job
        self._specs = None

    @property
    def id(self):
        return self._data['id']

    @property
    def properties(self):
        props = defaultdict(list)
        for prop in self._data['properties']:
            ets_id = prop['entity_type_selection']
            props[ets_id].append(PropertyField(prop['property'], self._job.get_entity_type_selection_by_id(ets_id)))

        return props

    @property
    def specs(self):
        if not self._specs:
            specs = self._data['specs']
            self._specs = LensElements(specs, self._job)
        return self._specs

    @property
    def linksets(self):
        return self.specs.linksets

    @property
    def lenses(self):
        return self.specs.lenses

    @property
    def entity_type_selections(self):
        return set(linkset.entity_type_selections for linkset in self.specs.linksets)

    @property
    def similarity_fields(self):
        return self.specs.similarity_fields

    @property
    def sql(self):
        return self.specs.sql

    @property
    def similarity_logic_ops_sql(self):
        return self.specs.similarity_logic_ops_sql

    @property
    def similarity_threshold_sqls(self):
        return [lens_element.similarity_threshold_sql
                for lens_element in self.specs.lens_elements
                if lens_element.similarity_threshold_sql]
