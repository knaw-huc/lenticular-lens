from config_db import execute_query, run_query
# from helpers import hash_string
from hashlib import md5
from psycopg2 import sql as psycopg2_sql


def hash_string(to_hash):
    return md5(to_hash.encode('utf-8')).hexdigest()


def get_node_values(uris, query_data):
    sqls = []

    uris = [uri.replace('<', '').replace('>', '') for uri in uris]

    for graph_set in query_data:
        for datatype_set in graph_set['data']:
            table_info = get_table_info(graph_set['graph'], datatype_set['entity_type'])
            if table_info:
                for property_name in datatype_set['properties']:
                    column_name = get_column_name(property_name)
                    template = '''
                    SELECT uri AS resource, {graph_name} AS dataset, {property_literal} AS property, 
                    jsonb_array_elements_text({property_name}) AS value
                    FROM {table_name}
                    WHERE uri IN %(uris)s
                    ''' if table_info[1][column_name]['LIST'] else '''
                    SELECT uri AS resource, {graph_name} AS dataset, {property_literal} AS property, 
                    {property_name} AS value
                    FROM {table_name}
                    WHERE uri IN %(uris)s
                    '''

                    sql = psycopg2_sql.SQL(template).format(
                        graph_name=psycopg2_sql.Literal(graph_set['graph']),
                        property_literal=psycopg2_sql.Literal(property_name),
                        property_name=psycopg2_sql.Identifier(column_name),
                        table_name=psycopg2_sql.Identifier(table_info[0]),
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

    return result if result else result


def get_column_name(property_name):
    return hash_string(property_name.lower())


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
