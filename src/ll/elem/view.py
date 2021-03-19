from ll.data.collection import Collection
from ll.job.property_field import PropertyField


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
    def properties(self) :
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

            properties[collection] = set(PropertyField(prop, collection=collection)
                                         for prop in dataset_props['properties'])

        return properties
