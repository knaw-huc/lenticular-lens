from hashlib import md5

hash_length = 15
postgresql_id_max_length = 63

known_endpoints = {
    'https://repository.goldenagents.org/v5/graphql': 'ga',
    'https://repository.huygens.knaw.nl/v5/graphql': 'huygens',
    'https://data.anansi.clariah.nl/v5/graphql': 'clariah',
}


def hasher(object):
    return F"H{hash_string_min(object)}"


def hash_string_min(object):
    return hash_string(object)[:hash_length]


def hash_string(object):
    return md5(bytes(object.__str__(), encoding='utf-8')).hexdigest()


def table_name_hash(graphql_endpoint, dataset_id, collection_id):
    dataset_id = dataset_id.split('__', 1)[1]
    prefix = known_endpoints[graphql_endpoint] + '_' if graphql_endpoint in known_endpoints else ''
    hash = hash_string(graphql_endpoint + dataset_id + collection_id)[:hash_length]

    min_collection_length = 15
    length = postgresql_id_max_length - 2 - len(prefix) - hash_length
    if len(dataset_id) > (length - min_collection_length):
        dataset_id = dataset_id[:length - min_collection_length]

    length -= len(dataset_id)
    collection_id_split = collection_id.split('__')
    collection_id = collection_id_split[len(collection_id_split) - 1]
    collection_id = collection_id[-length:]

    return prefix + dataset_id + '_' + collection_id + '_' + hash


def column_name_hash(column_name):
    column_name = column_name.lower()
    if column_name == 'uri':
        return column_name

    length = postgresql_id_max_length - hash_length - 1
    name_split = column_name.split('__')
    name = name_split[len(name_split) - 1]

    return name[-length:] + '_' + hash_string(column_name)[:hash_length]
