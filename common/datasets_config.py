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
                timbuctoo_data = Timbuctoo().datasets
                database_data = Dataset.datasets()

                combined = timbuctoo_data.copy()
                for dataset, dataset_data in database_data.items():
                    if not dataset in combined:
                        combined[dataset] = dataset_data.copy()
                    else:
                        for collection, dataset_data in dataset_data['collections'].items():
                            if not collection in combined[dataset]['collections']:
                                combined[dataset]['collections'][collection] = database_data.copy()

                self.__data = combined
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
