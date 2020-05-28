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


entity_type_selection_filter_elements_schema = Schema({
    'property': [And(str, len)],
    'type': And(str, Use(str.lower), lambda t: t in filter_functions.keys()),
    Optional('value'): Or(And(str, len), int),
    Optional('format'): And(str, len),
}, ignore_extra_keys=True)

mapping_method_elements_schema = Schema({
    'method_name': And(str, Use(str.upper), lambda m: m in matching_functions.keys()),
    'method_value': dict,
    'sources': [{
        'entity_type_selection': Use(int),
        'property': [And(str, len)],
        Optional('transformers', default=list): [{
            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
            'parameters': dict
        }]
    }],
    'targets': [{
        'entity_type_selection': Use(int),
        'property': [And(str, len)],
        Optional('transformers', default=list): [{
            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
            'parameters': dict
        }]
    }]
}, ignore_extra_keys=True)

lens_elements_schema = Schema({
    'id': Use(int),
    'type': Or('linkset', 'lens')
}, ignore_extra_keys=True)

entity_type_selection_schema = Schema({
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
    Optional('filter', default=None):
        Or(None, Elements(entity_type_selection_filter_elements_schema, 'conditions', ('and', 'or'))),
    Optional('limit', default=-1): And(int, lambda n: n > 0 or n == -1),
    Optional('random', default=False): bool,
    Optional('properties', default=list): [[str]],
    Optional('related', default=list): list,
    Optional('related_array', default=False): bool
}, ignore_extra_keys=True)

linkset_spec_schema = Schema({
    'id': Use(int),
    'label': And(str, len),
    Optional('description', default=None): Or(str, None),
    Optional('is_association', default=False): bool,
    'sources': [Use(int)],
    'targets': [Use(int)],
    'methods': And(Elements(mapping_method_elements_schema, 'conditions', ('and', 'or')), dict),
    Optional('properties', default=list): [{
        'entity_type_selection': Use(int),
        'property': [str],
    }]
}, ignore_extra_keys=True)

lens_spec_schema = Schema({
    'id': Use(int),
    'label': And(str, len),
    Optional('description', default=None): Or(str, None),
    'specs': And(Elements(lens_elements_schema, 'elements',
                          ('union', 'intersection', 'difference', 'sym_difference', 'in_set_and', 'in_set_or')), dict),
    Optional('properties', default=list): [{
        'entity_type_selection': Use(int),
        'property': [str],
    }]
}, ignore_extra_keys=True)


def transform(entity_type_selections_org, linkset_specs_org, lens_specs_org):
    def create_references_for_property(entity_type_selection, property):
        if len(property) == 1 or property[1] == '__value__':
            return [entity_type_selection['label'], property[0]]

        referenced_ets_label = hash_string(entity_type_selection['label'] + property[0] + property[1])
        referenced_ets = next((ref for ref in ref_entity_type_selections if ref['label'] == referenced_ets_label), {
            'label': referenced_ets_label,
            'dataset': {
                'timbuctoo_graphql': entity_type_selection['dataset']['timbuctoo_graphql'],
                'timbuctoo_hsid': entity_type_selection['dataset']['timbuctoo_hsid'],
                'dataset_id': entity_type_selection['dataset']['dataset_id'],
                'collection_id': property[1],
                'published': entity_type_selection['dataset']['published']
            },
            'related': []
        })

        if not any(ref for ref in ref_entity_type_selections if ref['label'] == referenced_ets_label):
            ref_entity_type_selections.append(referenced_ets)

        if not any(rel for rel in entity_type_selection['related']
                   if rel['entity_type_selection'] == referenced_ets_label
                      and rel['local_property'] == property[0]
                      and rel['remote_property'] == 'uri'):
            entity_type_selection['related'].append({
                'entity_type_selection': referenced_ets_label,
                'local_property': property[0],
                'remote_property': 'uri'
            })

        return create_references_for_property(referenced_ets, property[2:])

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

    def transform_entity_type_selection_condition(condition):
        res_condition = condition.copy()
        res_condition['property'] = create_references_for_property(entity_type_selection, condition['property'])

        return res_condition

    def transform_mapping_condition(mapping_conditions, condition):
        if condition['entity_type_selection'] not in ets_label_by_id:
            raise SchemaError('entity-type selection %s not valid' % condition['entity_type_selection'])

        ets_label = ets_label_by_id[condition['entity_type_selection']]
        entity_type_selection = next(ets for ets in entity_type_selections if ets['label'] == ets_label)
        property = create_references_for_property(entity_type_selection, condition['property'])

        entity_type_selection_list = mapping_conditions.get(ets_label, [])
        entity_type_selection_list.append({
            'property': property,
            'transformers': condition['transformers']
        })
        mapping_conditions[ets_label] = entity_type_selection_list

        return mapping_conditions

    def transform_property(properties, property):
        if '' in property['property'] or property['entity_type_selection'] not in ets_label_by_id:
            return properties

        ets_label = ets_label_by_id[property['entity_type_selection']]
        entity_type_selection = next(ets for ets in entity_type_selections if ets['label'] == ets_label)

        graph = entity_type_selection['dataset']['dataset_id']
        entity_type = entity_type_selection['dataset']['collection_id']

        target = next((prop_group for prop_group in properties if prop_group['graph'] == graph), {
            'graph': graph,
            'data': []
        })

        if not any(prop_group for prop_group in properties if prop_group['graph'] == graph):
            properties.append(target)

        entity_target = next((data for data in target['data'] if data['entity_type'] == entity_type), {
            'entity_type': entity_type,
            'properties': []
        })

        if not any(data for data in target['data'] if data['entity_type'] == entity_type):
            target['data'].append(entity_target)

        entity_target['properties'].append(property['property'])

        return properties

    entity_type_selections = []
    linkset_specs = []
    lens_specs = []

    for entity_type_selection_org in entity_type_selections_org:
        try:
            entity_type_selection = entity_type_selection_schema.validate(entity_type_selection_org)
            entity_type_selection['properties'] = [prop for prop in entity_type_selection['properties'] if prop != '']
            entity_type_selections.append(entity_type_selection)
        except SchemaError as se:
            pass

    ref_entity_type_selections = []
    ets_label_by_id = {ets['id']: ets['label'] for ets in entity_type_selections if 'id' in ets and 'label' in ets}

    for entity_type_selection in entity_type_selections:
        entity_type_selection['related'] = [{
            'entity_type_selection': ets_label_by_id[rel['entity_type_selection']],
            'local_property': rel['local_property'],
            'remote_property': rel['remote_property'],
        } for rel in entity_type_selection['related'] if rel['entity_type_selection'] in ets_label_by_id]

        if entity_type_selection['filter']:
            entity_type_selection['filter'] = \
                transform_elements(entity_type_selection['filter'], 'conditions',
                                   transform_entity_type_selection_condition)

    for linkset_spec_org in linkset_specs_org:
        try:
            linkset_spec = linkset_spec_schema.validate(linkset_spec_org)

            for entity_type_selection in (linkset_spec['sources'] + linkset_spec['targets']):
                if entity_type_selection not in ets_label_by_id:
                    raise SchemaError('entity-type selection %s not valid' % entity_type_selection)

            linkset_spec['sources'] = [ets_label_by_id[source] for source in linkset_spec['sources']]
            linkset_spec['targets'] = [ets_label_by_id[target] for target in linkset_spec['targets']]
            linkset_spec['methods'] = transform_elements(linkset_spec['methods'], 'conditions', lambda condition: {
                'method_name': condition['method_name'],
                'method_value': condition['method_value'],
                'sources': reduce(transform_mapping_condition, condition['sources'], {}),
                'targets': reduce(transform_mapping_condition, condition['targets'], {}),
            })
            linkset_spec['properties'] = reduce(transform_property, linkset_spec['properties'], [])

            linkset_specs.append(linkset_spec)
        except SchemaError:
            pass

    entity_type_selections += ref_entity_type_selections

    for lens_org in lens_specs_org:
        try:
            lens = lens_spec_schema.validate(lens_org)

            lens['properties'] = reduce(transform_property, lens['properties'], [])
            lens['specs'] = transform_elements(lens['specs'], 'elements', lambda element: {
                'id': int(element['id']),
                'type': element['type']
            })

            lens_specs.append(lens)
        except SchemaError as e:
            pass

    return entity_type_selections, linkset_specs, lens_specs
