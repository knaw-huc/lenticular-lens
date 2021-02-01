from functools import reduce
from schema import Schema, SchemaError, And, Or, Use, Optional

from ll.util.hasher import hash_string_min
from ll.util.helpers import get_json_from_file

filter_functions = get_json_from_file('filter_functions.json')
matching_methods = get_json_from_file('matching_methods.json')
transformers = get_json_from_file('transformers.json')


class LogicBox:
    def __init__(self, schema, name, types, elements_schema=None):
        self.schema = schema
        self.name = name
        self.types = types
        self.elements_schema = elements_schema

    def validate(self, data):
        if type(data) is not dict:
            raise SchemaError('not an dict')

        if 'type' in data and data['type'].lower() in self.types and \
                self.name in data and type(data[self.name]) is list:
            elements = [self.validate(c) for c in data[self.name]]
            if len(elements) == 0:
                return None

            logicbox = {}
            if self.elements_schema:
                logicbox = self.elements_schema.validate(data)

            logicbox['type'] = data['type'].upper()
            logicbox[self.name] = elements

            return logicbox

        return self.schema.validate(data)


entity_type_selection_filter_logicbox_schema = Schema({
    'property': [And(str, len)],
    'type': And(str, Use(str.lower), lambda t: t in filter_functions.keys()),
    Optional('value'): Or(And(str, len), int),
    Optional('format'): And(str, len),
}, ignore_extra_keys=True)

mapping_method_logicbox_schema = Schema({
    'method_name': And(str, Use(str.upper), lambda m: m in matching_methods.keys()),
    'method_config': dict,
    Optional('method_sim_name', default=None): Or(None, And(str, Use(str.upper),
                                                            lambda m: m in matching_methods.keys())),
    Optional('method_sim_config', default={}): dict,
    Optional('method_sim_normalized', default=False): bool,
    Optional('t_conorm', default='MAXIMUM_T_CONORM'):
        lambda s: s in ('MAXIMUM_T_CONORM', 'PROBABILISTIC_SUM', 'BOUNDED_SUM',
                        'DRASTIC_T_CONORM', 'NILPOTENT_MAXIMUM', 'EINSTEIN_SUM'),
    Optional('threshold', default=0): Or(float, Use(lambda t: 0)),
    Optional('list_matching', default={'threshold': 0, 'is_percentage': False,
                                       'unique_threshold': 0, 'unique_is_percentage': False}): {
        Optional('threshold', default=0): int,
        Optional('is_percentage', default=False): bool,
        Optional('unique_threshold', default=0): int,
        Optional('unique_is_percentage', default=False): bool,
    },
    'sources': [{
        'entity_type_selection': Use(int),
        'property': [And(str, len)],
        Optional('transformers', default=list): [{
            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
            'parameters': dict
        }],
        Optional('stopwords', default={'dictionary': '', 'additional': []}): {
            'dictionary': str,
            'additional': [And(str)]
        }
    }],
    'targets': [{
        'entity_type_selection': Use(int),
        'property': [And(str, len)],
        Optional('transformers', default=list): [{
            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
            'parameters': dict
        }],
        Optional('stopwords', default={'dictionary': '', 'additional': []}): {
            'dictionary': str,
            'additional': [And(str)]
        }
    }]
}, ignore_extra_keys=True)

lens_logicbox_schema = Schema({
    'id': Use(int),
    'type': Or('linkset', 'lens')
}, ignore_extra_keys=True)

lens_logicbox_elements_schema = Schema({
    'type': str,
    'elements': list,
    Optional('t_conorm', default=''): lambda s: s in ('', 'MAXIMUM_T_CONORM', 'PROBABILISTIC_SUM', 'BOUNDED_SUM',
                                                      'DRASTIC_T_CONORM', 'NILPOTENT_MAXIMUM', 'EINSTEIN_SUM'),
    Optional('threshold', default=0): Or(float, Use(lambda t: 0)),
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
        Or(None, LogicBox(entity_type_selection_filter_logicbox_schema, 'conditions', ('and', 'or'))),
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
    Optional('threshold', default=0): Or(float, Use(lambda t: 0)),
    'methods': And(LogicBox(mapping_method_logicbox_schema, 'conditions',
                            ('and', 'or', 'minimum_t_norm', 'product_t_norm', 'lukasiewicz_t_norm', 'drastic_t_norm',
                             'nilpotent_minimum', 'hamacher_product', 'maximum_t_conorm', 'probabilistic_sum',
                             'bounded_sum', 'drastic_t_conorm', 'nilpotent_maximum', 'einstein_sum')), dict),
    Optional('properties', default=list): [{
        'entity_type_selection': Use(int),
        'property': [str],
    }]
}, ignore_extra_keys=True)

lens_spec_schema = Schema({
    'id': Use(int),
    'label': And(str, len),
    Optional('description', default=None): Or(str, None),
    'specs': And(LogicBox(lens_logicbox_schema, 'elements',
                          ('union', 'intersection', 'difference', 'sym_difference', 'in_set_and', 'in_set_or'),
                          elements_schema=lens_logicbox_elements_schema), dict),
    Optional('properties', default=list): [{
        'entity_type_selection': Use(int),
        'property': [str],
    }]
}, ignore_extra_keys=True)


def transform(entity_type_selections_org, linkset_specs_org, lens_specs_org):
    def create_references_for_property(entity_type_selection, property):
        if len(property) == 1 or property[1] == '__value__':
            return [entity_type_selection['internal_id'], property[0]]

        referenced_ets_id = hash_string_min(entity_type_selection['internal_id'] + property[0] + property[1])
        referenced_ets = next((ref for ref in ref_entity_type_selections if ref['internal_id'] == referenced_ets_id), {
            'internal_id': referenced_ets_id,
            'dataset': {
                'timbuctoo_graphql': entity_type_selection['dataset']['timbuctoo_graphql'],
                'timbuctoo_hsid': entity_type_selection['dataset']['timbuctoo_hsid'],
                'dataset_id': entity_type_selection['dataset']['dataset_id'],
                'collection_id': property[1],
                'published': entity_type_selection['dataset']['published']
            },
            'related': []
        })

        if not any(ref for ref in ref_entity_type_selections if ref['internal_id'] == referenced_ets_id):
            ref_entity_type_selections.append(referenced_ets)

        if not any(rel for rel in entity_type_selection['related']
                   if rel['entity_type_selection'] == referenced_ets_id
                      and rel['local_property'] == property[0]
                      and rel['remote_property'] == 'uri'):
            entity_type_selection['related'].append({
                'entity_type_selection': referenced_ets_id,
                'local_property': property[0],
                'remote_property': 'uri'
            })

        return create_references_for_property(referenced_ets, property[2:])

    def get_elements(logicbox, name):
        if name in logicbox:
            return [element for elements in logicbox[name] for element in get_elements(elements, name)]

        return [logicbox]

    def transform_elements(logicbox, name, with_element):
        if type(logicbox) is list:
            return [transform_elements(elements, name, with_element) for elements in logicbox]

        if name in logicbox:
            logicbox[name] = [transform_elements(elements, name, with_element) for elements in logicbox[name]]
            return logicbox

        return with_element(logicbox)

    def transform_entity_type_selection_condition(condition):
        res_condition = condition.copy()
        res_condition['property'] = create_references_for_property(entity_type_selection, condition['property'])

        return res_condition

    def transform_mapping_condition(mapping_conditions, condition):
        if condition['entity_type_selection'] not in ets_internal_id_by_id:
            raise SchemaError('entity-type selection %s not valid' % condition['entity_type_selection'])

        ets_internal_id = ets_internal_id_by_id[condition['entity_type_selection']]
        entity_type_selection = next(ets for ets in entity_type_selections if ets['internal_id'] == ets_internal_id)
        property = create_references_for_property(entity_type_selection, condition['property'])

        entity_type_selection_list = mapping_conditions.get(ets_internal_id, [])
        entity_type_selection_list.append({
            'property': property,
            'transformers': condition['transformers'],
            'stopwords': condition['stopwords'],
        })
        mapping_conditions[ets_internal_id] = entity_type_selection_list

        return mapping_conditions

    def transform_method_value(name, values):
        if name == 'INTERMEDIATE':
            if values['entity_type_selection'] not in ets_internal_id_by_id:
                raise SchemaError('entity-type selection %s not valid' % values['entity_type_selection'])

            ets_internal_id = ets_internal_id_by_id[values['entity_type_selection']]
            entity_type_selection = next(ets for ets in entity_type_selections if ets['internal_id'] == ets_internal_id)
            source = create_references_for_property(entity_type_selection, values['intermediate_source'])
            target = create_references_for_property(entity_type_selection, values['intermediate_target'])

            return {
                'entity_type_selection': ets_internal_id,
                'intermediate_source': source,
                'intermediate_target': target
            }

        return values

    def transform_property(properties, property):
        if '' in property['property'] or property['entity_type_selection'] not in ets_internal_id_by_id:
            return properties

        ets_internal_id = ets_internal_id_by_id[property['entity_type_selection']]
        entity_type_selection = next(ets for ets in entity_type_selections if ets['internal_id'] == ets_internal_id)

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
            entity_type_selection['internal_id'] = hash_string_min(str(entity_type_selection['id']))
            entity_type_selection['properties'] = [prop for prop in entity_type_selection['properties'] if prop != '']
            entity_type_selections.append(entity_type_selection)
        except SchemaError:
            pass

    ref_entity_type_selections = []
    ets_internal_id_by_id = {ets['id']: ets['internal_id'] for ets in entity_type_selections if 'id' in ets}

    for entity_type_selection in entity_type_selections:
        entity_type_selection['related'] = [{
            'entity_type_selection': ets_internal_id_by_id[rel['entity_type_selection']],
            'local_property': rel['local_property'],
            'remote_property': rel['remote_property'],
        } for rel in entity_type_selection['related'] if rel['entity_type_selection'] in ets_internal_id_by_id]

        if entity_type_selection['filter']:
            entity_type_selection['filter'] = \
                transform_elements(entity_type_selection['filter'], 'conditions',
                                   transform_entity_type_selection_condition)

    for linkset_spec_org in linkset_specs_org:
        try:
            linkset_spec = linkset_spec_schema.validate(linkset_spec_org)

            for entity_type_selection in (linkset_spec['sources'] + linkset_spec['targets']):
                if entity_type_selection not in ets_internal_id_by_id:
                    raise SchemaError('entity-type selection %s not valid' % entity_type_selection)

            linkset_spec['sources'] = [ets_internal_id_by_id[source] for source in linkset_spec['sources']]
            linkset_spec['targets'] = [ets_internal_id_by_id[target] for target in linkset_spec['targets']]
            linkset_spec['methods'] = transform_elements(linkset_spec['methods'], 'conditions', lambda condition: {
                'method_name': condition['method_name'],
                'method_config': transform_method_value(condition['method_name'],
                                                        condition['method_config']),
                'method_sim_name': condition['method_sim_name'],
                'method_sim_config': transform_method_value(condition['method_sim_name'],
                                                            condition['method_sim_config']),
                'method_sim_normalized': condition['method_sim_normalized'],
                'list_matching': condition['list_matching'],
                't_conorm': condition['t_conorm'],
                'threshold': condition['threshold'],
                'sources': reduce(transform_mapping_condition, condition['sources'], {}),
                'targets': reduce(transform_mapping_condition, condition['targets'], {}),
            })
            linkset_spec['properties'] = reduce(transform_property, linkset_spec['properties'], [])
            linkset_spec['intermediates'] = [method['method_config']['entity_type_selection']
                                             for method in get_elements(linkset_spec['methods'], 'conditions')
                                             if method['method_name'] == 'INTERMEDIATE']

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
        except SchemaError:
            pass

    return entity_type_selections, linkset_specs, lens_specs
