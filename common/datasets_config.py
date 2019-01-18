from dataset import Dataset
from timbuctoo import Timbuctoo


class DatasetsConfig:
    def __init__(self):
        self.__data = Timbuctoo().datasets

    def dataset(self, dataset_id):
        return Dataset(dataset_id, self.__data[dataset_id])

    @property
    def datasets(self):
        return list(self.__data)

    @property
    def data(self):
        return self.__data
