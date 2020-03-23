from functools import reduce
from schema import Schema, SchemaError, And, Or, Use, Optional
from ll.util.helpers import hash_string, get_json_from_file

filter_functions = get_json_from_file('filter_functions.json')
matching_functions = get_json_from_file('matching_functions.json')
transformers = get_json_from_file('transformers.json')


class Elements:
    def __init__(self, schema, group_name, types):
        self.schema = schema
        self.group_name = group_name
        self.types = types

    def validate(self, data):
        if type(data) is not dict:
            raise SchemaError('not an dict')

        if 'type' in data and data['type'].lower() in self.types and \
                self.group_name in data and type(data[self.group_name]) is list:
            elements = [self.validate(c) for c in data[self.group_name]]
            if len(elements) == 0:
                return None

            return {'type': data['type'].upper(), self.group_name: elements}

        return self.schema.validate(data)


resource_filter_elements_schema = Schema({
    'property': [And(str, len)],
    'type': And(str, Use(str.lower), lambda t: t in filter_functions.keys()),
    Optional('value'): And(str, len),
}, ignore_extra_keys=True)

mapping_method_elements_schema = Schema({
    'method_name': And(str, Use(str.upper), lambda m: m in matching_functions.keys()),
    'method_value': dict,
    'sources': [{
        'resource': Use(int),
        'property': [And(str, len)],
        Optional('transformers', default=list): [{
            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
            'parameters': dict
        }]
    }],
    'targets': [{
        'resource': Use(int),
        'property': [And(str, len)],
        Optional('transformers', default=list): [{
            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
            'parameters': dict
        }]
    }]
}, ignore_extra_keys=True)

lens_elements_schema = Schema({
    'alignment': Use(int)
}, ignore_extra_keys=True)

resource_schema = Schema({
    'id': Use(int),
    'label': And(str, len),
    Optional('description', default=None): Or(str, None),
    'dataset': {
        'dataset_id': And(str, len),
        'collection_id': And(str, len),
        Optional('published', default=True): bool,
        'timbuctoo_graphql': And(str, len),
        Optional('timbuctoo_hsid'): Or(str, None),
    },
    Optional('filter', default=None): Or(None, Elements(resource_filter_elements_schema, 'conditions', ('and', 'or'))),
    Optional('limit', default=-1): And(int, lambda n: n > 0 or n == -1),
    Optional('random', default=False): bool,
    Optional('properties', default=list): [[str]],
    Optional('related', default=list): list,
    Optional('related_array', default=False): bool
}, ignore_extra_keys=True)

mapping_schema = Schema({
    'id': Use(int),
    'label': And(str, len),
    Optional('description', default=None): Or(str, None),
    Optional('is_association', default=False): bool,
    'sources': [Use(int)],
    'targets': [Use(int)],
    'methods': And(Elements(mapping_method_elements_schema, 'conditions', ('and', 'or')), dict),
    Optional('properties', default=list): [{
        'resource': Use(int),
        'property': [str],
    }]
}, ignore_extra_keys=True)

lenses_schema = Schema({
    'id': Use(int),
    'label': And(str, len),
    Optional('description', default=None): Or(str, None),
    'elements': And(Elements(lens_elements_schema, 'alignments',
                             ('union', 'intersection', 'difference', 'sym_difference')), dict),
    Optional('properties', default=list): [{
        'resource': Use(int),
        'property': [str],
    }]
}, ignore_extra_keys=True)


def transform(resources_org, mappings_org, lenses_org):
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

    def transform_elements(elements_group, group_name, with_element):
        if type(elements_group) is list:
            return [transform_elements(element, group_name, with_element) for element in elements_group]

        if group_name in elements_group:
            return {
                'type': elements_group['type'],
                group_name: [transform_elements(element, group_name, with_element)
                             for element in elements_group[group_name]]
            }

        return with_element(elements_group)

    def transform_resource_condition(condition):
        res_condition = condition.copy()
        res_condition['property'] = create_references_for_property(resource, condition['property'])

        return res_condition

    def transform_mapping_condition(mapping_conditions, condition):
        if condition['resource'] not in resource_label_by_id:
            raise SchemaError('resource %s not valid' % condition['resource'])

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
        if '' in property['property'] or property['resource'] not in resource_label_by_id:
            return mapping_properties

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
    lenses = []

    for resource_org in resources_org:
        try:
            resource = resource_schema.validate(resource_org)
            resource['properties'] = [prop for prop in resource['properties'] if prop != '']
            resources.append(resource)
        except SchemaError:
            pass

    ref_resources = []
    resource_label_by_id = {resource['id']: resource['label'] for resource in resources
                            if 'id' in resource and 'label' in resource}

    for resource in resources:
        resource['related'] = [{
            'resource': resource_label_by_id[rel['resource']],
            'local_property': rel['local_property'],
            'remote_property': rel['remote_property'],
        } for rel in resource['related'] if rel['resource'] in resource_label_by_id]

        if resource['filter']:
            resource['filter'] = transform_elements(resource['filter'], 'conditions', transform_resource_condition)

    for mapping_org in mappings_org:
        try:
            mapping = mapping_schema.validate(mapping_org)

            for resource in (mapping['sources'] + mapping['targets']):
                if resource not in resource_label_by_id:
                    raise SchemaError('resource %s not valid' % resource)

            mapping['sources'] = [resource_label_by_id[resource] for resource in mapping['sources']]
            mapping['targets'] = [resource_label_by_id[resource] for resource in mapping['targets']]
            mapping['methods'] = transform_elements(mapping['methods'], 'conditions', lambda condition: {
                'method_name': condition['method_name'],
                'method_value': condition['method_value'],
                'sources': reduce(transform_mapping_condition, condition['sources'], {}),
                'targets': reduce(transform_mapping_condition, condition['targets'], {}),
            })
            mapping['properties'] = reduce(transform_mapping_property, mapping['properties'], [])

            mappings.append(mapping)
        except SchemaError:
            pass

    resources += ref_resources

    for lens_org in lenses_org:
        try:
            lens = lenses_schema.validate(lens_org)

            lens['properties'] = reduce(transform_mapping_property, lens['properties'], [])
            lens['elements'] = transform_elements(lens['elements'], 'alignments',
                                                  lambda element: int(element['alignment']))

            lenses.append(lens)
        except SchemaError:
            pass

    return resources, mappings, lenses
