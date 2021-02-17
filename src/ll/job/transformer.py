from functools import reduce
from schema import Schema, SchemaError, And, Or, Use, Optional

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
    Optional('use_counter', default=True): bool,
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
        res_condition['property'] = condition['property']

        return res_condition

    def transform_mapping_condition(mapping_conditions, condition):
        if condition['entity_type_selection'] not in ets_ids:
            raise SchemaError('entity-type selection %s not valid' % condition['entity_type_selection'])

        entity_type_selection_list = mapping_conditions.get(condition['entity_type_selection'], [])
        entity_type_selection_list.append({
            'property': condition['property'],
            'transformers': condition['transformers'],
            'stopwords': condition['stopwords'],
        })
        mapping_conditions[condition['entity_type_selection']] = entity_type_selection_list

        return mapping_conditions

    def transform_method_value(name, values):
        if name == 'INTERMEDIATE':
            if values['entity_type_selection'] not in ets_ids:
                raise SchemaError('entity-type selection %s not valid' % values['entity_type_selection'])

            source = values['intermediate_source']
            target = values['intermediate_target']

            return {
                'entity_type_selection': values['entity_type_selection'],
                'intermediate_source': source,
                'intermediate_target': target
            }

        return values

    def filter_property_path(property_path):
        return [prop for prop in property_path if prop != '' and prop != '__value__']

    entity_type_selections = []
    linkset_specs = []
    lens_specs = []

    for entity_type_selection_org in entity_type_selections_org:
        try:
            entity_type_selection = entity_type_selection_schema.validate(entity_type_selection_org)

            entity_type_selection['properties'] = [filter_property_path(property_path)
                                                   for property_path in entity_type_selection['properties']
                                                   if filter_property_path(property_path)]

            if entity_type_selection['filter']:
                entity_type_selection['filter'] = \
                    transform_elements(entity_type_selection['filter'], 'conditions',
                                       transform_entity_type_selection_condition)

            del entity_type_selection['related']

            entity_type_selections.append(entity_type_selection)
        except SchemaError:
            pass

    ets_ids = [ets['id'] for ets in entity_type_selections]

    for linkset_spec_org in linkset_specs_org:
        try:
            linkset = linkset_spec_schema.validate(linkset_spec_org)

            for entity_type_selection in (linkset['sources'] + linkset['targets']):
                if entity_type_selection not in ets_ids:
                    raise SchemaError('entity-type selection %s not valid' % entity_type_selection)

            linkset['methods'] = transform_elements(linkset['methods'], 'conditions', lambda condition: {
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

            linkset['properties'] = [{
                'entity_type_selection': linkset_prop['entity_type_selection'],
                'property': filter_property_path(linkset_prop['property']),
            } for linkset_prop in linkset['properties'] if filter_property_path(linkset_prop['property'])]

            linkset['intermediates'] = [method['method_config']['entity_type_selection']
                                        for method in get_elements(linkset['methods'], 'conditions')
                                        if method['method_name'] == 'INTERMEDIATE']

            linkset_specs.append(linkset)
        except SchemaError:
            pass

    for lens_org in lens_specs_org:
        try:
            lens = lens_spec_schema.validate(lens_org)

            lens['properties'] = [{
                'entity_type_selection': lens_prop['entity_type_selection'],
                'property': filter_property_path(lens_prop['property']),
            } for lens_prop in lens['properties'] if filter_property_path(lens_prop['property'])]

            lens['specs'] = transform_elements(lens['specs'], 'elements', lambda element: {
                'id': int(element['id']),
                'type': element['type']
            })

            lens_specs.append(lens)
        except SchemaError:
            pass

    return entity_type_selections, linkset_specs, lens_specs
