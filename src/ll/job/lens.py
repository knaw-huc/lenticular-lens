from ll.job.lens_elements import LensElements


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
        return self._data['properties']

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
