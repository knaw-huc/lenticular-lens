from ll.util.helpers import hash_string
from ll.job.lens_elements import LensElements


class Lens:
    def __init__(self, data, job):
        self._data = data
        self._job = job
        self._specs = None

    @property
    def specs(self):
        if not self._specs:
            specs = self._data['specs']
            self._specs = LensElements(specs['elements'], specs['type'], self._job)
        return self._specs

    @property
    def joins_sql(self):
        return self.specs.joins_sql

    @property
    def linksets(self):
        return self.specs.linksets

    @property
    def id(self):
        return self._data.get('id', '')

    @property
    def properties(self):
        return self._data['properties']

    @property
    def name(self):
        return hash_string(self._data['label'])
