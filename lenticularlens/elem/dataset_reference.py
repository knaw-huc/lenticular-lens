from lenticularlens.data.timbuctoo.dataset import Dataset as TimbuctooDataset
from lenticularlens.data.sparql.dataset import Dataset as SparqlDataset

class DatasetReference:
    def __init__(self, data):
        self._data = data
        self._dataset = None

    @property
    def type(self):
        return self._data['type']

    @property
    def entity_type(self):
        if self._dataset is None:
            if self.type == 'timbuctoo':
                self._dataset = TimbuctooDataset(self._data['graphql_endpoint'], self._data['timbuctoo_id'])
            elif self.type == 'sparql':
                self._dataset = SparqlDataset(self._data['sparql_endpoint'])

        if self._dataset is not None:
            return self._dataset.entity_types.get(self._data['entity_type_id'])

        return None
