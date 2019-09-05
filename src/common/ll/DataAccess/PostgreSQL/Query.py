from collections import defaultdict
from psycopg2 import sql as psycopg2_sql

from common.helpers import hash_string
from common.config_db import execute_query, run_query
from common.property_field import PropertyField


def get_resource_value(resources, targets):
    """
    :param resources    : LIST OF RESOURCE URI FOR WHICH DATA NEEDS TO BE EXTRACTED
    :param targets      : A DICTIONARY WITH THE FOLLOWING KEYS
    :return             :

    DESCRIPTION OF THE PROPERTIES FOR NODE'S LABEL VISUALISATION OBJECT
    ------------------------------------------------------------------
    targets =
    [
        {
            graph           : THE DATASET URI
            data =
                [
                    entity_type : THE ENTITY TYPE OF INTEREST
                    properties  : THE PROPERTIES SELECTED BY THE USER FOR THE ABOVE TYPE
                ]
        },
        ...
    ]
    """
    return get_node_values(resources, targets)


def get_node_values(uris, query_data):
    sqls = []

    uris = [uri.replace('<', '').replace('>', '') for uri in uris]

    for graph_set in query_data:
        for datatype_set in graph_set['data']:
            table_info = get_table_info(graph_set['graph'], datatype_set['entity_type'])
            if table_info:
                for property_path in datatype_set['properties']:
                    joins = []
                    resource = table_info['table_name']

                    cur_resource = 'target'
                    cur_columns = table_info['columns']

                    if type(property_path) is list:
                        while len(property_path) > 1:
                            column = property_path.pop(0)
                            target_resource = property_path.pop(0)

                            next_table_info = get_table_info(graph_set['graph'], target_resource)
                            next_resource = hash_string(cur_resource + '_' + target_resource + '_' + column)

                            local_property = PropertyField(column, parent_label=cur_resource, columns=cur_columns)
                            remote_property = PropertyField('uri', parent_label=next_resource,
                                                            columns=next_table_info['columns'])

                            if local_property.is_list:
                                joins.append(local_property.left_join)

                            lhs = local_property.sql
                            rhs = remote_property.sql

                            joins.append(psycopg2_sql.SQL('\nLEFT JOIN {target} AS {alias}\nON {lhs} = {rhs}').format(
                                target=psycopg2_sql.Identifier(next_table_info['table_name']),
                                alias=psycopg2_sql.Identifier(next_resource),
                                lhs=lhs, rhs=rhs
                            ))

                            cur_resource = next_resource
                            cur_columns = next_table_info['columns']

                        property_name = property_path[0]
                    else:
                        property_name = property_path

                    property = PropertyField(property_name, parent_label=cur_resource, columns=cur_columns)

                    sql = psycopg2_sql.SQL('''
                    SELECT target.uri AS resource, {graph_name} AS dataset, {property} AS property, {value} AS value
                    FROM {table_name} AS target 
                    {joins}
                    WHERE target.uri IN %(uris)s
                    ''').format(
                        graph_name=psycopg2_sql.Literal(graph_set['graph']),
                        property=psycopg2_sql.Literal(property_name),
                        value=property.sql,
                        joins=psycopg2_sql.Composed(joins),
                        table_name=psycopg2_sql.Identifier(resource),
                    )

                    sqls.append(sql)

    union_sql = psycopg2_sql.SQL('\nUNION ALL\n').join(sqls)

    return {
        'query': union_sql,
        'header': ('resource', 'dataset', 'property', 'value'),
        'parameters': {'uris': tuple(uris)}
    }


def get_table_info(dataset_id, collection_id):
    result = run_query(
        'SELECT table_name, columns FROM timbuctoo_tables WHERE dataset_id = %s AND collection_id = %s',
        (dataset_id, collection_id)
    )

    return {'table_name': result[0], 'columns': result[1]} if result else result


def get_column_name(property_name):
    return hash_string(property_name.lower())


def get_values_for(resources, targets):
    query = get_resource_value(resources, targets)
    result = execute_query(query)

    response = defaultdict(list)
    res_idx = result[0].index('resource')
    for row in result[1:]:
        row_dict = {label: row[idx] for idx, label in enumerate(result[0])}
        del row_dict['resource']

        if row_dict['value']:
            targets = response[row[res_idx]]
            matching_targets = [target for target in targets
                                if target['dataset'] == row_dict['dataset']
                                and target['property'] == row_dict['property']]
            if matching_targets:
                matching_targets[0]['values'].append(row_dict['value'])
            else:
                row_dict['values'] = [row_dict['value']]
                del row_dict['value']
                targets.append(row_dict)

    return response


if __name__ == '__main__':
    test_query_data = [
        {
            "graph": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_begraafregisters",
            "data": [
                {
                    "entity_datatype": "saaOnt_Person",
                    "properties": [
                        "saaOnt_full_name",
                        "saaOnt_first_name",
                    ]
                }
            ]
        },
        {
            "graph": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_ondertrouwregister",
            "data": [
                {
                    "entity_datatype": "saaOnt_Person",
                    "properties": [
                        "saaOnt_full_nameList",
                    ]
                }
            ]
        },
    ]

    test_uris = [
        "http://goldenagents.org/uva/SAA/person/IndexOpBegraafregistersVoor1811/saaId11146456p2",
        "http://goldenagents.org/uva/SAA/person/IndexOpOndertrouwregister/saaId26543348p1",
        "http://goldenagents.org/uva/SAA/person/IndexOpBegraafregistersVoor1811/saaId10159286p1",
    ]

    print(get_node_values(test_query_data, test_uris))
