from collections import defaultdict
from common.config_db import execute_query, run_query
from psycopg2 import sql as psycopg2_sql
from common.helpers import hash_string


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
                for property_name in datatype_set['properties']:
                    column_name = get_column_name(property_name)
                    property_selection = psycopg2_sql.SQL('jsonb_array_elements_text({column_name})'). \
                        format(column_name=psycopg2_sql.Identifier(column_name)) \
                        if table_info['columns'][column_name]['LIST'] \
                        else psycopg2_sql.Identifier(column_name)

                    sql = psycopg2_sql.SQL('''
                    SELECT uri AS resource, {graph_name} AS dataset, {property} AS property, {value} AS value
                    FROM {table_name}
                    WHERE uri IN %(uris)s''').format(
                        graph_name=psycopg2_sql.Literal(graph_set['graph']),
                        property=psycopg2_sql.Literal(property_name),
                        value=property_selection,
                        table_name=psycopg2_sql.Identifier(table_info['table_name']),
                    )

                    sqls.append(sql)

                    # TODO: Work in progress
                    # for property_path in datatype_set['properties']:
                    #     joins = []
                    #
                    # resource = table_info['table_name']
                    # while len(property_path) > 1:
                    #     property = property_path.pop(0)
                    #     # TODO
                    #
                    #
                    # property_name = property_path[0]
                    # column_name = get_column_name(property_name)
                    #
                    # property_selection = psycopg2_sql.SQL('jsonb_array_elements_text({column_name})'). \
                    #     format(column_name=psycopg2_sql.Identifier(column_name)) \
                    #     if table_info['columns'][column_name]['LIST'] \
                    #     else psycopg2_sql.Identifier(column_name)
                    #
                    # sql = psycopg2_sql.SQL('''
                    # SELECT t.uri AS resource, {graph_name} AS dataset, {property} AS property, {value} AS value
                    # FROM {table_name} AS t
                    # {joins}
                    # WHERE t.uri IN %(uris)s
                    # ''').format(
                    #     graph_name=psycopg2_sql.Literal(graph_set['graph']),
                    #     property=psycopg2_sql.Literal(property_name),
                    #     value=property_selection,
                    #     joins=psycopg2_sql.Composable(joins),
                    #     table_name=psycopg2_sql.Identifier(table_info['table_name']),
                    # )
                    #
                    # sqls.append(sql)

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
                                if target['dataset'] == row_dict['dataset'] and target['property'] == row_dict['property']]
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
