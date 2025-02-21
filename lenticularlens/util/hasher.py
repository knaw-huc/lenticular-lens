from hashlib import md5

hash_length = 15
postgresql_id_max_length = 63


def hasher(object):
    return F"H{hash_string_min(object)}"


def hash_string_min(object):
    return hash_string(object)[:hash_length]


def hash_string(object):
    return md5(bytes(object.__str__(), encoding='utf-8')).hexdigest()


def table_name_hash(prefix, dataset_name, entity_type_name, full_name):
    prefix = prefix + '_' if prefix is not None and len(prefix) > 0 else ''
    hash = hash_string(full_name)[:hash_length]

    min_entity_type_name_length = 15
    length = postgresql_id_max_length - 2 - len(prefix) - hash_length
    if len(dataset_name) > (length - min_entity_type_name_length):
        dataset_name = dataset_name[:length - min_entity_type_name_length]

    length -= len(dataset_name)
    entity_type_name = entity_type_name[len(entity_type_name) - 1]
    entity_type_name = entity_type_name[-length:]

    return prefix + dataset_name + '_' + entity_type_name + '_' + hash


def column_name_hash(column_name):
    column_name = column_name.lower()
    if column_name == 'uri':
        return column_name

    length = postgresql_id_max_length - hash_length - 1
    name_split = column_name.split('__')
    name = name_split[len(name_split) - 1]

    return name[-length:] + '_' + hash_string(column_name)[:hash_length]
