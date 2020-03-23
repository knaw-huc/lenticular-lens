from ll.job.elements import Elements
from ll.util.helpers import hash_string


class Lens:
    def __init__(self, data, job):
        self._data = data
        self._job = job
        self._elements = None

    @property
    def elements(self):
        if not self._elements:
            elements = self._data['elements']
            self._elements = Elements(elements['alignments'], elements['type'], self._job)
        return self._elements

    @property
    def joins_sql(self):
        return self.elements.joins_sql

    @property
    def alignments(self):
        return self.elements.alignments

    @property
    def id(self):
        return self._data.get('id', '')

    @property
    def properties(self):
        return self._data['properties']

    @property
    def name(self):
        return hash_string(self._data['label'])
