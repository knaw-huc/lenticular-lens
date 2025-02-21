from typing import List

current_version = 2


def upgrade_job_config(version: int, entity_type_selections: List[dict], linkset_specs: List[dict],
                       lens_specs: List[dict], views: List[dict]) -> bool:
    if version == current_version:
        return False

    [upgrade_entity_type_selection(version, entity_type_selection) for entity_type_selection in entity_type_selections]
    # [upgrade_linkset_spec(version, linkset_spec) for linkset_spec in linkset_specs]
    # [upgrade_lens_spec(version, lens_spec) for lens_spec in lens_specs]
    [upgrade_view(version, view) for view in views]

    return True


def upgrade_entity_type_selection(version: int, entity_type_selection: dict):
    if version == 1:
        create_new_dataset_from_timbuctoo_dataset(entity_type_selection, entity_type_selection['dataset'])


def upgrade_view(version: int, view: dict):
    if version == 1:
        [create_new_dataset_from_timbuctoo_dataset(filter, filter) for filter in view['filters']]
        [create_new_dataset_from_timbuctoo_dataset(property, property) for property in view['properties']]


def create_new_dataset_from_timbuctoo_dataset(config: dict, timbuctoo_dataset: dict):
    dataset_id = timbuctoo_dataset['dataset_id']
    collection_id = timbuctoo_dataset['collection_id']
    timbuctoo_graphql = timbuctoo_dataset['timbuctoo_graphql']

    del timbuctoo_dataset['dataset_id']
    del timbuctoo_dataset['collection_id']
    del timbuctoo_dataset['timbuctoo_graphql']

    config['dataset'] = {
        'type': 'timbuctoo',
        'graphql_endpoint': timbuctoo_graphql,
        'timbuctoo_id': dataset_id,
        'entity_type_id': collection_id
    }
