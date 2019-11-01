from common.collection import Collection


class Dataset:
    def __init__(self, graphql_endpoint, hsid, dataset_id, dataset_name, title, description, collections):
        self.graphql_endpoint = graphql_endpoint
        self.hsid = hsid
        self.dataset_id = dataset_id
        self.dataset_name = dataset_name
        self.title = title
        self.description = description
        self.collections = collections

    def collection(self, collection_id):
        return Collection(self.graphql_endpoint, self.hsid, self.dataset_id, collection_id, self.dataset_name,
                          self.title, self.description, self.collections[collection_id])
