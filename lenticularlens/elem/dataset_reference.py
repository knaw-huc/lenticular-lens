from lenticularlens.data.timbuctoo.dataset import Dataset as TimbuctooDataset


class DatasetReference:
    def __init__(self, data):
        self._data = data

    @property
    def type(self):
        return self._data['type']

    @property
    def entity_type(self):
        dataset = None
        if self.type == 'timbuctoo':
            dataset = TimbuctooDataset(self._data['graphql_endpoint'], self._data['timbuctoo_id'])

        if dataset is not None:
            return dataset.entity_types.get(self._data['entity_type_id'])

        return None
