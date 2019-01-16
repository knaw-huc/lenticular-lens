from .collection import Collection


class Dataset:
    def __init__(self, dataset_id, collections):
        self.dataset_id = dataset_id
        self.__collections = collections

    def collection(self, collection_id):
        return Collection(self.dataset_id, collection_id, self.__collections[collection_id])
