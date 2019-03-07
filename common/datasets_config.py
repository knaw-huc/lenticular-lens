from dataset import Dataset
from timbuctoo import Timbuctoo
import psycopg2
import random
import time


class DatasetsConfig:
    def __init__(self):
        n = 0
        while True:
            try:
                self.__data = Timbuctoo().datasets
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                n += 1
                print('Database error. Retry %i' % n)
                time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
            else:
                break

    def dataset(self, dataset_id):
        return Dataset(dataset_id, self.__data[dataset_id]['collections'])

    @property
    def datasets(self):
        return list(self.__data)

    @property
    def data(self):
        return self.__data
