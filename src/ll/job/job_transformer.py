from functools import reduce
from ll.util.helpers import hash_string


def transform(resources_org, mappings_org):
    def create_references_for_property(resource, property):
        if len(property) == 1 or property[1] == '__value__':
            return [resource['label'], property[0]]

        referenced_resource_label = hash_string(resource['label'] + property[0] + property[1])
        referenced_resource = next((ref for ref in ref_resources if ref['label'] == referenced_resource_label), {
            'label': referenced_resource_label,
            'dataset': {
                'timbuctoo_graphql': resource['dataset']['timbuctoo_graphql'],
                'timbuctoo_hsid': resource['dataset']['timbuctoo_hsid'],
                'dataset_id': resource['dataset']['dataset_id'],
                'collection_id': property[1],
                'published': resource['dataset']['published']
            },
            'related': []
        })

        if not any(ref for ref in ref_resources if ref['label'] == referenced_resource_label):
            ref_resources.append(referenced_resource)

        if not any(rel for rel in resource['related'] if rel['resource'] == referenced_resource_label
                                                         and rel['local_property'] == property[0]
                                                         and rel['remote_property'] == 'uri'):
            resource['related'].append({
                'resource': referenced_resource_label,
                'local_property': property[0],
                'remote_property': 'uri'
            })

        return create_references_for_property(referenced_resource, property[2:])

    def transform_conditions(conditions_group, with_condition):
        if type(conditions_group) is list:
            return [transform_conditions(condition, with_condition) for condition in conditions_group]

        if 'conditions' in conditions_group:
            return {
                'type': conditions_group['type'],
                'conditions': [transform_conditions(condition, with_condition)
                               for condition in conditions_group['conditions']]
            }

        return with_condition(conditions_group)

    def transform_resource_condition(condition):
        res_condition = condition.copy()
        res_condition['property'] = create_references_for_property(resource, condition['property'])

        return res_condition

    def transform_mapping_condition(mapping_conditions, condition):
        resource_label = resource_label_by_id[condition['resource']]
        resource = next(resource for resource in resources if resource['label'] == resource_label)
        property = create_references_for_property(resource, condition['property'])

        resource_list = mapping_conditions.get(resource_label, [])
        resource_list.append({
            'property': property,
            'transformers': condition['transformers']
        })
        mapping_conditions[resource_label] = resource_list

        return mapping_conditions

    def transform_mapping_property(mapping_properties, property):
        resource_label = resource_label_by_id[property['resource']]
        resource = next(resource for resource in resources if resource['label'] == resource_label)

        graph = resource['dataset']['dataset_id']
        entity_type = resource['dataset']['collection_id']

        resource_target = next((prop_group for prop_group in mapping_properties if prop_group['graph'] == graph), {
            'graph': graph,
            'data': []
        })

        if not any(prop_group for prop_group in mapping_properties if prop_group['graph'] == graph):
            mapping_properties.append(resource_target)

        entity_target = next((data for data in resource_target['data'] if data['entity_type'] == entity_type), {
            'entity_type': entity_type,
            'properties': []
        })

        if not any(data for data in resource_target['data'] if data['entity_type'] == entity_type):
            resource_target['data'].append(entity_target)

        entity_target['properties'].append(property['property'])

        return mapping_properties

    resources = []
    mappings = []

    ref_resources = []
    resource_label_by_id = {resource['id']: resource['label'] for resource in resources_org}

    for resource_org in resources_org:
        resource = {
            'label': resource_org['label'],
            'description': resource_org['description'] if 'description' in resource_org else '',
            'dataset': resource_org['dataset'],
            'properties': resource_org['properties'],
            'limit': resource_org['limit'],
            'random': resource_org['random'] if 'random' in resource_org else False,
            'related': []
        }

        if 'filter' in resource_org and 'conditions' in resource_org['filter'] \
                and len(resource_org['filter']['conditions']) > 0:
            resource['filter'] = transform_conditions(resource_org['filter'], transform_resource_condition)

        if 'related' in resource_org:
            resource['related'] += [{
                'resource': resource_label_by_id[int(rel['resource'])],
                'local_property': rel['local_property'],
                'remote_property': rel['remote_property']
            } for rel in resource_org['related']]

        resources.append(resource)

    for mapping_org in mappings_org:
        mappings.append({
            'id': mapping_org['id'],
            'label': mapping_org['label'],
            'description': mapping_org['description'] if 'description' in mapping_org else '',
            'is_association': mapping_org['is_association'],
            'match_against': mapping_org['match_against'],
            'sources': [resource_label_by_id[resource] for resource in mapping_org['sources'] if resource != ''],
            'targets': [resource_label_by_id[resource] for resource in mapping_org['targets'] if resource != ''],
            'methods': transform_conditions(mapping_org['methods'], lambda condition: {
                'method_name': condition['method_name'],
                'method_value': condition['method_value'],
                'sources': reduce(transform_mapping_condition, condition['sources'], {}),
                'targets': reduce(transform_mapping_condition, condition['targets'], {}),
            }),
            'properties': reduce(transform_mapping_property, mapping_org['properties'], [])
        })

    resources += ref_resources

    return resources, mappings
